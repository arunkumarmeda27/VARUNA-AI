"""
VARUNA-AI: REST API Views
Owner: Member 5 (Backend + Platform Integration Engineer)

Provides structured, authenticated, documented JSON endpoints for operational
forecasts, districts, regimes, verification benchmarks, and provenance audit trails.
"""

import os
import json
import logging
from functools import wraps
from datetime import timedelta

from django.http import JsonResponse
from django.conf import settings
from django.db import DatabaseError, connections
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from backend.api_serializers import (
    APIErrorResponseSerializer,
    DistrictForecastRecordSerializer,
    DistrictForecastResponseSerializer,
    DistrictsResponseSerializer,
    FirebaseConfigurationResponseSerializer,
    ForecastListResponseSerializer,
    ForecastQuerySerializer,
    HealthResponseSerializer,
    LatestForecastResponseSerializer,
    ModelRegistryResponseSerializer,
    PredictForecastRequestSerializer,
    PredictForecastResponseSerializer,
    RealVerificationResponseSerializer,
    RegimeEvaluationResponseSerializer,
)
from backend.models import (
    ForecastRun,
    District,
    DistrictForecast,
    ModelProvenance,
)
from backend.service import ForecastService
from geospatial.districts.district_geometry import get_districts_geojson

VERIFICATION_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "verification",
)

