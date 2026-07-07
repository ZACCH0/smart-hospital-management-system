from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import Notification

@receiver(post_save, sender=Appointment)
def notify_on_appointment_status_change(sender, instance, created, **kwargs):
    if instance.status == 'approved':
        Notification.objects.create(
            user=instance.patient.user,
            message=f'Your appointment with Dr. {instance.doctor.user.get_full_name()} on {instance.appointment_date} has been approved.'
        )
    elif instance.status == 'cancelled':
        Notification.objects.create(
            user=instance.patient.user,
            message=f'Your appointment with Dr. {instance.doctor.user.get_full_name()} on {instance.appointment_date} has been cancelled.'
        )