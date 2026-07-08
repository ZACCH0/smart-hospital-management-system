from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('profile/', views.profile_settings, name='profile_settings'),
]