from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.create_invoice, name='create_invoice'),
    path('<int:invoice_id>/payment/', views.record_payment, name='record_payment'),
    path('<int:invoice_id>/insurance/', views.update_insurance_claim, name='insurance_claim'),
    path('insurance/providers/', views.insurance_providers, name='insurance_providers'),
    path('insurance/providers/add/', views.insurance_provider_form, name='insurance_provider_add'),
    path('insurance/providers/<int:provider_id>/edit/', views.insurance_provider_form, name='insurance_provider_edit'),
    path('my-invoices/', views.patient_invoices, name='patient_invoices'),
]