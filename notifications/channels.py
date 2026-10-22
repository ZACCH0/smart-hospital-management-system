import logging

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class ConsoleSMSBackend:
    """Development backend: writes the SMS to the server log."""

    def send(self, phone, message):
        logger.info('[SMS -> %s] %s', phone, message)
        return True


class ConsoleWhatsAppBackend:
    """Development backend: writes the WhatsApp message to the server log."""

    def send(self, phone, message):
        logger.info('[WhatsApp -> %s] %s', phone, message)
        return True


def _load_backend(kind, default):
    path = getattr(settings, f'{kind.upper()}_BACKEND', '')
    if not path:
        return default()
    if callable(path):
        return path()
    return import_string(path)()


def get_sms_backend():
    return _load_backend('SMS', ConsoleSMSBackend)


def get_whatsapp_backend():
    return _load_backend('WHATSAPP', ConsoleWhatsAppBackend)


def send_sms(phone, message):
    if not phone:
        return False
    try:
        return get_sms_backend().send(phone, message)
    except Exception:
        logger.exception('SMS delivery failed for %s', phone)
        return False


def send_whatsapp(phone, message):
    if not phone:
        return False
    try:
        return get_whatsapp_backend().send(phone, message)
    except Exception:
        logger.exception('WhatsApp delivery failed for %s', phone)
        return False
