"""Shared helpers for the automated test-suite."""
import itertools
from datetime import date

from accounts.models import CustomUser
from doctors.models import DoctorProfile, Specialty
from patients.models import PatientProfile

_counter = itertools.count(1)


def make_user(role='patient', email=None, password='testpass123', **extra):
    index = next(_counter)
    user = CustomUser.objects.create_user(
        email=email or f'{role}{index}@example.com',
        password=password,
        first_name=extra.pop('first_name', 'Test'),
        last_name=extra.pop('last_name', f'User{index}'),
        role=role,
        **extra,
    )
    return user


def make_patient(email=None, **extra):
    user = make_user('patient', email=email, **extra)
    return PatientProfile.objects.create(
        user=user,
        date_of_birth=date(1990, 1, 1),
        gender='female',
    )


def make_doctor(email=None, available=True, specialization='general', **extra):
    if not isinstance(specialization, Specialty):
        specialty, _ = Specialty.objects.get_or_create(
            slug=specialization,
            defaults={'name': specialization.replace('-', ' ').title()},
        )
    else:
        specialty = specialization
    user = make_user('doctor', email=email, **extra)
    return DoctorProfile.objects.create(
        user=user,
        specialization=specialty,
        qualification='MBBS',
        experience_years=5,
        consultation_fee=5000,
        available=available,
    )


def make_staff(role='receptionist', email=None, **extra):
    return make_user(role, email=email, **extra)
