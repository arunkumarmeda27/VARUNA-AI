# VARUNA-AI: Geospatial Pipeline & District Aggregation Engine

**Smart India Hackathon 2026 | Problem Statement: SIH26080**  
**Module**: `geospatial/` & `dashboard/` | **Owner**: Member 6 (Geospatial & Operational Interface Engineer)

---

## 1. Spatial Processing Architecture
Numerical weather prediction (NWP) models and satellite/radar products generate gridded point outputs. Operational disaster management authorities (NDMA, SDMA, District Collectors) require **administrative district-level forecast advisories**.

```
NWP & OBSERVATIONAL GRIDS (Regular 0.25° x 0.25° Mesh)
                          │
                          ▼
[CORRECTED RAINFALL GRID] (`correction/models/correction_engine.py`)
  • Post-processed rainfall (mm/day) at all active grid coordinates
                          │
                          ▼
[DISTRICT BOUNDARY GEOMETRIES] (`geospatial/districts/district_geometry.py`)
  • WGS84 (EPSG:4326) Polygon GeoJSON for representative Indian monsoon districts
                          │
                          ▼
[SPATIAL AGGREGATION ENGINE] (`geospatial/aggregation/grid_aggregator.py`)
  • Area-weighted Point-in-Polygon intersection
  • Conservative extreme rainfall preservation (calculates both district mean and peak max)
  • District-level exceedance probability aggregation: P_dist = 1 - prod(1 - P_grid)
                          │
                          ▼
[DISTRICT OPERATIONAL PRODUCT] (GeoJSON Layer + DB Records)
  • District Name, State, Raw NWP Mean, Corrected Mean, Corrected Max,
    Bias Delta, Heavy Rain Probability, Conformal Prediction Bounds [q10, q90],
    and IMD Risk Alert Code (GREEN / YELLOW / ORANGE / RED)
```

---

## 2. Representative District Coverage

| District ID | District Name | State | Terrain / Climate Zone | Centroid Coord |
| :--- | :--- | :--- | :--- | :--- |
| `DIST_MH_MUM` | Mumbai Suburban | Maharashtra | West Coast / Konkan Coastal | 19.08°N, 72.88°E |
| `DIST_MH_RAT` | Ratnagiri | Maharashtra | West Coast / Ghats Foothills | 16.99°N, 73.31°E |
| `DIST_KL_WAY` | Wayanad | Kerala | South Peninsular / Western Ghats | 11.68°N, 76.13°E |
| `DIST_MH_PUN` | Pune | Maharashtra | Central India / Leeward Plateau | 18.52°N, 73.86°E |
| `DIST_MH_NAG` | Nagpur | Maharashtra | Central India / Vidarbha Plains | 21.15°N, 79.09°E |
| `DIST_OR_CUT` | Cuttack | Odisha | East Coast / Cyclonic Track | 20.46°N, 85.88°E |
| `DIST_OR_SAM` | Sambalpur | Odisha | East India / Monsoon Trough | 21.47°N, 83.98°E |
| `DIST_BR_PAT` | Patna | Bihar | East India / Gangetic Plain | 25.60°N, 85.14°E |
| `DIST_UK_DEH` | Dehradun | Uttarakhand | Northwest / Himalayan Foothills | 30.32°N, 78.03°E |
| `DIST_RJ_JAI` | Jaipur | Rajasthan | Northwest / Semi-Arid | 26.91°N, 75.79°E |
| `DIST_AS_GUW` | Kamrup (Guwahati)| Assam | Northeast India / Brahmaputra | 26.14°N, 91.74°E |
| `DIST_TN_CHE` | Chennai | Tamil Nadu | South Peninsular / Rain Shadow | 13.08°N, 80.27°E |

---

## 3. Preservation of Localized Convective Peaks
Standard spatial averaging (arithmetic mean) dilutes high-intensity localized convective rainfall cells (e.g. 150 mm cloudburst in 1 grid cell surrounded by 10 mm cells averages to 45 mm, concealing flash flood risks).

VARUNA-AI solves this by computing and exposing **both**:
1. `corrected_mean_mm`: Area-averaged accumulation for hydrological runoff and reservoir balance modeling.
2. `corrected_max_mm`: Maximum grid-cell accumulation within district boundaries for localized urban flood & landslide risk alerting.
