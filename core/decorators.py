from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(*roles):
    """
    Decorator that restricts view access to users with specific roles.
    Usage: @role_required('doctor', 'admin')
    Raises 403 Forbidden if the user's role is not in the allowed list.
    """
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
    return role_required('patient')(view_func)


def doctor_required(view_func):
    return role_required('doctor')(view_func)


def receptionist_required(view_func):
    return role_required('receptionist')(view_func)


def admin_required(view_func):
    return role_required('admin')(view_func)


def staff_required(view_func):
    return role_required('doctor', 'receptionist', 'admin')(view_func)