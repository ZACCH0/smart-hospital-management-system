from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    path('', views.medicine_list, name='medicine_list'),
    path('add/', views.add_medicine, name='add_medicine'),
    path('<int:medicine_id>/edit/', views.edit_medicine, name='edit_medicine'),
    path('<int:medicine_id>/delete/', views.delete_medicine, name='delete_medicine'),
]