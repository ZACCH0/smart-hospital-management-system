from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LabTest, LabResult
from .forms import LabTestForm, LabResultForm
from core.decorators import doctor_required, lab_staff_required

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

    return render(request, 'laboratory/lab_test_list.html', {
        'tests': tests,
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

            from notifications.models import Notification
            Notification.objects.create(
                user=lab_test.patient.user,
                message=f'Dr. {doctor_profile.user.get_full_name()} has requested a {lab_test.test_name} test for you.'
            )
            messages.success(request, 'Lab test requested successfully.')
            return redirect('laboratory:lab_test_list')
    else:
        form = LabTestForm()

    return render(request, 'laboratory/request_lab_test.html', {'form': form})


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
            lab_test.save()

            from notifications.models import Notification
            Notification.objects.create(
                user=lab_test.patient.user,
                message=f'Your {lab_test.test_name} result is ready. Please check with your doctor.'
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
    lab_test.status = 'in_progress'
    lab_test.save()
    messages.success(request, 'Test marked as In Progress.')
    return redirect('laboratory:lab_test_list')