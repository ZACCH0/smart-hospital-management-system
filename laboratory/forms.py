from django import forms
from .models import LabTest, LabResult

class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ['patient', 'test_name']
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'test_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g. Full Blood Count, Malaria Test'
            }),
        }

class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = ['result', 'report_file']
        widgets = {
            'result': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Enter test result details'
            }),
            'report_file': forms.FileInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2'
            }),
        }