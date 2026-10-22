import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from accounts.models import CustomUser
from core.ai import answer_question
from core.decorators import role_required
from core.models import AuditLog
from doctors.models import DoctorProfile

DEMO_EMAILS = {
    "admin": "admin@shms-demo.com",
    "doctor": "doctor@shms-demo.com",
    "receptionist": "receptionist@shms-demo.com",
    "patient": "patient@shms-demo.com",
}


def home(request):
    """Public homepage — read-only context, no writes, no auth required."""
    from django.core.cache import cache

    doctors = cache.get('homepage_doctors')
    if doctors is None:
        doctors = list(
            DoctorProfile.objects.select_related("user", "specialization")
            .order_by("-available", "user__first_name")[:8]
        )
        cache.set('homepage_doctors', doctors, 300)

    doctor_count = cache.get('homepage_doctor_count')
    if doctor_count is None:
        doctor_count = DoctorProfile.objects.count()
        cache.set('homepage_doctor_count', doctor_count, 300)

    tabs = []
    seen = set()
    for doctor in doctors:
        specialty = doctor.specialization
        if specialty and specialty.slug not in seen:
            seen.add(specialty.slug)
            tabs.append((specialty.order, specialty.slug, specialty.name))
    specialty_tabs = [(slug, name) for _, slug, name in sorted(tabs)]

    return render(
        request,
        "home.html",
        {
            "homepage_doctors": doctors,
            "homepage_doctor_count": doctor_count,
            "specialty_tabs": specialty_tabs,
        },
    )


def demo_page(request):
    """Public demo role picker — read-only personas from real demo accounts, no auth required."""
    users = {
        u.email: u
        for u in CustomUser.objects.filter(email__in=DEMO_EMAILS.values())
    }
    personas = {}
    for role, email in DEMO_EMAILS.items():
        user = users.get(email)
        if user is None:
            continue
        extra = ""
        if role == "doctor" and hasattr(user, "doctor_profile"):
            extra = user.doctor_profile.specialization.name
        personas[role] = {
            "name": user.get_full_name() or user.email,
            "extra": extra,
        }
    return render(request, "demo/demo_page.html", {"demo_personas": personas})

@login_required
@role_required('admin')
def audit_log_list(request):
    """Read-only trail of privileged and clinical actions (admin only)."""
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')

    q = request.GET.get('q', '').strip()
    action = request.GET.get('action', '').strip()
    model_name = request.GET.get('model', '').strip()

    if q:
        logs = logs.filter(
            Q(user__email__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(object_repr__icontains=q)
            | Q(details__icontains=q)
            | Q(ip_address__icontains=q)
        )
    if action in dict(AuditLog.ACTION_CHOICES):
        logs = logs.filter(action=action)
    if model_name:
        logs = logs.filter(model_name=model_name)

    page_obj = Paginator(logs, 50).get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)

    return render(request, 'core/audit_log.html', {
        'logs': page_obj,
        'page_obj': page_obj,
        'action_choices': AuditLog.ACTION_CHOICES,
        'model_names': (
            AuditLog.objects.exclude(model_name='')
            .values_list('model_name', flat=True)
            .distinct()
            .order_by('model_name')
        ),
        'q': q,
        'selected_action': action,
        'selected_model': model_name,
        'querystring': querystring.urlencode(),
    })


@require_POST
def ai_chat(request):
    """Public homepage chatbot. The message is used for the reply only and is
    never stored; rate limiting is handled by the shared middleware."""
    try:
        data = json.loads(request.body or b'{}')
    except ValueError:
        data = request.POST

    message = str(data.get('message', '')).strip()
    if not message:
        return JsonResponse({'error': 'Please type a message.'}, status=400)
    if len(message) > 500:
        return JsonResponse(
            {'error': 'Please keep your message under 500 characters.'},
            status=400,
        )

    result = answer_question(message)
    return JsonResponse({
        'reply': result['reply'],
        'source': result['source'],
        'disclaimer': result['disclaimer'],
    })
