from datetime import timedelta

from django.test import Client, TestCase
from django.utils import timezone

from appointments.models import Appointment
from core.testing import login_2fa_verified, make_doctor, make_patient, make_staff


class AppointmentAPITests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.doctor = make_doctor()
        self.patient = make_patient()
        self.other_patient = make_patient()
        self.receptionist = make_staff()
        self.future = (timezone.now().date() + timedelta(days=10)).isoformat()

    def _payload(self, **overrides):
        data = {
            'patient': self.other_patient.id,
            'doctor': self.doctor.id,
            'appointment_date': self.future,
            'appointment_time': '09:30',
            'reason': 'Headache',
        }
        data.update(overrides)
        return data

    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get('/api/appointments/').status_code, 403)

    def test_pagination_envelope(self):
        self.client.force_login(self.receptionist)
        response = self.client.get('/api/appointments/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json().keys()),
            {'count', 'next', 'previous', 'results'},
        )

    def test_patient_only_sees_own_appointments(self):
        own = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='08:00',
        )
        Appointment.objects.create(
            patient=self.other_patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='08:30',
        )
        self.client.force_login(self.patient.user)
        response = self.client.get('/api/appointments/')
        self.assertEqual([row['id'] for row in response.json()['results']], [own.id])

    def test_patient_booking_is_forced_to_own_profile_and_pending(self):
        self.client.force_login(self.patient.user)
        response = self.client.post(
            '/api/appointments/', self._payload(), content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        created = Appointment.objects.get(id=response.json()['id'])
        self.assertEqual(created.patient, self.patient)
        self.assertEqual(created.status, 'pending')

    def test_patient_cannot_approve(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='10:00',
        )
        self.client.force_login(self.patient.user)
        response = self.client.patch(
            f'/api/appointments/{appointment.id}/',
            {'status': 'approved'}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'pending')

    def test_patient_can_cancel(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='10:30',
        )
        self.client.force_login(self.patient.user)
        response = self.client.patch(
            f'/api/appointments/{appointment.id}/',
            {'status': 'cancelled'}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')

    def test_past_date_is_rejected(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(
            '/api/appointments/',
            self._payload(
                appointment_date=(timezone.now().date() - timedelta(days=1)).isoformat()
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_slot_conflict_is_rejected(self):
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='09:30',
        )
        self.client.force_login(self.receptionist)
        response = self.client.post(
            '/api/appointments/', self._payload(), content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_doctor_cannot_create_appointments(self):
        login_2fa_verified(self.client, self.doctor.user)
        response = self.client.post(
            '/api/appointments/', self._payload(), content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_unsupported_api_version_is_rejected(self):
        self.client.force_login(self.receptionist)
        response = self.client.get('/api/appointments/', HTTP_ACCEPT='application/json; version=v9')
        self.assertEqual(response.status_code, 406)

    def test_page_size_is_applied_and_capped(self):
        for _ in range(105):
            Appointment.objects.create(
                patient=self.patient, doctor=self.doctor,
                appointment_date=self.future, appointment_time='09:30',
                status='cancelled',
            )
        self.client.force_login(self.receptionist)

        small = self.client.get('/api/appointments/?page_size=5')
        self.assertEqual(len(small.json()['results']), 5)
        self.assertEqual(small.json()['count'], 105)

        capped = self.client.get('/api/appointments/?page_size=500')
        self.assertEqual(len(capped.json()['results']), 100)

    def test_doctor_search_matches_name(self):
        matching = make_doctor(first_name='Zara', last_name='Searchme')
        self.client.force_login(self.receptionist)

        response = self.client.get('/api/doctors/?search=Searchme')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row['id'] for row in response.json()['results']], [matching.id],
        )

    def test_appointment_ordering_param(self):
        base = timezone.now().date() + timedelta(days=20)
        dates = [base + timedelta(days=3), base + timedelta(days=1), base + timedelta(days=2)]
        for date in dates:
            Appointment.objects.create(
                patient=self.patient, doctor=self.doctor,
                appointment_date=date, appointment_time='11:00',
            )
        self.client.force_login(self.receptionist)

        response = self.client.get('/api/appointments/?ordering=appointment_date')

        self.assertEqual(
            [row['appointment_date'] for row in response.json()['results']],
            sorted(date.isoformat() for date in dates),
        )

    def test_doctor_only_sees_own_appointments(self):
        other_doctor = make_doctor()
        own = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='12:00',
        )
        Appointment.objects.create(
            patient=self.patient, doctor=other_doctor,
            appointment_date=self.future, appointment_time='12:30',
        )
        login_2fa_verified(self.client, self.doctor.user)

        response = self.client.get('/api/appointments/')

        self.assertEqual([row['id'] for row in response.json()['results']], [own.id])

    def test_patient_only_sees_own_profile(self):
        self.client.force_login(self.patient.user)

        response = self.client.get('/api/patients/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row['id'] for row in response.json()['results']], [self.patient.id],
        )

    def test_delete_is_admin_only(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='13:00',
        )
        url = f'/api/appointments/{appointment.id}/'

        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())

        login_2fa_verified(self.client, make_staff('admin'))
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Appointment.objects.filter(pk=appointment.pk).exists())
