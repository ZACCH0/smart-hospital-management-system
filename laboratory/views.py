from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LabTest, LabResult
from .forms import LabTestForm, LabResultForm

# Create your views here.
@login_required
def lab_test_list(request):
    tests = LabTest.objects.all().order_by('-requested_date')
    pending = tests.filter(status='pending').count()
    in_progress = tests.filter(status='in_progress').count()
    completed = tests.filter(status='completed').count()

    return render(request, 'laboratory/lab_test_list.html', {
        'tests': tests,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
    })

@login_required
def request_lab_test(request):
    try:
        doctor_profile = request.user.doctor_profile
    except Exception:
        messages.error(request, 'Only doctors can request lab tests.')
        return redirect('laboratory:lab_test_list')

    if request.method == 'POST':
        form = LabTestForm(request.POST)
        if form.is_valid():
            lab_test = form.save(commit=False)
            lab_test.doctor = doctor_profile
            lab_test.save()

            # Notify patient
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
def upload_result(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)

    # Check if result already exists
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

            # Notify patient
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
def update_test_status(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)
    lab_test.status = 'in_progress'
    lab_test.save()
    messages.success(request, 'Test marked as In Progress.')
    return redirect('laboratory:lab_test_list')