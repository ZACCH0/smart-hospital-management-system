from django.db import transaction
from django.utils import timezone

from .models import Medicine, MedicineBatch, StockTransaction


class StockError(Exception):
    """Raised when a stock operation cannot be completed safely."""


@transaction.atomic
def receive_stock(medicine, batch_number, quantity, expiry_date,
                  supplier=None, unit_cost=None, user=None):
    """Add a delivery: create the batch, raise stock, write the ledger row."""
    medicine = Medicine.objects.select_for_update().get(pk=medicine.pk)

    batch = MedicineBatch.objects.create(
        medicine=medicine,
        supplier=supplier,
        batch_number=batch_number,
        quantity_received=quantity,
        quantity_remaining=quantity,
        unit_cost=unit_cost,
        expiry_date=expiry_date,
    )

    medicine.stock_quantity += quantity
    if medicine.expiry_date is None or expiry_date < medicine.expiry_date:
        medicine.expiry_date = expiry_date
    if supplier and medicine.supplier_id is None:
        medicine.supplier = supplier
    medicine.save(update_fields=['stock_quantity', 'expiry_date', 'supplier'])

    StockTransaction.objects.create(
        medicine=medicine,
        batch=batch,
        transaction_type='in',
        quantity=quantity,
        reference=f'Batch {batch_number}',
        performed_by=user,
    )
    return batch


@transaction.atomic
def dispense_prescription(prescription, user):
    """
    Issue a pending prescription against stock, oldest expiry first (FEFO).
    Decrements both the batch and the medicine total inside one transaction.
    """
    from prescriptions.models import Prescription

    rx = (
        Prescription.objects
        .select_for_update()
        .get(pk=prescription.pk)
    )

    if rx.status != 'pending':
        raise StockError('This prescription has already been handled.')

    medicine = rx.medicine
    if medicine is None:
        medicine = Medicine.objects.filter(name__iexact=rx.medicine_name.strip()).first()
    if medicine is None:
        raise StockError(f'"{rx.medicine_name}" is not stocked in the pharmacy.')

    medicine = Medicine.objects.select_for_update().get(pk=medicine.pk)
    quantity = rx.quantity or 1
    if medicine.stock_quantity < quantity:
        raise StockError(
            f'Not enough stock for {medicine.name}: {medicine.stock_quantity} left, '
            f'{quantity} needed.'
        )

    remaining = quantity
    batches = list(
        medicine.batches.select_for_update()
        .filter(quantity_remaining__gt=0)
        .order_by('expiry_date', 'received_date')
    )

    for batch in batches:
        take = min(batch.quantity_remaining, remaining)
        batch.quantity_remaining -= take
        batch.save(update_fields=['quantity_remaining'])
        StockTransaction.objects.create(
            medicine=medicine,
            batch=batch,
            transaction_type='out',
            quantity=take,
            reference=f'Prescription #{rx.id}',
            performed_by=user,
        )
        remaining -= take
        if remaining == 0:
            break

    if remaining:
        # Legacy stock added before batch tracking existed.
        StockTransaction.objects.create(
            medicine=medicine,
            batch=None,
            transaction_type='out',
            quantity=remaining,
            reference=f'Prescription #{rx.id} (unbatched stock)',
            performed_by=user,
        )

    medicine.stock_quantity -= quantity
    medicine.save(update_fields=['stock_quantity'])

    rx.medicine = medicine
    rx.status = 'dispensed'
    rx.dispensed_by = user
    rx.dispensed_at = timezone.now()
    rx.save(update_fields=['medicine', 'status', 'dispensed_by', 'dispensed_at'])

    from notifications.services import notify
    notify(
        rx.medical_record.patient.user,
        (
            f'Your prescription for {medicine.name} ({quantity} unit(s)) '
            f'has been dispensed. Please take it as instructed.'
        ),
        category='pharmacy',
        email_subject='Prescription dispensed',
        email_body=(
            f'Your prescription is ready.\n\n'
            f'Medicine: {medicine.name}\n'
            f'Quantity: {quantity} unit(s)\n'
            f'Instructions: {rx.instructions or "As directed by your doctor."}'
        ),
    )
    return rx
