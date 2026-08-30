"""
VARUNA-AI: Level 0 Baseline — Raw NWP Identity Model
Owner: Member 3 (Rainfall Post-Processing ML Engineer)
"""

import numpy as np
import pandas as pd
from typing import Union

class Level0RawNWP:
    """
    Level 0 Baseline: Direct uncorrected Numerical Weather Prediction rainfall.
    Preserves raw NWP physics without post-processing.
    """

    def __init__(self, rain_col: str = "nwp_rainfall"):
        self.rain_col = rain_col
        self.model_name = "Level0_Raw_NWP"
        self.model_version = "v1.0.0"

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Returns non-negative raw NWP precipitation."""
        return np.maximum(df[self.rain_col].values, 0.0)
