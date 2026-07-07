from django import forms
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full border rounded px-3 py-2'}),
            'patient': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'doctor': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 3}),
        }