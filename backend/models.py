"""
VARUNA-AI: Scientific Database Models
Owner: Member 5 (Backend + Platform Integration Engineer)
"""

from django.db import models
import json

class ForecastRun(models.Model):
    """Represents a discrete NWP cycle and post-processing forecast execution."""
    run_id = models.CharField(max_length=64, unique=True, primary_key=True)
    initialization_time = models.DateTimeField()
    valid_time = models.DateField()
    lead_time_hours = models.IntegerField(default=24)
    detected_regime = models.CharField(max_length=64)
    regime_confidence = models.FloatField()
    regime_probabilities_json = models.TextField(default="{}")
    synoptic_features_json = models.TextField(default="{}")
    model_version = models.CharField(max_length=64, default="VARUNA-Level3-XGB-v1.0.0")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_regime_probabilities(self):
        return json.loads(self.regime_probabilities_json)

    def get_synoptic_features(self):
        return json.loads(self.synoptic_features_json)

    def __str__(self):
        return f"ForecastRun {self.run_id} ({self.valid_time}) - {self.detected_regime}"

class District(models.Model):
    """Administrative district spatial metadata and geometry."""
    district_id = models.CharField(max_length=32, unique=True, primary_key=True)
    name = models.CharField(max_length=128)
    state = models.CharField(max_length=64)
    zone = models.CharField(max_length=64)
    centroid_lat = models.FloatField()
    centroid_lon = models.FloatField()
    polygon_geojson = models.TextField(default="{}")

    def __str__(self):
        return f"{self.name}, {self.state} ({self.district_id})"

class DistrictForecast(models.Model):
    """District-level aggregated rainfall forecast and uncertainty product."""
    forecast_run = models.ForeignKey(ForecastRun, on_delete=models.CASCADE, related_name="district_forecasts")
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="forecasts")
    raw_nwp_mean_mm = models.FloatField()
    corrected_mean_mm = models.FloatField()
    corrected_max_mm = models.FloatField()
    bias_correction_delta_mm = models.FloatField()
    heavy_rain_probability = models.FloatField()
    prob_exceed_115mm = models.FloatField(default=0.0)
    prob_exceed_204mm = models.FloatField(default=0.0)
    uncertainty_lower_10pct = models.FloatField()
    uncertainty_upper_90pct = models.FloatField()
    uncertainty_range_width = models.FloatField()
    risk_code = models.CharField(max_length=16, default="GREEN")
    risk_label = models.CharField(max_length=128)

    class Meta:
        unique_together = ("forecast_run", "district")

    def __str__(self):
        return f"{self.district.name} [{self.forecast_run.valid_time}]: Corrected={self.corrected_mean_mm}mm, Risk={self.risk_code}"

class ModelProvenance(models.Model):
    """Audit log for model artifact versions, training periods, and verification signatures."""
    model_name = models.CharField(max_length=128)
    model_version = models.CharField(max_length=64)
    component = models.CharField(max_length=64)
    dataset_version = models.CharField(max_length=32)
    training_period = models.CharField(max_length=64)
    val_period = models.CharField(max_length=32)
    test_period = models.CharField(max_length=32)
    metrics_json = models.TextField(default="{}")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} [{self.model_version}] - {self.component}"
