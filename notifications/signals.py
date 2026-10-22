from django.db.models.signals import post_save
from django.dispatch import receiver

from appointments.models import Appointment
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription

from .services import notify

# ---------------------------------------------------------------- Appointments


@receiver(post_save, sender=Appointment)
def notify_appointment_status_change(sender, instance, created, **kwargs):
    patient_name = instance.patient.user.get_full_name()
    doctor_name = f'Dr. {instance.doctor.user.get_full_name()}'

    if created:
        notify(
            instance.doctor.user,
            f'New appointment request from {patient_name} on {instance.appointment_date}.',
            category='appointment',
            email_subject='New appointment request',
            email_body=(
                f'{patient_name} has requested an appointment on '
                f'{instance.appointment_date} at {instance.appointment_time}.'
            ),
        )

        from accounts.models import CustomUser
        receptionists = CustomUser.objects.filter(role='receptionist', is_active=True)
        for receptionist in receptionists:
            notify(
                receptionist,
                f'New appointment pending approval: {patient_name} with {doctor_name} on {instance.appointment_date}.',
                category='appointment',
                email_subject='Appointment awaiting approval',
                email_body=(
                    f'{patient_name} booked with {doctor_name} on '
                    f'{instance.appointment_date} at {instance.appointment_time}.'
                ),
            )
        return

    if instance.status == 'approved':
        video_note = (
            ' This is a video consultation — open "My Appointments" and click Join Video at the appointment time.'
            if instance.is_video else ''
        )
        notify(
            instance.patient.user,
            f'Your appointment with {doctor_name} on {instance.appointment_date} has been approved.',
            category='appointment',
            email_subject='Your appointment is approved',
            email_body=(
                f'Your appointment with {doctor_name} on {instance.appointment_date} '
                f'at {instance.appointment_time} has been approved.{video_note}'
            ),
        )
    elif instance.status == 'cancelled':
        notify(
            instance.patient.user,
            f'Your appointment with {doctor_name} on {instance.appointment_date} has been cancelled.',
            category='appointment',
            email_subject='Your appointment was cancelled',
            email_body=(
                f'Your appointment with {doctor_name} on {instance.appointment_date} '
                f'at {instance.appointment_time} has been cancelled.'
            ),
        )
    elif instance.status == 'completed':
        notify(
            instance.patient.user,
            f'Your appointment with {doctor_name} on {instance.appointment_date} has been marked as completed.',
            category='appointment',
            email_subject='Appointment completed',
            email_body=(
                f'Your visit with {doctor_name} on {instance.appointment_date} is complete. '
                'Check your dashboard for records and prescriptions.'
            ),
        )


# ------------------------------------------------------------- Medical records


@receiver(post_save, sender=MedicalRecord)
def notify_medical_record_created(sender, instance, created, **kwargs):
    if created:
        notify(
            instance.patient.user,
            f'Dr. {instance.doctor.user.get_full_name()} has added a new medical record for you. '
            f'Diagnosis: {instance.diagnosis[:50]}...',
            category='medical_record',
            email_subject='New medical record available',
            email_body=(
                f'A new medical record was added by Dr. {instance.doctor.user.get_full_name()}.\n\n'
                f'Diagnosis: {instance.diagnosis}'
            ),
        )


# -------------------------------------------------------------- Prescriptions


@receiver(post_save, sender=Prescription)
def notify_prescription_added(sender, instance, created, **kwargs):
    if created:
        notify(
            instance.medical_record.patient.user,
            f'A new prescription has been added: {instance.medicine_name} — '
            f'{instance.dosage} for {instance.duration}.',
            category='prescription',
            email_subject='New prescription added',
            email_body=(
                f'Your doctor added a prescription.\n\n'
                f'Medicine: {instance.medicine_name}\n'
                f'Dosage: {instance.dosage}\n'
                f'Duration: {instance.duration}'
            ),
        )
