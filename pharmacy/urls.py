from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    path('', views.medicine_list, name='medicine_list'),
    path('add/', views.add_medicine, name='add_medicine'),
    path('<int:medicine_id>/edit/', views.edit_medicine, name='edit_medicine'),
    path('<int:medicine_id>/delete/', views.delete_medicine, name='delete_medicine'),
    path('<int:medicine_id>/receive/', views.receive_stock, name='receive_stock'),
    path('stock/', views.stock_history, name='stock_history'),
    path('prescriptions/', views.prescription_queue, name='prescription_queue'),
    path('prescriptions/<int:prescription_id>/dispense/', views.dispense_prescription, name='dispense_prescription'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_form, name='supplier_add'),
    path('suppliers/<int:supplier_id>/edit/', views.supplier_form, name='supplier_edit'),
]
