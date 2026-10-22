from django import forms
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'appointment', 'diagnosis', 'symptoms', 'treatment',
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'temperature_c',
            'oxygen_saturation', 'weight_kg', 'height_cm',
        ]
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
        numeric = 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        for name in (
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'temperature_c',
            'oxygen_saturation', 'weight_kg', 'height_cm',
        ):
            self.fields[name].widget = forms.NumberInput(attrs={
                'class': numeric,
                'step': '0.1',
                'inputmode': 'decimal',
            })
            self.fields[name].required = False

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
        fields = [
            'medicine', 'medicine_name', 'dosage', 'duration',
            'quantity', 'instructions',
        ]
        widgets = {
            'medicine': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
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
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 1,
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Additional instructions (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from pharmacy.models import Medicine
        self.fields['medicine'].queryset = Medicine.objects.filter(
            stock_quantity__gt=0
        ).order_by('name')
        self.fields['medicine'].required = False
        self.fields['medicine'].empty_label = 'Not from pharmacy stock'
        self.fields['medicine'].help_text = 'Link a stocked medicine so pharmacy can dispense in one tap.'
        self.fields['quantity'].required = False
        self.fields['quantity'].initial = 1