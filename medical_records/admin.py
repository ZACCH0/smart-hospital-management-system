from django.contrib import admin
from .models import MedicalRecord
# Register your models here.
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'diagnosis', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'diagnosis')
    readonly_fields = ('created_at', 'updated_at')