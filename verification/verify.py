"""
VARUNA-AI: Scientific Verification Pipeline

Runs scientific verification of:
    Level 0: Raw NWP
    Level 1: Quantile Mapping
    Level 2: Standard ML
    Level 3: VARUNA-AI Regime-Aware ML

Also evaluates:
    - Continuous metrics
    - Categorical rainfall-event metrics
    - Regime-wise performance
    - Probability outputs
    - Conformal uncertainty outputs

IMPORTANT:
The current v1.0.0 datasets are district-level records with:
    train = 70 rows
    validation = 15 rows
    test = 15 rows

They do NOT contain a valid_time column or a true spatial grid.
Therefore this verification script does NOT fabricate a spatial FSS grid.
Spatial FSS is explicitly reported as unavailable until a real spatial
verification dataset is supplied.
"""

import os
import json
import logging
from datetime import datetime

import numpy as np
import pandas as pd

from verification.metrics import (
    calculate_continuous_metrics,
    calculate_categorical_scores,
)

from weather_data.metadata.data_dictionary import (
    OPERATIONAL_THRESHOLDS,
    WEATHER_REGIMES,
)

from correction.models.correction_engine import RainfallCorrectionEngine
from probability.heavy_rainfall import HeavyRainfallProbabilityEstimator
from uncertainty.conformal_quantiles import ConformalQuantileEstimator


logger = logging.getLogger(__name__)


VERIFY_DIR = os.path.dirname(__file__)

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))

DOCS_DIR = os.path.join(
    PROJECT_DIR,
    "docs",
)

PROCESSED_DATA_DIR = os.path.join(
    PROJECT_DIR,
    "weather_data",
    "processed",
)


