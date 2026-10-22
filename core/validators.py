import os

from django.conf import settings
from django.core.exceptions import ValidationError

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
DOCUMENT_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}


def _extension(filename):
    return os.path.splitext(filename or '')[1].lower()


def _check_size(upload, limit_mb, label):
    if upload.size > limit_mb * 1024 * 1024:
        raise ValidationError(
            f'{label} is too large. Maximum size is {limit_mb} MB.'
        )


def validate_image_file(upload):
    """Extension, size and real-image check (blocks renamed executables)."""
    if not upload:
        return
    if _extension(upload.name) not in IMAGE_EXTENSIONS:
        raise ValidationError('Upload a JPG, PNG, WEBP or GIF image.')

    _check_size(upload, getattr(settings, 'MAX_IMAGE_UPLOAD_MB', 5), 'Image')

    from PIL import Image

    try:
        image = Image.open(upload)
        image.verify()
    except Exception:
        raise ValidationError('This file is not a valid image.')
    finally:
        upload.seek(0)


def validate_document_file(upload):
    """Extension + size check for lab reports and other attachments."""
    if not upload:
        return
    if _extension(upload.name) not in DOCUMENT_EXTENSIONS:
        raise ValidationError('Upload a PDF or an image (JPG, PNG, WEBP).')

    _check_size(upload, getattr(settings, 'MAX_DOCUMENT_UPLOAD_MB', 10), 'File')

    from PIL import Image

    if _extension(upload.name) in IMAGE_EXTENSIONS:
        try:
            image = Image.open(upload)
            image.verify()
        except Exception:
            raise ValidationError('This file is not a valid image.')
        finally:
            upload.seek(0)
