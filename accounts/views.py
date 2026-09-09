from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from .forms import PatientRegistrationForm


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