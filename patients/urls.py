from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('profile/', views.profile_settings, name='profile_settings'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.my_appointments, name='my_appointments'),
    path('records/', views.my_medical_records, name='my_medical_records'),
    path('prescriptions/', views.my_prescriptions, name='my_prescriptions'),
]