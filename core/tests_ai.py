import json
from unittest import mock
from urllib.error import URLError

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.ai import suggest_department
from core.testing import login_2fa_verified, make_doctor, make_patient
from doctors.models import Specialty


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

    def test_admin_added_specialty_drives_routing(self):
        Specialty.objects.create(
            name='ENT', slug='ent', keywords='ear pain, sore throat, sinus', order=20,
        )
        result = suggest_department('sore throat with blocked sinus')
        self.assertEqual(result['department'], 'ent')
        self.assertEqual(result['department_label'], 'ENT')

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
        cardiologist = make_doctor(specialization='cardiology')

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

    def test_doctor_of_admin_added_specialty_is_listed(self):
        ent = Specialty.objects.create(
            name='ENT', slug='ent', keywords='ear pain, sore throat, sinus', order=20,
        )
        doctor = make_doctor(specialization=ent)

        self.client.force_login(self.patient.user)
        response = self.client.post(
            reverse('patients:health_assistant'),
            {'symptoms': 'sore throat with blocked sinus'},
        )

        self.assertEqual(response.context['result']['department'], 'ent')
        self.assertIn(doctor, response.context['doctors'])

    def test_doctor_cannot_use_patient_assistant(self):
        login_2fa_verified(self.client, self.doctor_user.user)
        response = self.client.get(reverse('patients:health_assistant'))
        self.assertEqual(response.status_code, 403)


@override_settings(AI_API_KEY='')
class HomepageChatTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.url = reverse('ai_chat')

    def post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_empty_message_is_rejected(self):
        response = self.post({'message': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_oversized_message_is_rejected(self):
        response = self.post({'message': 'x' * 501})
        self.assertEqual(response.status_code, 400)

    def test_rules_fallback_without_key(self):
        response = self.post({'message': 'How do I book an appointment?'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['source'], 'rules')
        self.assertIn('not a diagnosis', data['reply'])
        self.assertTrue(data['disclaimer'])

    def test_urgent_symptoms_get_emergency_fallback(self):
        response = self.post({'message': 'I have severe chest pain'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('emergency', response.json()['reply'].lower())

    @mock.patch('core.views.answer_question')
    def test_ai_answer_is_returned(self, answer_question):
        answer_question.return_value = {
            'reply': 'Book from your patient dashboard.',
            'source': 'ai',
            'disclaimer': 'General guidance only.',
        }
        response = self.post({'message': 'How do I book?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reply'], 'Book from your patient dashboard.')
        self.assertEqual(response.json()['source'], 'ai')
        answer_question.assert_called_once_with('How do I book?')

    def test_homepage_widget_is_wired_to_backend(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, '/ai/chat/')
        self.assertContains(response, 'aiCsrfToken')
        self.assertNotContains(response, 'generativelanguage.googleapis.com')
        self.assertNotContains(response, 'const apiKey')
