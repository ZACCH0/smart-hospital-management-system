from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo accounts and realistic fake data for SHMS demo environment'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')

        # Clean up existing demo accounts
        User.objects.filter(email__endswith='@shms-demo.com').delete()

        #  Create Demo Users 
        demo_password = 'SHMSDemo2026!'

        # Demo Admin
        admin = User.objects.create_user(
            email='admin@shms-demo.com',
            password=demo_password,
            first_name='Demo',
            last_name='Admin',
            role='admin',
            is_staff=True,
            is_superuser=True,
            email_verified=True,
            is_active=True,
        )
        self.stdout.write(f'  ✓ Demo Admin created: {admin.email}')

        # Demo Receptionist
        receptionist = User.objects.create_user(
            email='receptionist@shms-demo.com',
            password=demo_password,
            first_name='Sarah',
            last_name='Bello',
            role='receptionist',
            email_verified=True,
            is_active=True,
        )
        self.stdout.write(f'  ✓ Demo Receptionist created: {receptionist.email}')

        # Demo Doctor
        doctor_user = User.objects.create_user(
            email='doctor@shms-demo.com',
            password=demo_password,
            first_name='Dr. James',
            last_name='Adeyemi',
            role='doctor',
            email_verified=True,
            is_active=True,
        )

        # Demo Patient
        patient_user = User.objects.create_user(
            email='patient@shms-demo.com',
            password=demo_password,
            first_name='Precious',
            last_name='Okafor',
            role='patient',
            email_verified=True,
            is_active=True,
        )

        #  Create Doctor Profile 
        from doctors.models import DoctorProfile
        doctor_profile = DoctorProfile.objects.create(
            user=doctor_user,
            specialization='general',
            qualification='MBBS, MD',
            experience_years=8,
            consultation_fee=5000.00,
            available=True,
        )
        self.stdout.write(f'  ✓ Demo Doctor created: {doctor_user.email}')

        #  Create Patient Profile 
        from patients.models import PatientProfile
        patient_profile = PatientProfile.objects.create(
            user=patient_user,
            date_of_birth=date(1995, 6, 15),
            gender='female',
            blood_group='O+',
            address='14 Ademola Street, Ikeja, Lagos',
            emergency_contact='08012345678',
        )
        self.stdout.write(f'  ✓ Demo Patient created: {patient_user.email}')

        #  Create Demo Appointments 
        from appointments.models import Appointment
        today = timezone.now().date()

        # Approved appointment today
        appt1 = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=today,
            appointment_time='10:00',
            status='approved',
            reason='Routine checkup and blood pressure monitoring',
            duration=30,
        )

        # Pending appointment tomorrow
        appt2 = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=today + timedelta(days=1),
            appointment_time='14:00',
            status='pending',
            reason='Follow-up consultation',
            duration=30,
        )

        # Completed appointment last week
        # Bypass clean() for past date demo data
        appt3 = Appointment(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=today - timedelta(days=7),
            appointment_time='09:00',
            status='completed',
            reason='Malaria treatment follow-up',
            duration=30,
        )
        Appointment.objects.bulk_create([appt3])
        self.stdout.write(f'  ✓ Demo Appointments created')

        #  Create Medical Record 
        from medical_records.models import MedicalRecord
        record = MedicalRecord.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            diagnosis='Acute Upper Respiratory Tract Infection (URTI)',
            symptoms='Sore throat, mild fever (38.2°C), runny nose, fatigue for 3 days',
            treatment='Rest, increased fluid intake, antipyretics for fever management. Antibiotics prescribed due to bacterial signs.',
        )
        self.stdout.write(f'  ✓ Demo Medical Record created')

        #  Create Prescriptions 
        from prescriptions.models import Prescription
        Prescription.objects.create(
            medical_record=record,
            medicine_name='Amoxicillin 500mg',
            dosage='1 capsule three times daily',
            duration='7 days',
            instructions='Take after meals. Complete the full course.',
        )
        Prescription.objects.create(
            medical_record=record,
            medicine_name='Paracetamol 500mg',
            dosage='2 tablets every 6 hours when needed',
            duration='3 days',
            instructions='Take only when temperature exceeds 38°C.',
        )
        self.stdout.write(f'  ✓ Demo Prescriptions created')

        #  Create Lab Test 
        from laboratory.models import LabTest, LabResult
        lab_test = LabTest.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            test_name='Full Blood Count (FBC)',
            status='completed',
        )
        LabResult.objects.create(
            lab_test=lab_test,
            result='WBC: 11.2 x10⁹/L (slightly elevated), RBC: 4.8 x10¹²/L (normal), Haemoglobin: 13.2 g/dL (normal), Platelets: 285 x10⁹/L (normal). Mild leukocytosis consistent with bacterial infection.',
        )
        self.stdout.write(f'  ✓ Demo Lab Test and Result created')

        # Create Invoice and Payment 
        from billing.models import Invoice, Payment
        invoice = Invoice.objects.create(
            patient=patient_profile,
            appointment=appt1,
            amount=7500.00,
            status='paid',
        )
        Payment.objects.create(
            invoice=invoice,
            amount=7500.00,
            payment_method='card',
        )
        self.stdout.write(f'  ✓ Demo Invoice and Payment created')

        # Create Pharmacy Items 
        from pharmacy.models import Medicine
        Medicine.objects.get_or_create(
            name='Amoxicillin 500mg',
            defaults={
                'category': 'antibiotic',
                'stock_quantity': 500,
                'price': 250.00,
                'expiry_date': today + timedelta(days=365),
            }
        )
        Medicine.objects.get_or_create(
            name='Paracetamol 500mg',
            defaults={
                'category': 'analgesic',
                'stock_quantity': 1000,
                'price': 50.00,
                'expiry_date': today + timedelta(days=730),
            }
        )
        Medicine.objects.get_or_create(
            name='Artemether/Lumefantrine 80/480mg',
            defaults={
                'category': 'antimalarial',
                'stock_quantity': 8,  # low stock for demo
                'price': 1500.00,
                'expiry_date': today + timedelta(days=180),
            }
        )
        self.stdout.write(f'  ✓ Demo Medicines created')

        #  Create Notifications 
        from notifications.models import Notification
        Notification.objects.create(
            user=patient_user,
            message=f'Your appointment with Dr. {doctor_user.get_full_name()} on {today} has been approved.',
            is_read=False,
        )
        Notification.objects.create(
            user=patient_user,
            message='Your Full Blood Count (FBC) result is ready. Please check with your doctor.',
            is_read=False,
        )
        Notification.objects.create(
            user=doctor_user,
            message=f'New appointment request from {patient_user.get_full_name()} on {today + timedelta(days=1)}.',
            is_read=False,
        )
        self.stdout.write(f'  ✓ Demo Notifications created')

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Demo data created successfully!\n'
            '\nDemo Login Credentials:\n'
            f'  Admin:        admin@shms-demo.com / {demo_password}\n'
            f'  Doctor:       doctor@shms-demo.com / {demo_password}\n'
            f'  Receptionist: receptionist@shms-demo.com / {demo_password}\n'
            f'  Patient:      patient@shms-demo.com / {demo_password}\n'
        ))