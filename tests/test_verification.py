"""
VARUNA-AI: Scientific Verification Metrics Unit Tests
Owner: Member 4 (Probability + Uncertainty + Verification Engineer)
"""

import numpy as np
import pytest
from verification.metrics import (
    calculate_continuous_metrics,
    calculate_contingency_table,
    calculate_categorical_scores,
    calculate_fractions_skill_score,
)

def test_continuous_metrics():
    obs = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    pred = np.array([12.0, 18.0, 33.0, 38.0, 55.0])

    m = calculate_continuous_metrics(obs, pred)

    assert "MAE" in m
    assert "RMSE" in m
    assert "Mean_Bias" in m
    assert "Correlation" in m
    assert m["MAE"] == pytest.approx(2.8, 0.1)
    assert m["Mean_Bias"] == pytest.approx(1.2, 0.1)
    assert m["Correlation"] > 0.98

def test_contingency_and_categorical_scores():
    # 10 samples, threshold = 64.5 mm
    obs = np.array([70.0, 80.0, 10.0, 15.0, 65.0, 100.0, 2.0, 5.0, 90.0, 0.0])
    pred = np.array([75.0, 50.0, 12.0, 70.0, 80.0, 110.0, 0.0, 0.0, 85.0, 0.0])
    # Obs >= 64.5: indices 0, 1, 4, 5, 8 (5 events)
    # Pred >= 64.5: indices 0, 3, 4, 5, 8 (5 events)
    # Hits: indices 0, 4, 5, 8 (4 hits)
    # False Alarm: index 3 (1 FA)
    # Miss: index 1 (1 Miss)
    # Correct Negatives: indices 2, 6, 7, 9 (4 CN)

    ct = calculate_contingency_table(obs, pred, 64.5)
    assert ct["Hits"] == 4
    assert ct["False_Alarms"] == 1
    assert ct["Misses"] == 1
    assert ct["Correct_Negatives"] == 4

    scores = calculate_categorical_scores(obs, pred, 64.5)
    # POD = H / (H + M) = 4 / 5 = 0.80
    assert pytest.approx(scores["POD"], 0.01) == 0.80
    # FAR = F / (H + F) = 1 / 5 = 0.20
    assert pytest.approx(scores["FAR"], 0.01) == 0.20
    # CSI = H / (H + F + M) = 4 / 6 = 0.667
    assert pytest.approx(scores["CSI"], 0.01) == 0.667

def test_fractions_skill_score():
    # Perfect alignment
    grid_a = np.array([[70.0, 10.0], [5.0, 80.0]])
    grid_b = np.array([[75.0, 8.0], [2.0, 85.0]])

    fss = calculate_fractions_skill_score(grid_a, grid_b, 64.5, window_size=1)
    assert fss == 1.0
