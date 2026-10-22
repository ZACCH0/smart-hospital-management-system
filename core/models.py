from django.db import models
from django.conf import settings

# Create your models here.

class AuditLog(models.Model):

    ACTION_CHOICES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('access', 'Accessed'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
        ('payment', 'Payment Recorded'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'timestamp'], name='audit_user_time_idx'),
            models.Index(fields=['action', 'timestamp'], name='audit_action_time_idx'),
            models.Index(fields=['model_name', 'object_id'], name='audit_object_idx'),
        ]

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else 'Anonymous'
        return f'{user_str} — {self.get_action_display()} — {self.model_name} — {self.timestamp:%Y-%m-%d %H:%M}'