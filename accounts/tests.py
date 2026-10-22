from django.core.cache import cache
from django.test import Client, TestCase

from core.testing import make_doctor, make_patient


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
