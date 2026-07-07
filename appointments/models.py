from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from doctors.models import DoctorProfile
from patients.models import PatientProfile
# Create your models here.

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f'{self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.appointment_date}'

    def clean(self):
        if self.appointment_date and self.appointment_date < timezone.now().date():
            raise ValidationError('Appointment date cannot be in the past.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)