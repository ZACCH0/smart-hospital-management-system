from django import forms
from .models import Medicine


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'category', 'stock_quantity', 'price', 'expiry_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Medicine name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }