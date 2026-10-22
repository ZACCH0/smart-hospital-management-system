"""Advanced intelligence helpers (P29).

Provider-agnostic on purpose: the app works with deterministic rules out of
the box, and upgrades to an OpenAI-compatible chat model the moment
``AI_API_KEY`` is configured. The public entry point never raises — callers
always receive an answer plus a ``source`` flag ("ai" or "rules").
"""
import json
import logging
from urllib import request as urlrequest
from urllib.error import URLError

from django.conf import settings

logger = logging.getLogger(__name__)

DISCLAIMER = (
    'This is general guidance, not a diagnosis. In an emergency, call your '
    'local emergency number or go to the nearest emergency room.'
)

URGENT_KEYWORDS = (
    'chest pain', 'shortness of breath', 'difficulty breathing', 'severe bleeding',
    'unconscious', 'stroke', 'suicidal', 'seizure', 'severe abdominal',
    'cannot breathe', 'numbness on one side',
)


def _active_specialties():
    """Admin-managed specialties, ordered the way they should be offered."""
    from doctors.models import Specialty
    return list(Specialty.objects.filter(is_active=True).order_by('order', 'name'))


def _default_specialty(specialties):
    for specialty in specialties:
        if specialty.slug == 'general':
            return specialty
    return specialties[0] if specialties else None


def _advice_for(department, urgent):
    if urgent:
        return (
            'Your symptoms may need urgent attention. Go to the emergency '
            'department now or call emergency services.'
        )
    return (
        'Book an appointment so a doctor can assess you properly. Bring any '
        'medication you are taking and note when the symptoms started.'
    )


def _rule_based(symptoms):
    text = (symptoms or '').lower()
    urgent = any(keyword in text for keyword in URGENT_KEYWORDS)

    specialties = _active_specialties()
    default = _default_specialty(specialties)

    # The catch-all default is only used when nothing more specific matches,
    # so "my baby has a fever" routes to Pediatrics, not General Medicine.
    match = None
    for specialty in specialties:
        if specialty == default:
            continue
        if any(keyword in text for keyword in specialty.keyword_list()):
            match = specialty
            break

    chosen = match or default
    department = chosen.slug if chosen else None
    label = chosen.name if chosen else 'General Medicine'
    return {
        'department': department,
        'department_label': label,
        'urgency': 'urgent' if urgent else 'routine',
        'advice': _advice_for(department, urgent),
        'source': 'rules',
        'disclaimer': DISCLAIMER,
    }


def _ai_suggest(symptoms):
    """Ask an OpenAI-compatible model. Return None on any failure."""
    api_key = getattr(settings, 'AI_API_KEY', '')
    if not api_key:
        return None

    specialties = _active_specialties()
    if not specialties:
        return None

    labels = {specialty.slug: specialty.name for specialty in specialties}
    allowed = ', '.join(labels)

    base = settings.AI_BASE_URL.rstrip('/')
    payload = {
        'model': settings.AI_MODEL,
        'temperature': 0,
        'messages': [
            {
                'role': 'system',
                'content': (
                    f'You are a hospital triage assistant. Reply with strict JSON '
                    f'only: {{"department": one of [{allowed}], '
                    f'"urgency": "urgent" or "routine", "advice": "one or two '
                    f'sentences"}}. Never give a diagnosis. Do not include any other keys.'
                ),
            },
            {'role': 'user', 'content': symptoms[:1500]},
        ],
    }
    request = urlrequest.Request(
        f'{base}/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'SHMS/1.0 (+https://smart-hospital-management-system-8zgy.onrender.com)',
        },
        method='POST',
    )

    try:
        with urlrequest.urlopen(request, timeout=settings.AI_TIMEOUT) as response:
            body = json.loads(response.read().decode('utf-8'))
        content = body['choices'][0]['message']['content']
        parsed = json.loads(content)
    except (URLError, KeyError, ValueError, IndexError, OSError) as exc:
        logger.warning('AI suggestion failed, falling back to rules: %s', exc)
        return None

    department = parsed.get('department')
    if department not in labels:
        department = _default_specialty(specialties).slug
    urgency = 'urgent' if parsed.get('urgency') == 'urgent' else 'routine'
    advice = str(parsed.get('advice') or '').strip() or _advice_for(department, urgency == 'urgent')

    return {
        'department': department,
        'department_label': labels.get(department, 'General Medicine'),
        'urgency': urgency,
        'advice': advice,
        'source': 'ai',
        'disclaimer': DISCLAIMER,
    }


def suggest_department(symptoms):
    """Best available triage suggestion for a free-text symptom description."""
    symptoms = (symptoms or '').strip()
    if not symptoms:
        return None
    return _ai_suggest(symptoms) or _rule_based(symptoms)
