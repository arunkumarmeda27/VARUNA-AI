\# M1 Task 1.2 — Real-Data Backtest \& Honest Verification



Status: COMPLETE



Dataset:

weather\_data/processed/real\_ml/master\_real\_weather\_2021\_2025.parquet



Evaluation period:

2021-01-08 to 2025-12-31



Rows evaluated:

8,723,845



Overall metrics:

MAE: 3.252 mm

RMSE: 11.109 mm

Mean Bias: -2.289 mm

Correlation: 0.363



Categorical verification:

1.0 mm — POD 0.6628, CSI 0.4642, FAR 0.3923

2.5 mm — POD 0.4622, CSI 0.3455, FAR 0.4223

10.0 mm — POD 0.0610, CSI 0.0570, FAR 0.5372



Year-wise evaluation was performed for:

2021, 2022, 2023, 2024, 2025



Important:

These results are reported as real-data verification/baseline results.

They are not presented as proof of high model accuracy.

The existing 15-sample correction evaluation is separate from this

8.7-million-row M1 real-data backtest.



Detailed results:

weather\_data/processed/real\_ml/M1\_REAL\_DATA\_BACKTEST\_RESULTS.txt

