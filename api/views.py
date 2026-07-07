from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from appointments.models import Appointment
from .serializers import DoctorSerializer, PatientSerializer, AppointmentSerializer


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]


class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PatientProfile.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by('-appointment_date')
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]