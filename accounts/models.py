from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from core.validators import validate_image_file
import uuid


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('patient', 'Patient'),
    )

    email           = models.EmailField(unique=True)
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    phone           = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, validators=[validate_image_file])
    profile_banner = models.ImageField(upload_to='profile_banners/', blank=True, null=True, validators=[validate_image_file])
    role            = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient', db_index=True)
    is_active       = models.BooleanField(default=True)
    is_staff        = models.BooleanField(default=False)
    date_joined     = models.DateTimeField(auto_now_add=True)

    # Email verification fields
    email_verified       = models.BooleanField(default=False)
    verification_token   = models.UUIDField(default=uuid.uuid4, unique=True)

    # Notification channels (in-app is always on)
    email_notifications    = models.BooleanField(default=True)
    sms_notifications      = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()