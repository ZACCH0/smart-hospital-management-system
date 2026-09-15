from django import forms
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    """Receptionist appointment booking form."""

    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_date',
            'appointment_time', 'duration', 'reason'
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded px-3 py-2'
            }),
            'appointment_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full border rounded px-3 py-2'
            }),
            'patient': forms.Select(attrs={
                'class': 'w-full border rounded px-3 py-2'
            }),
            'doctor': forms.Select(attrs={
                'class': 'w-full border rounded px-3 py-2'
            }),
            'duration': forms.Select(attrs={
                'class': 'w-full border rounded px-3 py-2'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'rows': 3
            }),
        }

class CancelAppointmentForm(forms.ModelForm):
    """Form for cancelling an appointment with a reason."""

    class Meta:
        model = Appointment
        fields = ['cancellation_reason']
        widgets = {
            'cancellation_reason': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': 'Please provide a reason for cancellation...'
            }),
        }
        labels = {
            'cancellation_reason': 'Reason for Cancellation'
        }


class MarkNoShowForm(forms.Form):
    """Simple confirmation form for marking no-show."""
    confirm = forms.BooleanField(
        required=True,
        label='I confirm this patient did not show up for their appointment'
    )