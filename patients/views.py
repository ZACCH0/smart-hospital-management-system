from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm, PatientProfileForm, PatientAppointmentForm
from appointments.models import Appointment


@login_required
def profile_settings(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        return redirect('dashboard:patient_home')

    if request.method == 'POST':
        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        profile_form = PatientProfileForm(
            request.POST,
            instance=patient_profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('patients:profile_settings')
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = PatientProfileForm(instance=patient_profile)

    return render(request, 'patients/profile_settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def book_appointment(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        messages.error(request, 'Please complete your profile first.')
        return redirect('patients:profile_settings')

    if request.method == 'POST':
        form = PatientAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient_profile
            appointment.status = 'pending'
            appointment.save()
            messages.success(request, 'Appointment booked successfully. Awaiting approval.')
            return redirect('patients:my_appointments')
    else:
        form = PatientAppointmentForm()

    return render(request, 'patients/book_appointment.html', {'form': form})


@login_required
def my_appointments(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        return redirect('dashboard:patient_home')

    appointments = patient_profile.appointments.all().order_by('-appointment_date')

    return render(request, 'patients/my_appointments.html', {
        'appointments': appointments
    })

@login_required
def my_medical_records(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        return redirect('dashboard:patient_home')

    records = patient_profile.medical_records.all().order_by('-created_at')
    return render(request, 'patients/my_medical_records.html', {
        'records': records
    })

@login_required
def my_prescriptions(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        return redirect('dashboard:patient_home')

    from prescriptions.models import Prescription
    prescriptions = Prescription.objects.filter(
        medical_record__patient=patient_profile
    ).order_by('-created_at')

    return render(request, 'patients/my_prescriptions.html', {
        'prescriptions': prescriptions
    })