from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import DoctorProfile, Specialty

CACHE_KEYS = ('homepage_doctors', 'homepage_doctor_count', 'directory_doctors',
              'directory_count', 'directory_specialties')


@receiver(post_save, sender=DoctorProfile)
@receiver(post_delete, sender=DoctorProfile)
@receiver(post_save, sender=Specialty)
@receiver(post_delete, sender=Specialty)
def clear_doctor_caches(sender, instance, **kwargs):
    cache.delete_many(CACHE_KEYS)
