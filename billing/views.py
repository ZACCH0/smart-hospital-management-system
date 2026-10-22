from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from core.audit import log_action
from core.decorators import patient_required, role_required
from notifications.services import notify

from .forms import (
    InsuranceClaimForm,
    InsuranceProviderForm,
    InvoiceForm,
    InvoiceItemFormSet,
    PaymentForm,
)
from .models import InsuranceProvider, Invoice, Payment


@login_required
@role_required('admin', 'receptionist')
def invoice_list(request):
    invoices = (
        Invoice.objects
        .select_related('patient__user')
        .prefetch_related('payments')
        .order_by('-issued_date')
    )

    total_billed = Invoice.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_paid = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_pending = total_billed - total_paid
    if total_pending < 0:
        total_pending = Decimal('0')

    page_obj = Paginator(invoices, 20).get_page(request.GET.get('page'))

    return render(request, 'billing/invoice_list.html', {
        'invoices': page_obj,
        'page_obj': page_obj,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_billed': total_billed,
    })


@login_required
@role_required('admin', 'receptionist')
def create_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.amount = invoice.amount or Decimal('0')

            items = [
                data for data in (f.cleaned_data for f in formset.forms)
                if data and data.get('description') and not data.get('DELETE')
            ]

            if not items and invoice.amount <= 0:
                form.add_error('amount', 'Add at least one line item or enter a total amount.')
            else:
                with transaction.atomic():
                    invoice.save()
                    formset.instance = invoice
                    formset.save()
                    invoice.recalculate()
                    invoice.save()

                notify(
                    invoice.patient.user,
                    (
                        f'A new invoice of ₦{invoice.amount} has been generated for your visit. '
                        f'Status: {invoice.get_status_display()}.'
                    ),
                    category='billing',
                    email_subject=f'Invoice #{invoice.id} generated',
                    email_body=(
                        f'Invoice #{invoice.id}\n'
                        f'Subtotal: ₦{invoice.subtotal}\n'
                        f'Tax: ₦{invoice.tax_amount}\n'
                        f'Total: ₦{invoice.amount}\n'
                        f'Status: {invoice.get_status_display()}'
                    ),
                )
                log_action(
                    request, 'create', 'Invoice', invoice.id, str(invoice),
                    details=f'Amount: ₦{invoice.amount}, Tax: ₦{invoice.tax_amount}, '
                            f'{len(items)} line item(s)'
                )
                messages.success(request, 'Invoice created successfully.')
                return redirect('billing:invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Invoice',
    })


@login_required
@role_required('admin', 'receptionist')
def record_payment(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related('patient__user').prefetch_related('payments'),
        id=invoice_id,
    )

    if invoice.balance_due <= 0:
        messages.error(request, 'This invoice is already fully paid.')
        return redirect('billing:invoice_list')

    if request.method == 'POST':
        form = PaymentForm(request.POST, invoice=invoice)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.received_by = request.user
            payment.save()

            invoice.refresh_status()

            log_action(
                request, 'payment', 'Payment', payment.id,
                f'Payment for Invoice #{invoice.id}',
                details=f'Amount: ₦{payment.amount}, '
                        f'Method: {payment.get_payment_method_display()}, '
                        f'Balance: ₦{invoice.balance_due}'
            )

            notify(
                invoice.patient.user,
                (
                    f'Payment of ₦{payment.amount} received via '
                    f'{payment.get_payment_method_display()}. '
                    f'Balance due: ₦{invoice.balance_due}.'
                ),
                category='billing',
                email_subject=f'Payment received for Invoice #{invoice.id}',
                email_body=(
                    f'We received ₦{payment.amount} via '
                    f'{payment.get_payment_method_display()}.\n'
                    f'Invoice total: ₦{invoice.amount}\n'
                    f'Balance due: ₦{invoice.balance_due}'
                ),
            )

            messages.success(request, 'Payment recorded successfully.')
            return redirect('billing:invoice_list')
    else:
        form = PaymentForm(invoice=invoice, initial={'amount': invoice.balance_due})

    return render(request, 'billing/record_payment.html', {
        'form': form,
        'invoice': invoice,
    })


@login_required
@patient_required
def patient_invoices(request):
    patient_profile = request.user.patient_profile

    invoices = (
        patient_profile.invoices
        .select_related('patient__user')
        .prefetch_related('payments')
        .order_by('-issued_date')
    )

    total_billed = invoices.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_paid = Decimal('0')
    for invoice in invoices:
        total_paid += invoice.amount_paid
    total_pending = total_billed - total_paid
    if total_pending < 0:
        total_pending = Decimal('0')

    return render(request, 'billing/patient_invoices.html', {
        'invoices': invoices,
        'total_paid': total_paid,
        'total_pending': total_pending,
    })


@login_required
@role_required('admin', 'receptionist')
def insurance_providers(request):
    providers = InsuranceProvider.objects.annotate(
        invoice_count=Count('invoices')
    ).order_by('name')
    return render(request, 'billing/insurance_provider_list.html', {
        'providers': providers,
    })


@login_required
@role_required('admin', 'receptionist')
def insurance_provider_form(request, provider_id=None):
    provider = None
    if provider_id:
        provider = get_object_or_404(InsuranceProvider, id=provider_id)

    if request.method == 'POST':
        form = InsuranceProviderForm(request.POST, instance=provider)
        if form.is_valid():
            saved = form.save()
            log_action(
                request,
                'update' if provider_id else 'create',
                'InsuranceProvider', saved.id, saved.name,
            )
            messages.success(request, 'Insurance provider saved.')
            return redirect('billing:insurance_providers')
    else:
        form = InsuranceProviderForm(instance=provider)

    return render(request, 'billing/insurance_provider_form.html', {
        'form': form,
        'provider': provider,
        'title': 'Edit Provider' if provider else 'Add Insurance Provider',
    })


@login_required
@role_required('admin', 'receptionist')
def update_insurance_claim(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related('patient__user', 'insurance_provider'),
        id=invoice_id,
    )

    if request.method == 'POST':
        previous_status = invoice.insurance_claim_status
        form = InsuranceClaimForm(request.POST, instance=invoice)
        if form.is_valid():
            claim = form.save()

            log_action(
                request, 'update', 'Invoice', claim.id,
                f'Insurance claim for Invoice #{claim.id}',
                details=(
                    f'{claim.insurance_provider} covers '
                    f'{claim.insurance_coverage_percent}% '
                    f'(N{claim.insurance_amount}); status: '
                    f'{claim.get_insurance_claim_status_display()}'
                ),
            )

            if claim.insurance_claim_status in ('approved', 'rejected', 'settled') and \
                    claim.insurance_claim_status != previous_status:
                notify(
                    claim.patient.user,
                    (
                        f'Your insurance claim for Invoice #{claim.id} was '
                        f'{claim.get_insurance_claim_status_display().lower()}. '
                        f'Patient share: N{claim.patient_responsibility}.'
                    ),
                    category='billing',
                    email_subject=f'Insurance claim update for Invoice #{claim.id}',
                    email_body=(
                        f'Provider: {claim.insurance_provider}\n'
                        f'Coverage: {claim.insurance_coverage_percent}% '
                        f'(N{claim.insurance_amount})\n'
                        f'Patient share: N{claim.patient_responsibility}\n'
                        f'Status: {claim.get_insurance_claim_status_display()}'
                    ),
                )

            messages.success(request, 'Insurance claim updated.')
            return redirect('billing:invoice_list')
    else:
        form = InsuranceClaimForm(instance=invoice)

    return render(request, 'billing/insurance_claim_form.html', {
        'form': form,
        'invoice': invoice,
    })
