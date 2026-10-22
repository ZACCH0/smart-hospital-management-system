from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from patients.models import PatientProfile
from appointments.models import Appointment


class InsuranceProvider(models.Model):
    """HMO / TPA that covers part of a patient's bill."""

    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Insurance Provider'
        verbose_name_plural = 'Insurance Providers'

    def __str__(self):
        return self.name


class Invoice(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )

    CLAIM_STATUS_CHOICES = (
        ('not_required', 'Not required'),
        ('pending', 'Claim pending'),
        ('approved', 'Claim approved'),
        ('rejected', 'Claim rejected'),
        ('settled', 'Settled by insurer'),
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percent',
    )
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    insurance_provider = models.ForeignKey(
        InsuranceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
    )
    insurance_coverage_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Share of the invoice covered by the insurer',
    )
    insurance_claim_status = models.CharField(
        max_length=20, choices=CLAIM_STATUS_CHOICES, default='not_required', db_index=True,
    )
    insurance_claim_reference = models.CharField(max_length=120, blank=True)
    issued_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['patient', 'status'], name='invoice_patient_status_idx'),
            models.Index(fields=['status', 'issued_date'], name='invoice_status_date_idx'),
            models.Index(fields=['insurance_claim_status'], name='invoice_claim_status_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name='invoice_amount_non_negative',
            ),
        ]

    def __str__(self):
        return f'Invoice #{self.id} - {self.patient.user.get_full_name()} - ₦{self.amount}'

    def recalculate(self):
        """Items drive the subtotal; without items the manual amount is the subtotal."""
        items = list(self.items.all())
        if items:
            subtotal = sum((item.line_total for item in items), Decimal('0'))
        else:
            subtotal = self.amount or Decimal('0')

        tax = (subtotal * (self.tax_rate or Decimal('0')) / Decimal('100')).quantize(Decimal('0.01'))
        self.subtotal = subtotal.quantize(Decimal('0.01'))
        self.tax_amount = tax
        self.amount = self.subtotal + tax
        return self.amount

    @property
    def amount_paid(self):
        return sum((p.amount for p in self.payments.all()), Decimal('0'))

    @property
    def balance_due(self):
        balance = self.amount - self.amount_paid
        return balance if balance > 0 else Decimal('0')

    @property
    def insurance_amount(self):
        """The portion of the invoice the insurer is expected to cover."""
        if not self.insurance_provider_id or not self.insurance_coverage_percent:
            return Decimal('0')
        total = Decimal(str(self.amount or 0))
        percent = Decimal(str(self.insurance_coverage_percent))
        covered = (total * percent / Decimal('100'))
        return covered.quantize(Decimal('0.01'))

    @property
    def patient_responsibility(self):
        """Amount the patient must pay after the insurer's share."""
        total = Decimal(str(self.amount or 0))
        share = total - self.insurance_amount
        return share if share > 0 else Decimal('0')

    def clean(self):
        super().clean()
        if self.insurance_coverage_percent and not self.insurance_provider_id:
            raise ValidationError({
                'insurance_coverage_percent': 'Choose an insurance provider first.',
            })
        if self.insurance_coverage_percent > 100:
            raise ValidationError({
                'insurance_coverage_percent': 'Coverage cannot exceed 100%.',
            })
        if self.insurance_provider_id and self.insurance_claim_status == 'not_required':
            self.insurance_claim_status = 'pending'

    def refresh_status(self, commit=True):
        cache = getattr(self, '_prefetched_objects_cache', {})
        cache.pop('payments', None)
        paid = self.amount_paid
        if paid >= self.amount and self.amount > 0:
            self.status = 'paid'
        elif paid > 0:
            self.status = 'partially_paid'
        else:
            self.status = 'pending'
        if commit:
            self.save(update_fields=['status'])
        return self.status


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.description} x{self.quantity}'

    @property
    def line_total(self):
        return (self.unit_price * self.quantity).quantize(Decimal('0.01'))


class Payment(models.Model):

    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('insurance', 'Insurance'),
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=120, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_payments',
    )
    payment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
        indexes = [models.Index(fields=['payment_date'], name='payment_date_idx')]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='payment_amount_positive',
            ),
        ]

    def __str__(self):
        return f'Payment of ₦{self.amount} for Invoice #{self.invoice.id}'
