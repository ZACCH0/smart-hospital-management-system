from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription
from .models import Notification

# ─── Appointment Signals ───────────────────────────────────────────

@receiver(post_save, sender=Appointment)
def notify_appointment_status_change(sender, instance, created, **kwargs):

    if created:
        # Notify doctor about new appointment request
        Notification.objects.create(
            user=instance.doctor.user,
            message=f'New appointment request from {instance.patient.user.get_full_name()} on {instance.appointment_date}.'
        )
        # Notify receptionist(s) about pending appointment
        from accounts.models import CustomUser
        receptionists = CustomUser.objects.filter(role='receptionist', is_active=True)
        for receptionist in receptionists:
            Notification.objects.create(
                user=receptionist,
                message=f'New appointment pending approval: {instance.patient.user.get_full_name()} with Dr. {instance.doctor.user.get_full_name()} on {instance.appointment_date}.'
            )

    else:
        # Notify patient when appointment approved
        if instance.status == 'approved':
            Notification.objects.create(
                user=instance.patient.user,
                message=f'Your appointment with Dr. {instance.doctor.user.get_full_name()} on {instance.appointment_date} has been approved.'
            )
        # Notify patient when appointment cancelled
        elif instance.status == 'cancelled':
            Notification.objects.create(
                user=instance.patient.user,
                message=f'Your appointment with Dr. {instance.doctor.user.get_full_name()} on {instance.appointment_date} has been cancelled.'
            )
        # Notify patient when appointment completed
        elif instance.status == 'completed':
            Notification.objects.create(
                user=instance.patient.user,
                message=f'Your appointment with Dr. {instance.doctor.user.get_full_name()} on {instance.appointment_date} has been marked as completed.'
            )


# ─── Medical Record Signals ────────────────────────────────────────

@receiver(post_save, sender=MedicalRecord)
def notify_medical_record_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.patient.user,
            message=f'Dr. {instance.doctor.user.get_full_name()} has added a new medical record for you. Diagnosis: {instance.diagnosis[:50]}...'
        )


# ─── Prescription Signals ──────────────────────────────────────────

@receiver(post_save, sender=Prescription)
def notify_prescription_added(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.medical_record.patient.user,
            message=f'A new prescription has been added: {instance.medicine_name} — {instance.dosage} for {instance.duration}.'
        )