"""
VARUNA-AI: Master Dataset Builder
Owner: Member 1 (Data Foundation / Data Engineer)

Builds versioned, leakage-proof, ML-ready master training, validation, and test datasets.
"""

import os
import logging
import pandas as pd
from typing import Tuple, Dict

from weather_data.ingestion.data_loader import MonsoonDataIngestion
from weather_data.preprocessing.validator import DataValidator
from weather_data.temporal.temporal_aligner import TemporalAligner
from weather_data.features.synoptic_features import SynopticFeatureEngineer

logger = logging.getLogger(__name__)

DATA_VERSION = "v1.0.0"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "processed")

class MasterDatasetBuilder:
    """
    Orchestrates ingestion, feature extraction, validation, and chronological splitting.
    """

    def __init__(self, output_dir: str = OUTPUT_DIR, version: str = DATA_VERSION):
        self.output_dir = output_dir
        self.version = version
        os.makedirs(self.output_dir, exist_ok=True)

    def build_and_save(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
        """
        Executes full data foundation pipeline and persists parquet artifacts.
        """
        logger.info(f"Generating multi-year monsoon dataset (2018-2024)...")
        raw_df = MonsoonDataIngestion.generate_synoptic_monsoon_dataset(
            start_year=2018,
            end_year=2024,
            random_seed=42,
        )

        # 1. Feature Engineering
        logger.info("Computing synoptic and thermodynamic features...")
        feat_df = SynopticFeatureEngineer.compute_all_features(raw_df)

        # 2. Validation & Physical Sanity Checks
        logger.info("Validating physical bounds and integrity...")
        validator = DataValidator()
        clean_df, val_report = validator.validate_dataframe(feat_df, drop_invalid=False)

        # 3. Leakage Check
        validator.verify_no_future_leakage(clean_df)

        # 4. IMD Classification
        clean_df["observed_imd_cat"] = validator.assign_imd_category(clean_df["observed_rainfall"])
        clean_df["nwp_imd_cat"] = validator.assign_imd_category(clean_df["nwp_rainfall"])

        # 5. Chronological Train / Val / Test Split
        logger.info("Splitting chronologically (Train: 2018-2022, Val: 2023, Test: 2024)...")
        train_df, val_df, test_df = TemporalAligner.create_chronological_splits(
            clean_df,
            time_col="valid_time",
            train_end_year=2022,
            val_year=2023,
            test_year=2024,
        )

        # 6. Save Parquet Datasets
        train_path = os.path.join(self.output_dir, f"train_{self.version}.parquet")
        val_path = os.path.join(self.output_dir, f"val_{self.version}.parquet")
        test_path = os.path.join(self.output_dir, f"test_{self.version}.parquet")
        master_path = os.path.join(self.output_dir, f"master_{self.version}.parquet")

        train_df.to_parquet(train_path, index=False)
        val_df.to_parquet(val_path, index=False)
        test_df.to_parquet(test_path, index=False)
        clean_df.to_parquet(master_path, index=False)

        summary = {
            "version": self.version,
            "total_records": len(clean_df),
            "train_records": len(train_df),
            "val_records": len(val_df),
            "test_records": len(test_df),
            "columns": list(clean_df.columns),
            "train_period": "2018-06-01 to 2022-09-30",
            "val_period": "2023-06-01 to 2023-09-30",
            "test_period": "2024-06-01 to 2024-09-30",
            "validation_report": val_report,
        }

        logger.info(f"Master dataset generation complete. Summary: {summary['total_records']} total rows.")
        return train_df, val_df, test_df, summary

if __name__ == "__main__":
    builder = MasterDatasetBuilder()
    train_df, val_df, test_df, summary = builder.build_and_save()
    print("Master dataset built successfully!")
    print(f"Train rows: {len(train_df)}, Val rows: {len(val_df)}, Test rows: {len(test_df)}")
