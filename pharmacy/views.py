from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from core.audit import log_action
from core.decorators import role_required
from prescriptions.models import Prescription

from .forms import BatchForm, MedicineForm, SupplierForm
from .models import Medicine, MedicineBatch, StockTransaction, Supplier
from .services import StockError, dispense_prescription as dispense_service
from .services import receive_stock as receive_stock_service


@login_required
@role_required('admin', 'receptionist')
def medicine_list(request):
    query = (request.GET.get('q') or '').strip()
    medicines = Medicine.objects.select_related('supplier')
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) | Q(supplier__name__icontains=query)
        )
    medicines = medicines.order_by('name')

    counts = medicines.aggregate(
        low_stock=Count('id', filter=Q(stock_quantity__lte=Medicine.LOW_STOCK_THRESHOLD)),
        expired=Count('id', filter=Q(expiry_date__lt=date.today())),
    )

    from django.core.paginator import Paginator
    page_obj = Paginator(medicines, 20).get_page(request.GET.get('page'))

    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': page_obj,
        'page_obj': page_obj,
        'low_stock_count': counts['low_stock'],
        'expired_count': counts['expired'],
        'query': query,
        'querystring': f'q={query}' if query else '',
    })


@login_required
@role_required('admin', 'receptionist')
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save()
            log_action(
                request, 'create', 'Medicine', medicine.id, str(medicine),
                details=f'Initial stock: {medicine.stock_quantity}'
            )
            messages.success(request, 'Medicine added successfully.')
            return redirect('pharmacy:medicine_list')
    else:
        form = MedicineForm()

    return render(request, 'pharmacy/medicine_form.html', {
        'form': form,
        'title': 'Add Medicine'
    })


@login_required
@role_required('admin', 'receptionist')
def edit_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)

    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            log_action(
                request, 'update', 'Medicine', medicine.id, str(medicine),
                details=f'Stock: {medicine.stock_quantity}'
            )
            messages.success(request, 'Medicine updated successfully.')
            return redirect('pharmacy:medicine_list')
    else:
        form = MedicineForm(instance=medicine)

    return render(request, 'pharmacy/medicine_form.html', {
        'form': form,
        'title': 'Edit Medicine',
        'medicine': medicine
    })


@login_required
@role_required('admin', 'receptionist')
def delete_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)

    if request.method != 'POST':
        messages.error(request, 'Use the delete button in the medicine list.')
        return redirect('pharmacy:medicine_list')

    if medicine.prescriptions.exists() or medicine.stock_transactions.exists():
        messages.error(
            request,
            f'{medicine.name} has stock history or prescriptions and cannot be deleted. '
            'Set its stock to 0 instead.'
        )
        return redirect('pharmacy:medicine_list')

    name = medicine.name
    log_action(request, 'delete', 'Medicine', medicine.id, name, details='Removed from catalogue')
    medicine.delete()
    messages.success(request, f'{name} deleted successfully.')
    return redirect('pharmacy:medicine_list')


@login_required
@role_required('admin', 'receptionist')
def receive_stock(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)

    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.medicine = medicine
            try:
                saved = receive_stock_service(
                    medicine=medicine,
                    batch_number=form.cleaned_data['batch_number'],
                    quantity=form.cleaned_data['quantity_received'],
                    expiry_date=form.cleaned_data['expiry_date'],
                    supplier=form.cleaned_data['supplier'],
                    unit_cost=form.cleaned_data['unit_cost'],
                    user=request.user,
                )
            except Exception as exc:
                messages.error(request, f'Could not receive stock: {exc}')
            else:
                log_action(
                    request, 'create', 'MedicineBatch', saved.id, str(saved),
                    details=f'+{saved.quantity_received} units for {medicine.name}'
                )
                messages.success(
                    request,
                    f'{saved.quantity_received} units added to {medicine.name} '
                    f'(batch {saved.batch_number}).'
                )
                return redirect('pharmacy:medicine_list')
    else:
        form = BatchForm()

    return render(request, 'pharmacy/receive_stock.html', {
        'form': form,
        'medicine': medicine,
    })


@login_required
@role_required('admin', 'receptionist')
def stock_history(request):
    transactions = (
        StockTransaction.objects
        .select_related('medicine', 'batch', 'performed_by')
        .order_by('-created_at')[:200]
    )
    return render(request, 'pharmacy/stock_history.html', {
        'transactions': transactions,
    })


@login_required
@role_required('admin', 'receptionist')
def prescription_queue(request):
    prescriptions = (
        Prescription.objects
        .select_related('medical_record__patient__user', 'medical_record__doctor__user', 'medicine')
        .filter(status='pending')
        .order_by('-created_at')
    )
    return render(request, 'pharmacy/prescription_queue.html', {
        'prescriptions': prescriptions,
    })


@login_required
@role_required('admin', 'receptionist')
def dispense_prescription(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)

    if request.method != 'POST':
        messages.error(request, 'Dispense from the prescription queue.')
        return redirect('pharmacy:prescription_queue')

    try:
        rx = dispense_service(prescription, request.user)
    except StockError as exc:
        messages.error(request, str(exc))
        return redirect('pharmacy:prescription_queue')

    log_action(
        request, 'update', 'Prescription', rx.id, str(rx),
        details=f'Dispensed {rx.quantity} unit(s) of {rx.medicine_name}'
    )
    messages.success(request, f'{rx.medicine_name} dispensed successfully.')
    return redirect('pharmacy:prescription_queue')


@login_required
@role_required('admin', 'receptionist')
def supplier_list(request):
    suppliers = Supplier.objects.annotate(
        medicine_count=Count('medicines', distinct=True)
    ).order_by('name')
    return render(request, 'pharmacy/supplier_list.html', {'suppliers': suppliers})


@login_required
@role_required('admin', 'receptionist')
def supplier_form(request, supplier_id=None):
    supplier = None
    if supplier_id:
        supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            saved = form.save()
            action = 'update' if supplier_id else 'create'
            log_action(request, action, 'Supplier', saved.id, saved.name)
            messages.success(request, 'Supplier saved successfully.')
            return redirect('pharmacy:supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'pharmacy/supplier_form.html', {
        'form': form,
        'supplier': supplier,
    })
