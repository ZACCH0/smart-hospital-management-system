from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm, CancelAppointmentForm, MarkNoShowForm
from core.decorators import receptionist_required, staff_required
from core.audit import log_action


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
            # Show form errors clearly
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
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

    paginator = __import__('django.core.paginator', fromlist=['Paginator']).Paginator
    from django.core.paginator import Paginator
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

    if request.method == 'POST':
        form = CancelAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = 'cancelled'
            appointment.save()

            log_action(
                request,
                action='cancel',
                model_name='Appointment',
                object_id=appointment.id,
                object_repr=str(appointment),
                details=f'Cancelled by {request.user.get_full_name()}. Reason: {appointment.cancellation_reason}'
            )
            messages.success(request, 'Appointment cancelled.')
            return redirect('appointments:appointment_list')
    else:
        form = CancelAppointmentForm(instance=appointment)

    return render(request, 'appointments/cancel_appointment.html', {
        'form': form,
        'appointment': appointment,
    })


@login_required
@staff_required
def mark_no_show(request, appointment_id):
    user = request.user
    if hasattr(user, 'doctor_profile'):
        appointment = get_object_or_404(
            Appointment, id=appointment_id, doctor=user.doctor_profile
        )
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        form = MarkNoShowForm(request.POST)
        if form.is_valid():
            appointment.status = 'no_show'
            appointment.save()

            log_action(
                request,
                action='update',
                model_name='Appointment',
                object_id=appointment.id,
                object_repr=str(appointment),
                details=f'Marked as No Show by {request.user.get_full_name()}'
            )
            messages.success(request, 'Appointment marked as No Show.')
            return redirect('appointments:appointment_list')
    else:
        form = MarkNoShowForm()

    return render(request, 'appointments/mark_no_show.html', {
        'form': form,
        'appointment': appointment,
    })