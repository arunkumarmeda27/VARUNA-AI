from rest_framework import serializers


class PredictForecastRequestSerializer(serializers.Serializer):
    nwp_rainfall = serializers.FloatField(min_value=0, required=False, default=45.0)
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False, default=12.97)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False, default=77.59)
    district_name = serializers.CharField(required=False, default="Bengaluru Urban")

    mslp = serializers.FloatField(required=False, default=1002.4)
    u850 = serializers.FloatField(required=False, default=18.5)
    v850 = serializers.FloatField(required=False, default=4.2)
    u200 = serializers.FloatField(required=False, default=-28.4)
    v200 = serializers.FloatField(required=False, default=0.5)
    tcwv = serializers.FloatField(min_value=0, required=False, default=58.6)
    rh700 = serializers.FloatField(min_value=0, max_value=100, required=False, default=82.0)
    cape = serializers.FloatField(min_value=0, required=False, default=2150.0)
    monsoon_trough_lat = serializers.FloatField(
        min_value=-90, max_value=90, required=False, default=22.4
    )
    vertical_wind_shear = serializers.FloatField(
        min_value=0, required=False, default=46.2
    )
