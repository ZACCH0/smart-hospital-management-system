from django.core.cache import cache
from django.test import Client, TestCase
from django_otp.plugins.otp_totp.models import TOTPDevice

from core.testing import make_doctor, make_patient, make_staff


class LoginThrottleTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.patient = make_patient()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_repeated_failed_logins_are_throttled(self):
        credentials = {
            'username': self.patient.user.email,
            'password': 'definitely-wrong',
        }
        for _ in range(10):
            response = self.client.post('/accounts/login/', credentials)
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post('/accounts/login/', credentials)
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)


class RoleRedirectTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')

    def test_patient_lands_on_patient_dashboard(self):
        patient = make_patient()
        self.client.force_login(patient.user)
        response = self.client.get('/accounts/redirect/')
        self.assertRedirects(response, '/dashboard/patient/')

    def test_doctor_is_asked_to_set_up_2fa_first(self):
        doctor = make_doctor()
        self.client.force_login(doctor.user)
        response = self.client.get('/accounts/redirect/')
        self.assertRedirects(response, '/accounts/2fa/setup/')

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get('/accounts/redirect/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


class TwoFactorEnforcementTests(TestCase):
    """2FA must gate EVERY app page for admin/doctor, not only the post-login redirect."""

    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')

    def test_unverified_admin_is_bounced_from_app_pages(self):
        admin = make_staff('admin')
        self.client.force_login(admin)
        response = self.client.get('/dashboard/admin/')
        self.assertRedirects(response, '/accounts/2fa/setup/')

    def test_unverified_doctor_is_bounced_from_app_pages(self):
        doctor = make_doctor()
        self.client.force_login(doctor.user)
        response = self.client.get('/dashboard/doctor/')
        self.assertRedirects(response, '/accounts/2fa/setup/')

    def _set_session_flags(self, flags):
        session = self.client.session
        session.update(flags)
        session.save()

    def test_verified_admin_reaches_dashboard(self):
        admin = make_staff('admin')
        self.client.force_login(admin)
        self._set_session_flags({'2fa_verified': True})
        response = self.client.get('/dashboard/admin/')
        self.assertEqual(response.status_code, 200)

    def test_doctor_with_2fa_enabled_goes_to_verify(self):
        doctor = make_doctor()
        TOTPDevice.objects.create(user=doctor.user, name='default', confirmed=True)
        self.client.force_login(doctor.user)
        response = self.client.get('/dashboard/doctor/')
        self.assertRedirects(response, '/accounts/2fa/verify/')

    def test_demo_admin_bypasses_2fa_gate(self):
        admin = make_staff('admin')
        self.client.force_login(admin)
        self._set_session_flags({'is_demo': True})
        response = self.client.get('/dashboard/admin/')
        self.assertEqual(response.status_code, 200)

    def test_patient_is_not_gated(self):
        patient = make_patient()
        self.client.force_login(patient.user)
        response = self.client.get('/dashboard/patient/')
        self.assertEqual(response.status_code, 200)

    def test_receptionist_is_not_gated(self):
        staff = make_staff('receptionist')
        self.client.force_login(staff)
        response = self.client.get('/dashboard/receptionist/')
        self.assertEqual(response.status_code, 200)

    def test_2fa_setup_page_reachable_while_unverified(self):
        admin = make_staff('admin')
        self.client.force_login(admin)
        response = self.client.get('/accounts/2fa/setup/')
        self.assertEqual(response.status_code, 200)

    def test_logout_reachable_while_unverified(self):
        admin = make_staff('admin')
        self.client.force_login(admin)
        response = self.client.post('/accounts/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')

    def test_demo_exit_is_a_post_form(self):
        """The demo bar's Exit must be a POST form (Django 5 LogoutView rejects GET)."""
        patient = make_patient()
        self.client.force_login(patient.user)
        self._set_session_flags({'is_demo': True})
        response = self.client.get('/dashboard/patient/')
        self.assertContains(response, 'method="post" action="/accounts/logout/"')
