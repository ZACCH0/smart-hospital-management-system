from django.shortcuts import render

from doctors.models import DoctorProfile


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
