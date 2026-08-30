# VARUNA-AI Data Dictionary

## 1. Overview
This document defines every variable ingested, derived, and produced across the **VARUNA-AI** scientific forecasting system.
All datasets adhere strictly to the World Meteorological Organization (WMO) and India Meteorological Department (IMD) standards.

---

## 2. Spatial & Temporal Standards
- **Coordinate Reference System (CRS)**: EPSG:4326 (WGS84)
- **Spatial Domain**: Indian Monsoon Region ($6.0^\circ\text{N} - 38.0^\circ\text{N}, 68.0^\circ\text{E} - 98.0^\circ\text{E}$)
- **Grid Resolution**: Standardized $0.25^\circ \times 0.25^\circ$ (~27 km) or $0.50^\circ \times 0.50^\circ$ (~55 km) regular latitude-longitude grid
- **Temporal Alignment**: Daily 24-hour accumulated rainfall (03:00 UTC to 03:00 UTC next day, corresponding to 08:30 IST to 08:30 IST standard IMD observational day)
- **Forecast Initialization Times**: 00:00 UTC, 12:00 UTC
- **Forecast Lead Times**: Day 1 (+24h), Day 2 (+48h), Day 3 (+72h)

---

## 3. Variable Specifications

### 3.1 Observed Ground Truth (`weather_data/raw/observed/`)
| Variable Name | Symbol | Unit | Range / Bounds | Description | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `observed_rainfall` | $R_{obs}$ | $\text{mm}/\text{day}$ | $[0.0, 1500.0]$ | 24-hr accumulated observed ground rainfall | IMD Gridded / High-density Raingauge Network |
| `station_density_flag` | $N_{stn}$ | count | $\ge 0$ | Number of reporting stations per grid cell | IMD Quality Metadata |

