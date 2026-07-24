from django import forms
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'symptoms', 'treatment', 'appointment']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter diagnosis'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Describe symptoms observed'
            }),
            'treatment': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Describe treatment plan'
            }),
            'appointment': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, doctor=None, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        if doctor and patient:
            from appointments.models import Appointment
            self.fields['appointment'].queryset = Appointment.objects.filter(
                doctor=doctor,
                patient=patient,
                status='approved'
            )
            self.fields['appointment'].required = False
            self.fields['appointment'].empty_label = 'No specific appointment'


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['medicine_name', 'dosage', 'duration', 'instructions']
        widgets = {
            'medicine_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g. Paracetamol 500mg'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g. 1 tablet twice daily'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g. 7 days'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Additional instructions (optional)'
            }),
        }