from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from core.testing import make_patient, make_staff

from .forms import InvoiceItemFormSet
from .models import InsuranceProvider, Invoice, Payment


class BillingTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.receptionist = make_staff()
        self.patient = make_patient()
        self.client.force_login(self.receptionist)
        self.prefix = InvoiceItemFormSet().prefix

    def _invoice_payload(self, items, tax='7.50', amount=''):
        data = {
            'patient': self.patient.id,
            'appointment': '',
            'tax_rate': tax,
            'amount': amount,
            f'{self.prefix}-TOTAL_FORMS': str(len(items)),
            f'{self.prefix}-INITIAL_FORMS': '0',
            f'{self.prefix}-MIN_NUM_FORMS': '0',
            f'{self.prefix}-MAX_NUM_FORMS': '1000',
        }
        for index, (description, quantity, price) in enumerate(items):
            data[f'{self.prefix}-{index}-description'] = description
            data[f'{self.prefix}-{index}-quantity'] = str(quantity)
            data[f'{self.prefix}-{index}-unit_price'] = str(price)
            data[f'{self.prefix}-{index}-id'] = ''
        return data

    def test_invoice_items_and_tax_are_calculated(self):
        response = self.client.post('/billing/create/', self._invoice_payload([
            ('Consultation', 1, '5000'),
            ('Lab panel', 2, '2000'),
        ]))
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.latest('id')
        self.assertEqual(invoice.subtotal, Decimal('9000.00'))
        self.assertEqual(invoice.tax_amount, Decimal('675.00'))
        self.assertEqual(invoice.amount, Decimal('9675.00'))
        self.assertEqual(invoice.items.count(), 2)

    def test_manual_amount_without_items(self):
        self.client.post('/billing/create/', self._invoice_payload([], tax='0', amount='1500'))
        invoice = Invoice.objects.latest('id')
        self.assertEqual(invoice.amount, Decimal('1500.00'))

    def test_empty_invoice_is_rejected(self):
        before = Invoice.objects.count()
        response = self.client.post('/billing/create/', self._invoice_payload([], tax='0', amount=''))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invoice.objects.count(), before)

    def test_partial_then_full_payment(self):
        invoice = Invoice.objects.create(
            patient=self.patient, subtotal='1000.00', amount='1000.00',
        )
        self.client.post(
            f'/billing/{invoice.id}/payment/',
            {'amount': '400', 'payment_method': 'cash', 'reference': 'RCPT-1'},
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'partially_paid')
        self.assertEqual(invoice.amount_paid, Decimal('400.00'))
        self.assertEqual(invoice.balance_due, Decimal('600.00'))

        self.client.post(
            f'/billing/{invoice.id}/payment/',
            {'amount': '600', 'payment_method': 'card'},
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(invoice.balance_due, Decimal('0'))
        self.assertEqual(invoice.payments.count(), 2)

    def test_overpayment_is_rejected(self):
        invoice = Invoice.objects.create(
            patient=self.patient, subtotal='1000.00', amount='1000.00',
        )
        self.client.post(
            f'/billing/{invoice.id}/payment/',
            {'amount': '400', 'payment_method': 'cash'},
        )
        response = self.client.post(
            f'/billing/{invoice.id}/payment/',
            {'amount': '9999', 'payment_method': 'cash'},
        )
        invoice.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(invoice.payments.count(), 1)
        self.assertEqual(invoice.balance_due, Decimal('600.00'))

    def test_patient_cannot_browse_all_invoices(self):
        patient_client = Client(SERVER_NAME='localhost')
        patient_client.force_login(self.patient.user)
        self.assertEqual(patient_client.get('/billing/').status_code, 403)
        self.assertEqual(patient_client.get('/billing/create/').status_code, 403)
        self.assertEqual(patient_client.get('/billing/my-invoices/').status_code, 200)


class InsuranceTests(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.receptionist = make_staff()
        self.patient = make_patient()
        self.provider = InsuranceProvider.objects.create(
            name='Hygeia HMO', phone='07000000000', email='claims@hygeia.example',
        )
        self.client.force_login(self.receptionist)

    def _invoice(self, coverage='50.00', claim_status='not_required'):
        return Invoice.objects.create(
            patient=self.patient,
            subtotal='20000.00',
            amount='20000.00',
            insurance_provider=self.provider,
            insurance_coverage_percent=coverage,
            insurance_claim_status=claim_status,
        )

    def test_insurance_share_is_calculated(self):
        invoice = self._invoice()
        self.assertEqual(invoice.insurance_amount, Decimal('10000.00'))
        self.assertEqual(invoice.patient_responsibility, Decimal('10000.00'))

    def test_claim_status_defaults_to_pending_when_provider_set(self):
        invoice = Invoice.objects.create(
            patient=self.patient, subtotal='1000.00', amount='1000.00',
            insurance_provider=self.provider, insurance_coverage_percent='20',
            insurance_claim_status='not_required',
        )
        invoice.full_clean()
        self.assertEqual(invoice.insurance_claim_status, 'pending')

    def test_coverage_without_provider_is_rejected(self):
        invoice = Invoice(
            patient=self.patient, subtotal='1000.00', amount='1000.00',
            insurance_coverage_percent='50',
        )
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_claim_update_notifies_patient(self):
        invoice = self._invoice(claim_status='pending')
        response = self.client.post(f'/billing/{invoice.id}/insurance/', {
            'insurance_provider': self.provider.id,
            'insurance_coverage_percent': '50',
            'insurance_claim_status': 'approved',
            'insurance_claim_reference': 'HMO-7788',
        })
        self.assertEqual(response.status_code, 302)

        invoice.refresh_from_db()
        self.assertEqual(invoice.insurance_claim_status, 'approved')
        self.assertEqual(invoice.insurance_claim_reference, 'HMO-7788')
        self.assertTrue(
            self.patient.user.notifications.filter(category='billing').exists()
        )

    def test_patient_cannot_manage_insurance(self):
        invoice = self._invoice()
        patient_client = Client(SERVER_NAME='localhost')
        patient_client.force_login(self.patient.user)
        self.assertEqual(
            patient_client.get('/billing/insurance/providers/').status_code, 403
        )
        self.assertEqual(
            patient_client.get(f'/billing/{invoice.id}/insurance/').status_code, 403
        )

    def test_provider_pages_render(self):
        self.assertEqual(
            self.client.get('/billing/insurance/providers/').status_code, 200
        )
        self.assertEqual(
            self.client.get('/billing/insurance/providers/add/').status_code, 200
        )
        invoice = self._invoice(claim_status='pending')
        self.assertEqual(
            self.client.get(f'/billing/{invoice.id}/insurance/').status_code, 200
        )
        self.assertEqual(self.client.get('/billing/').status_code, 200)

    def test_invoice_creation_captures_insurance(self):
        prefix = InvoiceItemFormSet().prefix
        response = self.client.post('/billing/create/', {
            'patient': self.patient.id,
            'appointment': '',
            'tax_rate': '0',
            'amount': '',
            'insurance_provider': self.provider.id,
            'insurance_coverage_percent': '80',
            'insurance_claim_status': '',
            'insurance_claim_reference': 'AUTH-42',
            f'{prefix}-TOTAL_FORMS': '1',
            f'{prefix}-INITIAL_FORMS': '0',
            f'{prefix}-MIN_NUM_FORMS': '0',
            f'{prefix}-MAX_NUM_FORMS': '1000',
            f'{prefix}-0-description': 'Surgery',
            f'{prefix}-0-quantity': '1',
            f'{prefix}-0-unit_price': '50000',
            f'{prefix}-0-id': '',
        })
        self.assertEqual(response.status_code, 302)
        invoice = Invoice.objects.latest('id')
        self.assertEqual(invoice.insurance_claim_status, 'pending')
        self.assertEqual(invoice.insurance_amount, Decimal('40000.00'))
        self.assertEqual(invoice.patient_responsibility, Decimal('10000.00'))
        self.assertEqual(invoice.insurance_claim_reference, 'AUTH-42')
