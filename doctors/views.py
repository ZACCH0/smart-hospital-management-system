from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription
from .forms import MedicalRecordForm, PrescriptionForm

# Create your views here.


@login_required
def patient_list(request):
    try:
        doctor_profile = request.user.doctor_profile
    except Exception:
        return redirect('dashboard:doctor_home')

    from appointments.models import Appointment
    patient_ids = Appointment.objects.filter(
        doctor=doctor_profile
    ).values_list('patient', flat=True).distinct()

    patients = PatientProfile.objects.filter(id__in=patient_ids)

    return render(request, 'doctors/patient_list.html', {
        'patients': patients
    })


@login_required
def patient_detail(request, patient_id):
    try:
        doctor_profile = request.user.doctor_profile
    except Exception:
        return redirect('dashboard:doctor_home')

    patient = get_object_or_404(PatientProfile, id=patient_id)
    records = MedicalRecord.objects.filter(
        patient=patient,
        doctor=doctor_profile
    ).order_by('-created_at')

    from appointments.models import Appointment
    appointments = Appointment.objects.filter(
        patient=patient,
        doctor=doctor_profile
    ).order_by('-appointment_date')

    return render(request, 'doctors/patient_detail.html', {
        'patient': patient,
        'records': records,
        'appointments': appointments,
    })


@login_required
def write_medical_record(request, patient_id):
    try:
        doctor_profile = request.user.doctor_profile
    except Exception:
        return redirect('dashboard:doctor_home')

    patient = get_object_or_404(PatientProfile, id=patient_id)

    if request.method == 'POST':
        form = MedicalRecordForm(
            request.POST,
            doctor=doctor_profile,
            patient=patient
        )
        if form.is_valid():
            record = form.save(commit=False)
            record.doctor = doctor_profile
            record.patient = patient
            record.save()
            messages.success(request, 'Medical record saved successfully.')
            return redirect('doctors:patient_detail', patient_id=patient.id)
    else:
        form = MedicalRecordForm(doctor=doctor_profile, patient=patient)

    return render(request, 'doctors/write_medical_record.html', {
        'form': form,
        'patient': patient,
    })


@login_required
def add_prescription(request, record_id):
    try:
        doctor_profile = request.user.doctor_profile
    except Exception:
        return redirect('dashboard:doctor_home')

    record = get_object_or_404(MedicalRecord, id=record_id, doctor=doctor_profile)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.medical_record = record
            prescription.save()
            messages.success(request, 'Prescription added successfully.')
            return redirect('doctors:patient_detail', patient_id=record.patient.id)
    else:
        form = PrescriptionForm()

    return render(request, 'doctors/add_prescription.html', {
        'form': form,
        'record': record,
    })