REGIMES_EVAL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "regimes",
    "evaluation",
)
logger = logging.getLogger(__name__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def _api_read_rate_limit(view):
    @wraps(view)
    def return_rate_limit_error(request, *args, **kwargs):
        if getattr(request, "limited", False):
            return JsonResponse(
                {"status": "ERROR", "message": "Request limit exceeded."},
                status=429,
            )
        return view(request, *args, **kwargs)

    return ratelimit(
        key="ip",
        rate=settings.API_READ_RATE,
        method="GET",
        block=False,
    )(return_rate_limit_error)


def _document_get_api(
    response_serializer=None,
    *,
    description,
    parameters=None,
    error_statuses=(429,),
):
    def decorate(view):
        responses = {}
        if response_serializer is not None:
            responses[200] = response_serializer
        for error_status in error_statuses:
            responses[error_status] = APIErrorResponseSerializer
        responses[500] = APIErrorResponseSerializer
        drf_view = api_view(["GET"])(view)
        documented_view = extend_schema(
            parameters=parameters or [],
            responses=responses,
            description=description,
        )(drf_view)
        return _api_read_rate_limit(documented_view)

    return decorate


def _forecast_unavailable_response():
    return JsonResponse(
        {
            "status": "ERROR",
            "message": "No persisted real forecast is currently available.",
        },
        status=503,
    )


REQUIRED_REAL_PREDICTION_COMPONENTS = {
    "Weather Regime Classifier",
    "Level 1 Statistical Bias Correction",
    "Level 2 Standard ML Correction (Model A)",
    "Level 3 Regime-Aware ML Correction (Model B / VARUNA-AI)",
    "Heavy Rainfall Probability Estimator",
    "Uncertainty & Prediction Intervals",
}


def _real_prediction_provenance_available():
    try:
        recorded_components = set(
            ModelProvenance.objects.filter(
                component__in=REQUIRED_REAL_PREDICTION_COMPONENTS
            ).values_list("component", flat=True)
        )
    except DatabaseError:
        return False
    return REQUIRED_REAL_PREDICTION_COMPONENTS.issubset(recorded_components)


@_document_get_api(
    HealthResponseSerializer,
    description="Return service, persisted-forecast, and model-artifact availability.",
)
def health_check(request):
    """System health and diagnostic status."""
    try:
        connections["default"].ensure_connection()
        database_status = "CONNECTED"
        forecast_data_available = ForecastRun.objects.exists()
        prediction_provenance_available = _real_prediction_provenance_available()
    except DatabaseError:
        database_status = "UNAVAILABLE"
        forecast_data_available = False
        prediction_provenance_available = False

    correction_dir = os.path.join(PROJECT_ROOT, "correction", "artifacts")
    probability_dir = os.path.join(PROJECT_ROOT, "probability", "artifacts")
    model_artifacts_available = {
        "regime_classifier": os.path.isfile(
            os.path.join(PROJECT_ROOT, "regimes", "models", "regime_xgb_artifact.joblib")
        ),
        "quantile_mapping": os.path.isfile(
            os.path.join(correction_dir, "level1_eqm.joblib")
        ),
        "standard_ml": os.path.isfile(
            os.path.join(correction_dir, "level2_standard_xgb.joblib")
        ),
        "regime_aware_ml": os.path.isfile(
            os.path.join(correction_dir, "level3_regime_aware_xgb.joblib")
        ),
        "heavy_rain_probability": all(
            os.path.isfile(os.path.join(probability_dir, f"prob_{threshold}.joblib"))
            for threshold in ("moderate", "heavy", "very_heavy", "extremely_heavy")
        ),
        "conformal_quantiles": os.path.isfile(
            os.path.join(
                PROJECT_ROOT,
                "uncertainty",
                "artifacts",
                "conformal_quantiles.joblib",
            )
        ),
    }
    return JsonResponse({
        "status": "HEALTHY",
        "service": "VARUNA-AI Forecast Engine",
        "version": "v1.0.0",
        "database": database_status,
        "forecast_data_available": forecast_data_available,
        "prediction_provenance_available": prediction_provenance_available,
        "model_artifacts_available": model_artifacts_available,
    })


@_document_get_api(
    ForecastListResponseSerializer,
    description="List persisted forecast runs.",
    error_statuses=(429, 503),
)
def list_forecast_runs(request):
    """Returns list of available forecast runs."""
    runs = ForecastRun.objects.all().order_by("-valid_time")
    if not runs.exists():
        return _forecast_unavailable_response()

    data = [
        {
            "run_id": r.run_id,
            "initialization_time": r.initialization_time.isoformat(),
            "valid_time": r.valid_time.isoformat(),
            "detected_regime": r.detected_regime,
            "regime_confidence": r.regime_confidence,
            "model_version": r.model_version,
        }
        for r in runs
    ]

    return JsonResponse({
        "runs": data,
        "count": len(data),
    })


@_document_get_api(
    LatestForecastResponseSerializer,
    description="Return a persisted forecast matching validated query filters.",
    parameters=[ForecastQuerySerializer],
    error_statuses=(400, 404, 429, 503),
)
def get_latest_forecast(request):
    """Returns latest forecast run with all district products and GeoJSON layer."""
    query_serializer = ForecastQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Invalid forecast query.",
                "errors": query_serializer.errors,
            },
            status=400,
        )
    query_params = query_serializer.validated_data
    lead_time = query_params.get("lead_time")
    date_param = query_params.get("date")
    cycle_param = query_params.get("cycle")
    run_id = query_params.get("run_id")

    query = ForecastRun.objects.all()

    if run_id:
        query = query.filter(run_id=run_id)

    if lead_time is not None:
        query = query.filter(lead_time_hours=lead_time)

    if date_param:
        if date_param in {"today", "tomorrow", "day3"}:
            day_offsets = {"today": 0, "tomorrow": 1, "day3": 2}
            date_param = timezone.localdate() + timedelta(
                days=day_offsets[date_param]
            )
        query = query.filter(valid_time=date_param)

    if cycle_param:
        cycle_time = cycle_param.removesuffix(" UTC")
        cycle_hour, cycle_minute = (int(part) for part in cycle_time.split(":", 1))
        query = query.filter(
            initialization_time__hour=cycle_hour,
            initialization_time__minute=cycle_minute,
        )

    run = query.order_by("-valid_time").first()

    if not run:
        if not ForecastRun.objects.exists():
            return _forecast_unavailable_response()
        return JsonResponse(
            {"status": "ERROR", "message": "Forecast run not found."},
            status=404,
        )

    return _format_forecast_run_response(
        run,
    )


