from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from appointments.models import Appointment
from core.testing import make_doctor, make_patient, make_staff

from .models import Notification
from .services import notify


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SMS_BACKEND='notifications.channels.ConsoleSMSBackend',
)
class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.patient = make_patient()
        mail.outbox = []

    def test_in_app_and_email_delivery(self):
        notification = notify(self.patient.user, 'Your results are ready.', category='lab')
        self.assertEqual(self.patient.user.notifications.count(), 1)
        self.assertEqual(notification.category, 'lab')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Your results are ready.', mail.outbox[0].body)

    def test_email_opt_out(self):
        self.patient.user.email_notifications = False
        self.patient.user.save(update_fields=['email_notifications'])
        notify(self.patient.user, 'Silent in-app only.', category='system')
        self.assertEqual(self.patient.user.notifications.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_sms_opt_in_uses_backend(self):
        self.patient.user.phone = '08030000000'
        self.patient.user.sms_notifications = True
        self.patient.user.save(update_fields=['phone', 'sms_notifications'])
        with mock.patch('notifications.services.send_sms') as send_sms:
            notify(self.patient.user, 'Appointment reminder.', category='appointment')
        send_sms.assert_called_once_with('08030000000', 'Appointment reminder.')

    def test_preferences_page_round_trip(self):
        self.client.force_login(self.patient.user)
        response = self.client.get('/notifications/preferences/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/notifications/preferences/', {
            'email_notifications': '',
            'sms_notifications': 'on',
            'whatsapp_notifications': '',
        })
        self.assertEqual(response.status_code, 302)
        self.patient.user.refresh_from_db()
        self.assertFalse(self.patient.user.email_notifications)
        self.assertTrue(self.patient.user.sms_notifications)

    def test_appointment_creation_notifies_doctor_and_receptionists(self):
        receptionist = make_staff()
        doctor = make_doctor()
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=doctor,
            appointment_date=timezone.now().date() + timedelta(days=5),
            appointment_time='14:00',
        )
        self.assertTrue(
            doctor.user.notifications.filter(category='appointment').exists()
        )
        self.assertTrue(
            receptionist.notifications.filter(category='appointment').exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                message__contains=appointment.patient.user.get_full_name()
            ).exists()
        )
        self.assertGreaterEqual(len(mail.outbox), 2)
