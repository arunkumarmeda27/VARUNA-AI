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
