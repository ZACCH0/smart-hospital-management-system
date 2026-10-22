from unittest import mock
from urllib.error import URLError

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.ai import suggest_department
from core.testing import make_doctor, make_patient


@override_settings(AI_API_KEY='')
class TriageRuleTests(TestCase):
    def test_chest_pain_is_urgent_cardiology(self):
        result = suggest_department('I have chest pain and it spreads to my arm')
        self.assertEqual(result['department'], 'cardiology')
        self.assertEqual(result['urgency'], 'urgent')
        self.assertEqual(result['source'], 'rules')
        self.assertIn('emergency', result['advice'].lower())

    def test_skin_issue_is_routine_dermatology(self):
        result = suggest_department('itchy rash on my arm for a week')
        self.assertEqual(result['department'], 'dermatology')
        self.assertEqual(result['urgency'], 'routine')

    def test_child_symptom_routes_to_pediatrics(self):
        result = suggest_department('my baby has a fever')
        self.assertEqual(result['department'], 'pediatrics')

    def test_vague_symptom_defaults_to_general(self):
        result = suggest_department('I just feel a bit off lately')
        self.assertEqual(result['department'], 'general')
        self.assertEqual(result['urgency'], 'routine')

    def test_blank_symptoms_return_nothing(self):
        self.assertIsNone(suggest_department('   '))

    @override_settings(AI_API_KEY='test-key')
    def test_ai_failure_falls_back_to_rules(self):
        with mock.patch('core.ai.urlrequest.urlopen', side_effect=URLError('down')):
            result = suggest_department('chest pain')
        self.assertEqual(result['source'], 'rules')
        self.assertEqual(result['department'], 'cardiology')


@override_settings(AI_API_KEY='')
class HealthAssistantViewTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.patient = make_patient()
        self.doctor_user = make_doctor()

    def test_patient_can_open_assistant(self):
        self.client.force_login(self.patient.user)
        response = self.client.get(reverse('patients:health_assistant'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Health Assistant')

    def test_post_symptoms_shows_department_and_matching_doctors(self):
        cardiologist = make_doctor()
        cardiologist.specialization = 'cardiology'
        cardiologist.save(update_fields=['specialization'])

        self.client.force_login(self.patient.user)
        response = self.client.post(
            reverse('patients:health_assistant'),
            {'symptoms': 'chest pain and shortness of breath'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result']['department'], 'cardiology')
        self.assertIn(cardiologist, response.context['doctors'])

    def test_empty_submission_shows_error(self):
        self.client.force_login(self.patient.user)
        response = self.client.post(reverse('patients:health_assistant'), {'symptoms': '  '})
        self.assertIsNone(response.context['result'])
        self.assertContains(response, 'Please describe your symptoms first.')

    def test_doctor_cannot_use_patient_assistant(self):
        self.client.force_login(self.doctor_user.user)
        response = self.client.get(reverse('patients:health_assistant'))
        self.assertEqual(response.status_code, 403)
