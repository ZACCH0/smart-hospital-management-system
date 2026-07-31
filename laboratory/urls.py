from django.urls import path
from . import views

app_name = 'laboratory'

urlpatterns = [
    path('', views.lab_test_list, name='lab_test_list'),
    path('request/', views.request_lab_test, name='request_lab_test'),
    path('<int:test_id>/result/', views.upload_result, name='upload_result'),
    path('<int:test_id>/progress/', views.update_test_status, name='update_test_status'),
]