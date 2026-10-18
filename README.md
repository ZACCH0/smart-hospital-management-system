# Smart Hospital Management System (SHMS)

A full-stack Django web application for managing hospital operations including patient registration, appointment booking, medical records, billing, pharmacy, and laboratory management.

## Features

- Role-based authentication (Admin, Doctor, Receptionist, Patient)
- Patient registration and appointment booking
- Doctor dashboard with daily schedule
- Receptionist appointment management
- Admin analytics dashboard with Chart.js
- REST API built with Django REST Framework
- Electronic Medical Records (EMR)
- Billing and invoice management
- Pharmacy inventory tracking
- Laboratory test and result management
- Automated notifications via Django Signals
- Profile picture upload support

## Tech Stack

- **Backend:** Python, Django 5.x, Django REST Framework
- **Frontend:** HTML5, Tailwind CSS, JavaScript, Chart.js
- **Database:** SQLite (development), PostgreSQL (production)
- **Other:** Django Signals, Pillow, django-cors-headers, WhiteNoise, django-otp (2FA)

## Setup Instructions

1. Clone the repository
2. Create and activate virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with your `SECRET_KEY` (and `DATABASE_URL`, email settings)
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

## Project Structure

```
smart/                   # Django project root (manage.py lives here)
├── accounts/            # Authentication, roles, email verification, 2FA
├── api/                 # REST API (DRF)
├── appointments/        # Appointment booking & management
├── billing/             # Invoices & payments
├── core/                # Shared helpers (audit logging, decorators, homepage)
├── dashboard/           # Role-based dashboards (admin/doctor/patient/receptionist)
├── doctors/             # Doctor profiles & availability
├── laboratory/          # Lab tests & results
├── medical_records/     # Electronic Medical Records
├── notifications/       # System notifications
├── patients/            # Patient profiles
├── pharmacy/            # Medicine inventory
├── prescriptions/       # Prescription management
├── smart/               # Project config (settings.py, urls.py)
├── templates/           # HTML templates (home, roles, partials, errors)
├── static/              # CSS, JS assets
├── staticfiles/         # Collected static files (production)
└── media/               # Uploaded files (local dev)
```

## Live Demo

- **Live:** https://smart-hospital-management-system-8zgy.onrender.com
- **Repository:** https://github.com/ZACCH0/smart-hospital-management-system

## Developer

**Alade Zaccheous Kehinde**  
Python & Django Developer | Data Analyst  
[GitHub](https://github.com/ZACCH0) | [LinkedIn](https://linkedin.com/in/zacchtech)
