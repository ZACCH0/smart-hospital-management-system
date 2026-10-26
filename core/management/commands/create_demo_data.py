from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

User = get_user_model()

CONSOLE_EMAIL = 'django.core.mail.backends.console.EmailBackend'


def attach_user_image(user, field_name, filename):
    """Attach a photo from the bundled seed_photos folder without overwriting."""
    field = getattr(user, field_name)
    if field:
        return False
    source = Path(settings.BASE_DIR) / 'seed_photos' / filename
    if not source.exists():
        return False
    with source.open('rb') as handle:
        field.save(source.name.replace('/', '_').replace('\\', '_'), File(handle), save=False)
    user.save(update_fields=[field_name])
    return True


class Command(BaseCommand):
    help = 'Create demo accounts and realistic fake data for SHMS demo environment'

    def handle(self, *args, **options):
        # Never send real emails from seed data (signals fire on creation).
        previous_email_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = CONSOLE_EMAIL
        try:
            self._seed()
        finally:
            settings.EMAIL_BACKEND = previous_email_backend

    def _seed(self):
        self.stdout.write('Creating demo data...')
        today = timezone.now().date()

        # Clean up existing demo accounts (demo-scoped only).
        # Admissions sit on PROTECT keys, so free them before the cascade.
        from ipd.models import Admission
        Admission.objects.filter(
            models.Q(patient__user__email__endswith='@shms-demo.com')
            | models.Q(doctor__user__email__endswith='@shms-demo.com')
        ).delete()
        User.objects.filter(email__endswith='@shms-demo.com').delete()

        demo_password = 'SHMSDemo2026!'

        #  Create Demo Users 
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

        doctor_user = User.objects.create_user(
            email='doctor@shms-demo.com',
            password=demo_password,
            first_name='James',
            last_name='Adeyemi',
            role='doctor',
            email_verified=True,
            is_active=True,
        )

        patient_user = User.objects.create_user(
            email='patient@shms-demo.com',
            password=demo_password,
            first_name='Precious',
            last_name='Okafor',
            role='patient',
            email_verified=True,
            is_active=True,
        )

        #  Seed photos (bundled in seed_photos/, survive deploys) 
        photos = [
            (doctor_user, 'profile_picture', 'doctors/james_adeyemi.jpg'),
            (doctor_user, 'profile_banner', 'banners/ward_corridor.jpg'),
            (patient_user, 'profile_picture', 'patients/precious_okafor.jpg'),
            (patient_user, 'profile_banner', 'banners/clinic_hall.jpg'),
            (receptionist, 'profile_picture', 'staff/sarah_bello.jpg'),
        ]
        attached = [
            f'{user.email}:{field}' for user, field, filename in photos if attach_user_image(user, field, filename)
        ]
        # Existing seeded doctors/receptionist from data.json (no @shms-demo.com email)
        for email, field, filename in [
            ('zacch@gmail.com', 'profile_picture', 'doctors/zacch_smart.jpg'),
            ('michealmorgan@gmail.com', 'profile_picture', 'doctors/micheal_morgan.jpg'),
            ('aladezaccheous74@gmail.com', 'profile_picture', 'doctors/hilda_titiloye.jpg'),
            ('lukegrace@gmail.com', 'profile_picture', 'doctors/grace_luke.jpg'),
            ('receptionist@gmail.com', 'profile_picture', 'staff/sarah_bello.jpg'),
        ]:
            existing = User.objects.filter(email=email).first()
            if existing and attach_user_image(existing, field, filename):
                attached.append(f'{email}:{field}')
        self.stdout.write(f'  ✓ Photos attached ({len(attached)})')
        for entry in attached:
            self.stdout.write(f'      · {entry}')

        #  Create Doctor Profile 
        from doctors.models import DoctorProfile, Specialty
        specialty, _ = Specialty.objects.get_or_create(
            slug='general', defaults={'name': 'General Medicine'},
        )
        doctor_profile = DoctorProfile.objects.create(
            user=doctor_user,
            specialization=specialty,
            qualification='MBBS, MD',
            experience_years=8,
            consultation_fee=Decimal('5000.00'),
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

        #  Extra showcase patients 
        extra_specs = [
            ('chidi@shms-demo.com', 'Chidi', 'Nwosu', date(1988, 3, 4), 'male', 'A-',
             'Penicillin', 'Hypertension', '12 Awolowo Road, Ikoyi, Lagos', '08123400002',
             'patients/chidi_nwosu.jpg'),
            ('amara@shms-demo.com', 'Amara', 'Obi', date(2001, 11, 23), 'female', 'O+',
             '', '', '5 Kudirat Abiola Way, Lagos', '08123400003', ''),
            ('tunde@shms-demo.com', 'Tunde', 'Bakare', date(2016, 7, 9), 'male', 'B+',
             '', 'Mild Asthma', '7 Adeola Odeku St, Victoria Island, Lagos', '08123400004', ''),
        ]
        extra_profiles = []
        for email, first, last, dob, gender, blood, allergies, conditions, address, phone, photo in extra_specs:
            extra_user = User.objects.create_user(
                email=email,
                password=demo_password,
                first_name=first,
                last_name=last,
                role='patient',
                email_verified=True,
                is_active=True,
                phone=phone,
            )
            if photo:
                attach_user_image(extra_user, 'profile_picture', photo)
            extra_profiles.append(
                PatientProfile.objects.create(
                    user=extra_user,
                    date_of_birth=dob,
                    gender=gender,
                    blood_group=blood,
                    allergies=allergies,
                    chronic_conditions=conditions,
                    address=address,
                )
            )
        chidi, amara, tunde = extra_profiles
        self.stdout.write('  ✓ Extra showcase patients created (Chidi, Amara, Tunde)')

        #  Appointments 
        from appointments.models import Appointment
        other_doctors = list(
            DoctorProfile.objects.filter(available=True)
            .exclude(user__email__endswith='@shms-demo.com')
            .order_by('id')[:2]
        )
        doctor_a = other_doctors[0] if other_doctors else doctor_profile
        doctor_b = other_doctors[1] if len(other_doctors) > 1 else doctor_profile

        Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=today,
            appointment_time='10:00',
            status='approved',
            reason='Routine checkup and blood pressure monitoring',
            duration=30,
        )
        Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=today + timedelta(days=1),
            appointment_time='14:00',
            status='pending',
            reason='Follow-up consultation',
            duration=30,
        )
        Appointment.objects.create(
            patient=chidi,
            doctor=doctor_a,
            appointment_date=today,
            appointment_time='12:00',
            status='approved',
            reason='High blood pressure review',
            duration=30,
        )
        Appointment.objects.create(
            patient=amara,
            doctor=doctor_profile,
            appointment_date=today + timedelta(days=1),
            appointment_time='15:00',
            status='pending',
            reason='Skin rash on arms',
            duration=30,
        )
        Appointment.objects.create(
            patient=tunde,
            doctor=doctor_b,
            appointment_date=today + timedelta(days=1),
            appointment_time='16:00',
            status='approved',
            reason='Persistent cough',
            duration=30,
        )
        Appointment.objects.create(
            patient=amara,
            doctor=doctor_profile,
            appointment_date=today + timedelta(days=2),
            appointment_time='13:00',
            status='approved',
            reason='Video follow-up on rash',
            duration=30,
            consultation_type='video',
        )
        # Completed appointment last week (bypass clean() for past-date demo)
        Appointment.objects.bulk_create([
            Appointment(
                patient=patient_profile,
                doctor=doctor_profile,
                appointment_date=today - timedelta(days=7),
                appointment_time='09:00',
                status='completed',
                reason='Malaria treatment follow-up',
                duration=30,
            ),
        ])
        self.stdout.write('  ✓ Demo Appointments created (incl. one video consult)')

        #  Medical records with vitals 
        from medical_records.models import MedicalRecord
        record = MedicalRecord.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            diagnosis='Acute Upper Respiratory Tract Infection (URTI)',
            symptoms='Sore throat, mild fever (38.2°C), runny nose, fatigue for 3 days',
            treatment='Rest, increased fluid intake, antipyretics for fever management. Antibiotics prescribed due to bacterial signs.',
            blood_pressure_systolic=118, blood_pressure_diastolic=76,
            heart_rate=88, temperature_c=Decimal('38.2'),
            oxygen_saturation=97, weight_kg=Decimal('64.0'), height_cm=Decimal('167.0'),
        )
        MedicalRecord.objects.create(
            patient=chidi,
            doctor=doctor_a,
            diagnosis='Essential Hypertension (Stage 1)',
            symptoms='Occasional headaches, high readings at home',
            treatment='Lifestyle modification, started Amlodipine 5mg daily. Review in 2 weeks.',
            blood_pressure_systolic=148, blood_pressure_diastolic=94,
            heart_rate=76, respiratory_rate=18, temperature_c=Decimal('36.8'),
            oxygen_saturation=98, weight_kg=Decimal('92.5'), height_cm=Decimal('176.0'),
        )
        MedicalRecord.objects.create(
            patient=amara,
            doctor=doctor_profile,
            diagnosis='Atopic Dermatitis — mild',
            symptoms='Itchy rash on both forearms, worse at night',
            treatment='Topical emollient + hydrocortisone 1% for 7 days. Avoid harsh soaps.',
            blood_pressure_systolic=110, blood_pressure_diastolic=70,
            heart_rate=72, temperature_c=Decimal('36.7'),
            weight_kg=Decimal('58.0'), height_cm=Decimal('163.0'),
        )
        MedicalRecord.objects.create(
            patient=tunde,
            doctor=doctor_b,
            diagnosis='Viral Upper Respiratory Infection',
            symptoms='Cough, catarrh, low-grade fever for 5 days',
            treatment='Supportive care, honey + warm fluids. Parent educated. Return if breathing worsens.',
            blood_pressure_systolic=100, blood_pressure_diastolic=60,
            heart_rate=92, respiratory_rate=22, temperature_c=Decimal('37.9'),
            oxygen_saturation=99, weight_kg=Decimal('34.0'), height_cm=Decimal('128.0'),
        )
        self.stdout.write('  ✓ Demo Medical Records created (with vitals)')

        #  Prescriptions 
        from pharmacy.services import dispense_prescription
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
        amoxicillin = self._ensure_medicine(
            'Amoxicillin 500mg', 'antibiotic', Decimal('250.00'), today + timedelta(days=365),
        )
        Prescription.objects.create(
            medical_record=MedicalRecord.objects.filter(patient=chidi).first(),
            medicine_name='Amoxicillin 500mg',
            dosage='1 capsule three times daily',
            duration='7 days',
            instructions='Take after meals. Complete the full course.',
            status='pending',
            medicine=amoxicillin,
            quantity=21,
        )
        dispense_rx = Prescription.objects.filter(
            medical_record__patient=chidi, status='pending',
        ).first()
        if dispense_rx:
            dispense_prescription(dispense_rx, admin)
        self.stdout.write('  ✓ Demo Prescriptions created (1 dispensed via FEFO)')

        #  Invoice and Payment 
        from billing.models import Invoice, Payment
        paid_invoice = Invoice.objects.create(
            patient=patient_profile,
            amount=Decimal('7500.00'),
            status='paid',
        )
        Payment.objects.create(
            invoice=paid_invoice,
            amount=Decimal('7500.00'),
            payment_method='card',
        )
        itemized_invoice = Invoice.objects.create(
            patient=chidi,
            amount=Decimal('0'),
        )
        from billing.models import InvoiceItem
        InvoiceItem.objects.create(
            invoice=itemized_invoice, description='Consultation — GP review',
            quantity=1, unit_price=Decimal('10000.00'),
        )
        InvoiceItem.objects.create(
            invoice=itemized_invoice, description='Lipid Profile (lab)',
            quantity=1, unit_price=Decimal('3500.00'),
        )
        InvoiceItem.objects.create(
            invoice=itemized_invoice, description='Ward bed — 1 night (Ward A)',
            quantity=1, unit_price=Decimal('15000.00'),
        )
        itemized_invoice.tax_rate = Decimal('7.5')
        itemized_invoice.recalculate()
        itemized_invoice.save()
        Payment.objects.create(
            invoice=itemized_invoice,
            amount=Decimal('10000.00'),
            payment_method='bank_transfer',
            reference='TRF-889201',
            received_by=admin,
        )
        itemized_invoice.refresh_status()
        self.stdout.write('  ✓ Demo Invoices created (itemized + tax + partial payment)')

        #  Insurance claim 
        from billing.models import InsuranceProvider
        hmo, _ = InsuranceProvider.objects.get_or_create(
            name='UnityCare HMO',
            defaults=dict(
                contact_person='Funke Adewale',
                phone='08099999999',
                email='claims@unitycare.example',
                address='22 Adeola Odeku, Victoria Island, Lagos',
            ),
        )
        Invoice.objects.create(
            patient=amara,
            amount=Decimal('18500.00'),
            subtotal=Decimal('18500.00'),
            insurance_provider=hmo,
            insurance_coverage_percent=Decimal('60.00'),
            insurance_claim_status='approved',
            insurance_claim_reference=f'UCM-{today.strftime("%y%m")}-0114',
        )
        self.stdout.write('  ✓ Demo Insurance claim created (UnityCare HMO, approved)')

        #  Pharmacy: suppliers, batches, low stock 
        from pharmacy.models import Medicine, Supplier
        Supplier.objects.get_or_create(
            name='ZacchMed Supplies Ltd',
            defaults=dict(
                contact_person='Kelechi Odo',
                phone='08000000000',
                email='sales@zacchmed.example',
                address='Plot 14, Industrial Layout, Ikeja, Lagos',
            ),
        )
        amlodipine = self._ensure_medicine(
            'Amlodipine 5mg', 'other', Decimal('90.00'), today + timedelta(days=400),
        )
        paracetamol = self._ensure_medicine(
            'Paracetamol 500mg', 'analgesic', Decimal('50.00'), today + timedelta(days=730),
        )
        self._ensure_medicine(
            'Artemether/Lumefantrine 80/480mg', 'antimalarial', Decimal('1500.00'),
            today + timedelta(days=180), stock_quantity=8,
        )
        self._receive_batches(
            [
                (amlodipine, 'AML-2601', 200, today + timedelta(days=400)),
                (paracetamol, 'PCM-1207', 500, today + timedelta(days=730)),
                (amoxicillin, 'AMX-3345', 100, today + timedelta(days=240)),
            ],
            admin,
        )
        self.stdout.write('  ✓ Demo Pharmacy created (supplier, batches, low-stock item)')

        #  Laboratory 
        from laboratory.models import LabResult, LabTest
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
        fbs = LabTest.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            test_name='Fasting Blood Sugar',
            status='completed',
            sample_status='collected',
            sample_collected_at=timezone.now(),
            technician=admin,
        )
        LabResult.objects.create(
            lab_test=fbs,
            result='Elevated fasting glucose. Repeat in 1 month; consider HbA1c.',
            result_value=Decimal('8.4'),
            unit='mmol/L',
            reference_low=Decimal('3.9'),
            reference_high=Decimal('5.5'),
        )
        LabTest.objects.create(
            patient=chidi,
            doctor=doctor_a,
            test_name='Lipid Profile',
            status='in_progress',
            sample_status='collected',
            sample_collected_at=timezone.now(),
            technician=admin,
        )
        LabTest.objects.create(
            patient=amara,
            doctor=doctor_profile,
            test_name='Blood Culture',
            status='pending',
        )
        self.stdout.write('  ✓ Demo Lab tests created (pending → in progress → abnormal completed)')

        #  Wards, beds, admissions (IPD) 
        from ipd.models import Admission, Bed, Ward
        ward_a, _ = Ward.objects.get_or_create(
            name='Ward A',
            defaults=dict(ward_type='general', floor='1', description='General medical ward'),
        )
        icu, _ = Ward.objects.get_or_create(
            name='Intensive Care Unit',
            defaults=dict(ward_type='icu', floor='2', description='Critical care'),
        )
        for ward, count in [(ward_a, 6), (icu, 4)]:
            for number in range(1, count + 1):
                Bed.objects.get_or_create(ward=ward, bed_number=str(number))
        bed_targets = [
            (Bed.objects.get(ward=ward_a, bed_number='2'), chidi, 'Hypertensive urgency observation'),
            (Bed.objects.get(ward=ward_a, bed_number='5'), amara, 'Dehydration + rashes observation'),
            (Bed.objects.get(ward=icu, bed_number='1'), patient_profile, 'Post-malaria recovery monitoring'),
        ]
        for bed, patient, diagnosis in bed_targets:
            if bed.admissions.filter(status='admitted').exists():
                continue
            Admission.objects.create(
                patient=patient,
                doctor=doctor_profile,
                bed=bed,
                diagnosis=diagnosis,
                admitted_by=admin,
                notes='Vitals every 8 hours. Nurse review morning and evening.',
            )
        self.stdout.write('  ✓ Demo Wards/Admissions created (3 occupied beds)')

        #  Notifications 
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
        self.stdout.write('  ✓ Demo Notifications created')

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Demo data created successfully!\n'
            '\nDemo Login Credentials:\n'
            f'  Admin:        admin@shms-demo.com / {demo_password}\n'
            f'  Doctor:       doctor@shms-demo.com / {demo_password}\n'
            f'  Receptionist: receptionist@shms-demo.com / {demo_password}\n'
            f'  Patient:      patient@shms-demo.com / {demo_password}\n'
            '  Extra patients (chidi/amara/tunde@shms-demo.com), same password.\n'
        ))

    def _ensure_medicine(self, name, category, price, expiry_date, stock_quantity=0):
        from pharmacy.models import Medicine
        medicine, created = Medicine.objects.get_or_create(
            name=name,
            defaults=dict(
                category=category,
                stock_quantity=stock_quantity,
                price=price,
                expiry_date=expiry_date,
            ),
        )
        return medicine

    def _receive_batches(self, items, admin):
        from pharmacy.models import Supplier
        from pharmacy.services import receive_stock
        supplier = Supplier.objects.filter(name='ZacchMed Supplies Ltd').first()
        for medicine, batch_number, quantity, expiry_date in items:
            if medicine.batches.filter(batch_number=batch_number).exists():
                continue
            receive_stock(
                medicine,
                batch_number,
                quantity,
                expiry_date,
                supplier=supplier,
                unit_cost=Decimal('45.00'),
                user=admin,
            )
