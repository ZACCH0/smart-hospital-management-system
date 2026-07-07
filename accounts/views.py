from django.shortcuts import render
# Create your views here.

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
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
