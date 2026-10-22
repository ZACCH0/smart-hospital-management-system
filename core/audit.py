from .models import AuditLog
def get_client_ip(request):
    """Extract the client IP, trusting only the closest proxy.

    Render appends the real client address to X-Forwarded-For, so the last
    entry is the one we can trust; earlier entries are client-supplied and
    spoofable (which would defeat IP-based rate limiting).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(request, action, model_name='', object_id='', object_repr='', details=''):
    """
    Create an audit log entry.

    Usage:
        log_action(request, 'create', 'MedicalRecord', record.id, str(record), 'Created during appointment')
        log_action(request, 'login')
        log_action(request, 'login_failed', details='Email: someone@gmail.com')
    """
    user_obj = getattr(request, 'user', None)
    user = user_obj if user_obj and user_obj.is_authenticated else None

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        object_repr=object_repr[:255],  # truncate to fit field
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        details=details,
    )