from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm
from core.decorators import receptionist_required, staff_required
from core.audit import log_action
from django.core.paginator import Paginator


@login_required
@receptionist_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            log_action(
                request,
                action='create',
                model_name='Appointment',
                object_id=appointment.id,
                object_repr=str(appointment),
                details=f'Booked by receptionist {request.user.get_full_name()}'
            )
            messages.success(request, 'Appointment booked successfully.')
            return redirect('dashboard:receptionist_home')
    else:
        form = AppointmentForm()
    return render(request, 'appointments/book_appointment.html', {'form': form})

@login_required
@staff_required
def appointment_list(request):
    user = request.user

    base_qs = Appointment.objects.select_related(
        'patient__user',
        'doctor__user',
    ).order_by('-appointment_date')

    if hasattr(user, 'doctor_profile'):
        appointments = base_qs.filter(doctor=user.doctor_profile)
    else:
        appointments = base_qs

    # Pagination — 20 appointments per page
    paginator = Paginator(appointments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'appointments/appointment_list.html', {
        'appointments': page_obj,
        'page_obj': page_obj,
        'is_doctor': hasattr(user, 'doctor_profile'),
    })

@login_required
@staff_required
def approve_appointment(request, appointment_id):
    user = request.user
    if hasattr(user, 'doctor_profile'):
        appointment = get_object_or_404(
            Appointment, id=appointment_id, doctor=user.doctor_profile
        )
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = 'approved'
    appointment.save()

    log_action(
        request,
        action='approve',
        model_name='Appointment',
        object_id=appointment.id,
        object_repr=str(appointment),
        details=f'Approved by {request.user.get_full_name()}'
    )
    messages.success(request, 'Appointment approved.')
    return redirect('appointments:appointment_list')


@login_required
@staff_required
def cancel_appointment(request, appointment_id):
    user = request.user
    if hasattr(user, 'doctor_profile'):
        appointment = get_object_or_404(
            Appointment, id=appointment_id, doctor=user.doctor_profile
        )
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = 'cancelled'
    appointment.save()

    log_action(
        request,
        action='cancel',
        model_name='Appointment',
        object_id=appointment.id,
        object_repr=str(appointment),
        details=f'Cancelled by {request.user.get_full_name()}'
    )
    messages.success(request, 'Appointment cancelled.')
    return redirect('appointments:appointment_list')