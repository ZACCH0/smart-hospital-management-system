import re

from django.conf import settings
from django.shortcuts import render

from .audit import get_client_ip, log_action
from .throttle import check_rate_limit

# (scope, path regex, method or '*', limit, window in seconds)
DEFAULT_RULES = (
    ('login', r'^/accounts/login/$', 'POST', 10, 300),
    ('register', r'^/accounts/register/$', 'POST', 5, 3600),
    ('password_reset', r'^/accounts/password-reset/$', 'POST', 5, 3600),
    ('password_reset_confirm', r'^/accounts/password-reset-confirm/', 'POST', 10, 3600),
    ('resend_verification', r'^/accounts/resend-verification/$', 'POST', 3, 3600),
    ('2fa_setup', r'^/accounts/2fa/setup/$', 'POST', 10, 300),
    ('2fa_verify', r'^/accounts/2fa/verify/$', 'POST', 10, 300),
    ('demo_login', r'^/accounts/demo/', 'GET', 30, 3600),
)

COMPILED_RULES = tuple(
    (scope, re.compile(pattern), method, limit, window)
    for scope, pattern, method, limit, window in DEFAULT_RULES
)


class RateLimitMiddleware:
    """
    Protects credential and account-recovery endpoints from brute force.

    Counters live in the configured cache so every gunicorn worker shares
    the same budget. Disable with RATE_LIMIT_ENABLED=False (tests/dev).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)

    def __call__(self, request):
        if self.enabled:
            response = self._check(request)
            if response is not None:
                return response
        return self.get_response(request)

    def _check(self, request):
        path = request.path_info
        method = request.method

        for scope, pattern, rule_method, limit, window in COMPILED_RULES:
            if not pattern.search(path):
                continue
            if rule_method != '*' and rule_method != method:
                continue

            ip = get_client_ip(request) or '0.0.0.0'
            allowed, count = check_rate_limit(scope, ip, limit, window)
            if allowed:
                return None

            log_action(
                request,
                action='access',
                model_name='RateLimit',
                object_repr=scope,
                details=f'Rate limit exceeded ({count} hits, limit {limit}/{window}s).',
            )
            response = render(
                request,
                '429.html',
                {'retry_after': window, 'scope': scope},
                status=429,
            )
            response['Retry-After'] = str(window)
            return response

        return None
