from django import forms
from accounts.models import CustomUser
from doctors.models import DoctorProfile


INPUT_CLS = 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'


class ReceptionistProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'profile_picture', 'profile_banner']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
            }),
            'profile_banner': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
            }),
        }


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'profile_picture', 'profile_banner']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLS}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLS}),
            'profile_picture': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
            }),
            'profile_banner': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
            }),
        }


class DoctorClinicalForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['qualification', 'experience_years', 'consultation_fee']
        widgets = {
            'qualification': forms.TextInput(attrs={
                'class': INPUT_CLS,
                'placeholder': 'e.g. MBBS, MD Dermatology',
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': INPUT_CLS, 'min': 0,
            }),
            'consultation_fee': forms.NumberInput(attrs={
                'class': INPUT_CLS, 'min': 0, 'step': '0.01',
            }),
        }
