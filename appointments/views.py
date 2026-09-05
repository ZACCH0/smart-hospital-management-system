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
    appointments = Appointment.objects.all().order_by('-appointment_date')
    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments
    })


@login_required
@staff_required
def approve_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'approved'
    appointment.save()
    messages.success(request, 'Appointment approved.')
    return redirect('appointments:appointment_list')


@login_required
@staff_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, 'Appointment cancelled.')
    return redirect('appointments:appointment_list')