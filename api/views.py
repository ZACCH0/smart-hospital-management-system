from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
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
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Doctors only see their own appointments
        if hasattr(user, 'doctor_profile'):
            return Appointment.objects.filter(
                doctor=user.doctor_profile
            ).order_by('-appointment_date')

        # Patients only see their own appointments
        if hasattr(user, 'patient_profile') and user.role == 'patient':
            return Appointment.objects.filter(
                patient=user.patient_profile
            ).order_by('-appointment_date')

        # Receptionists and Admins see all
        return Appointment.objects.all().order_by('-appointment_date')

    def create(self, request, *args, **kwargs):
        """Block doctors and patients from creating appointments via API."""
        user = request.user
        if hasattr(user, 'doctor_profile') and user.role == 'doctor':
            raise PermissionDenied(
                'Doctors cannot create appointments. Please contact reception.'
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Block doctors from updating appointments they don't own."""
        user = request.user
        if hasattr(user, 'doctor_profile'):
            appointment = self.get_object()
            if appointment.doctor != user.doctor_profile:
                raise PermissionDenied(
                    'You can only update your own appointments.'
                )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Block doctors from deleting appointments."""
        user = request.user
        if hasattr(user, 'doctor_profile') and user.role == 'doctor':
            raise PermissionDenied(
                'Doctors cannot delete appointments.'
            )
        return super().destroy(request, *args, **kwargs)