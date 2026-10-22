from django.urls import path

from . import views

app_name = 'ipd'

urlpatterns = [
    path('', views.ward_board, name='ward_board'),
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/new/', views.admit_patient, name='admit_patient'),
    path('admissions/<int:admission_id>/discharge/', views.discharge_patient, name='discharge_patient'),
    path('wards/new/', views.ward_create, name='ward_create'),
    path('wards/<int:ward_id>/edit/', views.ward_edit, name='ward_edit'),
    path('wards/<int:ward_id>/beds/new/', views.bed_create, name='bed_create'),
    path('my-admissions/', views.my_admissions, name='my_admissions'),
]
