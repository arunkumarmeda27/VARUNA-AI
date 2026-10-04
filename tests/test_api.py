"""
VARUNA-AI: REST API Endpoint Tests
Owner: Member 5 (Backend + Platform Integration Engineer)
"""

import os
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
from backend.models import ForecastRun
from backend.api_exceptions import api_exception_handler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

class TestForecastAPI(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_endpoint(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertEqual(data["service"], "VARUNA-AI Forecast Engine")
        self.assertFalse(data["forecast_data_available"])
        self.assertFalse(data["prediction_provenance_available"])

    def test_latest_forecast_endpoint(self):
        response = self.client.get("/api/v1/forecasts/latest/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "ERROR")

    def test_latest_forecast_rejects_malformed_query_parameters(self):
        invalid_lead = self.client.get(
            "/api/v1/forecasts/latest/?lead_time=invalid"
        )
        self.assertEqual(invalid_lead.status_code, 400)
        self.assertIn("lead_time", invalid_lead.json()["errors"])

        invalid_date = self.client.get(
            "/api/v1/forecasts/latest/?date=not-a-date"
        )
        self.assertEqual(invalid_date.status_code, 400)
        self.assertIn("date", invalid_date.json()["errors"])

    def test_forecast_list_is_unavailable_without_real_runs(self):
        response = self.client.get("/api/v1/forecasts/list/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(ForecastRun.objects.count(), 0)

    def test_districts_endpoint(self):
        response = self.client.get("/api/v1/districts/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("districts", data)
        self.assertIn("geojson", data)

    def test_verification_benchmarks_endpoint(self):
        response = self.client.get("/api/v1/verification/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "AVAILABLE")
        self.assertEqual(data["levels"]["level2_standard_ml"]["status"], "unavailable")

    def test_regime_analytics_reports_missing_real_evaluation(self):
        response = self.client.get("/api/v1/regimes/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "ERROR")

    def test_models_registry_endpoint(self):
        response = self.client.get("/api/v1/models/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["message"], "Model provenance is unavailable.")

    def test_predict_rejects_missing_scientific_inputs(self):
        response = self.client.post(
            "/api/v1/predict/",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("nwp_rainfall", response.json()["errors"])

    def test_predict_rejects_malformed_json(self):
        response = self.client.post(
            "/api/v1/predict/",
            data="{",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_schema_endpoint(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)
        schema_text = response.content.decode("utf-8")
        for api_path in (
            "/api/v1/health/",
            "/api/v1/forecasts/latest/",
            "/api/v1/forecasts/list/",
            "/api/v1/forecasts/{run_id}/",
            "/api/v1/districts/",
            "/api/v1/districts/{district_id}/forecast/",
            "/api/v1/regimes/",
            "/api/v1/verification/",
            "/api/v1/models/",
            "/api/v1/auth/config/",
            "/api/v1/predict/",
        ):
            self.assertIn(api_path, schema_text)

    def test_unexpected_api_exception_is_sanitized(self):
        response = api_exception_handler(
            RuntimeError("sensitive internal detail"),
            {"request": self.client.get("/").wsgi_request, "view": None},
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data["message"],
            "Request could not be completed.",
        )
        self.assertNotIn("sensitive internal detail", str(response.data))

    def test_dashboard_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VARUNA")

    def test_dashboard_page(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VARUNA")

    def test_login_page(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secure Login")
        # Firebase config is now dynamically fetched from /api/v1/auth/config/ (no hardcoded secrets in HTML)
        self.assertContains(response, "/api/v1/auth/config/")

    def test_login_page_is_throttled(self):
        cache.clear()
        request_limit = int(settings.API_LOGIN_PAGE_RATE.split("/", maxsplit=1)[0])
        for _ in range(request_limit):
            response = self.client.get("/login/")
            self.assertEqual(response.status_code, 200)
        limited_response = self.client.get("/login/")
        self.assertEqual(limited_response.status_code, 429)
        cache.clear()

