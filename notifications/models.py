from django.db import models
from django.conf import settings
# Create your models here.

class Notification(models.Model):

    CATEGORY_CHOICES = (
        ('system', 'System'),
        ('appointment', 'Appointment'),
        ('medical_record', 'Medical Record'),
        ('prescription', 'Prescription'),
        ('laboratory', 'Laboratory'),
        ('pharmacy', 'Pharmacy'),
        ('billing', 'Billing'),
        ('admission', 'Admission'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system', db_index=True)
    is_read = models.BooleanField(default=False,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at'], name='notif_user_read_date_idx'),
            models.Index(fields=['category', 'created_at'], name='notif_category_date_idx'),
        ]

    def __str__(self):
        return f'{self.user.get_full_name()}: {self.message[:50]}'