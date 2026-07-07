from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import PatientRegistrationForm
# Create your views here.

@login_required
def role_redirect_view(request):
    role = request.user.role
    if role == 'admin':
        return redirect('dashboard:admin_home')
    elif role == 'doctor':
        return redirect('dashboard:doctor_home')
    elif role == 'receptionist':
        return redirect('dashboard:receptionist_home')
    elif role == 'patient':
        return redirect('dashboard:patient_home')
    return redirect('accounts:login')


def register_patient(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Automatically create PatientProfile
            from patients.models import PatientProfile
            PatientProfile.objects.create(
                user=user,
                date_of_birth='2000-01-01',  # placeholder — patient updates later
                gender='other'
            )

            # Log them in immediately
            login(request, user)
            return redirect('dashboard:patient_home')
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})