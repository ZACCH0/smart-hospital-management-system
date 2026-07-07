from django.contrib import admin
from .models import Invoice, Payment
# Register your models here.
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'amount', 'status', 'issued_date')
    list_filter = ('status', 'issued_date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('issued_date',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_method', 'payment_date')
    list_filter = ('payment_method', 'payment_date')
    readonly_fields = ('payment_date',)
    