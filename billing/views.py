from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Invoice, Payment
from .forms import InvoiceForm, PaymentForm
from core.audit import log_action
from notifications.models import Notification

# Create your views here.
@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-issued_date')
    total_paid = Invoice.objects.filter(
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = Invoice.objects.filter(
        status='pending'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices,
        'total_paid': total_paid,
        'total_pending': total_pending,
    })


@login_required
def create_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()

            # Notify patient
            from notifications.models import Notification
            Notification.objects.create(
                user=invoice.patient.user,
                message=f'A new invoice of ₦{invoice.amount} has been generated for your visit. Status: {invoice.get_status_display()}.'
            )
            messages.success(request, 'Invoice created successfully.')
            return redirect('billing:invoice_list')
    else:
        form = InvoiceForm()
    log_action(
    request,
    action='create',
    model_name='Invoice',
    object_id=invoice.id,
    object_repr=str(invoice),
    details=f'Amount: ₦{invoice.amount}, Status: {invoice.status}'
)

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'title': 'Create Invoice'
    })

@login_required
def record_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # Check if payment already exists
    if hasattr(invoice, 'payment'):
        messages.error(request, 'Payment already recorded for this invoice.')
        return redirect('billing:invoice_list')

    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()

            # Mark invoice as paid
            invoice.status = 'paid'
            invoice.save()

            log_action(
                request,
                action='payment',
                model_name='Payment',
                object_id=payment.id,
                object_repr=f'Payment for Invoice #{invoice.id}',
                details=f'Amount: ₦{payment.amount}, Method: {payment.get_payment_method_display()}'
            )

            # Notify patient
            Notification.objects.create(
                user=invoice.patient.user,
                message=f'Payment of ₦{payment.amount} received via {payment.get_payment_method_display()}. Thank you!'
            )

            messages.success(request, 'Payment recorded successfully.')
            return redirect('billing:invoice_list')

    else:
        form = PaymentForm(initial={'amount': invoice.amount})

        return render(request, 'billing/record_payment.html', {
            'form': form,
            'invoice': invoice,
        })
        
@login_required
def patient_invoices(request):
    try:
        patient_profile = request.user.patient_profile
    except Exception:
        return redirect('dashboard:patient_home')

    invoices = patient_profile.invoices.all().order_by('-issued_date')

    return render(request, 'billing/patient_invoices.html', {
        'invoices': invoices,
    })