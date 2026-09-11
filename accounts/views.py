from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from .forms import PatientRegistrationForm
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import PatientRegistrationForm
from .two_factor import (
    get_user_totp_device,
    create_totp_device,
    get_qr_code_base64,
    user_requires_2fa,
    user_has_2fa_enabled,
    user_is_2fa_verified,
)
from core.audit import log_action



@login_required
def role_redirect_view(request):
    user = request.user

    has_doctor = hasattr(user, 'doctor_profile')
    has_patient = hasattr(user, 'patient_profile')
    is_admin = user.role == 'admin'
    is_receptionist = user.role == 'receptionist'

    # Admin and Receptionist go directly
    if is_admin:
        return redirect('dashboard:admin_home')
    if is_receptionist:
        return redirect('dashboard:receptionist_home')

    # If user has BOTH profiles
    if has_doctor and has_patient:
        # Check if they already chose a role this session
        active_role = request.session.get('active_role')
        if active_role == 'doctor' and has_doctor:
            return redirect('dashboard:doctor_home')
        elif active_role == 'patient' and has_patient:
            return redirect('dashboard:patient_home')
        else:
            # No session choice yet — show choose role page
            return redirect('accounts:choose_role')

    # Single profile — go directly
    if has_doctor:
        return redirect('dashboard:doctor_home')
    if has_patient:
        return redirect('dashboard:patient_home')

    return redirect('accounts:login')


@login_required
def choose_role_view(request):
    user = request.user

    has_doctor = hasattr(user, 'doctor_profile')
    has_patient = hasattr(user, 'patient_profile')

    # Only users with multiple profiles should reach this page
    if not (has_doctor and has_patient):
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        selected_role = request.POST.get('role')

        # Backend security check — verify role actually exists
        if selected_role == 'doctor' and has_doctor:
            request.session['active_role'] = 'doctor'
            return redirect('dashboard:doctor_home')
        elif selected_role == 'patient' and has_patient:
            request.session['active_role'] = 'patient'
            return redirect('dashboard:patient_home')
        else:
            raise PermissionDenied

    return render(request, 'accounts/choose_role.html', {
        'has_doctor': has_doctor,
        'has_patient': has_patient,
    })


def register_patient(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            from patients.models import PatientProfile
            PatientProfile.objects.create(
                user=user,
                date_of_birth='2000-01-01',
                gender='other'
            )

            login(request, user)
            return redirect('dashboard:patient_home')
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

#TWO FACTOR AUTHENTICATION

@login_required
def role_redirect_view(request):
    user = request.user

    has_doctor = hasattr(user, 'doctor_profile')
    has_patient = hasattr(user, 'patient_profile')
    is_admin = user.role == 'admin'
    is_receptionist = user.role == 'receptionist'

    # Check if this user requires 2FA
    if user_requires_2fa(user):
        # If 2FA not set up yet — send to setup
        if not user_has_2fa_enabled(user):
            return redirect('accounts:setup_2fa')
        # If 2FA set up but not verified this session — send to verify
        if not user_is_2fa_verified(request):
            return redirect('accounts:verify_2fa')

    # Admin and Receptionist go directly
    if is_admin:
        return redirect('dashboard:admin_home')
    if is_receptionist:
        return redirect('dashboard:receptionist_home')

    # Multi-profile check
    if has_doctor and has_patient:
        active_role = request.session.get('active_role')
        if active_role == 'doctor' and has_doctor:
            return redirect('dashboard:doctor_home')
        elif active_role == 'patient' and has_patient:
            return redirect('dashboard:patient_home')
        else:
            return redirect('accounts:choose_role')

    if has_doctor:
        return redirect('dashboard:doctor_home')
    if has_patient:
        return redirect('dashboard:patient_home')

    return redirect('accounts:login')


@login_required
def setup_2fa(request):
    """Allow admin/doctor to set up 2FA."""
    user = request.user

    if not user_requires_2fa(user):
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()

        if device and device.verify_token(code):
            device.confirmed = True
            device.save()
            request.session['2fa_verified'] = True

            log_action(
                request,
                action='update',
                model_name='TOTPDevice',
                object_id=device.id,
                object_repr=f'2FA enabled for {user.email}',
                details='2FA setup completed successfully.'
            )

            messages.success(request, '2FA has been enabled successfully.')
            return redirect('accounts:role_redirect')
        else:
            messages.error(request, 'Invalid code. Please try again.')

    # Create a new device and show QR code
    device = create_totp_device(user)
    qr_code = get_qr_code_base64(device, user)

    return render(request, 'accounts/setup_2fa.html', {
        'qr_code': qr_code,
        'secret_key': device.bin_key.hex(),
    })


@login_required
def verify_2fa(request):
    """Verify 2FA code during login."""
    user = request.user

    if not user_requires_2fa(user):
        return redirect('accounts:role_redirect')

    if not user_has_2fa_enabled(user):
        return redirect('accounts:setup_2fa')

    if user_is_2fa_verified(request):
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        device = get_user_totp_device(user)

        if device and device.verify_token(code):
            request.session['2fa_verified'] = True

            log_action(
                request,
                action='login',
                details=f'2FA verification successful for {user.email}'
            )

            messages.success(request, '2FA verified successfully.')
            return redirect('accounts:role_redirect')
        else:
            log_action(
                request,
                action='login_failed',
                details=f'Failed 2FA attempt for {user.email}'
            )
            messages.error(request, 'Invalid code. Please try again.')

    return render(request, 'accounts/verify_2fa.html')


@login_required
def disable_2fa(request):
    """Allow user to disable 2FA."""
    user = request.user

    if not user_requires_2fa(user):
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        TOTPDevice.objects.filter(user=user).delete()
        request.session.pop('2fa_verified', None)

        log_action(
            request,
            action='update',
            model_name='TOTPDevice',
            object_repr=f'2FA disabled for {user.email}',
            details='2FA disabled by user.'
        )

        messages.success(request, '2FA has been disabled.')
        return redirect('accounts:role_redirect')

    return render(request, 'accounts/disable_2fa.html')


@login_required
def choose_role_view(request):
    user = request.user
    has_doctor = hasattr(user, 'doctor_profile')
    has_patient = hasattr(user, 'patient_profile')

    if not (has_doctor and has_patient):
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        selected_role = request.POST.get('role')
        if selected_role == 'doctor' and has_doctor:
            request.session['active_role'] = 'doctor'
            return redirect('dashboard:doctor_home')
        elif selected_role == 'patient' and has_patient:
            request.session['active_role'] = 'patient'
            return redirect('dashboard:patient_home')
        else:
            raise PermissionDenied

    return render(request, 'accounts/choose_role.html', {
        'has_doctor': has_doctor,
        'has_patient': has_patient,
    })


def register_patient(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            from patients.models import PatientProfile
            PatientProfile.objects.create(
                user=user,
                date_of_birth='2000-01-01',
                gender='other'
            )
            login(request, user)
            return redirect('dashboard:patient_home')
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})