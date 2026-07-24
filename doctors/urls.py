from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/record/', views.write_medical_record, name='write_medical_record'),
    path('records/<int:record_id>/prescription/', views.add_prescription, name='add_prescription'),
]