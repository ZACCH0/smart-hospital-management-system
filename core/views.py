from django.shortcuts import render

from accounts.models import CustomUser
from doctors.models import DoctorProfile

DEMO_EMAILS = {
    "admin": "admin@shms-demo.com",
    "doctor": "doctor@shms-demo.com",
    "receptionist": "receptionist@shms-demo.com",
    "patient": "patient@shms-demo.com",
}


def home(request):
    """Public homepage — read-only context, no writes, no auth required."""
    doctors = (
        DoctorProfile.objects.select_related("user")
        .order_by("-available", "user__first_name")[:8]
    )
    return render(
        request,
        "home.html",
        {
            "homepage_doctors": doctors,
            "homepage_doctor_count": DoctorProfile.objects.count(),
        },
    )


def demo_page(request):
    """Public demo role picker — read-only personas from real demo accounts, no auth required."""
    users = {
        u.email: u
        for u in CustomUser.objects.filter(email__in=DEMO_EMAILS.values())
    }
    personas = {}
    for role, email in DEMO_EMAILS.items():
        user = users.get(email)
        if user is None:
            continue
        extra = ""
        if role == "doctor" and hasattr(user, "doctor_profile"):
            extra = user.doctor_profile.get_specialization_display()
        personas[role] = {
            "name": user.get_full_name() or user.email,
            "extra": extra,
        }
    return render(request, "demo/demo_page.html", {"demo_personas": personas})
