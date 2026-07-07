from django.contrib import admin
from .models import DoctorProfile
# Register your models here.

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'consultation_fee', 'available')
    list_filter = ('specialization', 'available')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')