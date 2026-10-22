from django.db import models
from django.conf import settings

class Specialty(models.Model):
    """Admin-managed clinical specialty (department).

    The Health Assistant routes symptoms by matching typed words against each
    specialty's ``keywords``, so a new specialty works end to end as soon as an
    admin adds it here.
    """

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    keywords = models.TextField(
        blank=True,
        help_text='Comma-separated words the Health Assistant uses to route symptoms here.',
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Specialties'

    def __str__(self):
        return self.name

    def keyword_list(self):
        return [word.strip().lower() for word in self.keywords.split(',') if word.strip()]


class DoctorProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    specialization = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name='doctors',
    )
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(consultation_fee__gte=0),
                name='doctor_fee_non_negative',
            ),
        ]

    def __str__(self):
        return f'Dr. {self.user.get_full_name()} - {self.specialization.name}'