from django import forms
from accounts.models import CustomUser


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