class ScientificVerificationPipeline:
    """
    Complete scientific verification runner for VARUNA-AI.

    The pipeline evaluates the actual v1.0.0 train/validation/test
    datasets without inventing dates or spatial grids.
    """

    def __init__(self, data_version: str = "v1.0.0"):
        self.data_version = data_version

        self.correction_engine = RainfallCorrectionEngine()

        self.prob_estimator = HeavyRainfallProbabilityEstimator()

        self.uncertainty_estimator = ConformalQuantileEstimator()

        os.makedirs(DOCS_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------

    def _load_dataset(self, split_name: str) -> pd.DataFrame:
        """
        Load one processed Parquet dataset.
        """

        path = os.path.join(
            PROCESSED_DATA_DIR,
            f"{split_name}_{self.data_version}.parquet",
        )

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Required dataset not found: {path}"
            )

        df = pd.read_parquet(path)

        if df.empty:
            raise ValueError(
                f"Dataset is empty: {path}"
            )

        logger.info(
            "Loaded %s dataset: %d rows, %d columns",
            split_name,
            len(df),
            len(df.columns),
        )

        return df

    # ------------------------------------------------------------------
    # DATASET DESCRIPTION
    # ------------------------------------------------------------------

    @staticmethod
    def _describe_dataset(
        name: str,
        df: pd.DataFrame,
    ) -> dict:
        """
        Return factual metadata about a dataset.
        """

        description = {
            "name": name,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "has_valid_time": "valid_time" in df.columns,
            "has_latitude": "latitude" in df.columns,
            "has_longitude": "longitude" in df.columns,
            "has_observed_rainfall": "observed_rainfall" in df.columns,
            "has_true_regime": "true_regime" in df.columns,
        }

        if "valid_time" in df.columns:
            times = pd.to_datetime(
                df["valid_time"],
                errors="coerce",
            ).dropna()

            if len(times) > 0:
                description["time_min"] = str(times.min())
                description["time_max"] = str(times.max())

        if "district" in df.columns:
            description["unique_districts"] = int(
                df["district"].nunique()
            )

        if "true_regime" in df.columns:
            description["regime_counts"] = {
                str(k): int(v)
                for k, v in df["true_regime"]
                .value_counts()
                .to_dict()
                .items()
            }

        return description

    # ------------------------------------------------------------------
    # MAIN VERIFICATION
    # ------------------------------------------------------------------

    def run_full_verification(self) -> dict:
        """
        Execute complete verification.
        """

        logger.info("Starting VARUNA-AI scientific verification")

        # --------------------------------------------------------------
        # 1. LOAD DATA
        # --------------------------------------------------------------

        train_df = self._load_dataset("train")
        val_df = self._load_dataset("val")
        test_df = self._load_dataset("test")

        dataset_summary = {
            "train": self._describe_dataset(
                "train",
                train_df,
            ),
            "validation": self._describe_dataset(
                "validation",
                val_df,
            ),
            "test": self._describe_dataset(
                "test",
                test_df,
            ),
        }

        # --------------------------------------------------------------
        # 2. REQUIRED TEST COLUMNS
        # --------------------------------------------------------------

        required_columns = [
            "nwp_rainfall",
            "observed_rainfall",
            "true_regime",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in test_df.columns
        ]

        if missing_columns:
            raise ValueError(
                "Test dataset is missing required columns: "
                + ", ".join(missing_columns)
            )

        # --------------------------------------------------------------
        # 3. TRAIN PROBABILITY / UNCERTAINTY MODULES
        # --------------------------------------------------------------

        logger.info(
            "Fitting probability and uncertainty modules..."
        )

        self.prob_estimator.train_probability_models(
            train_df,
            val_df,
        )

        self.uncertainty_estimator.fit_quantiles(
            train_df,
            val_df,
        )

        # --------------------------------------------------------------
        # 4. RUN MODEL LADDER
        # --------------------------------------------------------------

        logger.info(
            "Running VARUNA-AI model ladder on independent test dataset..."
        )

        eval_df = self.correction_engine.process_forecast(
            test_df.copy()
        )

        eval_df = self.prob_estimator.estimate_probabilities(
            eval_df
        )

        eval_df = self.uncertainty_estimator.estimate_uncertainty(
            eval_df
        )

        # --------------------------------------------------------------
        # 5. EXTRACT OBSERVATIONS AND PREDICTIONS
        # --------------------------------------------------------------

        obs = pd.to_numeric(
            eval_df["observed_rainfall"],
            errors="coerce",
        ).to_numpy()

        nwp = pd.to_numeric(
            eval_df["nwp_rainfall"],
            errors="coerce",
        ).to_numpy()

        l1_eqm = pd.to_numeric(
            eval_df["rain_level1_eqm"],
            errors="coerce",
        ).to_numpy()

        l2_std = pd.to_numeric(
            eval_df["rain_level2_std_ml"],
            errors="coerce",
        ).to_numpy()

        l3_varuna = pd.to_numeric(
            eval_df["corrected_rainfall"],
            errors="coerce",
        ).to_numpy()

        # --------------------------------------------------------------
        # 6. REMOVE INVALID NUMERIC ROWS
        # --------------------------------------------------------------

        valid_mask = (
            np.isfinite(obs)
            & np.isfinite(nwp)
            & np.isfinite(l1_eqm)
            & np.isfinite(l2_std)
            & np.isfinite(l3_varuna)
        )

        invalid_count = int(
            np.sum(~valid_mask)
        )

        if invalid_count > 0:
            logger.warning(
                "Removing %d rows containing invalid numeric values",
                invalid_count,
            )

        obs = obs[valid_mask]
        nwp = nwp[valid_mask]
        l1_eqm = l1_eqm[valid_mask]
        l2_std = l2_std[valid_mask]
        l3_varuna = l3_varuna[valid_mask]

        eval_df = eval_df.loc[
            valid_mask
        ].reset_index(drop=True)

        # --------------------------------------------------------------
        # 7. MODEL LADDER
        # --------------------------------------------------------------

        models = {
            "Raw_NWP": nwp,
            "Level1_Quantile_Mapping": l1_eqm,
            "Level2_Standard_ML": l2_std,
            "VARUNA_AI_Level3_Regime_Aware": l3_varuna,
        }

        # --------------------------------------------------------------
        # 8. CONTINUOUS METRICS
        # --------------------------------------------------------------

        continuous_results = {}

        for model_name, predictions in models.items():

            continuous_results[model_name] = (
                calculate_continuous_metrics(
                    obs,
                    predictions,
                )
            )

        # --------------------------------------------------------------
        # 9. CATEGORICAL METRICS
        # --------------------------------------------------------------

        categorical_results = []

        for threshold in OPERATIONAL_THRESHOLDS:

            for model_name, predictions in models.items():

                result = calculate_categorical_scores(
                    obs,
                    predictions,
                    threshold,
                )

                result["Model"] = model_name

                categorical_results.append(
                    result
                )

        categorical_df = pd.DataFrame(
            categorical_results
        )

        # --------------------------------------------------------------
        # 10. REGIME-WISE VERIFICATION
        # --------------------------------------------------------------

        regime_results = {}

        if "true_regime" in eval_df.columns:

            regimes = (
                eval_df["true_regime"]
                .astype(str)
                .to_numpy()
            )

            for regime in WEATHER_REGIMES:

                mask = regimes == str(regime)

                sample_count = int(
                    np.sum(mask)
                )

                if sample_count == 0:
                    regime_results[str(regime)] = {
                        "sample_count": 0,
                        "models": {},
                    }

                    continue

                regime_results[str(regime)] = {
                    "sample_count": sample_count,
                    "models": {},
                }

                for model_name, predictions in models.items():

                    regime_obs = obs[mask]
                    regime_predictions = predictions[mask]

                    regime_results[str(regime)]["models"][
                        model_name
                    ] = {
                        "continuous": calculate_continuous_metrics(
                            regime_obs,
                            regime_predictions,
                        ),
                        "heavy_rain_64.5mm": calculate_categorical_scores(
                            regime_obs,
                            regime_predictions,
                            64.5,
                        ),
                    }

        # --------------------------------------------------------------
        # 11. HEAVY RAIN PROBABILITY SUMMARY
        # --------------------------------------------------------------

        probability_summary = {}

        probability_columns = [
            "heavy_rain_probability",
            "prob_exceed_64.5",
        ]

        for column in probability_columns:

            if column in eval_df.columns:

                values = pd.to_numeric(
                    eval_df[column],
                    errors="coerce",
                ).dropna()

                if len(values) > 0:

                    probability_summary[column] = {
                        "sample_count": int(len(values)),
                        "mean": round(
                            float(values.mean()),
                            4,
                        ),
                        "minimum": round(
                            float(values.min()),
                            4,
                        ),
                        "maximum": round(
                            float(values.max()),
                            4,
                        ),
                    }

        # --------------------------------------------------------------
        # 12. UNCERTAINTY SUMMARY
        # --------------------------------------------------------------

        uncertainty_summary = {}

        lower_column = "uncertainty_lower_10pct"
        upper_column = "uncertainty_upper_90pct"

        if (
            lower_column in eval_df.columns
            and upper_column in eval_df.columns
        ):

            lower = pd.to_numeric(
                eval_df[lower_column],
                errors="coerce",
            )

            upper = pd.to_numeric(
                eval_df[upper_column],
                errors="coerce",
            )

            valid_uncertainty = (
                lower.notna()
                & upper.notna()
            )

            if valid_uncertainty.any():

                interval_width = (
                    upper[valid_uncertainty]
                    - lower[valid_uncertainty]
                )

                uncertainty_summary = {
                    "sample_count": int(
                        valid_uncertainty.sum()
                    ),
                    "mean_lower_10pct": round(
                        float(
                            lower[valid_uncertainty].mean()
                        ),
                        3,
                    ),
                    "mean_upper_90pct": round(
                        float(
                            upper[valid_uncertainty].mean()
                        ),
                        3,
                    ),
                    "mean_interval_width": round(
                        float(
                            interval_width.mean()
                        ),
                        3,
                    ),
                }

        # --------------------------------------------------------------
        # 13. SPATIAL FSS STATUS
        # --------------------------------------------------------------

        has_real_spatial_grid = (
            "latitude" in eval_df.columns
            and "longitude" in eval_df.columns
            and len(eval_df) >= 120
        )

        spatial_fss = {
            "status": "NOT_AVAILABLE",
            "reason": (
                "The current v1.0.0 test dataset contains "
                f"{len(eval_df)} district-level records and does not "
                "contain a validated 2D spatial grid suitable for "
                "Fractions Skill Score calculation."
            ),
            "required_for_future_fss": [
                "real latitude/longitude grid",
                "spatially ordered observations",
                "matching spatial NWP predictions",
                "matching spatial VARUNA-AI predictions",
            ],
        }

        if has_real_spatial_grid:

            spatial_fss["status"] = (
                "AVAILABLE_FOR_IMPLEMENTATION"
            )

            spatial_fss["reason"] = (
                "Latitude and longitude columns are present, "
                "but the current verification pipeline does not "
                "assume that district records form a rectangular "
                "spatial grid."
            )

        # --------------------------------------------------------------
        # 14. IMPROVEMENT CALCULATIONS
        # --------------------------------------------------------------

        raw_rmse = continuous_results[
            "Raw_NWP"
        ]["RMSE"]

        varuna_rmse = continuous_results[
            "VARUNA_AI_Level3_Regime_Aware"
        ]["RMSE"]

        if raw_rmse != 0:

            rmse_improvement_pct = (
                (
                    raw_rmse
                    - varuna_rmse
                )
                / raw_rmse
            ) * 100.0

        else:

            rmse_improvement_pct = 0.0

        raw_mae = continuous_results[
            "Raw_NWP"
        ]["MAE"]

        varuna_mae = continuous_results[
            "VARUNA_AI_Level3_Regime_Aware"
        ]["MAE"]

        if raw_mae != 0:

            mae_improvement_pct = (
                (
                    raw_mae
                    - varuna_mae
                )
                / raw_mae
            ) * 100.0

        else:

            mae_improvement_pct = 0.0

        improvement_summary = {
            "RMSE_improvement_percent": round(
                float(rmse_improvement_pct),
                3,
            ),
            "MAE_improvement_percent": round(
                float(mae_improvement_pct),
                3,
            ),
        }

        # --------------------------------------------------------------
        # 15. DATASET FACTS
        # --------------------------------------------------------------

        dataset_facts = {
            "train_rows": int(len(train_df)),
            "validation_rows": int(len(val_df)),
            "test_rows": int(len(test_df)),
            "verified_rows": int(len(eval_df)),
            "invalid_rows_removed": invalid_count,
            "has_valid_time_column": (
                "valid_time" in test_df.columns
            ),
            "has_real_spatial_grid": False,
        }

        # --------------------------------------------------------------
        # 16. FINAL VERIFICATION OBJECT
        # --------------------------------------------------------------

        full_verification = {
            "verification_version": self.data_version,
            "verification_type": (
                "District-level independent test-set verification"
            ),
            "test_period": None,
            "test_period_status": (
                "NOT_SPECIFIED"
            ),
            "test_samples": int(len(eval_df)),
            "dataset_summary": dataset_summary,
            "dataset_facts": dataset_facts,
            "continuous_metrics": continuous_results,
            "categorical_metrics": (
                categorical_df.to_dict(
                    orient="records"
                )
            ),
            "regime_breakdown": regime_results,
            "probability_summary": probability_summary,
            "uncertainty_summary": uncertainty_summary,
            "spatial_fss": spatial_fss,
            "improvement_summary": improvement_summary,
            "timestamp": datetime.now().isoformat(),
        }

        # --------------------------------------------------------------
        # 17. SAVE CSV
        # --------------------------------------------------------------

        csv_path = os.path.join(
            VERIFY_DIR,
            "results.csv",
        )

        categorical_df.to_csv(
            csv_path,
            index=False,
        )

        # --------------------------------------------------------------
        # 18. SAVE JSON
        # --------------------------------------------------------------

        json_path = os.path.join(
            VERIFY_DIR,
            "verification_matrix.json",
        )

        with open(
            json_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                full_verification,
                file,
                indent=2,
            )

        # --------------------------------------------------------------
        # 19. GENERATE REPORT
        # --------------------------------------------------------------

        self.generate_markdown_report(
            full_verification
        )

        logger.info(
            "Scientific verification completed successfully."
        )

        return full_verification

    # ------------------------------------------------------------------
    # MARKDOWN REPORT
    # ------------------------------------------------------------------

    def generate_markdown_report(
        self,
        verification_data: dict,
    ):
        """
        Generate a truthful scientific verification report.

        No unsupported test-period or spatial-grid claims are inserted.
        """

        md_path = os.path.join(
            DOCS_DIR,
            "verification_report.md",
        )

        cm = verification_data[
            "continuous_metrics"
        ]

        cats = verification_data[
            "categorical_metrics"
        ]

        improvement = verification_data[
            "improvement_summary"
        ]

        dataset_facts = verification_data[
            "dataset_facts"
        ]

        spatial = verification_data[
            "spatial_fss"
        ]

        lines = []

        lines.append(
            "# VARUNA-AI Scientific Verification Report"
        )

        lines.append("")

        lines.append(
            f"**Dataset Version**: "
            f"`{verification_data['verification_version']}`  "
        )

        lines.append(
            "**Verification Type**: "
            "District-level independent test-set verification  "
        )

        lines.append(
            f"**Test Samples Verified**: "
            f"{verification_data['test_samples']}  "
        )

        lines.append(
            f"**Generated At**: "
            f"{verification_data['timestamp']}  "
        )

        lines.append("")

        lines.append("---")

        lines.append("")

        # --------------------------------------------------------------
        # DATASET SUMMARY
        # --------------------------------------------------------------

        lines.append(
            "## 1. Dataset Verification"
        )

        lines.append("")

        lines.append(
            f"- Training samples: "
            f"{dataset_facts['train_rows']}"
        )

        lines.append(
            f"- Validation samples: "
            f"{dataset_facts['validation_rows']}"
        )

        lines.append(
            f"- Test samples: "
            f"{dataset_facts['test_rows']}"
        )

        lines.append(
            f"- Valid samples used for verification: "
            f"{dataset_facts['verified_rows']}"
        )

        lines.append(
            f"- Invalid rows removed: "
            f"{dataset_facts['invalid_rows_removed']}"
        )

        lines.append("")

        if dataset_facts[
            "has_valid_time_column"
        ]:

            lines.append(
                "The test dataset contains a `valid_time` "
                "column."
            )

        else:

            lines.append(
                "The current test dataset does not contain "
                "a `valid_time` column. Therefore no specific "
                "calendar test period is asserted by this report."
            )

        lines.append("")

        # --------------------------------------------------------------
        # RESEARCH QUESTION
        # --------------------------------------------------------------

        lines.append(
            "## 2. Research Question"
        )

        lines.append("")

        lines.append(
            "> Can explicitly identifying the prevailing "
            "weather regime and using that information during "
            "rainfall post-processing improve raw NWP rainfall "
            "forecasts?"
        )

        lines.append("")

        lines.append(
            "The results below provide quantitative evidence "
            "from the available independent test records. "
            "They should be interpreted in the context of the "
            "current dataset size."
        )

        lines.append("")

        # --------------------------------------------------------------
        # CONTINUOUS METRICS
        # --------------------------------------------------------------

        lines.append(
            "## 3. Continuous Verification Metrics"
        )

        lines.append("")

        lines.append(
            "| Model | MAE (mm) | RMSE (mm) | "
            "Mean Bias (mm) | Pearson Correlation |"
        )

        lines.append(
            "|---|---:|---:|---:|---:|"
        )

        model_order = [
            "Raw_NWP",
            "Level1_Quantile_Mapping",
            "Level2_Standard_ML",
            "VARUNA_AI_Level3_Regime_Aware",
        ]

        display_names = {
            "Raw_NWP": "Level 0: Raw NWP",
            "Level1_Quantile_Mapping": (
                "Level 1: Quantile Mapping"
            ),
            "Level2_Standard_ML": (
                "Level 2: Standard ML"
            ),
            "VARUNA_AI_Level3_Regime_Aware": (
                "Level 3: VARUNA-AI Regime-Aware"
            ),
        }

        for model_name in model_order:

            metrics = cm[model_name]

            lines.append(
                f"| **{display_names[model_name]}** "
                f"| {metrics['MAE']} "
                f"| {metrics['RMSE']} "
                f"| {metrics['Mean_Bias']} "
                f"| {metrics['Correlation']} |"
            )

        lines.append("")

        lines.append(
            f"Observed RMSE change from Raw NWP to "
            f"VARUNA-AI Level 3: "
            f"**{improvement['RMSE_improvement_percent']:.3f}%**."
        )

        lines.append("")

        lines.append(
            f"Observed MAE change from Raw NWP to "
            f"VARUNA-AI Level 3: "
            f"**{improvement['MAE_improvement_percent']:.3f}%**."
        )

        lines.append("")

        # --------------------------------------------------------------
        # CATEGORICAL
        # --------------------------------------------------------------

        lines.append(
            "## 4. Categorical Rainfall Verification"
        )

        lines.append("")

        lines.append(
            "| Threshold | Model | Hits | False Alarms | "
            "Misses | POD | FAR | CSI | ETS |"
        )

        lines.append(
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|"
        )

        for result in cats:

            lines.append(
                f"| {result['Threshold_mm']} "
                f"| {result['Model']} "
                f"| {result['Hits']} "
                f"| {result['False_Alarms']} "
                f"| {result['Misses']} "
                f"| {result['POD']:.4f} "
                f"| {result['FAR']:.4f} "
                f"| {result['CSI']:.4f} "
                f"| {result['ETS']:.4f} |"
            )

        lines.append("")

        # --------------------------------------------------------------
        # REGIME
        # --------------------------------------------------------------

        lines.append(
            "## 5. Regime-Wise Verification"
        )

        lines.append("")

        regime_breakdown = verification_data[
            "regime_breakdown"
        ]

        for regime, regime_data in regime_breakdown.items():

            lines.append(
                f"### {regime}"
            )

            lines.append("")

            lines.append(
                f"Sample count: "
                f"**{regime_data['sample_count']}**"
            )

            lines.append("")

            if not regime_data["models"]:

                lines.append(
                    "No samples from this regime are present "
                    "in the current test dataset."
                )

                lines.append("")

                continue

            lines.append(
                "| Model | MAE | RMSE | Bias | Correlation | "
                "Heavy Rain CSI | Heavy Rain POD |"
            )

            lines.append(
                "|---|---:|---:|---:|---:|---:|---:|"
            )

            for model_name, model_data in (
                regime_data["models"].items()
            ):

                continuous = model_data[
                    "continuous"
                ]

                heavy = model_data[
                    "heavy_rain_64.5mm"
                ]

                lines.append(
                    f"| {model_name} "
                    f"| {continuous['MAE']} "
                    f"| {continuous['RMSE']} "
                    f"| {continuous['Mean_Bias']} "
                    f"| {continuous['Correlation']} "
                    f"| {heavy['CSI']:.4f} "
                    f"| {heavy['POD']:.4f} |"
                )

            lines.append("")

        # --------------------------------------------------------------
        # PROBABILITY
        # --------------------------------------------------------------

        lines.append(
            "## 6. Heavy Rainfall Probability"
        )

        lines.append("")

        probability_summary = verification_data[
            "probability_summary"
        ]

        if probability_summary:

            for column, values in (
                probability_summary.items()
            ):

                lines.append(
                    f"### `{column}`"
                )

                lines.append("")

                lines.append(
                    f"- Samples: {values['sample_count']}"
                )

                lines.append(
                    f"- Mean: {values['mean']}"
                )

                lines.append(
                    f"- Minimum: {values['minimum']}"
                )

                lines.append(
                    f"- Maximum: {values['maximum']}"
                )

                lines.append("")

        else:

            lines.append(
                "No probability output column was available "
                "for summary."
            )

            lines.append("")

        # --------------------------------------------------------------
        # UNCERTAINTY
        # --------------------------------------------------------------

        lines.append(
            "## 7. Conformal Uncertainty"
        )

        lines.append("")

        uncertainty_summary = verification_data[
            "uncertainty_summary"
        ]

        if uncertainty_summary:

            lines.append(
                f"- Samples: "
                f"{uncertainty_summary['sample_count']}"
            )

            lines.append(
                f"- Mean lower 10% bound: "
                f"{uncertainty_summary['mean_lower_10pct']} mm"
            )

            lines.append(
                f"- Mean upper 90% bound: "
                f"{uncertainty_summary['mean_upper_90pct']} mm"
            )

            lines.append(
                f"- Mean interval width: "
                f"{uncertainty_summary['mean_interval_width']} mm"
            )

        else:

            lines.append(
                "No conformal uncertainty columns were "
                "available for summary."
            )

        lines.append("")

        # --------------------------------------------------------------
        # SPATIAL FSS
        # --------------------------------------------------------------

        lines.append(
            "## 8. Spatial Fractions Skill Score"
        )

        lines.append("")

        lines.append(
            f"**Status**: `{spatial['status']}`"
        )

        lines.append("")

        lines.append(
            spatial["reason"]
        )

        lines.append("")

        lines.append(
            "No fabricated 2D grid is used in this report."
        )

        lines.append("")

        # --------------------------------------------------------------
        # LIMITATIONS
        # --------------------------------------------------------------

        lines.append(
            "## 9. Current Scientific Limitations"
        )

        lines.append("")

        lines.append(
            "- The current v1.0.0 verification dataset "
            "contains only 15 independent test records."
        )

        lines.append(
            "- The dataset is district-level rather than "
            "a validated rectangular spatial grid."
        )

        lines.append(
            "- The current test data does not contain "
            "a `valid_time` column."
        )

        lines.append(
            "- Therefore this report does not claim a "
            "specific calendar test period."
        )

        lines.append(
            "- Spatial FSS is not reported as a numerical "
            "scientific result until a genuine spatial "
            "verification dataset is available."
        )

        lines.append(
            "- Larger multi-year independent datasets are "
            "required for stronger scientific conclusions."
        )

        lines.append("")

        # --------------------------------------------------------------
        # REPRODUCIBILITY
        # --------------------------------------------------------------

        lines.append(
            "## 10. Reproducibility"
        )

        lines.append("")

        lines.append(
            f"- Dataset version: "
            f"`{verification_data['verification_version']}`"
        )

        lines.append(
            "- Verification outputs:"
        )

        lines.append(
            "  - `verification/results.csv`"
        )

        lines.append(
            "  - `verification/verification_matrix.json`"
        )

        lines.append(
            "  - `docs/verification_report.md`"
        )

        lines.append("")

        lines.append(
            "---"
        )

        lines.append("")

        lines.append(
            "Generated automatically by the "
            "VARUNA-AI scientific verification pipeline."
        )

        lines.append("")

        with open(
            md_path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n".join(lines)
            )

        logger.info(
            "Verification report written to %s",
            md_path,
        )


# ----------------------------------------------------------------------
# SCRIPT ENTRY POINT
# ----------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
    )

    pipeline = ScientificVerificationPipeline(
        data_version="v1.0.0"
    )

    result = pipeline.run_full_verification()

    print(
        "\nScientific Verification Completed Successfully!"
    )

    print(
        "\nTest samples:",
        result["test_samples"],
    )

    print(
        "\nContinuous Metrics:"
    )

    print(
        json.dumps(
            result["continuous_metrics"],
            indent=2,
        )
    )

    print(
        "\nImprovement Summary:"
    )

    print(
        json.dumps(
            result["improvement_summary"],
            indent=2,
        )
    )

    print(
        "\nSpatial FSS Status:"
    )

    print(
        result["spatial_fss"]["status"]
    )