### 3.2 Raw Numerical Weather Prediction (NWP) (`weather_data/raw/nwp/`)
| Variable Name | Symbol | Unit | Range / Bounds | Description | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nwp_rainfall` | $R_{nwp}$ | $\text{mm}/\text{day}$ | $[0.0, 1000.0]$ | Raw 24-hr accumulated precipitation forecast | NCMRWF Unified Model (NCUM) / GFS / ECMWF |
| `forecast_init_time` | $t_{init}$ | UTC Timestamp | ISO 8601 | Model run start timestamp | NWP Metadata |
| `forecast_lead_hours` | $\tau$ | hours | $24, 48, 72$ | Lead time from initialization | NWP Metadata |
| `valid_time` | $t_{valid}$ | UTC Timestamp | ISO 8601 | $t_{valid} = t_{init} + \tau$ | Calculated |

### 3.3 Multi-Level Atmospheric & Synoptic Features (`weather_data/raw/synoptic/`)
| Variable Name | Symbol | Unit | Range / Bounds | Physical Significance |
| :--- | :--- | :--- | :--- | :--- |
| `mslp` | $P_{sfc}$ | $\text{hPa}$ | $[870.0, 1085.0]$ | Mean Sea Level Pressure (Monsoon trough & low-pressure tracking) |
| `u850` | $u_{850}$ | $\text{m/s}$ | $[-60.0, 60.0]$ | Zonal wind at 850 hPa (Low-Level Jet / Somali Jet strength) |
| `v850` | $v_{850}$ | $\text{m/s}$ | $[-60.0, 60.0]$ | Meridional wind at 850 hPa (Cross-equatorial flow & cyclonic turning) |
| `u200` | $u_{200}$ | $\text{m/s}$ | $[-90.0, 90.0]$ | Zonal wind at 200 hPa (Tropical Easterly Jet strength) |
| `v200` | $v_{200}$ | $\text{m/s}$ | $[-90.0, 90.0]$ | Meridional wind at 200 hPa (Upper-level divergence) |
| `tcwv` | $\text{TCWV}$ | $\text{kg/m}^2$ | $[0.0, 100.0]$ | Total Column Water Vapour (Atmospheric moisture reservoir) |
| `rh700` | $\text{RH}_{700}$ | $\%$ | $[0.0, 100.0]$ | Relative Humidity at 700 hPa (Mid-tropospheric moisture saturation) |
| `cape` | $\text{CAPE}$ | $\text{J/kg}$ | $[0.0, 7000.0]$ | Convective Available Potential Energy (Convective instability) |
| `vorticity_850` | $\zeta_{850}$ | $10^{-5}\text{ s}^{-1}$ | $[-50.0, 50.0]$ | Relative vorticity at 850 hPa ($\frac{\partial v_{850}}{\partial x} - \frac{\partial u_{850}}{\partial y}$) |
| `vertical_wind_shear` | $\text{VWS}$ | $\text{m/s}$ | $[0.0, 80.0]$ | Deep tropospheric shear ($\sqrt{(u_{200}-u_{850})^2 + (v_{200}-v_{850})^2}$) |
| `monsoon_trough_lat` | $\phi_{trough}$ | ${}^\circ\text{N}$ | $[15.0, 32.0]$ | Latitude of minimum MSLP across central longitude corridor ($78^\circ - 84^\circ\text{E}$) |
| `offshore_trough_idx` | $I_{ost}$ | $\text{hPa}$ | $[-10.0, 10.0]$ | Pressure anomaly indicating West Coast offshore trough |
| `orographic_flux_idx` | $F_{oro}$ | $\text{m/s}$ | $[-50.0, 50.0]$ | Perpendicular low-level wind component impinging on Western Ghats / NE hills |

---

## 4. IMD Rainfall Categorization Thresholds
| Rainfall Category | 24-hr Accumulation Threshold | Operational Alert Code |
| :--- | :--- | :--- |
| **No Rain / Very Light** | $< 2.5\text{ mm}$ | `NO_ALERT` (Green) |
| **Light to Moderate** | $2.5\text{ mm} \le R < 15.6\text{ mm}$ | `LOW_ALERT` (Green) |
| **Moderate to Heavy** | $15.6\text{ mm} \le R < 64.5\text{ mm}$ | `ADVISORY` (Yellow) |
| **Heavy Rain** | $64.5\text{ mm} \le R < 115.6\text{ mm}$ | `WATCH` (Orange) |
| **Very Heavy Rain** | $115.6\text{ mm} \le R < 204.5\text{ mm}$ | `WARNING` (Orange/Red) |
| **Extremely Heavy Rain** | $\ge 204.5\text{ mm}$ | `SEVERE_WARNING` (Red) |

---

## 5. Weather Regime Taxonomy
1. **Active Monsoon (`ACTIVE_MONSOON`)**: Strong low-level westerly jet ($u_{850} > 15\text{ m/s}$), normal trough position ($20^\circ-24^\circ\text{N}$), widespread central/peninsular rainfall.
2. **Break Monsoon (`BREAK_MONSOON`)**: Trough shifted north to Himalayan foothills ($>27^\circ\text{N}$), subdued central Indian rain, enhanced foothills and southeast peninsular rain.
3. **Monsoon Low / Depression (`MONSOON_LOW_DEPRESSION`)**: Intense cyclonic vortex ($\zeta_{850} > 3\times 10^{-5}\text{ s}^{-1}$), closed MSLP isobar $< 996\text{ hPa}$, heavy rain along southwest quadrant.
4. **Coastal Rainfall (`COASTAL_RAINFALL`)**: Active offshore trough along the Konkan-Goa-Karnataka coast, strong cross-isobaric moisture convergence.
5. **Orographic Rainfall (`OROGRAPHIC_RAINFALL`)**: Strong perpendicular westerly flow impinging Western Ghats or southerly flow hitting Meghalaya plateau.
6. **Western Disturbance (`WESTERN_DISTURBANCE`)**: Mid-latitude upper-tropospheric trough moving across Northwest India, inducing pre-monsoon or monsoon-interaction precipitation.

---

## 6. Missing Value Policy & Quality Assurance
- **Negative Rainfall**: Strictly set to $0.0\text{ mm}$ (physically impossible). Values $<0$ or $\text{NaN}$ in raw forecast or observation are flagged.
- **Atmospheric Variables**: Range-checked against climatological physical limits. Records with missing atmospheric covariates are discarded during training and flagged with fallback strategies during operational inference.
- **Future Leakage Check**: A strict assertions layer validates that no record utilizes features timestamped at or after $t_{valid}$.
