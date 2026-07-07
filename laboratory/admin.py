from django.contrib import admin
from .models import LabTest, LabResult
# Register your models here.

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'patient', 'doctor', 'status', 'requested_date')
    list_filter = ('status', 'requested_date')
    search_fields = ('test_name', 'patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('requested_date',)

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('lab_test', 'created_at')
    readonly_fields = ('created_at',)