@_document_get_api(
    LatestForecastResponseSerializer,
    description="Return a persisted forecast by run identifier.",
    parameters=[
        OpenApiParameter("run_id", OpenApiTypes.STR, OpenApiParameter.PATH)
    ],
    error_statuses=(404, 429, 503),
)
def get_forecast_by_id(request, run_id):
    """Returns specific forecast run data."""
    if not ForecastRun.objects.exists():
        return _forecast_unavailable_response()

    run = get_object_or_404(ForecastRun, run_id=run_id)

    return _format_forecast_run_response(run)


def _format_forecast_run_response(
    run: ForecastRun,
):
    district_forecasts = (
        DistrictForecast.objects
        .filter(forecast_run=run)
        .select_related("district")
    )

    districts_data = []

    for df in district_forecasts:
        districts_data.append({
            "district_id": df.district.district_id,
            "district_name": df.district.name,
            "state": df.district.state,
            "zone": df.district.zone,
            "centroid_lat": df.district.centroid_lat,
            "centroid_lon": df.district.centroid_lon,
            "raw_nwp_mean_mm": df.raw_nwp_mean_mm,
            "corrected_mean_mm": df.corrected_mean_mm,
            "corrected_max_mm": df.corrected_max_mm,
            "bias_correction_delta_mm": df.bias_correction_delta_mm,
            "heavy_rain_probability": df.heavy_rain_probability,
            "prob_exceed_115mm": df.prob_exceed_115mm,
            "prob_exceed_204mm": df.prob_exceed_204mm,
            "uncertainty_lower_10pct": df.uncertainty_lower_10pct,
            "uncertainty_upper_90pct": df.uncertainty_upper_90pct,
            "uncertainty_range_width": df.uncertainty_range_width,
            "risk_code": df.risk_code,
            "risk_label": df.risk_label,
        })

    gj = get_districts_geojson(include_all_100=True)

    d_map = {
        d["district_id"]: d
        for d in districts_data
    }

    for feat in gj["features"]:
        d_id = feat["id"]

        if d_id in d_map:
            feat["properties"].update(
                d_map[d_id]
            )

    return JsonResponse({
        "forecast_run": {
            "run_id": run.run_id,
            "initialization_time": run.initialization_time.isoformat(),
            "valid_time": run.valid_time.isoformat(),
            "lead_time_hours": run.lead_time_hours,
            "cycle": run.initialization_time.strftime("%H:%M UTC"),
            "date_param": run.valid_time.isoformat(),
            "detected_regime": run.detected_regime,
            "regime_confidence": run.regime_confidence,
            "regime_probabilities": run.get_regime_probabilities(),
            "synoptic_features": run.get_synoptic_features(),
            "model_version": run.model_version,
            "created_at": run.created_at.isoformat(),
        },
        "districts_forecast": districts_data,
        "geojson_layer": gj,
    })


@_document_get_api(
    DistrictsResponseSerializer,
    description="Return district metadata and GeoJSON boundaries.",
    error_statuses=(404, 429),
)
def get_districts(request):
    """Returns all district metadata and administrative boundaries."""
    ForecastService.seed_districts_if_needed()
    if not District.objects.exists():
        return JsonResponse({"status": "ERROR", "message": "No districts available."}, status=404)

    districts = District.objects.all()

    data = [
        {
            "district_id": d.district_id,
            "name": d.name,
            "state": d.state,
            "zone": d.zone,
            "centroid": [
                d.centroid_lat,
                d.centroid_lon,
            ],
        }
        for d in districts
    ]

    return JsonResponse({
        "districts": data,
        "geojson": get_districts_geojson(),
    })


