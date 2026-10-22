from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from appointments.models import Appointment

# Create your models here.

class MedicalRecord(models.Model):

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_records'
    )
    diagnosis = models.TextField()
    symptoms = models.TextField(blank=True)
    treatment = models.TextField(blank=True)

    # Vital signs captured during the visit (all optional)
    blood_pressure_systolic = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text='mmHg',
    )
    blood_pressure_diastolic = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        help_text='mmHg',
    )
    heart_rate = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        help_text='beats per minute',
    )
    respiratory_rate = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(80)],
        help_text='breaths per minute',
    )
    temperature_c = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(45)],
        help_text='degrees Celsius',
    )
    oxygen_saturation = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        help_text='percent',
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'created_at'], name='record_patient_date_idx'),
        ]

    def __str__(self):
        return f'Record: {self.patient.user.get_full_name()} - {self.created_at.strftime("%Y-%m-%d")}'

    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f'{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}'
        return ''

    @property
    def bmi(self):
        if not (self.weight_kg and self.height_cm):
            return None
        height_m = float(self.height_cm) / 100
        if height_m <= 0:
            return None
        return round(float(self.weight_kg) / (height_m ** 2), 1)

    @property
    def has_vitals(self):
        return any((
            self.blood_pressure_systolic,
            self.blood_pressure_diastolic,
            self.heart_rate,
            self.respiratory_rate,
            self.temperature_c,
            self.oxygen_saturation,
            self.weight_kg,
            self.height_cm,
        ))