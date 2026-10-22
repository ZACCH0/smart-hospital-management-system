from decimal import Decimal

from django.test import Client, TestCase

from core.testing import make_doctor, make_patient, make_staff

from .models import LabResult, LabTest


class LaboratoryTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.receptionist = make_staff()
        self.doctor = make_doctor()
        self.patient = make_patient()
        self.client.force_login(self.receptionist)
        self.test = LabTest.objects.create(
            patient=self.patient, doctor=self.doctor, test_name='Full Blood Count',
        )

    def test_collect_sample_assigns_technician(self):
        self.client.post(f'/laboratory/{self.test.id}/collect/')
        self.test.refresh_from_db()
        self.assertEqual(self.test.sample_status, 'collected')
        self.assertEqual(self.test.status, 'in_progress')
        self.assertEqual(self.test.technician, self.receptionist)
        self.assertIsNotNone(self.test.sample_collected_at)

    def test_reject_sample(self):
        self.client.post(f'/laboratory/{self.test.id}/reject/')
        self.test.refresh_from_db()
        self.assertEqual(self.test.sample_status, 'rejected')

    def test_result_abnormal_flag_and_completion(self):
        self.client.post(f'/laboratory/{self.test.id}/result/', {
            'result': 'Haemoglobin low',
            'result_value': '9.5',
            'unit': 'g/dL',
            'reference_low': '12',
            'reference_high': '16',
        })
        self.test.refresh_from_db()
        result = LabResult.objects.get(lab_test=self.test)
        self.assertEqual(self.test.status, 'completed')
        self.assertEqual(self.test.sample_status, 'collected')
        self.assertTrue(result.is_abnormal)
        self.assertEqual(result.reference_range_display, '12.00 – 16.00')

    def test_invalid_reference_range_is_rejected(self):
        self.client.post(f'/laboratory/{self.test.id}/result/', {
            'result': 'x',
            'result_value': '5',
            'reference_low': '10',
            'reference_high': '2',
        })
        self.assertFalse(LabResult.objects.filter(lab_test=self.test).exists())

    def test_patient_sees_only_own_tests(self):
        make_patient()
        patient_client = Client(SERVER_NAME='localhost')
        patient_client.force_login(self.patient.user)
        response = patient_client.get('/laboratory/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['tests']), [self.test])
