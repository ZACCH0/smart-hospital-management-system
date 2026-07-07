from django.contrib import admin
from .models import Medicine
# Register your models here.
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'stock_quantity', 'price', 'expiry_date', 'is_low_stock', 'is_expired')
    list_filter = ('category',)
    search_fields = ('name',)