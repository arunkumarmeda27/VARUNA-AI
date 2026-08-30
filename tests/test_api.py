"""
VARUNA-AI: REST API Endpoint Tests
Owner: Member 5 (Backend + Platform Integration Engineer)
"""

import os
import django
from django.test import TestCase, Client
from django.urls import reverse

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

    def test_latest_forecast_endpoint(self):
        response = self.client.get("/api/v1/forecasts/latest/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("forecast_run", data)
        self.assertIn("districts_forecast", data)
        self.assertIn("geojson_layer", data)

    def test_districts_endpoint(self):
        response = self.client.get("/api/v1/districts/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("districts", data)
        self.assertIn("geojson", data)

    def test_verification_benchmarks_endpoint(self):
        response = self.client.get("/api/v1/verification/")
        self.assertEqual(response.status_code, 200)

    def test_models_registry_endpoint(self):
        response = self.client.get("/api/v1/models/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("registered_models", data)
        self.assertGreater(data["count"], 0)

    def test_dashboard_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VARUNA-AI")
