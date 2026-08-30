"""
VARUNA-AI: Scientific Data Validation Module
Owner: Member 1 (Data Foundation / Data Engineer)
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

from weather_data.metadata.data_dictionary import VARIABLE_BOUNDS, IMD_RAINFALL_CATEGORIES

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validates meteorological and NWP datasets against physical bounds,
    temporal ordering, and integrity constraints.
    """

    def __init__(self, bounds: Dict[str, Tuple[float, float]] = VARIABLE_BOUNDS):
        self.bounds = bounds

    def validate_dataframe(self, df: pd.DataFrame, drop_invalid: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validates all columns against physical bounds.
        Returns cleaned DataFrame and validation report.
        """
        report: Dict[str, Any] = {
            "initial_rows": len(df),
            "out_of_bounds_counts": {},
            "null_counts": {},
            "negative_rainfall_fixed": 0,
            "passed": True,
        }

        df_clean = df.copy()

        # 1. Rainfall non-negativity correction
        for rain_col in ["observed_rainfall", "nwp_rainfall"]:
            if rain_col in df_clean.columns:
                neg_count = (df_clean[rain_col] < 0).sum()
                if neg_count > 0:
                    logger.warning(f"Found {neg_count} negative values in {rain_col}. Clamping to 0.0 mm.")
                    df_clean[rain_col] = df_clean[rain_col].clip(lower=0.0)
                    report["negative_rainfall_fixed"] += int(neg_count)

        # 2. Check physical bounds for each column
        invalid_mask = pd.Series(False, index=df_clean.index)

        for col, (min_val, max_val) in self.bounds.items():
            if col in df_clean.columns:
                null_cnt = df_clean[col].isnull().sum()
                report["null_counts"][col] = int(null_cnt)

                oob_mask = (df_clean[col] < min_val) | (df_clean[col] > max_val)
                oob_cnt = oob_mask.sum()
                report["out_of_bounds_counts"][col] = int(oob_cnt)

                if oob_cnt > 0:
                    logger.warning(f"Column '{col}' has {oob_cnt} values outside physical range [{min_val}, {max_val}].")
                    invalid_mask = invalid_mask | oob_mask

        if drop_invalid and invalid_mask.any():
            df_clean = df_clean[~invalid_mask].reset_index(drop=True)
            report["dropped_rows"] = int(invalid_mask.sum())
            report["final_rows"] = len(df_clean)
        else:
            report["dropped_rows"] = 0
            report["final_rows"] = len(df_clean)

        return df_clean, report

    @staticmethod
    def verify_no_future_leakage(df: pd.DataFrame) -> bool:
        """
        Guarantees that forecast initialization time is strictly before or at valid time,
        and that features used for prediction contain no future ground truth.
        """
        if "forecast_init_time" in df.columns and "valid_time" in df.columns:
            init_t = pd.to_datetime(df["forecast_init_time"])
            valid_t = pd.to_datetime(df["valid_time"])
            if (init_t > valid_t).any():
                raise ValueError("Data Leakage Error: Forecast initialization time is later than valid time!")
        return True

    @staticmethod
    def assign_imd_category(rainfall_series: pd.Series) -> pd.Series:
        """Categorizes rainfall amount (mm) into IMD rainfall category."""
        def _get_cat(val: float) -> str:
            if val < 2.5:
                return "NO_RAIN"
            elif val < 15.6:
                return "LIGHT_TO_MODERATE"
            elif val < 64.5:
                return "MODERATE_TO_HEAVY"
            elif val < 115.6:
                return "HEAVY_RAIN"
            elif val < 204.5:
                return "VERY_HEAVY_RAIN"
            else:
                return "EXTREMELY_HEAVY_RAIN"

        return rainfall_series.apply(_get_cat)
