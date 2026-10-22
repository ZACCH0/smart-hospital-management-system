from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.audit import log_action
from core.decorators import patient_required, role_required
from notifications.services import notify

from .forms import AdmissionForm, BedForm, DischargeForm, WardForm
from .models import Admission, Bed, Ward


def _active_admissions():
    return Admission.objects.filter(status='admitted').select_related(
        'patient__user', 'doctor__user', 'bed__ward'
    )


@login_required
@role_required('admin', 'receptionist', 'doctor')
def ward_board(request):
    wards = (
        Ward.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                'beds',
                queryset=Bed.objects.filter(is_active=True).prefetch_related(
                    Prefetch('admissions', queryset=_active_admissions(), to_attr='active_admissions')
                ),
                to_attr='active_beds',
            )
        )
        .order_by('name')
    )

    total_beds = 0
    occupied_beds = 0
    for ward in wards:
        total_beds += len(ward.active_beds)
        for bed in ward.active_beds:
            occupied_beds += len(bed.active_admissions)

    return render(request, 'ipd/ward_board.html', {
        'wards': wards,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': total_beds - occupied_beds,
        'active_admissions': _active_admissions().count(),
    })


@login_required
@role_required('admin', 'receptionist', 'doctor')
def admission_list(request):
    status = request.GET.get('status', 'admitted')
    if status not in ('admitted', 'discharged', 'all'):
        status = 'admitted'

    admissions = (
        Admission.objects
        .select_related('patient__user', 'doctor__user', 'bed__ward', 'admitted_by')
        .order_by('-admitted_at')
    )
    if status != 'all':
        admissions = admissions.filter(status=status)

    from django.core.paginator import Paginator
    page_obj = Paginator(admissions, 20).get_page(request.GET.get('page'))

    return render(request, 'ipd/admission_list.html', {
        'admissions': page_obj,
        'page_obj': page_obj,
        'status': status,
        'querystring': f'status={status}',
        'admitted_count': Admission.objects.filter(status='admitted').count(),
        'discharged_count': Admission.objects.filter(status='discharged').count(),
    })


@login_required
@role_required('admin', 'receptionist', 'doctor')
def admit_patient(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    admission = form.save(commit=False)
                    admission.admitted_by = request.user
                    admission.save()
            except IntegrityError:
                form.add_error(None, 'That bed or patient was just taken. Please pick another bed.')
            else:
                notify(
                    admission.patient.user,
                    (
                        f'You have been admitted to {admission.bed.ward.name} '
                        f'(Bed {admission.bed.bed_number}). Attending doctor: '
                        f'Dr. {admission.doctor.user.get_full_name()}.'
                    ),
                    category='admission',
                    email_subject='You have been admitted',
                    email_body=(
                        f'Ward: {admission.bed.ward.name}\n'
                        f'Bed: {admission.bed.bed_number}\n'
                        f'Doctor: Dr. {admission.doctor.user.get_full_name()}\n'
                        f'Diagnosis: {admission.diagnosis}'
                    ),
                )
                log_action(
                    request, 'admit', 'Admission', admission.id, str(admission),
                    details=f'Bed: {admission.bed}, Doctor: {admission.doctor}'
                )
                messages.success(request, 'Patient admitted successfully.')
                return redirect('ipd:admission_list')
    else:
        form = AdmissionForm()

    return render(request, 'ipd/admission_form.html', {
        'form': form,
        'title': 'Admit Patient',
    })


@login_required
@role_required('admin', 'receptionist', 'doctor')
def discharge_patient(request, admission_id):
    admission = get_object_or_404(
        Admission.objects.select_related('patient__user', 'bed__ward', 'doctor__user'),
        id=admission_id,
    )

    if admission.status != 'admitted':
        messages.error(request, 'This admission is already closed.')
        return redirect('ipd:admission_list')

    if request.method == 'POST':
        form = DischargeForm(request.POST, instance=admission)
        if form.is_valid():
            admission = form.save(commit=False)
            admission.status = 'discharged'
            admission.discharged_at = timezone.now()
            admission.discharged_by = request.user
            admission.save()

            notify(
                admission.patient.user,
                (
                    f'You have been discharged from {admission.bed.ward.name}. '
                    f'Summary: {admission.discharge_summary[:120]}'
                ),
                category='admission',
                email_subject='Discharge summary',
                email_body=(
                    f'You have been discharged from {admission.bed.ward.name} '
                    f'(Bed {admission.bed.bed_number}).\n\n'
                    f'{admission.discharge_summary}'
                ),
            )
            log_action(
                request, 'discharge', 'Admission', admission.id, str(admission),
                details=f'Length of stay: {admission.length_of_stay} day(s)'
            )
            messages.success(request, 'Patient discharged. Bed is now available.')
            return redirect('ipd:admission_list')
    else:
        form = DischargeForm(instance=admission)

    return render(request, 'ipd/discharge_form.html', {
        'form': form,
        'admission': admission,
    })


@login_required
@role_required('admin')
def ward_create(request):
    if request.method == 'POST':
        form = WardForm(request.POST)
        if form.is_valid():
            ward = form.save()
            log_action(request, 'create', 'Ward', ward.id, str(ward))
            messages.success(request, 'Ward created.')
            return redirect('ipd:ward_board')
    else:
        form = WardForm()

    return render(request, 'ipd/ward_form.html', {'form': form, 'title': 'Add Ward'})


@login_required
@role_required('admin')
def ward_edit(request, ward_id):
    ward = get_object_or_404(Ward, id=ward_id)

    if request.method == 'POST':
        form = WardForm(request.POST, instance=ward)
        if form.is_valid():
            ward = form.save()
            log_action(request, 'update', 'Ward', ward.id, str(ward))
            messages.success(request, 'Ward updated.')
            return redirect('ipd:ward_board')
    else:
        form = WardForm(instance=ward)

    return render(request, 'ipd/ward_form.html', {'form': form, 'title': f'Edit {ward.name}'})


@login_required
@role_required('admin')
def bed_create(request, ward_id):
    ward = get_object_or_404(Ward, id=ward_id)

    if request.method == 'POST':
        form = BedForm(request.POST)
        if form.is_valid():
            bed = form.save(commit=False)
            bed.ward = ward
            bed.save()
            log_action(request, 'create', 'Bed', bed.id, str(bed))
            messages.success(request, 'Bed added.')
            return redirect('ipd:ward_board')
    else:
        form = BedForm()

    return render(request, 'ipd/bed_form.html', {'form': form, 'ward': ward})


@login_required
@patient_required
def my_admissions(request):
    admissions = (
        request.user.patient_profile.admissions
        .select_related('doctor__user', 'bed__ward')
        .order_by('-admitted_at')
    )
    return render(request, 'ipd/my_admissions.html', {'admissions': admissions})
