from django.contrib import admin
from .models import Appointment
# Register your models here.
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'consultation_type')
    list_filter = ('status', 'consultation_type', 'appointment_date', 'doctor')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name')
    ordering = ('-appointment_date',)
    readonly_fields = ('video_room',)
