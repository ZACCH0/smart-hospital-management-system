from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def patient_required(view_func):
    """
    Restricts view to users who have a PatientProfile.
    Checks profile existence, not just the role field.
    This allows a doctor who is also a patient to access patient views.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not hasattr(request.user, 'patient_profile'):
            raise PermissionDenied
        return wrapper_func(request, *args, **kwargs)
    return wrapper


def doctor_required(view_func):
    """
    Restricts view to users who have a DoctorProfile.
    Checks profile existence, not just the role field.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not hasattr(request.user, 'doctor_profile'):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def receptionist_required(view_func):
    return role_required('receptionist')(view_func)


def admin_required(view_func):
    return role_required('admin')(view_func)


def staff_required(view_func):
    return role_required('doctor', 'receptionist', 'admin')(view_func)