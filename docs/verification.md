# VARUNA-AI: Scientific Verification Suite & WMO Metrics Engine

**Smart India Hackathon 2026 | Problem Statement: SIH26080**  
**Module**: `verification/` | **Owner**: Member 4 (Probability, Uncertainty & Verification Engineer)

---

## 1. WMO & IMD Standard Verification Framework
VARUNA-AI evaluates all model ladder outputs against observational ground truth using World Meteorological Organization (WMO) and India Meteorological Department (IMD) compliant metrics across continuous, categorical, spatial, and regime-stratified dimensions.

---

## 2. Mathematical Definitions of Core Verification Metrics

### Continuous Metrics:
1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N}\sum_{i=1}^N |\hat{R}_i - R_{i}|$$
2. **Root Mean Square Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (\hat{R}_i - R_{i})^2}$$
3. **Mean Bias**:
   $$\text{Bias} = \frac{1}{N}\sum_{i=1}^N (\hat{R}_i - R_{i})$$
4. **Pearson Correlation Coefficient ($r$)**:
   $$r = \frac{\sum (\hat{R}_i - \bar{\hat{R}})(R_i - \bar{R})}{\sqrt{\sum (\hat{R}_i - \bar{\hat{R}})^2 \sum (R_i - \bar{R})^2}}$$

---

### Categorical 2x2 Contingency Table Metrics (Event: $R \ge T$):

| | Observed Event ($R \ge T$) | Observed Non-Event ($R < T$) |
| :--- | :---: | :---: |
| **Forecast Event ($\hat{R} \ge T$)** | **Hits ($H$)** | **False Alarms ($F$)** |
| **Forecast Non-Event ($\hat{R} < T$)** | **Misses ($M$)** | **Correct Negatives ($C$)** |

1. **Probability of Detection (POD / Hit Rate)**:
   $$\text{POD} = \frac{H}{H + M} \in [0, 1] \quad (\text{Target: } 1.0)$$
2. **False Alarm Ratio (FAR)**:
   $$\text{FAR} = \frac{F}{H + F} \in [0, 1] \quad (\text{Target: } 0.0)$$
3. **Critical Success Index (CSI / Threat Score)**:
   $$\text{CSI} = \frac{H}{H + F + M} \in [0, 1] \quad (\text{Target: } 1.0)$$
4. **Equitable Threat Score (ETS / Gilbert Skill Score)**:
   $$\text{ETS} = \frac{H - H_{rand}}{H + F + M - H_{rand}}, \quad H_{rand} = \frac{(H + M)(H + F)}{N}$$
5. **Frequency Bias Index (FBIAS)**:
   $$\text{FBIAS} = \frac{H + F}{H + M} \quad (1.0 = \text{Unbiased}, >1.0 = \text{Overforecast}, <1.0 = \text{Underforecast})$$

---

### Spatial Verification: Fractions Skill Score (FSS):
$$\text{FSS} = 1 - \frac{\text{MSE}_{(n)}}{\text{MSE}_{(n), ref}} = 1 - \frac{\frac{1}{N_x N_y}\sum (P_{pred} - P_{obs})^2}{\frac{1}{N_x N_y}\sum (P_{pred}^2 + P_{obs}^2)}$$
Evaluated at spatial neighborhood scales ($1\times1$, $3\times3$, $5\times5$ grid windows) to account for spatial displacement errors.

---

## 3. Automated Execution
Run the verification suite locally:
```bash
python -m verification.verify
```
Outputs are automatically written to `verification/results.csv`, `verification/verification_matrix.json`, and `docs/verification_report.md`.
