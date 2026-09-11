import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from django_otp.plugins.otp_totp.models import TOTPDevice


def get_user_totp_device(user):
    """Get the user's TOTP device if it exists."""
    devices = TOTPDevice.objects.filter(user=user, confirmed=True)
    return devices.first()


def create_totp_device(user):
    """
    Create a new TOTP device for the user.
    Deletes any existing unconfirmed devices first.
    """
    # Remove any unconfirmed devices
    TOTPDevice.objects.filter(user=user, confirmed=False).delete()

    # Create new device
    device = TOTPDevice.objects.create(
        user=user,
        name=f'{user.email} - SHMS',
        confirmed=False
    )
    return device


def get_qr_code_base64(device, user):
    """
    Generate a QR code image for the device.
    Returns base64-encoded PNG image.
    """
    # Build the OTP auth URI
    issuer = 'SHMS Hospital'
    uri = device.config_url

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    # Convert to base64 PNG
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_base64


def user_requires_2fa(user):
    """Check if this user's role requires 2FA."""
    return user.role in ('admin', 'doctor')


def user_has_2fa_enabled(user):
    """Check if user has a confirmed 2FA device."""
    return TOTPDevice.objects.filter(user=user, confirmed=True).exists()


def user_is_2fa_verified(request):
    """Check if user has completed 2FA verification this session."""
    return request.session.get('2fa_verified', False)