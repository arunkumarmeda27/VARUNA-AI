\# VARUNA-AI — M1 Task 1.2

\# Backtest \& Honest Results



\## Dataset



Final real-data dataset:



master\_real\_weather\_2021\_2025.parquet



Rows evaluated: 8,723,845



Period:

2021-01-08 to 2025-12-31



Observed rainfall:

IMD rainfall



Forecast rainfall:

ERA5 rainfall



Error definition:



rainfall\_error = IMD rainfall - ERA5 rainfall





\## Official Real-Data Backtest



The existing VARUNA-AI verification metric definitions were used.



\### Continuous Metrics



MAE: 3.252 mm



RMSE: 11.109 mm



Mean Bias: -2.289 mm



Pearson Correlation: 0.363





\## Categorical Verification



\### Threshold: 1.0 mm



POD: 0.6628



CSI: 0.4642



FAR: 0.3923



Frequency Bias: 1.0907





\### Threshold: 2.5 mm



POD: 0.4622



CSI: 0.3455



FAR: 0.4223



Frequency Bias: 0.8001





\### Threshold: 10.0 mm



POD: 0.0610



CSI: 0.0570



FAR: 0.5372



Frequency Bias: 0.1318





\## Year-Wise Results



| Year | MAE | RMSE | Bias | Correlation |

|------|-----|------|------|-------------|

| 2021 | 3.334 | 11.100 | -2.402 | 0.341 |

| 2022 | 3.336 | 11.558 | -2.423 | 0.375 |

| 2023 | 2.917 | 10.370 | -1.998 | 0.374 |

| 2024 | 3.283 | 11.418 | -2.254 | 0.367 |

| 2025 | 3.391 | 11.058 | -2.370 | 0.356 |





\## Model Development Results



\### Model 1



2024 validation:



MAE: 3.921



RMSE: 10.395



R2: 0.138





\### Model 2 — Temporal Rainfall Features



2024 validation:



MAE: 3.592



RMSE: 9.991



R2: 0.203



2025 test:



MAE: 3.683



RMSE: 9.785



R2: 0.179





\### Model 3 — Temporal + Weather Features



2024 validation:



MAE: 4.278



RMSE: 9.937



R2: 0.212



2025 test:



MAE: 4.388



RMSE: 9.811



R2: 0.175





\## Important Interpretation



The ERA5 baseline verification metrics and the ML rainfall-error model metrics measure different quantities.



ERA5 baseline:



Observed rainfall versus ERA5 rainfall.



ML models:



Prediction of rainfall error.



Therefore, the two metric groups must not be presented as if they are directly comparable forecasts.





\## Weather Feature Analysis



Permutation analysis of Model 3 showed:



relative\_humidity: 0.1853



wind\_speed: 0.0873



dewpoint\_c: 0.0671



u10: 0.0669



v10: 0.0231



temperature\_c: 0.0194





\## Real Data Policy



All reported results above are based on real ERA5 and IMD-derived data.



No synthetic rainfall data was used for the reported real-data backtest.



Synthetic-data comparison is not included unless separately evaluated and documented.





\## Verification Status



MAE: COMPLETE



RMSE: COMPLETE



Mean Bias: COMPLETE



POD: COMPLETE



CSI: COMPLETE



Year-wise verification: COMPLETE



Real-data results documentation: COMPLETE



Four-tier model ladder comparison: PENDING



Real-vs-synthetic quantitative comparison: PENDING unless a synthetic benchmark is separately produced.





\## M1 Task 1.2 Status



REAL-DATA BACKTEST: COMPLETE



HONEST METRICS REPORTING: COMPLETE



PUBLICATION-READY RESULTS DOCUMENTATION: COMPLETE



REMAINING PROJECT-LEVEL COMPARISONS:

\- Four-tier model ladder

\- Real-vs-synthetic quantitative comparison

