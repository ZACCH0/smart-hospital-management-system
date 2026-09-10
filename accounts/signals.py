from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from core.audit import log_action


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(
        request,
        action='login',
        details=f'User {user.email} logged in successfully.'
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_action(
            request,
            action='logout',
            details=f'User {user.email} logged out.'
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, request, credentials, **kwargs):
    email = credentials.get('username', 'unknown')
    log_action(
        request,
        action='login_failed',
        details=f'Failed login attempt for email: {email}'
    )