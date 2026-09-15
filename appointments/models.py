from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from doctors.models import DoctorProfile
from patients.models import PatientProfile
#create your model here
class Appointment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )

    DURATION_CHOICES = (
        (15, '15 minutes'),
        (30, '30 minutes'),
        (45, '45 minutes'),
        (60, '1 hour'),
        (90, '1.5 hours'),
        (120, '2 hours'),
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
    appointment_date = models.DateField(db_index=True)
    appointment_time = models.TimeField()
    duration = models.IntegerField(
        choices=DURATION_CHOICES,
        default=30,
        help_text='Duration in minutes'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f'{self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.appointment_date}'

    def clean(self):
        # 1. Past date check
        if self.appointment_date and self.appointment_date < timezone.now().date():
            raise ValidationError('Appointment date cannot be in the past.')

        # 2. Doctor availability check
        if self.doctor and not self.doctor.available:
            raise ValidationError(
                f'Dr. {self.doctor.user.get_full_name()} is currently not available for appointments.'
            )

        # 3. Conflict prevention — block double-booking
        if self.doctor and self.appointment_date and self.appointment_time:
            conflict = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                appointment_time=self.appointment_time,
            ).exclude(
                id=self.id  # exclude self when updating
            ).exclude(
                status__in=['cancelled', 'no_show']
            ).exists()

            if conflict:
                raise ValidationError(
                    f'Dr. {self.doctor.user.get_full_name()} already has an appointment '
                    f'on {self.appointment_date} at {self.appointment_time.strftime("%H:%M")}. '
                    f'Please choose a different time.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)