from django.db.models import ProtectedError
from django.test import TestCase

from core.testing import make_doctor
from doctors.models import Specialty


class SpecialtyTests(TestCase):
    def test_default_specialties_are_seeded(self):
        slugs = set(Specialty.objects.values_list('slug', flat=True))
        self.assertTrue({'general', 'cardiology', 'dermatology'}.issubset(slugs))
        self.assertEqual(Specialty.objects.count(), 8)

    def test_admin_can_add_a_new_specialty(self):
        ent = Specialty.objects.create(name='ENT', slug='ent', order=20)
        self.assertTrue(ent.is_active)
        self.assertIn('ENT', str(ent))

    def test_specialty_in_use_cannot_be_deleted(self):
        specialty = Specialty.objects.get(slug='general')
        make_doctor(specialization=specialty)
        with self.assertRaises(ProtectedError):
            specialty.delete()

    def test_doctor_uses_the_assigned_specialty(self):
        neurology = Specialty.objects.get(slug='neurology')
        doctor = make_doctor(specialization=neurology)
        self.assertEqual(doctor.specialization, neurology)
        self.assertEqual(
            str(doctor), f'Dr. {doctor.user.get_full_name()} - Neurology',
        )
