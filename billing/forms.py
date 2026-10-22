from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from .models import InsuranceProvider, Invoice, InvoiceItem, Payment


FIELD_CLASS = 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'patient', 'appointment', 'tax_rate', 'amount',
            'insurance_provider', 'insurance_coverage_percent',
            'insurance_claim_status', 'insurance_claim_reference',
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': FIELD_CLASS}),
            'appointment': forms.Select(attrs={'class': FIELD_CLASS}),
            'tax_rate': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01', 'min': 0, 'max': 100}),
            'amount': forms.NumberInput(attrs={
                'class': FIELD_CLASS,
                'step': '0.01',
                'placeholder': 'Ignored when line items are added'
            }),
            'insurance_provider': forms.Select(attrs={'class': FIELD_CLASS}),
            'insurance_coverage_percent': forms.NumberInput(
                attrs={'class': FIELD_CLASS, 'step': '0.01', 'min': 0, 'max': 100}
            ),
            'insurance_claim_status': forms.Select(attrs={'class': FIELD_CLASS}),
            'insurance_claim_reference': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'Claim / authorization number (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['appointment'].required = False
        self.fields['appointment'].empty_label = 'No specific appointment'
        self.fields['amount'].required = False
        self.fields['amount'].help_text = (
            'Use this only for a simple invoice without line items.'
        )
        self.fields['insurance_provider'].required = False
        self.fields['insurance_provider'].empty_label = 'Self-pay (no insurance)'
        self.fields['insurance_coverage_percent'].required = False
        self.fields['insurance_claim_status'].required = False
        self.fields['insurance_claim_reference'].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('insurance_claim_status'):
            cleaned['insurance_claim_status'] = (
                'pending' if cleaned.get('insurance_provider') else 'not_required'
            )
        return cleaned


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'e.g. Consultation fee'
            }),
            'quantity': forms.NumberInput(attrs={'class': FIELD_CLASS, 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].required = False
        self.fields['unit_price'].required = False

    def clean(self):
        cleaned = super().clean()
        description = cleaned.get('description')
        if not description:
            return cleaned
        if cleaned.get('quantity') in (None, ''):
            cleaned['quantity'] = 1
        if cleaned.get('unit_price') in (None, ''):
            self.add_error('unit_price', 'Enter a unit price for this line.')
        return cleaned


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=3,
    can_delete=True,
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': FIELD_CLASS, 'step': '0.01', 'min': 0}),
            'payment_method': forms.Select(attrs={'class': FIELD_CLASS}),
            'reference': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'Receipt / transaction reference (optional)'
            }),
        }

    def __init__(self, *args, invoice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice = invoice
        self.fields['reference'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Enter an amount greater than zero.')
        if self.invoice is not None and amount > self.invoice.balance_due:
            raise forms.ValidationError(
                f'Amount exceeds the balance due (₦{self.invoice.balance_due}).'
            )
        return amount


class InsuranceProviderForm(forms.ModelForm):
    class Meta:
        model = InsuranceProvider
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g. Hygeia HMO'}),
            'contact_person': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'phone': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'email': forms.EmailInput(attrs={'class': FIELD_CLASS}),
            'address': forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('contact_person', 'phone', 'email', 'address'):
            self.fields[name].required = False


class InsuranceClaimForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['insurance_provider', 'insurance_coverage_percent',
                  'insurance_claim_status', 'insurance_claim_reference']
        widgets = {
            'insurance_provider': forms.Select(attrs={'class': FIELD_CLASS}),
            'insurance_coverage_percent': forms.NumberInput(
                attrs={'class': FIELD_CLASS, 'step': '0.01', 'min': 0, 'max': 100}
            ),
            'insurance_claim_status': forms.Select(attrs={'class': FIELD_CLASS}),
            'insurance_claim_reference': forms.TextInput(attrs={'class': FIELD_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['insurance_provider'].required = True
        self.fields['insurance_provider'].empty_label = 'Choose a provider'
        self.fields['insurance_coverage_percent'].required = False
        self.fields['insurance_claim_reference'].required = False
