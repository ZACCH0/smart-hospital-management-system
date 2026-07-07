from django.db import models
from doctors.models import DoctorProfile
from patients.models import PatientProfile
# Create your models here.

class LabTest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
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

    class Meta:
        ordering = ['-requested_date']

    def __str__(self):
        return f'{self.test_name} - {self.patient.user.get_full_name()} ({self.status})'


class LabResult(models.Model):

    lab_test = models.OneToOneField(
        LabTest,
        on_delete=models.CASCADE,
        related_name='result'
    )
    result = models.TextField()
    report_file = models.FileField(upload_to='lab_reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Result for {self.lab_test.test_name}'