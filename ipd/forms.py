from django import forms

from .models import Admission, Bed, Ward


FIELD_CLASS = 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'


class WardForm(forms.ModelForm):
    class Meta:
        model = Ward
        fields = ['name', 'ward_type', 'floor', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g. Medical Ward A'}),
            'ward_type': forms.Select(attrs={'class': FIELD_CLASS}),
            'floor': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g. 2nd floor'}),
            'description': forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 3}),
        }


class BedForm(forms.ModelForm):
    class Meta:
        model = Bed
        fields = ['bed_number', 'is_active']
        widgets = {
            'bed_number': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g. 12A'}),
        }


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['patient', 'doctor', 'bed', 'diagnosis', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': FIELD_CLASS}),
            'doctor': forms.Select(attrs={'class': FIELD_CLASS}),
            'bed': forms.Select(attrs={'class': FIELD_CLASS}),
            'diagnosis': forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bed'].queryset = (
            Bed.objects.filter(is_active=True, ward__is_active=True)
            .exclude(admissions__status='admitted')
            .select_related('ward')
            .order_by('ward__name', 'bed_number')
        )
        self.fields['bed'].label_from_instance = lambda bed: f'{bed.ward.name} — Bed {bed.bed_number}'
        self.fields['notes'].required = False

    def clean_patient(self):
        patient = self.cleaned_data['patient']
        if Admission.objects.filter(patient=patient, status='admitted').exists():
            raise forms.ValidationError('This patient already has an active admission.')
        return patient

    def clean_bed(self):
        bed = self.cleaned_data['bed']
        if Admission.objects.filter(bed=bed, status='admitted').exists():
            raise forms.ValidationError('This bed is already occupied.')
        return bed


class DischargeForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['discharge_summary']
        widgets = {
            'discharge_summary': forms.Textarea(attrs={
                'class': FIELD_CLASS,
                'rows': 4,
                'placeholder': 'Treatment given, outcome, follow-up plan...',
            }),
        }
