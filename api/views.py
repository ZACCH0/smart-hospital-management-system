from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from appointments.models import Appointment
from doctors.models import DoctorProfile
from patients.models import PatientProfile

from .serializers import AppointmentSerializer, DoctorSerializer, PatientSerializer


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['user__first_name', 'user__last_name', 'specialization__name', 'qualification']
    ordering_fields = ['consultation_fee', 'experience_years', 'user__last_name']
    ordering = ['user__last_name']

    def get_queryset(self):
        return DoctorProfile.objects.select_related('user', 'specialization').all()


class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'blood_group', 'gender',
    ]
    ordering_fields = ['user__last_name', 'date_of_birth', 'created_at']
    ordering = ['user__last_name']

    def get_queryset(self):
        user = self.request.user
        queryset = PatientProfile.objects.select_related('user')

        if user.role == 'patient':
            return queryset.filter(user=user)
        if user.role in ('admin', 'receptionist', 'doctor'):
            return queryset
        return queryset.none()


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = [
        'patient__user__first_name', 'patient__user__last_name',
        'doctor__user__first_name', 'doctor__user__last_name', 'reason',
    ]
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at', 'status']
    ordering = ['-appointment_date', '-appointment_time']

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related('patient__user', 'doctor__user')

        if user.role == 'doctor' and hasattr(user, 'doctor_profile'):
            queryset = queryset.filter(doctor=user.doctor_profile)
        elif user.role == 'patient' and hasattr(user, 'patient_profile'):
            queryset = queryset.filter(patient=user.patient_profile)

        status_param = self.request.query_params.get('status')
        if status_param in dict(Appointment.STATUS_CHOICES):
            queryset = queryset.filter(status=status_param)

        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(appointment_date=date_param)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == 'doctor':
            raise PermissionDenied('Doctors cannot create appointments through the API.')

        if user.role == 'patient':
            if not hasattr(user, 'patient_profile'):
                raise PermissionDenied('No patient profile linked to this account.')
            try:
                serializer.save(patient=user.patient_profile, status='pending')
            except Exception as exc:
                raise ValidationError({'detail': str(exc)}) from exc
            return

        if user.role not in ('admin', 'receptionist'):
            raise PermissionDenied('Your role cannot create appointments.')

        try:
            serializer.save()
        except Exception as exc:
            raise ValidationError({'detail': str(exc)}) from exc

    def perform_update(self, serializer):
        user = self.request.user
        appointment = self.get_object()

        if user.role == 'doctor':
            if appointment.doctor != getattr(user, 'doctor_profile', None):
                raise PermissionDenied('You can only update your own appointments.')
            serializer.save()
            return

        if user.role == 'patient':
            if appointment.patient != getattr(user, 'patient_profile', None):
                raise PermissionDenied('You can only update your own appointments.')

            new_status = serializer.validated_data.get('status', appointment.status)
            if new_status not in ('pending', 'cancelled'):
                raise PermissionDenied('Patients can only cancel their appointments.')

            serializer.save(
                patient=user.patient_profile,
                doctor=appointment.doctor,
            )
            return

        if user.role not in ('admin', 'receptionist'):
            raise PermissionDenied('Your role cannot update appointments.')

        try:
            serializer.save()
        except Exception as exc:
            raise ValidationError({'detail': str(exc)}) from exc

    def perform_destroy(self, instance):
        if self.request.user.role != 'admin':
            raise PermissionDenied('Only administrators can delete appointments.')
        instance.delete()
