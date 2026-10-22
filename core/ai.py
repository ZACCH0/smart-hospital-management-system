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

DEPARTMENT_KEYWORDS = (
    ('cardiology', (
        'chest pain', 'heart', 'palpitation', 'blood pressure', 'hypertension',
        'cardiac', 'cholesterol',
    )),
    ('dermatology', (
        'rash', 'skin', 'itch', 'acne', 'eczema', 'mole', 'hair loss', 'wound',
    )),
    ('pediatrics', (
        'child', 'baby', 'infant', 'toddler', 'kid', 'newborn', 'vaccination',
    )),
    ('orthopedics', (
        'bone', 'fracture', 'joint', 'knee', 'back pain', 'sprain', 'shoulder',
        'neck pain', 'sports injury',
    )),
    ('gynecology', (
        'pregnan', 'period', 'menstrual', 'vaginal', 'pelvic', 'prenatal',
        'contraception',
    )),
    ('neurology', (
        'headache', 'migraine', 'seizure', 'numbness', 'dizzy', 'fainting',
        'tremor', 'memory',
    )),
    ('psychiatry', (
        'anxiety', 'depress', 'panic', 'insomnia', 'mood', 'stress', 'suicidal',
        'hearing voices',
    )),
)

URGENT_KEYWORDS = (
    'chest pain', 'shortness of breath', 'difficulty breathing', 'severe bleeding',
    'unconscious', 'stroke', 'suicidal', 'seizure', 'severe abdominal',
    'cannot breathe', 'numbness on one side',
)


def _specialty_labels():
    from doctors.models import DoctorProfile
    return dict(DoctorProfile.SPECIALIZATION_CHOICES)


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

    department = 'general'
    for candidate, keywords in DEPARTMENT_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            department = candidate
            break

    labels = _specialty_labels()
    return {
        'department': department,
        'department_label': labels.get(department, 'General Medicine'),
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

    base = settings.AI_BASE_URL.rstrip('/')
    payload = {
        'model': settings.AI_MODEL,
        'temperature': 0,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'You are a hospital triage assistant. Reply with strict JSON '
                    'only: {"department": one of [general, cardiology, dermatology, '
                    'pediatrics, orthopedics, gynecology, neurology, psychiatry], '
                    '"urgency": "urgent" or "routine", "advice": "one or two '
                    'sentences"}. Never give a diagnosis. Do not include any other keys.'
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

    labels = _specialty_labels()
    department = parsed.get('department')
    if department not in labels:
        department = 'general'
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
