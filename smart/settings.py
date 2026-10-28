from pathlib import Path
from decouple import config
import os
import sys
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Local apps
    'core',  
    'accounts',
    'smart',
    'doctors',
    'patients',
    'appointments',
    'medical_records',
    'prescriptions',
    'billing',
    'pharmacy',
    'laboratory',
    'ipd',
    'notifications',
    'api',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.RateLimitMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'core.middleware.TwoFactorMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smart.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'smart.wsgi.application'

# Database
DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=60)
}

AUTH_USER_MODEL = 'accounts.CustomUser'

# Shared cache — also backs rate limiting, so every gunicorn worker sees
# the same counters. Table is created by `manage.py createcachetable`.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'shms_cache_table',
        'TIMEOUT': 300,
        'OPTIONS': {'MAX_ENTRIES': 10000},
    }
}

RATE_LIMIT_ENABLED = config('RATE_LIMIT_ENABLED', default=True, cast=bool)

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Upload limits enforced by core.validators
MAX_IMAGE_UPLOAD_MB = config('MAX_IMAGE_UPLOAD_MB', default=5, cast=int)
MAX_DOCUMENT_UPLOAD_MB = config('MAX_DOCUMENT_UPLOAD_MB', default=10, cast=int)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'accounts:role_redirect'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
}

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000'
).split(',')


# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='SHMS <noreply@shms.com>')

# Automated tests never touch a real inbox and may use a fast hasher.
if 'test' in sys.argv:
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Notification channels (swap for a real provider class when available)
SMS_BACKEND = config('SMS_BACKEND', default='notifications.channels.ConsoleSMSBackend')
WHATSAPP_BACKEND = config('WHATSAPP_BACKEND', default='notifications.channels.ConsoleWhatsAppBackend')

# Telehealth (P28) — provider-agnostic video rooms; swap the base URL for
# Daily.co, Whereby, Zoom, etc. without code changes.
TELEHEALTH_MEETING_BASE_URL = config('TELEHEALTH_MEETING_BASE_URL', default='https://meet.jit.si/')
TELEHEALTH_ROOM_PREFIX = config('TELEHEALTH_ROOM_PREFIX', default='shms-')

# Advanced intelligence (P29) — empty key keeps the built-in rule-based
# triage; set these to use any OpenAI-compatible endpoint.
AI_API_KEY = config('AI_API_KEY', default='')
AI_MODEL = config('AI_MODEL', default='gpt-4o-mini')
AI_BASE_URL = config('AI_BASE_URL', default='https://api.openai.com/v1')
AI_TIMEOUT = config('AI_TIMEOUT', default=8, cast=int)

# CSRF
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# SESSION SECURITY
SESSION_COOKIE_HTTPONLY = True    # JS cannot access session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 86400 * 7   # 7 days in seconds

#  SECURITY HEADERS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# Render terminates TLS and forwards the original scheme in this header.
# Without it SECURE_SSL_REDIRECT can loop in production.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HTTPS SETTINGS (only active in production) 
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000       # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True         # Cookie only sent over HTTPS
    CSRF_COOKIE_SECURE = True            # CSRF cookie only over HTTPS

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

