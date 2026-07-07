from django.contrib import admin
from .models import PatientProfile
# Register your models here.

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'blood_group', 'age', 'emergency_contact')
    list_filter = ('gender', 'blood_group')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')