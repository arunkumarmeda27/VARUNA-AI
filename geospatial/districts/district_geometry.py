"""
VARUNA-AI: Geospatial District Geometries and Metadata
Owner: Member 6 (Geospatial + Operational Interface Engineer)

Provides valid GeoJSON polygon boundaries and coordinates for representative
monsoon districts across distinct meteorological and terrain zones in India.
"""

import json
from typing import Dict, List, Any
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, shape

DISTRICTS_METADATA: List[Dict[str, Any]] = [
    {
        "district_id": "DIST_MH_MUM",
        "district_name": "Mumbai Suburban",
        "state": "Maharashtra",
        "zone": "West Coast / Konkan",
        "centroid": [19.10, 72.88],
        "polygon_coords": [
            [72.78, 19.00], [72.95, 19.00], [72.98, 19.25], [72.82, 19.25], [72.78, 19.00]
        ],
    },
    {
        "district_id": "DIST_MH_RAT",
        "district_name": "Ratnagiri",
        "state": "Maharashtra",
        "zone": "West Coast / Konkan",
        "centroid": [17.00, 73.30],
        "polygon_coords": [
            [73.15, 16.60], [73.55, 16.60], [73.60, 17.40], [73.20, 17.40], [73.15, 16.60]
        ],
    },
    {
        "district_id": "DIST_KL_WAY",
        "district_name": "Wayanad",
        "state": "Kerala",
        "zone": "South Peninsular / Western Ghats",
        "centroid": [11.70, 76.10],
        "polygon_coords": [
            [75.90, 11.50], [76.35, 11.50], [76.40, 11.95], [75.95, 11.95], [75.90, 11.50]
        ],
    },
    {
        "district_id": "DIST_MH_PUN",
        "district_name": "Pune",
        "state": "Maharashtra",
        "zone": "Madhya Maharashtra / Leeward",
        "centroid": [18.52, 73.85],
        "polygon_coords": [
            [73.40, 18.10], [74.30, 18.10], [74.35, 19.00], [73.45, 19.00], [73.40, 18.10]
        ],
    },
    {
        "district_id": "DIST_MH_NAG",
        "district_name": "Nagpur",
        "state": "Maharashtra",
        "zone": "Central India / Vidarbha",
        "centroid": [21.15, 79.10],
        "polygon_coords": [
            [78.70, 20.70], [79.60, 20.70], [79.65, 21.60], [78.75, 21.60], [78.70, 20.70]
        ],
    },
    {
        "district_id": "DIST_OR_CUT",
        "district_name": "Cuttack",
        "state": "Odisha",
        "zone": "East Coast / Cyclone Vulnerable",
        "centroid": [20.45, 85.90],
        "polygon_coords": [
            [85.50, 20.20], [86.30, 20.20], [86.35, 20.75], [85.55, 20.75], [85.50, 20.20]
        ],
    },
    {
        "district_id": "DIST_OR_SAM",
        "district_name": "Sambalpur",
        "state": "Odisha",
        "zone": "East India / Monsoon Trough",
        "centroid": [21.45, 84.00],
        "polygon_coords": [
            [83.60, 21.10], [84.40, 21.10], [84.45, 21.80], [83.65, 21.80], [83.60, 21.10]
        ],
    },
    {
        "district_id": "DIST_BR_PAT",
        "district_name": "Patna",
        "state": "Bihar",
        "zone": "East India / Gangetic Plain",
        "centroid": [25.60, 85.15],
        "polygon_coords": [
            [84.75, 25.30], [85.55, 25.30], [85.60, 25.80], [84.80, 25.80], [84.75, 25.30]
        ],
    },
    {
        "district_id": "DIST_UK_DDN",
        "district_name": "Dehradun",
        "state": "Uttarakhand",
        "zone": "Northwest India / Himalayan Foothills",
        "centroid": [30.30, 78.00],
        "polygon_coords": [
            [77.60, 29.95], [78.40, 29.95], [78.45, 30.70], [77.65, 30.70], [77.60, 29.95]
        ],
    },
    {
        "district_id": "DIST_RJ_JAI",
        "district_name": "Jaipur",
        "state": "Rajasthan",
        "zone": "Northwest India / Semi-Arid",
        "centroid": [26.90, 75.80],
        "polygon_coords": [
            [75.20, 26.40], [76.40, 26.40], [76.45, 27.35], [75.25, 27.35], [75.20, 26.40]
        ],
    },
    {
        "district_id": "DIST_AS_KAM",
        "district_name": "Kamrup (Guwahati)",
        "state": "Assam",
        "zone": "Northeast India / Brahmaputra Valley",
        "centroid": [26.20, 91.75],
        "polygon_coords": [
            [91.30, 25.90], [92.15, 25.90], [92.20, 26.50], [91.35, 26.50], [91.30, 25.90]
        ],
    },
    {
        "district_id": "DIST_TN_CHE",
        "district_name": "Chennai",
        "state": "Tamil Nadu",
        "zone": "South Peninsular / Rain Shadow",
        "centroid": [13.10, 80.25],
        "polygon_coords": [
            [80.10, 12.95], [80.35, 12.95], [80.35, 13.25], [80.10, 13.25], [80.10, 12.95]
        ],
    },
]

def get_districts_geojson() -> Dict[str, Any]:
    """Generates standard FeatureCollection GeoJSON of all districts."""
    features = []
    for d in DISTRICTS_METADATA:
        poly = {
            "type": "Polygon",
            "coordinates": [d["polygon_coords"]],
        }
        features.append({
            "type": "Feature",
            "id": d["district_id"],
            "properties": {
                "district_id": d["district_id"],
                "district_name": d["district_name"],
                "state": d["state"],
                "zone": d["zone"],
                "centroid_lat": d["centroid"][0],
                "centroid_lon": d["centroid"][1],
            },
            "geometry": poly,
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }

def get_districts_geodataframe() -> gpd.GeoDataFrame:
    """Returns GeoDataFrame with EPSG:4326 CRS."""
    gj = get_districts_geojson()
    gdf = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")
    return gdf
