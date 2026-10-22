from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from doctors.models import DoctorProfile
from patients.models import PatientProfile
from core.validators import validate_document_file


class LabTest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    SAMPLE_STATUS_CHOICES = (
        ('awaiting', 'Awaiting collection'),
        ('collected', 'Collected'),
        ('rejected', 'Rejected'),
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='lab_tests'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='lab_tests'
    )
    test_name = models.CharField(max_length=200)
    requested_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sample_status = models.CharField(
        max_length=20, choices=SAMPLE_STATUS_CHOICES, default='awaiting'
    )
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_tests_technician',
        limit_choices_to={'role__in': ['admin', 'receptionist']},
    )

    class Meta:
        ordering = ['-requested_date']
        indexes = [
            models.Index(fields=['patient', 'status'], name='lab_patient_status_idx'),
            models.Index(fields=['status', 'requested_date'], name='lab_status_date_idx'),
            models.Index(fields=['sample_status'], name='lab_sample_status_idx'),
        ]

    def __str__(self):
        return f'{self.test_name} - {self.patient.user.get_full_name()} ({self.status})'


class LabResult(models.Model):

    lab_test = models.OneToOneField(
        LabTest,
        on_delete=models.CASCADE,
        related_name='result'
    )
    result = models.TextField()
    result_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    unit = models.CharField(max_length=30, blank=True)
    reference_low = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reference_high = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    report_file = models.FileField(
        upload_to='lab_reports/', blank=True, null=True,
        validators=[validate_document_file],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Result for {self.lab_test.test_name}'

    def clean(self):
        if (self.reference_low is not None and self.reference_high is not None
                and self.reference_low > self.reference_high):
            raise ValidationError('Reference low cannot be greater than reference high.')

    @property
    def is_abnormal(self):
        if self.result_value is None:
            return False
        if self.reference_low is not None and self.result_value < self.reference_low:
            return True
        if self.reference_high is not None and self.result_value > self.reference_high:
            return True
        return False

    @property
    def reference_range_display(self):
        if self.reference_low is None and self.reference_high is None:
            return ''
        low = '' if self.reference_low is None else f'{self.reference_low}'
        high = '' if self.reference_high is None else f'{self.reference_high}'
        return f'{low} – {high}'.strip()
