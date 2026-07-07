from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.admin_home, name='admin_home'),
    path('doctor/', views.doctor_home, name='doctor_home'),
    path('receptionist/', views.receptionist_home, name='receptionist_home'),
    path('patient/', views.patient_home, name='patient_home'),
]