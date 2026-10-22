from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from core.testing import make_doctor, make_patient

from medical_records.models import MedicalRecord
from prescriptions.models import Prescription

from .models import Medicine, MedicineBatch, StockTransaction, Supplier
from .services import StockError, dispense_prescription, receive_stock


class PharmacyTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_patient()
        self.supplier = Supplier.objects.create(name='Acme Pharma')
        self.medicine = Medicine.objects.create(
            name='Amoxicillin 500mg',
            category='antibiotic',
            stock_quantity=0,
            price='250.00',
            expiry_date=date.today() + timedelta(days=365),
        )
        self.record = MedicalRecord.objects.create(
            patient=self.patient, doctor=self.doctor, diagnosis='Infection',
        )

    def _prescription(self, quantity=6):
        return Prescription.objects.create(
            medical_record=self.record,
            medicine=self.medicine,
            medicine_name=self.medicine.name,
            dosage='1 tablet three times daily',
            duration='5 days',
            quantity=quantity,
        )

    def test_receive_stock_creates_batch_and_ledger(self):
        receive_stock(
            self.medicine, 'B-001', 20,
            date.today() + timedelta(days=365), supplier=self.supplier,
        )
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 20)
        self.assertEqual(self.medicine.batches.count(), 1)
        self.assertEqual(StockTransaction.objects.filter(transaction_type='in').count(), 1)

    def test_dispense_uses_oldest_expiry_first(self):
        receive_stock(self.medicine, 'LATE', 10, date.today() + timedelta(days=365))
        receive_stock(self.medicine, 'EARLY', 10, date.today() + timedelta(days=30))

        rx = self._prescription(quantity=6)
        dispense_prescription(rx, self.patient.user)

        rx.refresh_from_db()
        self.assertEqual(rx.status, 'dispensed')
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 14)

        early = MedicineBatch.objects.get(batch_number='EARLY')
        late = MedicineBatch.objects.get(batch_number='LATE')
        self.assertEqual(early.quantity_remaining, 4)
        self.assertEqual(late.quantity_remaining, 10)
        self.assertEqual(
            StockTransaction.objects.filter(transaction_type='out').count(), 1
        )

    def test_short_stock_is_rejected_and_unchanged(self):
        receive_stock(self.medicine, 'ONLY', 5, date.today() + timedelta(days=90))
        rx = self._prescription(quantity=10)
        with self.assertRaises(StockError):
            dispense_prescription(rx, self.patient.user)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 5)
        rx.refresh_from_db()
        self.assertEqual(rx.status, 'pending')

    def test_patient_is_notified_on_dispense(self):
        receive_stock(self.medicine, 'B-2', 10, date.today() + timedelta(days=90))
        rx = self._prescription(quantity=3)
        dispense_prescription(rx, self.patient.user)
        self.assertTrue(
            self.patient.user.notifications.filter(category='pharmacy').exists()
        )