@_document_get_api(
    DistrictForecastResponseSerializer,
    description="Return a persisted district forecast.",
    parameters=[
        OpenApiParameter("district_id", OpenApiTypes.STR, OpenApiParameter.PATH)
    ],
    error_statuses=(404, 429, 503),
)
def get_district_forecast(request, district_id):
    """Returns forecast history and current prediction for a specific district."""
    latest_run = ForecastRun.objects.all().order_by("-valid_time").first()
    if latest_run is None:
        return _forecast_unavailable_response()

    district = get_object_or_404(
        District,
        district_id=district_id,
    )

    df = get_object_or_404(
        DistrictForecast,
        forecast_run=latest_run,
        district=district,
    )

    return JsonResponse({
        "district": {
            "district_id": district.district_id,
            "name": district.name,
            "state": district.state,
            "zone": district.zone,
            "centroid": [
                district.centroid_lat,
                district.centroid_lon,
            ],
        },
        "forecast_run": {
            "run_id": latest_run.run_id,
            "valid_time": latest_run.valid_time.isoformat(),
            "detected_regime": latest_run.detected_regime,
            "regime_confidence": latest_run.regime_confidence,
        },
        "rainfall_prediction": {
            "raw_nwp_mean_mm": df.raw_nwp_mean_mm,
            "corrected_mean_mm": df.corrected_mean_mm,
            "corrected_max_mm": df.corrected_max_mm,
            "bias_correction_delta_mm": df.bias_correction_delta_mm,
        },
        "heavy_rain_risk": {
            "heavy_rain_probability": df.heavy_rain_probability,
            "prob_exceed_115mm": df.prob_exceed_115mm,
            "prob_exceed_204mm": df.prob_exceed_204mm,
            "risk_code": df.risk_code,
            "risk_label": df.risk_label,
        },
        "uncertainty": {
            "lower_10pct": df.uncertainty_lower_10pct,
            "upper_90pct": df.uncertainty_upper_90pct,
            "range_width": df.uncertainty_range_width,
            "confidence_level": "80% Conformal Interval",
        },
    })


@_document_get_api(
    None,
    description="Return real-data regime verification when such evaluation exists.",
    error_statuses=(429, 503),
)
def get_regime_analytics(request):
    """Return real-data regime verification only when available."""
    return JsonResponse(
        {
            "status": "ERROR",
            "message": "Real-data regime evaluation is unavailable.",
        },
        status=503,
    )


@_document_get_api(
    RealVerificationResponseSerializer,
    description="Return the calculated held-out real IMD/ERA5 verification report.",
    error_statuses=(429, 503),
)
def get_verification_benchmarks(request):
    """Returns held-out verification derived from real IMD/ERA5 data."""
    v_path = os.path.join(
        VERIFICATION_DIR,
        "..",
        "weather_data",
        "processed",
        "real_ml",
        "M1_REAL_MODEL_LADDER_BACKTEST_2025.json",
    )

    if not os.path.isfile(v_path):
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Real-data verification is unavailable.",
            },
            status=503,
        )

    try:
        with open(v_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Real-data verification is unavailable.",
            },
            status=503,
        )

    return JsonResponse({"status": "AVAILABLE", **v_data})


@_document_get_api(
    ModelRegistryResponseSerializer,
    description="Return model records backed by persisted provenance.",
    error_statuses=(429, 503),
)
def get_model_registry(request):
    """Returns model versions, feature sets, training periods, and provenance."""
    provenance_rows = ModelProvenance.objects.all().order_by(
        "component",
        "-created_at",
    )
    if not provenance_rows.exists():
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Model provenance is unavailable.",
            },
            status=503,
        )

    models_info = []
    for provenance in provenance_rows:
        try:
            metrics = json.loads(provenance.metrics_json)
        except (TypeError, json.JSONDecodeError):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "message": "Model provenance is unavailable.",
                },
                status=503,
            )
        models_info.append(
            {
                "component": provenance.component,
                "model_name": provenance.model_name,
                "model_version": provenance.model_version,
                "dataset_version": provenance.dataset_version,
                "training_period": provenance.training_period,
                "val_period": provenance.val_period,
                "test_period": provenance.test_period,
                "metrics": metrics,
                "created_at": provenance.created_at.isoformat(),
            }
        )
    return JsonResponse({
        "registered_models": models_info,
        "count": len(models_info),
    })


