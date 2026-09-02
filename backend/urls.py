"""
VARUNA-AI: Root URL Configuration
Owner: Member 5 (Backend + Platform Integration Engineer)
"""

from django.contrib import admin
from django.urls import path, include
from backend import api_views

urlpatterns = [
    # Admin Interface
    path("admin/", admin.site.urls),

    # Operational Scientific Dashboard
    path("", include("dashboard.urls")),

    # Scientific REST API v1
    path("api/v1/health/", api_views.health_check, name="api_health"),
    path("api/v1/forecasts/latest/", api_views.get_latest_forecast, name="api_latest_forecast"),
    path("api/v1/forecasts/list/", api_views.list_forecast_runs, name="api_list_forecasts"),
    path("api/v1/forecasts/<str:run_id>/", api_views.get_forecast_by_id, name="api_forecast_by_id"),
    path("api/v1/districts/", api_views.get_districts, name="api_districts"),
    path("api/v1/districts/<str:district_id>/forecast/", api_views.get_district_forecast, name="api_district_forecast"),
    path("api/v1/regimes/", api_views.get_regime_analytics, name="api_regimes"),
    path("api/v1/verification/", api_views.get_verification_benchmarks, name="api_verification"),
    path("api/v1/models/", api_views.get_model_registry, name="api_models"),
    path("api/v1/auth/config/", api_views.get_firebase_config, name="api_firebase_config"),
    path("api/v1/predict/", api_views.predict_custom_forecast, name="api_predict_forecast"),
]

