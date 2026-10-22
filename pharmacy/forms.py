from django import forms
from .models import Medicine, Supplier, MedicineBatch


FIELD_CLASS = 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'category', 'stock_quantity', 'price', 'expiry_date', 'supplier']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'Medicine name'
            }),
            'category': forms.Select(attrs={'class': FIELD_CLASS}),
            'stock_quantity': forms.NumberInput(attrs={'class': FIELD_CLASS}),
            'price': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': FIELD_CLASS}),
            'supplier': forms.Select(attrs={'class': FIELD_CLASS}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Supplier name'}),
            'contact_person': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'phone': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'email': forms.EmailInput(attrs={'class': FIELD_CLASS}),
            'address': forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300'}),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model = MedicineBatch
        fields = ['batch_number', 'supplier', 'quantity_received', 'unit_cost', 'expiry_date']
        widgets = {
            'batch_number': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'e.g. PCM-2026-04'
            }),
            'supplier': forms.Select(attrs={'class': FIELD_CLASS}),
            'quantity_received': forms.NumberInput(attrs={'class': FIELD_CLASS, 'min': 1}),
            'unit_cost': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': FIELD_CLASS}),
        }
