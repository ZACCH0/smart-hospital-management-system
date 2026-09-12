from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum


@login_required
def admin_home(request):
    from accounts.models import CustomUser
    from appointments.models import Appointment
    from billing.models import Invoice

    total_doctors = CustomUser.objects.filter(role='doctor').count()
    total_patients = CustomUser.objects.filter(role='patient').count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    approved_appointments = Appointment.objects.filter(status='approved').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    cancelled_appointments = Appointment.objects.filter(status='cancelled').count()

    total_revenue = Invoice.objects.filter(
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    pending_revenue = Invoice.objects.filter(
        status='pending'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'approved_appointments': approved_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
    }
    return render(request, 'dashboard/admin_home.html', context)


@login_required
def doctor_home(request):
    try:
        doctor_profile = request.user.doctor_profile
    except AttributeError:
        return render(request, 'dashboard/doctor_home.html', {
            'error': 'No doctor profile found for this account.'
        })

    today = timezone.now().date()

    todays_appointments = doctor_profile.appointments.select_related(
        'patient__user'
    ).filter(
        appointment_date=today
    ).order_by('appointment_time')

    from patients.models import PatientProfile
    patient_ids = doctor_profile.appointments.values_list(
        'patient', flat=True
    ).distinct()
    patient_list = PatientProfile.objects.filter(
        id__in=patient_ids
    ).select_related('user')

    notifications = request.user.notifications.order_by('-created_at').filter(
        is_read=False
    )[:5]

    context = {
        'todays_appointments': todays_appointments,
        'patient_list': patient_list,
        'notifications': notifications,
    }
    return render(request, 'dashboard/doctor_home.html', context)


@login_required
def receptionist_home(request):
    from appointments.models import Appointment
    pending_count = Appointment.objects.filter(status='pending').count()
    return render(request, 'dashboard/receptionist_home.html', {
        'pending_count': pending_count
    })


@login_required
def patient_home(request):
    try:
        patient_profile = request.user.patient_profile
    except AttributeError:
        return render(request, 'dashboard/patient_home.html', {
            'error': 'No patient profile found for this account.'
        })

    today = timezone.now().date()

    upcoming_appointments = patient_profile.appointments.select_related(
        'doctor__user'
    ).filter(
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')

    notifications = request.user.notifications.filter(
        is_read=False
    ).order_by('-created_at')[:5]

    context = {
        'upcoming_appointments': upcoming_appointments,
        'notifications': notifications,
    }
    return render(request, 'dashboard/patient_home.html', context)