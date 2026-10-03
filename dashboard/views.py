"""
VARUNA-AI: Operational Scientific Dashboard Views
Owner: Member 6 (Geospatial + Operational Interface Engineer)
"""

import json
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from backend.models import ForecastRun, District, DistrictForecast

def dashboard_index(request):
    """Renders the main operational scientific meteorological interface."""
    # Get available runs
    all_runs = ForecastRun.objects.all().order_by("-valid_time")
    selected_run_id = request.GET.get("run_id")

    if selected_run_id:
        current_run = ForecastRun.objects.filter(run_id=selected_run_id).first() or all_runs.first()
    else:
        current_run = all_runs.first()

    district_forecasts = []
    if current_run:
        district_forecasts = DistrictForecast.objects.filter(forecast_run=current_run).select_related("district")

    context = {
        "all_runs": all_runs,
        "current_run": current_run,
        "district_forecasts": district_forecasts,
        "district_count": len(district_forecasts),
    }
    return render(request, "dashboard/index.html", context)


@ratelimit(
    key="ip",
    rate=settings.API_LOGIN_PAGE_RATE,
    method="GET",
    block=False,
)
def login_view(request):
    """Renders the Firebase-authenticated login page."""
    if getattr(request, "limited", False):
        return HttpResponse("Request limit exceeded.", status=429)
    return render(request, "dashboard/login.html")
