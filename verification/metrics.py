"""
VARUNA-AI: Scientific Meteorological Verification Metrics
Owner: Member 4 (Probability + Uncertainty + Verification Engineer)

Comprehensive verification library complying with WMO / IMD standard forecast verification:
- Continuous: MAE, RMSE, Mean Bias, Pearson Correlation
- Categorical: 2x2 Contingency Table (Hits, False Alarms, Misses, Correct Negatives),
               POD, FAR, CSI (Threat Score), ETS (Equitable Threat Score), Frequency Bias, HK
- Spatial: Fractions Skill Score (FSS) across neighborhood scales
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from scipy.stats import pearsonr

def calculate_continuous_metrics(obs: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    """Calculates MAE, RMSE, Mean Bias, and Pearson correlation."""
    obs_clean = np.asarray(obs, dtype=float)
    pred_clean = np.asarray(pred, dtype=float)

    mae = float(np.mean(np.abs(pred_clean - obs_clean)))
    rmse = float(np.sqrt(np.mean((pred_clean - obs_clean)**2)))
    bias = float(np.mean(pred_clean - obs_clean))

    if len(obs_clean) > 1 and np.std(obs_clean) > 1e-5 and np.std(pred_clean) > 1e-5:
        corr, _ = pearsonr(obs_clean, pred_clean)
        corr_val = float(corr)
    else:
        corr_val = 0.0

    return {
        "MAE": round(mae, 3),
        "RMSE": round(rmse, 3),
        "Mean_Bias": round(bias, 3),
        "Correlation": round(corr_val, 3),
    }

def calculate_contingency_table(obs: np.ndarray, pred: np.ndarray, threshold: float) -> Dict[str, int]:
    """
    Computes 2x2 contingency table components for event >= threshold:
    - Hits (H): Pred >= T and Obs >= T
    - False Alarms (F): Pred >= T and Obs < T
    - Misses (M): Pred < T and Obs >= T
    - Correct Negatives (C): Pred < T and Obs < T
    """
    obs_event = obs >= threshold
    pred_event = pred >= threshold

    hits = int(np.sum(pred_event & obs_event))
    false_alarms = int(np.sum(pred_event & (~obs_event)))
    misses = int(np.sum((~pred_event) & obs_event))
    correct_negatives = int(np.sum((~pred_event) & (~obs_event)))

    return {
        "Hits": hits,
        "False_Alarms": false_alarms,
        "Misses": misses,
        "Correct_Negatives": correct_negatives,
        "Total": len(obs),
    }

def calculate_categorical_scores(obs: np.ndarray, pred: np.ndarray, threshold: float) -> Dict[str, float]:
    """
    Computes POD, FAR, CSI, ETS, Frequency Bias, and HK discriminant.
    """
    ct = calculate_contingency_table(obs, pred, threshold)
    H = ct["Hits"]
    F = ct["False_Alarms"]
    M = ct["Misses"]
    C = ct["Correct_Negatives"]
    N = ct["Total"]

    # Probability of Detection (POD / Hit Rate)
    pod = H / (H + M) if (H + M) > 0 else 0.0

    # False Alarm Ratio (FAR)
    far = F / (H + F) if (H + F) > 0 else 0.0

    # Critical Success Index (CSI / Threat Score)
    csi = H / (H + F + M) if (H + F + M) > 0 else 0.0

    # Frequency Bias (FBIAS)
    fbias = (H + F) / (H + M) if (H + M) > 0 else 0.0

    # Equitable Threat Score (ETS / Gilbert Skill Score)
    H_rand = ((H + M) * (H + F)) / N if N > 0 else 0.0
    ets_denom = H + F + M - H_rand
    ets = (H - H_rand) / ets_denom if ets_denom > 0 else 0.0

    # Hanssen-Kuipers Discriminant (HK / Peirce Skill Score)
    pod_val = H / (H + M) if (H + M) > 0 else 0.0
    pofd_val = F / (F + C) if (F + C) > 0 else 0.0
    hk = pod_val - pofd_val

    return {
        "Threshold_mm": threshold,
        "Hits": H,
        "False_Alarms": F,
        "Misses": M,
        "Correct_Negatives": C,
        "POD": round(float(pod), 4),
        "FAR": round(float(far), 4),
        "CSI": round(float(csi), 4),
        "ETS": round(float(ets), 4),
        "Frequency_Bias": round(float(fbias), 4),
        "HK_Score": round(float(hk), 4),
    }

def calculate_fractions_skill_score(
    obs_grid: np.ndarray,
    pred_grid: np.ndarray,
    threshold: float,
    window_size: int = 3,
) -> float:
    """
    Computes spatial Fractions Skill Score (FSS) over a neighborhood window.
    obs_grid and pred_grid are 2D arrays.
    """
    from scipy.ndimage import uniform_filter

    binary_obs = (obs_grid >= threshold).astype(float)
    binary_pred = (pred_grid >= threshold).astype(float)

    # Neighborhood fractions
    frac_obs = uniform_filter(binary_obs, size=window_size, mode="constant", cval=0.0)
    frac_pred = uniform_filter(binary_pred, size=window_size, mode="constant", cval=0.0)

    mse = np.mean((frac_pred - frac_obs)**2)
    mse_ref = np.mean(frac_pred**2) + np.mean(frac_obs**2)

    if mse_ref < 1e-9:
        return 1.0 if mse < 1e-9 else 0.0

    fss = 1.0 - (mse / mse_ref)
    return round(float(np.clip(fss, 0.0, 1.0)), 4)
