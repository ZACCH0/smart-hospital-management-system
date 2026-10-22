from django import forms
from .models import LabTest, LabResult


FIELD_CLASS = 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'


class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ['patient', 'test_name']
        widgets = {
            'patient': forms.Select(attrs={'class': FIELD_CLASS}),
            'test_name': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'e.g. Full Blood Count, Malaria Test'
            }),
        }


class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = [
            'result', 'result_value', 'unit',
            'reference_low', 'reference_high', 'report_file',
        ]
        widgets = {
            'result': forms.Textarea(attrs={
                'class': FIELD_CLASS,
                'rows': 4,
                'placeholder': 'Enter test result details'
            }),
            'result_value': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g. g/dL'}),
            'reference_low': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01'}),
            'reference_high': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01'}),
            'report_file': forms.FileInput(attrs={'class': FIELD_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('result_value', 'unit', 'reference_low', 'reference_high'):
            self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        low = cleaned.get('reference_low')
        high = cleaned.get('reference_high')
        if low is not None and high is not None and low > high:
            raise forms.ValidationError('Reference low cannot be greater than reference high.')
        return cleaned
