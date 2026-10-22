from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser

from accounts.models import CustomUser
from core.audit import get_client_ip, log_action
from core.models import AuditLog


class AuditLogTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='auditor@example.com', password='x', role='admin',
        )

    def test_log_action_records_actor_and_target(self):
        request = self.factory.post('/somewhere/')
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'

        log_action(
            request, 'create', model_name='Invoice', object_id=42,
            object_repr='Invoice #42', details='Created from test',
        )
        entry = AuditLog.objects.get()
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.action, 'create')
        self.assertEqual(entry.model_name, 'Invoice')
        self.assertEqual(entry.object_id, '42')
        self.assertEqual(entry.object_repr, 'Invoice #42')

    def test_anonymous_actions_store_no_user(self):
        request = self.factory.post('/login/')
        request.user = AnonymousUser()
        log_action(request, 'login_failed', details='bad password')
        self.assertIsNone(AuditLog.objects.get().user)

    def test_forwarded_for_uses_last_hop_only(self):
        request = self.factory.get(
            '/', HTTP_X_FORWARDED_FOR='6.6.6.6, 203.0.113.9',
        )
        self.assertEqual(get_client_ip(request), '203.0.113.9')


class AuditLogViewTests(TestCase):
    def setUp(self):
        from django.test import Client
        from core.testing import make_patient, make_user

        self.client = Client(SERVER_NAME='localhost')
        self.admin = make_user('admin')
        self.patient = make_patient()
        AuditLog.objects.create(
            user=self.admin, action='payment', model_name='Invoice',
            object_id='7', object_repr='Invoice #7', details='Cash received',
            ip_address='203.0.113.9',
        )
        AuditLog.objects.create(
            user=self.patient.user, action='login', details='Patient signed in',
            ip_address='198.51.100.4',
        )

    def test_admin_can_view_the_trail(self):
        self.client.force_login(self.admin)
        response = self.client.get('/audit-log/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invoice #7')
        self.assertContains(response, 'Payment Recorded')

    def test_filter_by_action_and_search(self):
        self.client.force_login(self.admin)
        response = self.client.get('/audit-log/?action=payment')
        self.assertContains(response, 'Invoice #7')
        self.assertNotContains(response, 'Patient signed in')

        response = self.client.get('/audit-log/?q=198.51.100.4')
        self.assertContains(response, 'Patient signed in')
        self.assertNotContains(response, 'Invoice #7')

    def test_non_admin_is_forbidden(self):
        self.client.force_login(self.patient.user)
        self.assertEqual(self.client.get('/audit-log/').status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get('/audit-log/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])
