"""
VARUNA-AI: Temporal Alignment Module
Owner: Member 1 (Data Foundation / Data Engineer)
"""

import pandas as pd
import numpy as np
from typing import Tuple

class TemporalAligner:
    """
    Handles temporal alignment between NWP forecasts (init_time + lead_time)
    and observed ground truth (valid_time matching 24h accumulation windows).
    """

    @staticmethod
    def align_forecast_with_observation(
        forecast_df: pd.DataFrame,
        observation_df: pd.DataFrame,
        time_key: str = "valid_time",
        spatial_keys: Tuple[str, ...] = ("latitude", "longitude"),
    ) -> pd.DataFrame:
        """
        Inner-joins NWP forecast records with ground truth observation records
        on identical valid_time and spatial coordinates.
        """
        f_df = forecast_df.copy()
        o_df = observation_df.copy()

        f_df[time_key] = pd.to_datetime(f_df[time_key]).dt.floor("D")
        o_df[time_key] = pd.to_datetime(o_df[time_key]).dt.floor("D")

        # Ensure spatial keys match precision (round to 2 decimals)
        for sk in spatial_keys:
            if sk in f_df.columns:
                f_df[sk] = f_df[sk].round(2)
            if sk in o_df.columns:
                o_df[sk] = o_df[sk].round(2)

        merged = pd.merge(
            f_df,
            o_df,
            on=[time_key, *spatial_keys],
            how="inner",
            suffixes=("_nwp_meta", "_obs_meta")
        )

        return merged.sort_values(by=[time_key, *spatial_keys]).reset_index(drop=True)

    @staticmethod
    def create_chronological_splits(
        df: pd.DataFrame,
        time_col: str = "valid_time",
        train_end_year: int = 2022,
        val_year: int = 2023,
        test_year: int = 2024,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Strict chronological splitting to prevent temporal data leakage:
        - Train: <= train_end_year
        - Val: == val_year
        - Test: >= test_year
        """
        df_time = pd.to_datetime(df[time_col])
        train_df = df[df_time.dt.year <= train_end_year].copy().reset_index(drop=True)
        val_df = df[df_time.dt.year == val_year].copy().reset_index(drop=True)
        test_df = df[df_time.dt.year >= test_year].copy().reset_index(drop=True)

        return train_df, val_df, test_df
