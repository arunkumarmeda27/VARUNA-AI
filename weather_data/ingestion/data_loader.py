"""
VARUNA-AI: Scientific Data Ingestion & Monsoon Simulation Engine
Owner: Member 1 (Data Foundation / Data Engineer)

Generates scientifically sound, physically coupled Indian Monsoon meteorological
datasets spanning 2018-2024 with authentic synoptic patterns, NWP systematic errors,
and IMD observational ground truth.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, List, Dict

from weather_data.metadata.data_dictionary import WEATHER_REGIMES
from weather_data.preprocessing.validator import DataValidator
from weather_data.features.synoptic_features import SynopticFeatureEngineer

class MonsoonDataIngestion:
    """
    Generates and manages multi-year meteorological datasets across Indian monsoon regimes,
    ensuring physical consistency, coordinate mapping, and reproducible seeds.
    """

    REPRESENTATIVE_LOCATIONS = [
        {"grid_id": "G_19.00_72.85", "name": "Mumbai (Konkan / Coastal)", "latitude": 19.00, "longitude": 72.85, "terrain": "coastal_orographic", "zone": "West Coast"},
        {"grid_id": "G_16.98_73.30", "name": "Ratnagiri (Konkan)", "latitude": 17.00, "longitude": 73.30, "terrain": "coastal_orographic", "zone": "West Coast"},
        {"grid_id": "G_11.68_76.13", "name": "Wayanad (Western Ghats)", "latitude": 11.70, "longitude": 76.10, "terrain": "orographic", "zone": "South Peninsular"},
        {"grid_id": "G_18.52_73.85", "name": "Pune (Madhya Maharashtra)", "latitude": 18.50, "longitude": 73.85, "terrain": "leeward", "zone": "Central India"},
        {"grid_id": "G_21.15_79.08", "name": "Nagpur (Vidarbha)", "latitude": 21.15, "longitude": 79.10, "terrain": "plains", "zone": "Central India"},
        {"grid_id": "G_20.46_85.88", "name": "Cuttack (Odisha Coast)", "latitude": 20.45, "longitude": 85.90, "terrain": "cyclonic_coastal", "zone": "East Coast"},
        {"grid_id": "G_21.46_83.98", "name": "Sambalpur (Odisha)", "latitude": 21.45, "longitude": 84.00, "terrain": "monsoon_trough", "zone": "East India"},
        {"grid_id": "G_25.60_85.13", "name": "Patna (Bihar / Gangetic)", "latitude": 25.60, "longitude": 85.15, "terrain": "gangetic_plain", "zone": "East India"},
        {"grid_id": "G_30.31_78.03", "name": "Dehradun (Himalayan Foothills)", "latitude": 30.30, "longitude": 78.00, "terrain": "foothills", "zone": "Northwest India"},
        {"grid_id": "G_26.91_75.78", "name": "Jaipur (East Rajasthan)", "latitude": 26.90, "longitude": 75.80, "terrain": "semi_arid", "zone": "Northwest India"},
        {"grid_id": "G_26.23_91.73", "name": "Guwahati (Assam / NE)", "latitude": 26.20, "longitude": 91.75, "terrain": "orographic_valley", "zone": "Northeast India"},
        {"grid_id": "G_13.08_80.27", "name": "Chennai (Tamil Nadu)", "latitude": 13.10, "longitude": 80.25, "terrain": "rain_shadow", "zone": "South Peninsular"},
    ]

    @classmethod
    def generate_synoptic_monsoon_dataset(
        cls,
        start_year: int = 2018,
        end_year: int = 2024,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """
        Synthesizes physically coupled monsoon seasons (June 1 - Sept 30) for each year.
        Maintains authentic regime transitions and characteristic NWP bias signatures.
        """
        np.random.seed(random_seed)
        records: List[Dict] = []

        for year in range(start_year, end_year + 1):
            start_date = datetime(year, 6, 1)
            num_days = 122  # June to Sept (122 days)

            # Generate realistic synoptic regime episodes (Markov-chain style persistence)
            regime_timeline = []
            curr_regime = np.random.choice(WEATHER_REGIMES, p=[0.35, 0.20, 0.15, 0.15, 0.10, 0.05])
            regime_durations = {"ACTIVE_MONSOON": (5, 12), "BREAK_MONSOON": (3, 8), "MONSOON_LOW_DEPRESSION": (3, 6),
                                "COASTAL_RAINFALL": (4, 9), "OROGRAPHIC_RAINFALL": (4, 10), "WESTERN_DISTURBANCE": (2, 5)}

            day_idx = 0
            while day_idx < num_days:
                min_d, max_d = regime_durations[curr_regime]
                dur = np.random.randint(min_d, max_d + 1)
                for _ in range(dur):
                    if day_idx < num_days:
                        regime_timeline.append(curr_regime)
                        day_idx += 1
                # Transition matrix with realistic meteorological probabilities
                if curr_regime == "ACTIVE_MONSOON":
                    curr_regime = np.random.choice(["BREAK_MONSOON", "MONSOON_LOW_DEPRESSION", "COASTAL_RAINFALL", "OROGRAPHIC_RAINFALL"], p=[0.4, 0.3, 0.15, 0.15])
                elif curr_regime == "BREAK_MONSOON":
                    curr_regime = np.random.choice(["ACTIVE_MONSOON", "MONSOON_LOW_DEPRESSION", "WESTERN_DISTURBANCE"], p=[0.6, 0.3, 0.1])
                elif curr_regime == "MONSOON_LOW_DEPRESSION":
                    curr_regime = np.random.choice(["ACTIVE_MONSOON", "COASTAL_RAINFALL", "OROGRAPHIC_RAINFALL"], p=[0.5, 0.25, 0.25])
                else:
                    curr_regime = np.random.choice(["ACTIVE_MONSOON", "BREAK_MONSOON", "MONSOON_LOW_DEPRESSION"], p=[0.5, 0.3, 0.2])

            for d_offset in range(num_days):
                valid_date = start_date + timedelta(days=d_offset)
                init_date = valid_date - timedelta(days=1)  # 24h lead forecast initialized D-1
                true_regime = regime_timeline[d_offset]

                # Synoptic base fields for the day based on regime
                if true_regime == "ACTIVE_MONSOON":
                    base_mslp = 1000.0 + np.random.normal(0, 1.5)
                    base_u850 = 18.0 + np.random.normal(0, 2.5)  # Strong LLJ
                    base_v850 = 4.0 + np.random.normal(0, 1.5)
                    base_u200 = -28.0 + np.random.normal(0, 3.0) # Strong Tropical Easterly Jet
                    base_tcwv = 58.0 + np.random.normal(0, 3.0)
                    base_rh700 = 82.0 + np.random.normal(0, 4.0)
                    trough_lat = 22.0 + np.random.normal(0, 1.0)
                elif true_regime == "BREAK_MONSOON":
                    base_mslp = 1006.0 + np.random.normal(0, 1.5)
                    base_u850 = 6.0 + np.random.normal(0, 2.0)   # Weak LLJ
                    base_v850 = -1.0 + np.random.normal(0, 1.5)
                    base_u200 = -14.0 + np.random.normal(0, 2.5)
                    base_tcwv = 42.0 + np.random.normal(0, 3.5)
                    base_rh700 = 55.0 + np.random.normal(0, 5.0)
                    trough_lat = 28.5 + np.random.normal(0, 0.8) # Shifted to foothills
                elif true_regime == "MONSOON_LOW_DEPRESSION":
                    base_mslp = 994.0 + np.random.normal(0, 2.0)  # Intense low pressure
                    base_u850 = 22.0 + np.random.normal(0, 3.0)
                    base_v850 = 12.0 + np.random.normal(0, 2.5)
                    base_u200 = -32.0 + np.random.normal(0, 3.0)
                    base_tcwv = 65.0 + np.random.normal(0, 2.5)
                    base_rh700 = 92.0 + np.random.normal(0, 3.0)
                    trough_lat = 20.5 + np.random.normal(0, 1.0)
                elif true_regime == "COASTAL_RAINFALL":
                    base_mslp = 1002.0 + np.random.normal(0, 1.2)
                    base_u850 = 16.0 + np.random.normal(0, 2.0)
                    base_v850 = 6.0 + np.random.normal(0, 1.5)
                    base_u200 = -24.0 + np.random.normal(0, 2.5)
                    base_tcwv = 62.0 + np.random.normal(0, 2.0)
                    base_rh700 = 86.0 + np.random.normal(0, 3.0)
                    trough_lat = 21.5 + np.random.normal(0, 1.0)
                elif true_regime == "OROGRAPHIC_RAINFALL":
                    base_mslp = 1003.0 + np.random.normal(0, 1.2)
                    base_u850 = 20.0 + np.random.normal(0, 2.5) # Heavy westerly push against Ghats
                    base_v850 = 2.0 + np.random.normal(0, 1.5)
                    base_u200 = -22.0 + np.random.normal(0, 2.5)
                    base_tcwv = 60.0 + np.random.normal(0, 2.5)
                    base_rh700 = 85.0 + np.random.normal(0, 3.0)
                    trough_lat = 22.0 + np.random.normal(0, 1.0)
                else: # WESTERN_DISTURBANCE
                    base_mslp = 1005.0 + np.random.normal(0, 1.8)
                    base_u850 = 8.0 + np.random.normal(0, 2.0)
                    base_v850 = 5.0 + np.random.normal(0, 2.0)
                    base_u200 = 15.0 + np.random.normal(0, 4.0)  # Subtropical Westerly Jet intrusion
                    base_tcwv = 40.0 + np.random.normal(0, 3.0)
                    base_rh700 = 65.0 + np.random.normal(0, 4.0)
                    trough_lat = 29.0 + np.random.normal(0, 1.0)

                for loc in cls.REPRESENTATIVE_LOCATIONS:
                    lat = loc["latitude"]
                    lon = loc["longitude"]
                    terrain = loc["terrain"]

                    # Location-specific meteorological adjustments
                    loc_mslp = base_mslp + (lat - 20.0) * 0.4 + np.random.normal(0, 0.5)
                    loc_u850 = base_u850 + (15.0 - lat) * 0.2 + np.random.normal(0, 1.0)
                    loc_v850 = base_v850 + np.random.normal(0, 1.0)
                    loc_u200 = base_u200 + np.random.normal(0, 1.5)
                    loc_v200 = np.random.normal(0, 2.0)
                    loc_tcwv = max(10.0, base_tcwv - (lat - 10.0) * 0.5 + np.random.normal(0, 1.5))
                    loc_rh700 = np.clip(base_rh700 + np.random.normal(0, 3.0), 10.0, 99.0)
                    loc_cape = np.clip(1200.0 + (loc_tcwv - 40.0) * 40.0 + np.random.normal(0, 300.0), 0.0, 5500.0)

                    # True physical rainfall generation based on terrain & regime
                    rain_mean = 2.0
                    if terrain in ["coastal_orographic", "orographic"]:
                        if true_regime in ["ACTIVE_MONSOON", "OROGRAPHIC_RAINFALL", "COASTAL_RAINFALL"]:
                            rain_mean = 45.0 + loc_u850 * 2.2
                        elif true_regime == "MONSOON_LOW_DEPRESSION":
                            rain_mean = 35.0
                        else: # BREAK_MONSOON
                            rain_mean = 6.0
                    elif terrain == "cyclonic_coastal":
                        if true_regime == "MONSOON_LOW_DEPRESSION":
                            rain_mean = 75.0 + np.random.exponential(30.0) # High heavy rainfall event
                        elif true_regime == "ACTIVE_MONSOON":
                            rain_mean = 30.0
                        else:
                            rain_mean = 4.0
                    elif terrain == "foothills":
                        if true_regime in ["BREAK_MONSOON", "WESTERN_DISTURBANCE"]:
                            rain_mean = 55.0 + np.random.exponential(25.0) # Break monsoon heavy rain in foothills
                        else:
                            rain_mean = 12.0
                    elif terrain == "plains":
                        if true_regime in ["ACTIVE_MONSOON", "MONSOON_LOW_DEPRESSION"]:
                            rain_mean = 28.0
                        else:
                            rain_mean = 3.0
                    elif terrain == "gangetic_plain":
                        if true_regime == "ACTIVE_MONSOON":
                            rain_mean = 22.0
                        elif true_regime == "BREAK_MONSOON":
                            rain_mean = 38.0
                        else:
                            rain_mean = 5.0
                    elif terrain == "semi_arid":
                        if true_regime == "MONSOON_LOW_DEPRESSION":
                            rain_mean = 25.0
                        elif true_regime == "WESTERN_DISTURBANCE":
                            rain_mean = 20.0
                        else:
                            rain_mean = 1.5
                    elif terrain == "rain_shadow":
                        if true_regime == "BREAK_MONSOON":
                            rain_mean = 15.0
                        else:
                            rain_mean = 2.0
                    else: # orographic_valley
                        rain_mean = 30.0 if true_regime in ["ACTIVE_MONSOON", "BREAK_MONSOON"] else 10.0

                    # Gamma/Lognormal physical rainfall distribution
                    if np.random.rand() < 0.25 and rain_mean < 10.0:
                        obs_rain = 0.0
                    else:
                        obs_rain = np.random.gamma(shape=1.8, scale=max(0.1, rain_mean / 1.8))
                    obs_rain = float(np.round(np.clip(obs_rain, 0.0, 500.0), 2))

                    # Raw NWP Simulation (Includes classic NWP errors: drizzle bias, convective peak underestimation, orographic displacement)
                    nwp_bias_noise = np.random.normal(0, 5.0)
                    if obs_rain < 2.5:
                        # NWP Drizzle overestimation bias
                        nwp_rain = max(0.0, obs_rain + np.random.uniform(0.5, 6.0))
                    elif obs_rain > 64.5:
                        # NWP convective peak underestimation bias (underpredicts extreme rain by ~20-35%)
                        nwp_rain = max(0.0, obs_rain * np.random.uniform(0.55, 0.80) + nwp_bias_noise)
                    else:
                        # Moderate rain with systematic regime-dependent bias
                        if true_regime == "BREAK_MONSOON" and terrain == "plains":
                            nwp_rain = obs_rain + np.random.uniform(5.0, 18.0) # False alarm in plains
                        elif true_regime == "ACTIVE_MONSOON" and terrain == "orographic":
                            nwp_rain = obs_rain * 0.75 # Underestimated orographic enhancement
                        else:
                            nwp_rain = max(0.0, obs_rain * 0.90 + nwp_bias_noise)
                    nwp_rain = float(np.round(np.clip(nwp_rain, 0.0, 450.0), 2))

                    records.append({
                        "valid_time": valid_date.strftime("%Y-%m-%d"),
                        "forecast_init_time": init_date.strftime("%Y-%m-%d 00:00:00"),
                        "lead_time_hours": 24,
                        "grid_id": loc["grid_id"],
                        "district_name": loc["name"],
                        "latitude": lat,
                        "longitude": lon,
                        "terrain_type": terrain,
                        "climate_zone": loc["zone"],
                        "true_regime": true_regime,
                        "observed_rainfall": obs_rain,
                        "nwp_rainfall": nwp_rain,
                        "mslp": round(loc_mslp, 2),
                        "u850": round(loc_u850, 2),
                        "v850": round(loc_v850, 2),
                        "u200": round(loc_u200, 2),
                        "v200": round(loc_v200, 2),
                        "tcwv": round(loc_tcwv, 2),
                        "rh700": round(loc_rh700, 2),
                        "cape": round(loc_cape, 2),
                        "monsoon_trough_lat": round(trough_lat, 2),
                    })

        df = pd.DataFrame(records)
        return df
