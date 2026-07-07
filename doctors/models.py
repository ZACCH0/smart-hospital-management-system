from django.db import models
from django.conf import settings

# Create your models here.
class DoctorProfile(models.Model):

    SPECIALIZATION_CHOICES = (
        ('general', 'General Medicine'),
        ('cardiology', 'Cardiology'),
        ('dermatology', 'Dermatology'),
        ('pediatrics', 'Pediatrics'),
        ('orthopedics', 'Orthopedics'),
        ('gynecology', 'Gynecology'),
        ('neurology', 'Neurology'),
        ('psychiatry', 'Psychiatry'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f'Dr. {self.user.get_full_name()} - {self.get_specialization_display()}'