from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Medicine(models.Model):

    CATEGORY_CHOICES = (
        ('analgesic', 'Analgesic / Pain Relief'),
        ('antibiotic', 'Antibiotic'),
        ('antimalarial', 'Antimalarial'),
        ('antiviral', 'Antiviral'),
        ('vitamin', 'Vitamin / Supplement'),
        ('other', 'Other'),
    )

    LOW_STOCK_THRESHOLD = 10

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    stock_quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    expiry_date = models.DateField()
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicines'
    )

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['expiry_date'], name='medicine_expiry_idx')]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name='medicine_price_non_negative',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.stock_quantity} in stock)'

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.LOW_STOCK_THRESHOLD

    @property
    def is_expired(self):
        return self.expiry_date < date.today()


class MedicineBatch(models.Model):
    """One delivery of a medicine. Stock is issued oldest-expiry first."""

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches'
    )
    batch_number = models.CharField(max_length=80)
    quantity_received = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000000)]
    )
    quantity_remaining = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    expiry_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date', 'received_date']
        constraints = [
            models.UniqueConstraint(
                fields=['medicine', 'batch_number'],
                name='unique_medicine_batch_number',
            ),
        ]

    def __str__(self):
        return f'{self.medicine.name} batch {self.batch_number}'

    @property
    def is_expired(self):
        return self.expiry_date < date.today()


class StockTransaction(models.Model):

    TYPE_CHOICES = (
        ('in', 'Stock in'),
        ('out', 'Dispensed'),
        ('adjustment', 'Adjustment'),
        ('expired', 'Expired write-off'),
    )

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='stock_transactions')
    batch = models.ForeignKey(
        MedicineBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', 'created_at'], name='stock_med_date_idx'),
            models.Index(fields=['transaction_type', 'created_at'], name='stock_type_date_idx'),
        ]

    def __str__(self):
        return f'{self.get_transaction_type_display()} {self.quantity} x {self.medicine.name}'
