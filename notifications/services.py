import logging

from django.conf import settings
from django.core.mail import send_mail

from .channels import send_sms, send_whatsapp
from .models import Notification

logger = logging.getLogger(__name__)


def notify(user, message, category='system', email_subject=None, email_body=None):
    """Create an in-app notification and fan it out to enabled channels.

    In-app delivery always happens; email/SMS/WhatsApp follow the user's
    preferences (and the configured backend). Delivery failures never break
    the calling workflow.
    """
    notification = Notification.objects.create(
        user=user,
        message=message,
        category=category,
    )

    if user.email and getattr(user, 'email_notifications', True):
        try:
            send_mail(
                email_subject or 'SHMS notification',
                email_body or message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception:
            logger.exception('Email delivery failed for %s', user.email)

    phone = getattr(user, 'phone', '')
    if phone and getattr(user, 'sms_notifications', False):
        send_sms(phone, message)

    if phone and getattr(user, 'whatsapp_notifications', False):
        send_whatsapp(phone, message)

    return notification


def notify_many(users, message, category='system', **kwargs):
    return [notify(user, message, category=category, **kwargs) for user in users]
