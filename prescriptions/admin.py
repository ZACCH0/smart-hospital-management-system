from django.contrib import admin
from .models import Prescription
# Register your models here.

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('medicine_name', 'dosage', 'duration', 'medical_record', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('medicine_name', 'medical_record__patient__user__first_name')
    readonly_fields = ('created_at',)