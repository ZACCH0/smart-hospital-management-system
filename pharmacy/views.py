from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Medicine
from .forms import MedicineForm

# Create your views here.
@login_required
def medicine_list(request):
    medicines = Medicine.objects.all().order_by('name')
    low_stock = [m for m in medicines if m.is_low_stock]
    expired = [m for m in medicines if m.is_expired]

    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': medicines,
        'low_stock_count': len(low_stock),
        'expired_count': len(expired),
    })


@login_required
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine added successfully.')
            return redirect('pharmacy:medicine_list')
    else:
        form = MedicineForm()

    return render(request, 'pharmacy/medicine_form.html', {
        'form': form,
        'title': 'Add Medicine'
    })


@login_required
def edit_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)

    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
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
def delete_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    medicine.delete()
    messages.success(request, f'{medicine.name} deleted successfully.')
    return redirect('pharmacy:medicine_list')