from django import forms
from django.contrib.auth import get_user_model


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email_notifications', 'sms_notifications', 'whatsapp_notifications']
        labels = {
            'email_notifications': 'Email notifications',
            'sms_notifications': 'SMS notifications',
            'whatsapp_notifications': 'WhatsApp notifications',
        }
        help_texts = {
            'email_notifications': 'Appointment, billing and result updates by email.',
            'sms_notifications': 'Short text messages to the phone number on your profile.',
            'whatsapp_notifications': 'WhatsApp messages to the phone number on your profile.',
        }
