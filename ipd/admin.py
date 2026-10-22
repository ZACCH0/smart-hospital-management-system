from django.contrib import admin

from .models import Admission, Bed, Ward


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('name', 'ward_type', 'floor', 'is_active')
    list_filter = ('ward_type', 'is_active')
    search_fields = ('name',)


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('ward', 'bed_number', 'is_active')
    list_filter = ('ward', 'is_active')
    search_fields = ('bed_number', 'ward__name')


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'bed', 'status', 'admitted_at', 'discharged_at')
    list_filter = ('status', 'bed__ward')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'diagnosis')
    date_hierarchy = 'admitted_at'
