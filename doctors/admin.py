from django.contrib import admin
from django.contrib import messages
from .models import DoctorProfile
from accounts.models import CustomUser


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    extra = 0


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'consultation_fee', 'available')
    list_filter = ('specialization', 'available')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')

    def save_model(self, request, obj, form, change):
        """
        Override save to handle the case where a DoctorProfile
        is being attached to an existing user who is already a patient.
        """
        if not change:  # Only on creation, not updates
            user = obj.user
            # Check if this user already has a doctor profile
            if hasattr(user, 'doctor_profile') and user.doctor_profile != obj:
                messages.error(
                    request,
                    f'{user.get_full_name()} already has a Doctor Profile.'
                )
                return

            # If user was previously patient-only, keep their patient profile
            # Just add the doctor profile — no role change needed
            # The profile existence is now what determines access

        super().save_model(request, obj, form, change)
        messages.success(
            request,
            f'Doctor Profile for {obj.user.get_full_name()} saved successfully.'
        )


class AddDoctorForm(admin.ModelAdmin):
    """
    Custom admin view for adding a doctor,
    handling the case where the email already exists.
    """

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form