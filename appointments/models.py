import secrets

from django.conf import settings
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

    CONSULTATION_CHOICES = (
        ('in_person', 'In person'),
        ('video', 'Video consultation'),
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
        default='pending'
    )
    reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    consultation_type = models.CharField(
        max_length=12,
        choices=CONSULTATION_CHOICES,
        default='in_person',
        db_index=True,
    )
    video_room = models.CharField(
        max_length=64,
        blank=True,
        help_text='Auto-generated room token for video consultations.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['doctor', 'appointment_date'], name='appt_doctor_date_idx'),
            models.Index(fields=['patient', 'appointment_date'], name='appt_patient_date_idx'),
            models.Index(fields=['status', 'appointment_date'], name='appt_status_date_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=~models.Q(status__in=['cancelled', 'no_show']),
                name='unique_active_doctor_slot',
            ),
        ]

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
        if self.consultation_type == 'video':
            if not self.video_room:
                self.video_room = secrets.token_hex(8)
        else:
            self.video_room = ''
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_video(self):
        return self.consultation_type == 'video' and bool(self.video_room)

    @property
    def video_url(self):
        """Provider-agnostic meeting link, built from settings."""
        if not self.is_video:
            return ''
        base = settings.TELEHEALTH_MEETING_BASE_URL
        if not base.endswith('/'):
            base += '/'
        return f'{base}{settings.TELEHEALTH_ROOM_PREFIX}{self.video_room}'

    @property
    def can_join_video(self):
        return self.is_video and self.status == 'approved'
