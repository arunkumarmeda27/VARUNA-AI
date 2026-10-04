from datetime import date

from rest_framework import serializers


class PredictForecastRequestSerializer(serializers.Serializer):
    nwp_rainfall = serializers.FloatField(min_value=0)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    district_name = serializers.CharField(required=False, allow_blank=True)

    mslp = serializers.FloatField()
    u850 = serializers.FloatField()
    v850 = serializers.FloatField()
    u200 = serializers.FloatField()
    v200 = serializers.FloatField()
    tcwv = serializers.FloatField(min_value=0)
    rh700 = serializers.FloatField(min_value=0, max_value=100)
    cape = serializers.FloatField(min_value=0)
    monsoon_trough_lat = serializers.FloatField(
        min_value=-90, max_value=90
    )
    vertical_wind_shear = serializers.FloatField(
        min_value=0
    )
    valid_time = serializers.DateField(required=False)


class PredictForecastResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    district_name = serializers.CharField(allow_blank=True)
    raw_nwp_rainfall_mm = serializers.FloatField()
    corrected_rainfall_mm = serializers.FloatField()
    bias_correction_delta_mm = serializers.FloatField()
    detected_regime = serializers.CharField()
    regime_confidence = serializers.FloatField()
    regime_probabilities = serializers.DictField(
        child=serializers.FloatField()
    )
    model_ladder = serializers.DictField(child=serializers.FloatField())
    heavy_rainfall_probability = serializers.FloatField()
    uncertainty_interval_80pct = serializers.DictField(
        child=serializers.FloatField()
    )
    risk_assessment = serializers.DictField()


class APIErrorResponseSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)
    errors = serializers.JSONField(required=False)


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    version = serializers.CharField()
    database = serializers.CharField()
    forecast_data_available = serializers.BooleanField()
    prediction_provenance_available = serializers.BooleanField()
    model_artifacts_available = serializers.DictField(
        child=serializers.BooleanField()
    )


class ForecastListItemSerializer(serializers.Serializer):
    run_id = serializers.CharField()
    initialization_time = serializers.DateTimeField()
    valid_time = serializers.DateField()
    detected_regime = serializers.CharField()
    regime_confidence = serializers.FloatField()
    model_version = serializers.CharField()


class ForecastListResponseSerializer(serializers.Serializer):
    runs = ForecastListItemSerializer(many=True)
    count = serializers.IntegerField()


class ForecastQuerySerializer(serializers.Serializer):
    run_id = serializers.CharField(required=False)
    lead_time = serializers.IntegerField(required=False, min_value=0)
    date = serializers.CharField(required=False)
    cycle = serializers.CharField(required=False)

    def validate_date(self, value):
        if value in {"today", "tomorrow", "day3"}:
            return value
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise serializers.ValidationError(
                "Use an ISO date or a supported forecast-day selector."
            ) from exc
        return value

    def validate_cycle(self, value):
        try:
            time_value = value.removesuffix(" UTC")
            hour, minute = time_value.split(":", maxsplit=1)
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError
        except (ValueError, TypeError) as exc:
            raise serializers.ValidationError(
                "Cycle must be an HH:MM time, optionally followed by UTC."
            ) from exc
        return value


class ForecastRunDetailsSerializer(serializers.Serializer):
    run_id = serializers.CharField()
    initialization_time = serializers.DateTimeField()
    valid_time = serializers.DateField()
    lead_time_hours = serializers.IntegerField()
    cycle = serializers.CharField()
    date_param = serializers.CharField()
    detected_regime = serializers.CharField()
    regime_confidence = serializers.FloatField()
    regime_probabilities = serializers.DictField(
        child=serializers.FloatField()
    )
    synoptic_features = serializers.JSONField()
    model_version = serializers.CharField()
    created_at = serializers.DateTimeField()


class DistrictForecastItemSerializer(serializers.Serializer):
    district_id = serializers.CharField()
    district_name = serializers.CharField()
    state = serializers.CharField()
    zone = serializers.CharField()
    centroid_lat = serializers.FloatField()
    centroid_lon = serializers.FloatField()
    raw_nwp_mean_mm = serializers.FloatField()
    corrected_mean_mm = serializers.FloatField()
    corrected_max_mm = serializers.FloatField()
    bias_correction_delta_mm = serializers.FloatField()
    heavy_rain_probability = serializers.FloatField()
    prob_exceed_115mm = serializers.FloatField()
    prob_exceed_204mm = serializers.FloatField()
    uncertainty_lower_10pct = serializers.FloatField()
    uncertainty_upper_90pct = serializers.FloatField()
    uncertainty_range_width = serializers.FloatField()
    risk_code = serializers.CharField()
    risk_label = serializers.CharField()


class LatestForecastResponseSerializer(serializers.Serializer):
    forecast_run = ForecastRunDetailsSerializer()
    districts_forecast = DistrictForecastItemSerializer(many=True)
    geojson_layer = serializers.JSONField()


class DistrictMetadataSerializer(serializers.Serializer):
    district_id = serializers.CharField()
    name = serializers.CharField()
    state = serializers.CharField()
    zone = serializers.CharField()
    centroid = serializers.ListField(child=serializers.FloatField())


class DistrictsResponseSerializer(serializers.Serializer):
    districts = DistrictMetadataSerializer(many=True)
    geojson = serializers.JSONField()


class DistrictForecastResponseSerializer(serializers.Serializer):
    district = DistrictMetadataSerializer()
    forecast_run = serializers.JSONField()
    rainfall_prediction = serializers.JSONField()
    heavy_rain_risk = serializers.JSONField()
    uncertainty = serializers.JSONField()


class DistrictForecastRecordSerializer(serializers.Serializer):
    forecast_run = serializers.CharField()
    district = serializers.CharField()
    raw_nwp_mean_mm = serializers.FloatField()
    corrected_mean_mm = serializers.FloatField()
    corrected_max_mm = serializers.FloatField()
    bias_correction_delta_mm = serializers.FloatField()
    heavy_rain_probability = serializers.FloatField()
    prob_exceed_115mm = serializers.FloatField()
    prob_exceed_204mm = serializers.FloatField()
    uncertainty_lower_10pct = serializers.FloatField()
    uncertainty_upper_90pct = serializers.FloatField()
    uncertainty_range_width = serializers.FloatField()
    risk_code = serializers.CharField()
    risk_label = serializers.CharField()


class RegimeEvaluationResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()


class RealVerificationResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    dataset = serializers.CharField()
    dataset_sha256 = serializers.CharField()
    target = serializers.CharField()
    raw_forecast = serializers.CharField()
    split = serializers.JSONField()
    levels = serializers.JSONField()


class ModelProvenanceResponseItemSerializer(serializers.Serializer):
    component = serializers.CharField()
    model_name = serializers.CharField()
    model_version = serializers.CharField()
    dataset_version = serializers.CharField()
    training_period = serializers.CharField()
    val_period = serializers.CharField()
    test_period = serializers.CharField()
    metrics = serializers.JSONField()
    created_at = serializers.DateTimeField()


class ModelRegistryResponseSerializer(serializers.Serializer):
    registered_models = ModelProvenanceResponseItemSerializer(many=True)
    count = serializers.IntegerField()


class FirebaseConfigurationResponseSerializer(serializers.Serializer):
    apiKey = serializers.CharField()
    authDomain = serializers.CharField()
    projectId = serializers.CharField()
    storageBucket = serializers.CharField()
    messagingSenderId = serializers.CharField()
    appId = serializers.CharField()
    measurementId = serializers.CharField()
