from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import LabTest, LabResult
from .forms import LabTestForm, LabResultForm
from core.decorators import doctor_required, lab_staff_required
from core.audit import log_action

@login_required
def lab_test_list(request):
    user = request.user
    # Scope queryset based on role
    if user.role in ('admin', 'receptionist'):
        # Admin and receptionist see all tests
        tests = LabTest.objects.select_related(
            'patient__user', 'doctor__user'
        ).order_by('-requested_date')

    elif hasattr(user, 'doctor_profile'):
        # Doctor sees ONLY tests they ordered
        tests = LabTest.objects.filter(
            doctor=user.doctor_profile
        ).select_related(
            'patient__user', 'doctor__user'
        ).order_by('-requested_date')

    elif hasattr(user, 'patient_profile'):
        # Patient sees ONLY their own tests
        tests = LabTest.objects.filter(
            patient=user.patient_profile
        ).select_related(
            'patient__user', 'doctor__user'
        ).order_by('-requested_date')

    else:
        # No recognized profile — show nothing
        tests = LabTest.objects.none()

    pending = tests.filter(status='pending').count()
    in_progress = tests.filter(status='in_progress').count()
    completed = tests.filter(status='completed').count()

    from django.core.paginator import Paginator
    page_obj = Paginator(tests, 20).get_page(request.GET.get('page'))

    return render(request, 'laboratory/lab_test_list.html', {
        'tests': page_obj,
        'page_obj': page_obj,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'is_doctor': hasattr(user, 'doctor_profile'),
        'is_patient': hasattr(user, 'patient_profile') and user.role == 'patient',
    })


@login_required
@doctor_required
def request_lab_test(request):
    doctor_profile = request.user.doctor_profile

    if request.method == 'POST':
        form = LabTestForm(request.POST)
        if form.is_valid():
            lab_test = form.save(commit=False)
            lab_test.doctor = doctor_profile
            lab_test.save()

            from notifications.services import notify
            notify(
                lab_test.patient.user,
                f'Dr. {doctor_profile.user.get_full_name()} has requested a {lab_test.test_name} test for you.',
                category='laboratory',
                email_subject='New lab test requested',
                email_body=(
                    f'Dr. {doctor_profile.user.get_full_name()} requested a '
                    f'{lab_test.test_name} test. Please visit the laboratory.'
                ),
            )
            messages.success(request, 'Lab test requested successfully.')
            return redirect('laboratory:lab_test_list')
    else:
        form = LabTestForm()

    return render(request, 'laboratory/request_lab_test.html', {'form': form})


@login_required
@lab_staff_required
def collect_sample(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)

    if request.method != 'POST':
        messages.error(request, 'Collect samples from the test list.')
        return redirect('laboratory:lab_test_list')

    lab_test.sample_status = 'collected'
    lab_test.sample_collected_at = timezone.now()
    lab_test.technician = request.user
    if lab_test.status == 'pending':
        lab_test.status = 'in_progress'
    lab_test.save(update_fields=['sample_status', 'sample_collected_at', 'technician', 'status'])

    log_action(
        request, 'update', 'LabTest', lab_test.id, str(lab_test),
        details=f'Sample collected by {request.user.get_full_name()}'
    )
    messages.success(request, f'Sample collected for {lab_test.test_name}.')
    return redirect('laboratory:lab_test_list')


@login_required
@lab_staff_required
def reject_sample(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)

    if request.method != 'POST':
        messages.error(request, 'Reject samples from the test list.')
        return redirect('laboratory:lab_test_list')

    lab_test.sample_status = 'rejected'
    lab_test.save(update_fields=['sample_status'])

    log_action(
        request, 'update', 'LabTest', lab_test.id, str(lab_test),
        details=f'Sample rejected by {request.user.get_full_name()}'
    )
    messages.warning(request, f'Sample rejected for {lab_test.test_name}.')
    return redirect('laboratory:lab_test_list')


@login_required
@lab_staff_required
def upload_result(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)

    if hasattr(lab_test, 'result'):
        messages.error(request, 'A result has already been uploaded for this test.')
        return redirect('laboratory:lab_test_list')

    if request.method == 'POST':
        form = LabResultForm(request.POST, request.FILES)
        if form.is_valid():
            result = form.save(commit=False)
            result.lab_test = lab_test
            result.save()

            lab_test.status = 'completed'
            if lab_test.sample_status == 'awaiting':
                lab_test.sample_status = 'collected'
                lab_test.sample_collected_at = lab_test.sample_collected_at or timezone.now()
            if lab_test.technician_id is None:
                lab_test.technician = request.user
            lab_test.save(update_fields=['status', 'sample_status', 'sample_collected_at', 'technician'])

            log_action(
                request, 'create', 'LabResult', result.id, str(result),
                details=f'Result for {lab_test.test_name} ({lab_test.patient.user.get_full_name()})'
            )

            from notifications.services import notify
            notify(
                lab_test.patient.user,
                f'Your {lab_test.test_name} result is ready. Please check with your doctor.',
                category='laboratory',
                email_subject=f'{lab_test.test_name} result ready',
                email_body=(
                    f'Your {lab_test.test_name} result is ready.\n\n'
                    f'Result: {result.result_value or result.result}\n'
                    f'Reference range: {result.reference_range_display}\n\n'
                    'Please discuss it with your doctor.'
                ),
            )
            messages.success(request, 'Result uploaded successfully.')
            return redirect('laboratory:lab_test_list')
    else:
        form = LabResultForm()

    return render(request, 'laboratory/upload_result.html', {
        'form': form,
        'lab_test': lab_test,
    })


@login_required
@lab_staff_required
def update_test_status(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)

    if request.method != 'POST':
        messages.error(request, 'Update test status from the test list.')
        return redirect('laboratory:lab_test_list')

    lab_test.status = 'in_progress'
    lab_test.save(update_fields=['status'])
    messages.success(request, 'Test marked as In Progress.')
    return redirect('laboratory:lab_test_list')