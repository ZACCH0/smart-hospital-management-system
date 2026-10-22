from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q, F

from core.decorators import (
    admin_required,
    doctor_required,
    receptionist_required,
    patient_required,
)


@admin_required
def admin_home(request):
    from accounts.models import CustomUser
    from appointments.models import Appointment
    from billing.models import Invoice, Payment
    from core.models import AuditLog
    from doctors.models import DoctorProfile
    from ipd.models import Admission, Bed
    from laboratory.models import LabTest
    from patients.models import PatientProfile
    from pharmacy.models import Medicine

    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_doctors = CustomUser.objects.filter(role='doctor').count()
    total_patients = CustomUser.objects.filter(role='patient').count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    approved_appointments = Appointment.objects.filter(status='approved').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    cancelled_appointments = Appointment.objects.filter(status='cancelled').count()

    total_billed = Invoice.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_revenue = total_billed - total_revenue
    if pending_revenue < 0:
        pending_revenue = 0

    revenue_total = total_billed
    if revenue_total:
        collected_share = round(float(total_revenue or 0) / float(revenue_total) * 100)
    else:
        collected_share = 0
    outstanding_share = 100 - collected_share if revenue_total else 0

    month_revenue = Payment.objects.filter(
        payment_date__date__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    month_appointments = Appointment.objects.filter(
        appointment_date__gte=month_start
    ).count()
    month_new_patients = PatientProfile.objects.filter(
        user__date_joined__date__gte=month_start
    ).count()

    total_beds = Bed.objects.filter(is_active=True, ward__is_active=True).count()
    occupied_beds = Admission.objects.filter(status='admitted').count()

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
        'total_billed': total_billed,
        'collected_share': collected_share,
        'outstanding_share': outstanding_share,
        'month_revenue': month_revenue,
        'month_start': month_start,
        'month_appointments': month_appointments,
        'month_new_patients': month_new_patients,
        'pending_labs': LabTest.objects.exclude(status='completed').count(),
        'low_stock_count': Medicine.objects.filter(
            stock_quantity__lte=Medicine.LOW_STOCK_THRESHOLD
        ).count(),
        'admitted_count': occupied_beds,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'specialty_load': (
            DoctorProfile.objects
            .values(department=F('specialization__name'))
            .annotate(total=Count('appointments'))
            .order_by('-total')[:6]
        ),
        'recent_activity': AuditLog.objects.select_related('user')[:8],
    }
    return render(request, 'dashboard/admin_home.html', context)


@doctor_required
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

    all_appointments = doctor_profile.appointments.select_related(
        'patient__user'
    ).order_by('-appointment_date', '-appointment_time')
    total_appointments = all_appointments.count()

    seen = set()
    recent_patients = []
    for appt in all_appointments:
        if appt.patient_id not in seen:
            seen.add(appt.patient_id)
            appt.patient.last_appt = appt
            recent_patients.append(appt.patient)
        if len(recent_patients) >= 8:
            break

    context = {
        'doctor_profile': doctor_profile,
        'todays_appointments': todays_appointments,
        'patient_list': patient_list,
        'notifications': notifications,
        'total_appointments': total_appointments,
        'recent_patients': recent_patients,
    }
    return render(request, 'dashboard/doctor_home.html', context)


@receptionist_required
def receptionist_home(request):
    from appointments.models import Appointment
    from doctors.models import DoctorProfile

    today = timezone.now().date()

    todays_appointments = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).filter(
        appointment_date=today
    ).exclude(
        status__in=['cancelled', 'no_show']
    ).order_by('appointment_time')

    pending_approvals = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).filter(
        status='pending'
    ).order_by('appointment_date', 'appointment_time')[:10]

    doctors = DoctorProfile.objects.select_related('user').annotate(
        today_load=Count(
            'appointments',
            filter=Q(appointments__appointment_date=today) & ~Q(
                appointments__status__in=['cancelled', 'no_show']
            ),
        )
    ).order_by('-available', 'user__first_name')

    return render(request, 'dashboard/receptionist_home.html', {
        'today': today,
        'today_count': todays_appointments.count(),
        'pending_count': Appointment.objects.filter(status='pending').count(),
        'available_count': DoctorProfile.objects.filter(available=True).count(),
        'unavailable_count': DoctorProfile.objects.filter(available=False).count(),
        'doctor_count': DoctorProfile.objects.count(),
        'todays_appointments': todays_appointments[:12],
        'pending_approvals': pending_approvals,
        'doctors': doctors,
    })


@doctor_required
def doctor_profile(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from dashboard.forms import DoctorProfileForm, DoctorClinicalForm

    try:
        doctor_profile = request.user.doctor_profile
    except AttributeError:
        return render(request, 'dashboard/doctor_home.html', {
            'error': 'No doctor profile found for this account.'
        })

    if request.method == 'POST':
        form = DoctorProfileForm(
            request.POST, request.FILES, instance=request.user
        )
        clinical_form = DoctorClinicalForm(
            request.POST, instance=doctor_profile
        )
        if form.is_valid() and clinical_form.is_valid():
            form.save()
            clinical_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard:doctor_profile')
    else:
        form = DoctorProfileForm(instance=request.user)
        clinical_form = DoctorClinicalForm(instance=doctor_profile)

    return render(request, 'dashboard/doctor_profile.html', {
        'form': form,
        'clinical_form': clinical_form,
        'doctor_profile': doctor_profile,
    })


@receptionist_required
def receptionist_profile(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from dashboard.forms import ReceptionistProfileForm

    if request.method == 'POST':
        form = ReceptionistProfileForm(
            request.POST, request.FILES, instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard:receptionist_profile')
    else:
        form = ReceptionistProfileForm(instance=request.user)

    return render(request, 'dashboard/receptionist_profile.html', {
        'form': form,
    })


@patient_required
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

    total_appointments = patient_profile.appointments.count()
    total_records = patient_profile.medical_records.count()
    from prescriptions.models import Prescription
    total_prescriptions = Prescription.objects.filter(
        medical_record__patient=patient_profile
    ).count()
    from billing.models import Invoice
    from django.db.models import Sum as _Sum
    pending_invoices_qs = patient_profile.invoices.filter(status='pending')
    pending_invoices_count = pending_invoices_qs.count()
    pending_invoices_amount = pending_invoices_qs.aggregate(
        _Sum('amount')
    )['amount__sum'] or 0

    context = {
        'patient_profile': patient_profile,
        'upcoming_appointments': upcoming_appointments,
        'upcoming_count': upcoming_appointments.count(),
        'total_appointments': total_appointments,
        'total_records': total_records,
        'total_prescriptions': total_prescriptions,
        'pending_invoices_count': pending_invoices_count,
        'pending_invoices_amount': pending_invoices_amount,
        'notifications': notifications,
    }
    return render(request, 'dashboard/patient_home.html', context)