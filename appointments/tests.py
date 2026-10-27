from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.testing import login_2fa_verified, make_doctor, make_patient, make_staff

from .models import Appointment


class AppointmentRuleTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.doctor = make_doctor()
        self.patient = make_patient()
        self.other_patient = make_patient()
        self.receptionist = make_staff()
        self.future = timezone.now().date() + timedelta(days=30)

    def test_active_slot_cannot_be_double_booked(self):
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='10:00',
        )
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.other_patient, doctor=self.doctor,
                appointment_date=self.future, appointment_time='10:00',
            )

    def test_cancelled_slot_can_be_rebooked(self):
        first = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='11:00',
            status='cancelled',
        )
        second = Appointment.objects.create(
            patient=self.other_patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='11:00',
        )
        self.assertNotEqual(first.id, second.id)

    def test_past_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.patient, doctor=self.doctor,
                appointment_date=timezone.now().date() - timedelta(days=1),
                appointment_time='09:00',
            )

    def test_unavailable_doctor_cannot_be_booked(self):
        self.doctor.available = False
        self.doctor.save(update_fields=['available'])
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.patient, doctor=self.doctor,
                appointment_date=self.future, appointment_time='12:00',
            )

    def test_past_appointments_can_be_approved_without_crash(self):
        appt = Appointment(
            patient=self.patient, doctor=self.doctor,
            appointment_date=timezone.now().date() - timedelta(days=2),
            appointment_time='09:00',
            status='pending',
        )
        appt.save(validate_rules=False)
        self.client.force_login(self.receptionist)
        response = self.client.get(
            reverse('appointments:approve_appointment', args=[appt.id])
        )
        self.assertEqual(response.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, 'approved')

    def test_doctor_only_sees_own_appointments_in_api(self):
        other_doctor = make_doctor()
        mine = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='13:00',
        )
        Appointment.objects.create(
            patient=self.patient, doctor=other_doctor,
            appointment_date=self.future, appointment_time='13:00',
        )
        login_2fa_verified(self.client, self.doctor.user)
        response = self.client.get('/api/appointments/')
        ids = [row['id'] for row in response.json()['results']]
        self.assertEqual(ids, [mine.id])


class TelehealthTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.doctor = make_doctor()
        self.other_doctor = make_doctor()
        self.patient = make_patient()
        self.other_patient = make_patient()
        self.receptionist = make_staff()
        self.future = timezone.now().date() + timedelta(days=14)

    def make_video(self, status='approved', patient=None, doctor=None):
        return Appointment.objects.create(
            patient=patient or self.patient,
            doctor=doctor or self.doctor,
            appointment_date=self.future,
            appointment_time='10:30',
            consultation_type='video',
            status=status,
        )

    def test_video_appointment_generates_room_and_url(self):
        appt = self.make_video()
        self.assertTrue(appt.video_room)
        self.assertTrue(appt.video_url.startswith(settings.TELEHEALTH_MEETING_BASE_URL))
        self.assertTrue(appt.video_url.endswith(appt.video_room))

    def test_in_person_appointment_has_no_video_room(self):
        appt = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=self.future, appointment_time='11:30',
        )
        self.assertEqual(appt.video_room, '')
        self.assertEqual(appt.video_url, '')
        self.assertFalse(appt.is_video)

    def test_switching_to_in_person_clears_room(self):
        appt = self.make_video()
        appt.consultation_type = 'in_person'
        appt.save()
        self.assertEqual(appt.video_room, '')
        self.assertEqual(appt.video_url, '')

    def test_patient_sees_join_link_only_when_approved(self):
        appt = self.make_video(status='pending')
        self.client.force_login(self.patient.user)
        pending = self.client.get(reverse('patients:my_appointments')).content.decode()
        self.assertNotIn(reverse('appointments:telehealth_join', args=[appt.id]), pending)

        appt.status = 'approved'
        appt.save()
        approved = self.client.get(reverse('patients:my_appointments')).content.decode()
        self.assertIn(reverse('appointments:telehealth_join', args=[appt.id]), approved)

    def test_owning_patient_is_redirected_to_meeting(self):
        appt = self.make_video()
        self.client.force_login(self.patient.user)
        response = self.client.get(reverse('appointments:telehealth_join', args=[appt.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, appt.video_url)

    def test_other_patient_cannot_join(self):
        appt = self.make_video()
        self.client.force_login(self.other_patient.user)
        response = self.client.get(reverse('appointments:telehealth_join', args=[appt.id]))
        self.assertEqual(response.status_code, 403)

    def test_assigned_doctor_and_receptionist_can_join(self):
        appt = self.make_video()
        login_2fa_verified(self.client, self.doctor.user)
        self.assertEqual(
            self.client.get(reverse('appointments:telehealth_join', args=[appt.id])).status_code,
            302,
        )
        self.client.force_login(self.receptionist)
        self.assertEqual(
            self.client.get(reverse('appointments:telehealth_join', args=[appt.id])).status_code,
            302,
        )

    def test_other_doctor_cannot_join(self):
        appt = self.make_video()
        login_2fa_verified(self.client, self.other_doctor.user)
        response = self.client.get(reverse('appointments:telehealth_join', args=[appt.id]))
        self.assertEqual(response.status_code, 403)

    def test_cancelled_video_cannot_be_joined(self):
        appt = self.make_video(status='cancelled')
        self.client.force_login(self.patient.user)
        response = self.client.get(reverse('appointments:telehealth_join', args=[appt.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('patients:my_appointments'))

    def test_join_is_audited(self):
        from core.models import AuditLog

        appt = self.make_video()
        login_2fa_verified(self.client, self.doctor.user)
        self.client.get(reverse('appointments:telehealth_join', args=[appt.id]))
        self.assertTrue(
            AuditLog.objects.filter(action='access', object_id=str(appt.id)).exists()
        )
