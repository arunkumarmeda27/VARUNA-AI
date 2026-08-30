"""
VARUNA-AI: Backend Forecast & Data Service
Owner: Member 5 (Backend + Platform Integration Engineer)

Bridges the ML pipeline (Members 1, 2, 3, 4, 6) with Django ORM and REST API.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date

from backend.models import ForecastRun, District, DistrictForecast, ModelProvenance
from geospatial.districts.district_geometry import DISTRICTS_METADATA
from geospatial.aggregation.grid_aggregator import GridToDistrictAggregator
from correction.models.correction_engine import RainfallCorrectionEngine
from probability.heavy_rainfall import HeavyRainfallProbabilityEstimator
from uncertainty.conformal_quantiles import ConformalQuantileEstimator

logger = logging.getLogger(__name__)

class ForecastService:
    """
    Central service interface executing operational forecast cycles and database sync.
    """

    @classmethod
    def seed_districts_if_needed(cls):
        """Populates district boundaries from GIS registry if table is empty."""
        if District.objects.count() == 0:
            logger.info("Seeding district spatial metadata into database...")
            for d in DISTRICTS_METADATA:
                poly = {
                    "type": "Polygon",
                    "coordinates": [d["polygon_coords"]],
                }
                District.objects.create(
                    district_id=d["district_id"],
                    name=d["district_name"],
                    state=d["state"],
                    zone=d["zone"],
                    centroid_lat=d["centroid"][0],
                    centroid_lon=d["centroid"][1],
                    polygon_geojson=json.dumps(poly),
                )
            logger.info(f"Seeded {len(DISTRICTS_METADATA)} districts.")

    @classmethod
    def seed_sample_forecast_runs(cls):
        """Generates representative forecast runs across distinct synoptic regimes."""
        cls.seed_districts_if_needed()

        if ForecastRun.objects.count() > 0:
            return

        logger.info("Initializing operational forecast runs for demonstration...")
        from weather_data.ingestion.data_loader import MonsoonDataIngestion
        raw_df = MonsoonDataIngestion.generate_synoptic_monsoon_dataset(start_year=2026, end_year=2026, random_seed=101)

        # Run pipeline
        from weather_data.features.synoptic_features import SynopticFeatureEngineer
        feat_df = SynopticFeatureEngineer.compute_all_features(raw_df)

        corr_engine = RainfallCorrectionEngine()
        prob_estimator = HeavyRainfallProbabilityEstimator()
        unc_estimator = ConformalQuantileEstimator()
        aggregator = GridToDistrictAggregator()

        # Group by valid_time and create 3 distinct demonstration runs
        unique_dates = feat_df["valid_time"].unique()[:4]

        for v_date_str in unique_dates:
            sub_df = feat_df[feat_df["valid_time"] == v_date_str].copy()
            run_id = f"RUN_2026_{v_date_str.replace('-', '')}_00Z"

            # Execute pipeline
            proc_df = corr_engine.process_forecast(sub_df)
            proc_df = prob_estimator.estimate_probabilities(proc_df)
            proc_df = unc_estimator.estimate_uncertainty(proc_df)

            # Spatial aggregation
            dist_df = aggregator.aggregate_forecast_to_districts(proc_df)

            # Synoptic summary
            first_row = proc_df.iloc[0]
            detected_regime = first_row.get("predicted_regime", "ACTIVE_MONSOON")
            reg_conf = float(first_row.get("regime_confidence", 0.82))

            prob_cols = [c for c in proc_df.columns if c.startswith("prob_") and not c.startswith("prob_exceed")]
            reg_probs = {c.replace("prob_", "").upper(): float(round(first_row[c], 4)) for c in prob_cols}

            synoptic_summary = {
                "mslp": float(first_row.get("mslp", 1002.0)),
                "u850": float(first_row.get("u850", 18.0)),
                "v850": float(first_row.get("v850", 4.0)),
                "u200": float(first_row.get("u200", -28.0)),
                "v200": float(first_row.get("v200", 0.0)),
                "tcwv": float(first_row.get("tcwv", 58.0)),
                "rh700": float(first_row.get("rh700", 82.0)),
                "cape": float(first_row.get("cape", 1800.0)),
                "monsoon_trough_lat": float(first_row.get("monsoon_trough_lat", 22.0)),
                "vertical_wind_shear": float(first_row.get("vertical_wind_shear", 46.0)),
            }

            from datetime import timezone
            v_date = datetime.strptime(v_date_str, "%Y-%m-%d").date()
            init_time = datetime.combine(v_date, datetime.min.time(), tzinfo=timezone.utc)

            run_obj = ForecastRun.objects.create(
                run_id=run_id,
                initialization_time=init_time,
                valid_time=v_date,
                lead_time_hours=24,
                detected_regime=detected_regime,
                regime_confidence=reg_conf,
                regime_probabilities_json=json.dumps(reg_probs),
                synoptic_features_json=json.dumps(synoptic_summary),
                model_version="VARUNA-Level3-XGB-v1.0.0",
            )

            # Store district forecasts
            for _, row in dist_df.iterrows():
                try:
                    d_obj = District.objects.get(district_id=row["district_id"])
                    DistrictForecast.objects.create(
                        forecast_run=run_obj,
                        district=d_obj,
                        raw_nwp_mean_mm=row["raw_nwp_mean_mm"],
                        corrected_mean_mm=row["corrected_mean_mm"],
                        corrected_max_mm=row["corrected_max_mm"],
                        bias_correction_delta_mm=row["bias_correction_delta_mm"],
                        heavy_rain_probability=row["heavy_rain_probability"],
                        prob_exceed_115mm=row.get("prob_exceed_115mm", 0.0),
                        prob_exceed_204mm=row.get("prob_exceed_204mm", 0.0),
                        uncertainty_lower_10pct=row["uncertainty_lower_10pct"],
                        uncertainty_upper_90pct=row["uncertainty_upper_90pct"],
                        uncertainty_range_width=row["uncertainty_range_width"],
                        risk_code=row["risk_code"],
                        risk_label=row["risk_label"],
                    )
                except District.DoesNotExist:
                    continue

        logger.info("Sample forecast runs seeded successfully!")
