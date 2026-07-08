from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm, PatientProfileForm
# Create your views here.
@login_required
def profile_settings(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        return redirect('dashboard:patient_home')

    if request.method == 'POST':
        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        profile_form = PatientProfileForm(
            request.POST,
            instance=patient_profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('patients:profile_settings')
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = PatientProfileForm(instance=patient_profile)

    return render(request, 'patients/profile_settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })