"""
VARUNA-AI: Backend Forecast & Data Service
Owner: Member 5 (Backend + Platform Integration Engineer)

Bridges the ML pipeline (Members 1, 2, 3, 4, 6) with Django ORM and REST API.
Operates on the 100-district named dataset and trained ML models.
"""

import os
import json
import logging
import pandas as pd

from backend.models import ForecastRun, District
from geospatial.districts.district_geometry import DISTRICTS_METADATA

logger = logging.getLogger(__name__)

CSV_DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VARUNA_AI_100_district_sample_named.csv")

class ForecastService:
    """
    Central service interface executing operational forecast cycles and database sync.
    """

    @classmethod
    def seed_districts_if_needed(cls):
        """Populates district boundaries from GIS registry and named dataset."""
        # 1. Seed base metadata
        for d in DISTRICTS_METADATA:
            poly = {
                "type": "Polygon",
                "coordinates": [d["polygon_coords"]],
            }
            District.objects.update_or_create(
                district_id=d["district_id"],
                defaults={
                    "name": d["district_name"],
                    "state": d["state"],
                    "zone": d["zone"],
                    "centroid_lat": d["centroid"][0],
                    "centroid_lon": d["centroid"][1],
                    "polygon_geojson": json.dumps(poly),
                }
            )

        # 2. Seed all 100 named districts if available
        if os.path.exists(CSV_DATASET_PATH):
            try:
                df = pd.read_csv(CSV_DATASET_PATH)
                for _, row in df.iterrows():
                    d_name = str(row.get("district", "Unknown"))
                    lat = float(row.get("latitude", 20.0))
                    lon = float(row.get("longitude", 78.0))
                    d_id = f"DIST_{d_name.replace(' ', '_').upper()[:12]}"
                    delta = 0.25
                    poly = {
                        "type": "Polygon",
                        "coordinates": [[
                            [round(lon - delta, 4), round(lat - delta, 4)],
                            [round(lon - delta, 4), round(lat + delta, 4)],
                            [round(lon + delta, 4), round(lat + delta, 4)],
                            [round(lon + delta, 4), round(lat - delta, 4)],
                            [round(lon - delta, 4), round(lat - delta, 4)],
                        ]]
                    }
                    District.objects.update_or_create(
                        district_id=d_id,
                        defaults={
                            "name": d_name,
                            "state": "India",
                            "zone": "National Meteorological Grid",
                            "centroid_lat": lat,
                            "centroid_lon": lon,
                            "polygon_geojson": json.dumps(poly),
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not load named CSV for districts: {e}")

        logger.info(f"Synchronized {District.objects.count()} districts in database.")

    @classmethod
    def seed_sample_forecast_runs(cls):
        """Reject sample forecast generation for operational forecast storage."""
        if ForecastRun.objects.exists():
            return
        raise RuntimeError(
            "No persisted real forecast is available; sample forecast generation is disabled."
        )
