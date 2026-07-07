from django.db import models
from datetime import date
# Create your models here.
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

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.stock_quantity} in stock)'

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.LOW_STOCK_THRESHOLD

    @property
    def is_expired(self):
        return self.expiry_date < date.today()