@_document_get_api(
    FirebaseConfigurationResponseSerializer,
    description="Return environment-configured Firebase client settings.",
    error_statuses=(429, 503),
)
def get_firebase_config(request):
    """Returns Firebase client initialization parameters."""
    configuration = {
        "apiKey": os.environ.get("FIREBASE_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.environ.get("FIREBASE_APP_ID"),
        "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID"),
    }
    if not all(configuration.values()):
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Authentication configuration is unavailable.",
            },
            status=503,
        )
    return JsonResponse(configuration)


@ratelimit(
    key="ip",
    rate=settings.API_PREDICT_RATE,
    method="ALL",
    block=False,
)
@extend_schema(
    methods=["POST"],
    request=PredictForecastRequestSerializer,
    responses={
        200: PredictForecastResponseSerializer,
        400: APIErrorResponseSerializer,
        429: APIErrorResponseSerializer,
        500: APIErrorResponseSerializer,
        503: APIErrorResponseSerializer,
    },
    description="Run forecast inference with explicitly supplied model inputs.",
)
@extend_schema(
    methods=["GET"],
    parameters=[PredictForecastRequestSerializer],
    responses={
        200: PredictForecastResponseSerializer,
        400: APIErrorResponseSerializer,
        429: APIErrorResponseSerializer,
        500: APIErrorResponseSerializer,
        503: APIErrorResponseSerializer,
    },
    description="Run forecast inference with explicitly supplied model inputs.",
)
@api_view(["GET", "POST"])
def predict_custom_forecast(request):
    """
    On-demand inference endpoint.

    Runs:
    - Weather Regime Classifier
    - Level 0: Raw NWP
    - Level 1: Quantile Mapping
    - Level 2: Standard ML
    - Level 3: VARUNA-AI Regime-Aware ML
    - Heavy Rainfall Probability Estimator
    - 80% Conformal Prediction Uncertainty Bounds
    """

    import pandas as pd

    if getattr(request, "limited", False):
        return JsonResponse(
            {"status": "ERROR", "message": "Request limit exceeded."},
            status=429,
        )

    try:
        body = request.data if request.method == "POST" else request.query_params
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"status": "ERROR", "message": "Malformed request body."},
            status=400,
        )

    serializer = PredictForecastRequestSerializer(
        data=body
    )

    if not serializer.is_valid():
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Invalid forecast input",
                "errors": serializer.errors,
            },
            status=400,
        )

    body = serializer.validated_data

    if not _real_prediction_provenance_available():
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Real-data model provenance is unavailable.",
            },
            status=503,
        )

    from correction.models.correction_engine import (
        RainfallCorrectionEngine,
    )
    from probability.heavy_rainfall import (
        HeavyRainfallProbabilityEstimator,
    )
    from uncertainty.conformal_quantiles import (
        ConformalQuantileEstimator,
    )

    try:
        nwp_rain = body["nwp_rainfall"]
        lat = body["latitude"]
        lon = body["longitude"]
        district_name = body.get("district_name", "")
        mslp = body["mslp"]
        u850 = body["u850"]
        v850 = body["v850"]
        u200 = body["u200"]
        v200 = body["v200"]
        tcwv = body["tcwv"]
        rh700 = body["rh700"]
        cape = body["cape"]
        trough_lat = body["monsoon_trough_lat"]
        shear = body["vertical_wind_shear"]
        valid_time = body.get("valid_time") or timezone.now().date()

        df_in = pd.DataFrame([{
            "nwp_rainfall": nwp_rain,
            "latitude": lat,
            "longitude": lon,
            "mslp": mslp,
            "u850": u850,
            "v850": v850,
            "u200": u200,
            "v200": v200,
            "tcwv": tcwv,
            "rh700": rh700,
            "cape": cape,
            "monsoon_trough_lat": trough_lat,
            "vertical_wind_shear": shear,
            "day_of_year": valid_time.timetuple().tm_yday,
        }])

        engine = RainfallCorrectionEngine()

        proc = engine.process_forecast(
            df_in
        )

        prob_est = (
            HeavyRainfallProbabilityEstimator()
        )
        if set(prob_est.THRESHOLDS) - set(prob_est.models):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "message": "Forecast model artifacts are unavailable.",
                },
                status=503,
            )

        proc = prob_est.estimate_probabilities(
            proc
        )

        unc_est = (
            ConformalQuantileEstimator()
        )
        if not all((unc_est.q10_model, unc_est.q50_model, unc_est.q90_model)):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "message": "Forecast model artifacts are unavailable.",
                },
                status=503,
            )

        if not all((engine.level1, engine.level2, engine.level3)):
            return JsonResponse(
                {
                    "status": "ERROR",
                    "message": "Forecast model artifacts are unavailable.",
                },
                status=503,
            )

        proc = unc_est.estimate_uncertainty(
            proc
        )

        row = proc.iloc[0]

        detected_regime = row["predicted_regime"]
        regime_conf = float(row["regime_confidence"])
        l0 = float(row["rain_level0_raw"])
        l1 = float(row["rain_level1_eqm"])
        l2 = float(row["rain_level2_std_ml"])
        l3 = float(row["rain_level3_varuna"])

        delta = float(
            round(abs(l3 - l0), 2)
        )

        prob_heavy = float(row["heavy_rain_probability"])
        unc_lower = float(row["uncertainty_lower_10pct"])
        unc_upper = float(row["uncertainty_upper_90pct"])

        risk_category = row["operational_risk_level"]
        if risk_category.startswith("RED_ALERT"):
            risk_code = "RED"
            action = (
                "IMMEDIATE EVACUATION & FLOOD PREPAREDNESS. "
                "NDRF & SDMA standby."
            )
        elif risk_category.startswith("ORANGE_ALERT"):
            risk_code = "ORANGE"
            action = (
                "BE PREPARED. Heavy rainfall warning; "
                "restrict movement in riparian areas."
            )
        elif risk_category.startswith("YELLOW_ALERT"):
            risk_code = "YELLOW"
            action = (
                "BE AWARE. Moderate rainfall; "
                "check local drainage channels."
            )
        else:
            risk_code = "GREEN"
            action = (
                "NORMAL seasonal rainfall; "
                "routine agricultural water management."
            )

        prob_cols = [
            c
            for c in proc.columns
            if c.startswith("prob_")
            and not c.startswith("prob_exceed")
        ]

        reg_probs = {
            c.replace(
                "prob_",
                "",
            ).upper(): float(
                round(
                    row[c],
                    4,
                )
            )
            for c in prob_cols
        }

        return JsonResponse({
            "status": "SUCCESS",
            "district_name": district_name,
            "raw_nwp_rainfall_mm": l0,
            "corrected_rainfall_mm": l3,
            "bias_correction_delta_mm": delta,
            "detected_regime": detected_regime,
            "regime_confidence": regime_conf,
            "regime_probabilities": reg_probs,
            "model_ladder": {
                "level0_raw_nwp_mm": l0,
                "level1_quantile_mapping_mm": l1,
                "level2_standard_ml_mm": l2,
                "level3_regime_aware_ml_mm": l3,
            },
            "heavy_rainfall_probability": prob_heavy,
            "uncertainty_interval_80pct": {
                "lower_10pct_mm": unc_lower,
                "upper_90pct_mm": unc_upper,
            },
            "risk_assessment": {
                "risk_code": risk_code,
                "action_advisory": action,
            },
        })

    except Exception:
        logger.exception("Forecast inference failed.")
        return JsonResponse(
            {
                "status": "ERROR",
                "message": "Forecast inference failed.",
            },
            status=500,
        )