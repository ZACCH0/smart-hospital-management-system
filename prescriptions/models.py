from django.db import models
from medical_records.models import MedicalRecord
# Create your models here.
class Prescription(models.Model):

    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.medicine_name} for {self.medical_record.patient.user.get_full_name()}'