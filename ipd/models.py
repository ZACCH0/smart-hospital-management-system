from django.conf import settings
from django.db import models
from django.utils import timezone

from doctors.models import DoctorProfile
from patients.models import PatientProfile


class Ward(models.Model):

    WARD_TYPES = (
        ('general', 'General'),
        ('private', 'Private'),
        ('icu', 'ICU'),
        ('maternity', 'Maternity'),
        ('pediatric', 'Pediatric'),
        ('surgical', 'Surgical'),
    )

    name = models.CharField(max_length=100, unique=True)
    ward_type = models.CharField(max_length=20, choices=WARD_TYPES, default='general')
    floor = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_ward_type_display()})'

    @property
    def total_beds(self):
        return self.beds.filter(is_active=True).count()

    @property
    def occupied_beds(self):
        return self.beds.filter(is_active=True, admissions__status='admitted').count()

    @property
    def available_beds(self):
        return self.total_beds - self.occupied_beds


class Bed(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ward__name', 'bed_number']
        constraints = [
            models.UniqueConstraint(
                fields=['ward', 'bed_number'],
                name='unique_bed_per_ward',
            ),
        ]

    def __str__(self):
        return f'{self.ward.name} / Bed {self.bed_number}'

    @property
    def current_admission(self):
        return self.admissions.filter(status='admitted').select_related('patient__user').first()

    @property
    def is_occupied(self):
        return self.current_admission is not None


class Admission(models.Model):

    STATUS_CHOICES = (
        ('admitted', 'Admitted'),
        ('discharged', 'Discharged'),
    )

    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name='admissions'
    )
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.PROTECT, related_name='admissions'
    )
    bed = models.ForeignKey(
        Bed, on_delete=models.PROTECT, related_name='admissions'
    )
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='admitted', db_index=True)
    admitted_at = models.DateTimeField(default=timezone.now)
    discharged_at = models.DateTimeField(null=True, blank=True)
    discharge_summary = models.TextField(blank=True)
    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admissions_created',
    )
    discharged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admissions_discharged',
    )

    class Meta:
        ordering = ['-admitted_at']
        indexes = [
            models.Index(fields=['status', 'admitted_at'], name='admission_status_date_idx'),
            models.Index(fields=['patient', 'status'], name='admission_patient_status_idx'),
            models.Index(fields=['bed', 'status'], name='admission_bed_status_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['patient'],
                condition=models.Q(status='admitted'),
                name='unique_active_admission_patient',
            ),
            models.UniqueConstraint(
                fields=['bed'],
                condition=models.Q(status='admitted'),
                name='unique_active_admission_bed',
            ),
        ]

    def __str__(self):
        return f'{self.patient.user.get_full_name()} - {self.bed} ({self.get_status_display()})'

    @property
    def length_of_stay(self):
        end = self.discharged_at or timezone.now()
        days = (end - self.admitted_at).days
        return max(days, 0)
