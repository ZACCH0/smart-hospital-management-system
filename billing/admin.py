from django.contrib import admin
from .models import InsuranceProvider, Invoice, Payment
# Register your models here.
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'amount', 'status', 'insurance_provider',
        'insurance_claim_status', 'issued_date',
    )
    list_filter = ('status', 'insurance_claim_status', 'insurance_provider', 'issued_date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('issued_date',)

@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'email')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_method', 'payment_date')
    list_filter = ('payment_method', 'payment_date')
    readonly_fields = ('payment_date',)
    