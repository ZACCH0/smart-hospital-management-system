from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.create_invoice, name='create_invoice'),
    path('<int:invoice_id>/payment/', views.record_payment, name='record_payment'),
    path('my-invoices/', views.patient_invoices, name='patient_invoices'),
]