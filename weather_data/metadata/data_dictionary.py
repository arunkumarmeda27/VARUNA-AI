"""
VARUNA-AI: Data Dictionary Metadata and Validation Schemas.
Owner: Member 1 (Data Foundation / Data Engineer)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

# IMD Rainfall Categories (in mm / 24 hr)
IMD_RAINFALL_CATEGORIES: Dict[str, Tuple[float, float]] = {
    "NO_RAIN": (0.0, 2.5),
    "LIGHT_TO_MODERATE": (2.5, 15.6),
    "MODERATE_TO_HEAVY": (15.6, 64.5),
    "HEAVY_RAIN": (64.5, 115.6),
    "VERY_HEAVY_RAIN": (115.6, 204.5),
    "EXTREMELY_HEAVY_RAIN": (204.5, 9999.0),
}

# Standard Operational Verification Thresholds (mm/day)
OPERATIONAL_THRESHOLDS: List[float] = [2.5, 15.6, 64.5, 115.6, 204.5]

# Recognized Weather Regimes
WEATHER_REGIMES: List[str] = [
    "ACTIVE_MONSOON",
    "BREAK_MONSOON",
    "MONSOON_LOW_DEPRESSION",
    "COASTAL_RAINFALL",
    "OROGRAPHIC_RAINFALL",
    "WESTERN_DISTURBANCE",
]

# Physical Variable Bounds for Data Validation
VARIABLE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "observed_rainfall": (0.0, 1500.0),       # mm/day
    "nwp_rainfall": (0.0, 1000.0),            # mm/day
    "mslp": (870.0, 1085.0),                  # hPa
    "u850": (-60.0, 60.0),                    # m/s
    "v850": (-60.0, 60.0),                    # m/s
    "u200": (-90.0, 90.0),                    # m/s
    "v200": (-90.0, 90.0),                    # m/s
    "tcwv": (0.0, 100.0),                     # kg/m^2
    "rh700": (0.0, 100.0),                    # %
    "cape": (0.0, 7000.0),                    # J/kg
    "latitude": (5.0, 40.0),                  # deg N
    "longitude": (65.0, 100.0),               # deg E
}

@dataclass
class VariableMetadata:
    name: str
    symbol: str
    unit: str
    valid_range: Tuple[float, float]
    description: str

METADATA_REGISTRY: Dict[str, VariableMetadata] = {
    var: VariableMetadata(
        name=var,
        symbol=var.upper(),
        unit="mm/day" if "rainfall" in var else "SI",
        valid_range=bounds,
        description=f"Physical meteorological parameter {var}",
    )
    for var, bounds in VARIABLE_BOUNDS.items()
}
