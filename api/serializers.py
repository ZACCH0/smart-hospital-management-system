from rest_framework import serializers
from django.utils import timezone

from accounts.models import CustomUser
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from appointments.models import Appointment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'role']


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'full_name', 'specialization', 'qualification',
            'experience_years', 'consultation_fee', 'available',
        ]

    def get_full_name(self, obj):
        return f'Dr. {obj.user.get_full_name()}'


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'gender', 'blood_group',
            'address', 'emergency_contact', 'age',
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'patient_name', 'doctor_name',
            'appointment_date', 'appointment_time', 'duration', 'status',
            'reason', 'cancellation_reason', 'consultation_type', 'video_url',
        ]

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()

    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name()

    def get_video_url(self, obj):
        return obj.video_url if obj.can_join_video else ''

    def validate(self, attrs):
        date = attrs.get('appointment_date', getattr(self.instance, 'appointment_date', None))
        time = attrs.get('appointment_time', getattr(self.instance, 'appointment_time', None))
        doctor = attrs.get('doctor', getattr(self.instance, 'doctor', None))

        if date and date < timezone.now().date():
            raise serializers.ValidationError({
                'appointment_date': 'Appointment date cannot be in the past.'
            })

        if doctor and not doctor.available:
            raise serializers.ValidationError({
                'doctor': f'Dr. {doctor.user.get_full_name()} is not available for appointments.'
            })

        if doctor and date and time:
            conflict = (
                Appointment.objects
                .filter(doctor=doctor, appointment_date=date, appointment_time=time)
                .exclude(status__in=['cancelled', 'no_show'])
            )
            if self.instance:
                conflict = conflict.exclude(pk=self.instance.pk)
            if conflict.exists():
                raise serializers.ValidationError({
                    'appointment_time': 'That doctor already has an appointment at this time.'
                })

        return attrs
