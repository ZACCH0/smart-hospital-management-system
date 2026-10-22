from django.db import IntegrityError, transaction
from django.test import Client, TestCase

from core.testing import make_doctor, make_patient, make_staff

from .models import Admission, Bed, Ward


class IPDTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.admin = make_staff('admin')
        self.receptionist = make_staff()
        self.doctor = make_doctor()
        self.patient = make_patient()
        self.ward = Ward.objects.create(name='Ward A', ward_type='general')
        self.bed_one = Bed.objects.create(ward=self.ward, bed_number='01')
        self.bed_two = Bed.objects.create(ward=self.ward, bed_number='02')
        self.client.force_login(self.receptionist)

    def _admit(self, patient=None, bed=None):
        return self.client.post('/ipd/admissions/new/', {
            'patient': (patient or self.patient).id,
            'doctor': self.doctor.id,
            'bed': (bed or self.bed_one).id,
            'diagnosis': 'Severe malaria',
            'notes': '',
        })

    def test_admit_and_discharge_frees_bed(self):
        response = self._admit()
        self.assertEqual(response.status_code, 302)

        admission = Admission.objects.get(bed=self.bed_one)
        self.assertEqual(admission.status, 'admitted')
        self.assertEqual(admission.admitted_by, self.receptionist)
        self.assertTrue(self.bed_one.is_occupied)

        self.client.post(
            f'/ipd/admissions/{admission.id}/discharge/',
            {'discharge_summary': 'Recovered. Follow-up in one week.'},
        )
        admission.refresh_from_db()
        self.assertEqual(admission.status, 'discharged')
        self.assertIsNotNone(admission.discharged_at)
        self.assertFalse(self.bed_one.is_occupied)

    def test_patient_cannot_be_admitted_twice(self):
        self._admit()
        response = self._admit(bed=self.bed_two)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Admission.objects.filter(status='admitted').count(), 1)

    def test_occupied_bed_is_not_offered(self):
        self._admit()
        response = self.client.get('/ipd/admissions/new/')
        beds = response.context['form'].fields['bed'].queryset
        self.assertNotIn(self.bed_one, beds)
        self.assertIn(self.bed_two, beds)

    def test_database_blocks_two_active_admissions_per_bed(self):
        Admission.objects.create(
            patient=self.patient, doctor=self.doctor, bed=self.bed_one,
            diagnosis='First',
        )
        other_patient = make_patient()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Admission.objects.create(
                    patient=other_patient, doctor=self.doctor, bed=self.bed_one,
                    diagnosis='Second',
                )

    def test_patient_can_view_own_admissions(self):
        self._admit()
        patient_client = Client(SERVER_NAME='localhost')
        patient_client.force_login(self.patient.user)
        response = patient_client.get('/ipd/my-admissions/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ward A')
        self.assertEqual(patient_client.get('/ipd/').status_code, 403)
