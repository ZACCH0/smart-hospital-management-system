from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription
from appointments.models import Appointment
from .forms import MedicalRecordForm, PrescriptionForm
from core.decorators import doctor_required
from core.audit import log_action


@login_required
@doctor_required
def patient_list(request):
    doctor_profile = request.user.doctor_profile
    patient_ids = Appointment.objects.filter(
        doctor=doctor_profile
    ).values_list('patient', flat=True).distinct()
    patients = PatientProfile.objects.filter(id__in=patient_ids)
    return render(request, 'doctors/patient_list.html', {'patients': patients})


@login_required
@doctor_required
def patient_detail(request, patient_id):
    doctor_profile = request.user.doctor_profile
    patient = get_object_or_404(PatientProfile, id=patient_id)

    has_relationship = Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient
    ).exists()

    if not has_relationship:
        messages.error(request, 'You do not have access to this patient.')
        return redirect('doctors:patient_list')

    # Log that this doctor accessed this patient's records
    log_action(
        request,
        action='access',
        model_name='PatientProfile',
        object_id=patient.id,
        object_repr=str(patient.user.get_full_name()),
        details=f'Dr. {request.user.get_full_name()} accessed patient record.'
    )

    records = MedicalRecord.objects.filter(
        patient=patient,
        doctor=doctor_profile
    ).order_by('-created_at')

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
@doctor_required
def write_medical_record(request, patient_id):
    doctor_profile = request.user.doctor_profile
    patient = get_object_or_404(PatientProfile, id=patient_id)

    has_relationship = Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient
    ).exists()

    if not has_relationship:
        messages.error(request, 'You do not have access to this patient.')
        return redirect('doctors:patient_list')

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, doctor=doctor_profile, patient=patient)
        if form.is_valid():
            record = form.save(commit=False)
            record.doctor = doctor_profile
            record.patient = patient
            record.save()

            # Log medical record creation
            log_action(
                request,
                action='create',
                model_name='MedicalRecord',
                object_id=record.id,
                object_repr=str(record),
                details=f'Diagnosis: {record.diagnosis[:100]}'
            )

            messages.success(request, 'Medical record saved successfully.')
            return redirect('doctors:patient_detail', patient_id=patient.id)
    else:
        form = MedicalRecordForm(doctor=doctor_profile, patient=patient)

    return render(request, 'doctors/write_medical_record.html', {
        'form': form,
        'patient': patient,
    })


@login_required
@doctor_required
def add_prescription(request, record_id):
    doctor_profile = request.user.doctor_profile
    record = get_object_or_404(MedicalRecord, id=record_id, doctor=doctor_profile)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.medical_record = record
            prescription.save()

            # Log prescription creation
            log_action(
                request,
                action='create',
                model_name='Prescription',
                object_id=prescription.id,
                object_repr=f'{prescription.medicine_name} for {record.patient.user.get_full_name()}',
                details=f'Dosage: {prescription.dosage}, Duration: {prescription.duration}'
            )

            messages.success(request, 'Prescription added successfully.')
            return redirect('doctors:patient_detail', patient_id=record.patient.id)
    else:
        form = PrescriptionForm()

    return render(request, 'doctors/add_prescription.html', {
        'form': form,
        'record': record,
    })