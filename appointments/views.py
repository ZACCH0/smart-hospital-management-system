from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm
from core.decorators import receptionist_required, staff_required


@login_required
@receptionist_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment booked successfully.')
            return redirect('dashboard:receptionist_home')
    else:
        form = AppointmentForm()

    return render(request, 'appointments/book_appointment.html', {'form': form})


@login_required
@staff_required
def appointment_list(request):
    user = request.user

    # Doctors only see their own appointments
    if hasattr(user, 'doctor_profile'):
        appointments = Appointment.objects.filter(
            doctor=user.doctor_profile
        ).order_by('-appointment_date')
    else:
        # Receptionists and Admins see all appointments
        appointments = Appointment.objects.all().order_by('-appointment_date')

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments,
        'is_doctor': hasattr(user, 'doctor_profile'),
    })


@login_required
@staff_required
def approve_appointment(request, appointment_id):
    user = request.user

    if hasattr(user, 'doctor_profile'):
        # Doctor can only approve their own appointments
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor=user.doctor_profile
        )
    else:
        # Receptionist and Admin can approve any appointment
        appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = 'approved'
    appointment.save()
    messages.success(request, 'Appointment approved.')
    return redirect('appointments:appointment_list')


@login_required
@staff_required
def cancel_appointment(request, appointment_id):
    user = request.user

    if hasattr(user, 'doctor_profile'):
        # Doctor can only cancel their own appointments
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor=user.doctor_profile
        )
    else:
        # Receptionist and Admin can cancel any appointment
        appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, 'Appointment cancelled.')
    return redirect('appointments:appointment_list')