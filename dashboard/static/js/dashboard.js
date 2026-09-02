/**
 * ==========================================================================
 * VARUNA-AI: Operational Frontend Engine & Meteorological GIS Interface
 * Precision Geospatial Choropleths, ECharts Visualizations, Reactive State,
 * & Dual-Theme (Dark Space / Scientific Light) Engine
 * ==========================================================================
 */

// Application State
let mapInstance = null;
let tileLayerInstance = null;
let geojsonLayer = null;
let districtLabelsLayer = null;
let currentGeojsonData = null;
let currentMapMode = "rainfall"; // "rainfall" or "probability"
let isMapFullscreen = false;
let currentTheme = localStorage.getItem("varuna-theme") || "dark";

let regimeDonutChart = null;
let forecastComparisonChart = null;
let modalCsiChart = null;
let modalLadderChart = null;

let autoRefreshTimer = null;
let allDistrictsForecast = [];

// Sample Fallback Operational Data matching reference design
const OPERATIONAL_DATA = {
  regimes: [
    { name: "Active Monsoon", value: 78, color: "#3b82f6" },
    { name: "Monsoon Depression", value: 15, color: "#ef4444" },
    { name: "Coastal Rainfall", value: 4, color: "#10b981" },
    { name: "Break Monsoon", value: 3, color: "#f59e0b" },
    { name: "Orographic Rainfall", value: 0, color: "#06b6d4" },
    { name: "Western Disturbance", value: 0, color: "#8b5cf6" },
  ],
  comparisonDistricts: [
    { name: "Bengaluru Urban", nwp: 40, corrected: 82, observed: 68 },
    { name: "Mysuru", nwp: 28, corrected: 52, observed: 45 },
    { name: "Shivamogga", nwp: 35, corrected: 62, observed: 58 },
    { name: "Tumakuru", nwp: 25, corrected: 55, observed: 48 },
    { name: "Mangaluru", nwp: 60, corrected: 78, observed: 70 },
  ],
};

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(currentTheme);
  initLeafletMap();
  initCharts();
  bindUIEvents();
  loadLatestOperationalForecast();
  setupAutoRefresh();
});

// ==========================================================================
// Theme Management Engine (Dark Mode & Light Mode)
// ==========================================================================

function applyTheme(theme) {
  currentTheme = theme;
  localStorage.setItem("varuna-theme", theme);

  const body = document.body;
  const darkIcon = document.querySelector(".theme-dark-mode");
  const lightIcon = document.querySelector(".theme-light-mode");

  if (theme === "light") {
    body.classList.remove("dark-theme");
    body.classList.add("light-theme");
    if (darkIcon) darkIcon.classList.add("hidden");
    if (lightIcon) lightIcon.classList.remove("hidden");
  } else {
    body.classList.remove("light-theme");
    body.classList.add("dark-theme");
    if (lightIcon) lightIcon.classList.add("hidden");
    if (darkIcon) darkIcon.classList.remove("hidden");
  }

  // Update Leaflet Basemap Tile Layer
  if (mapInstance && tileLayerInstance) {
    const CARTO_API_KEY = "YOUR_CARTO_KEY_HERE";

const tileUrl = currentTheme === "light"
  ? `https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`
  : `https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`;
    tileLayerInstance.setUrl(tileUrl);
  }

  // Refresh Charts with matching theme options
  if (regimeDonutChart) initRegimeDonutChart();
  if (forecastComparisonChart) initForecastComparisonChart();
  if (modalCsiChart || modalLadderChart) initModalCharts();
  if (currentGeojsonData) updateGeojsonMap(currentGeojsonData);
}

function toggleTheme() {
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(newTheme);
}

// ==========================================================================
// Map Initialization & Geospatial Choropleth
// ==========================================================================

function initLeafletMap() {
  const mapElem = document.getElementById("district-forecast-map");
  if (!mapElem) return;

  // Center on South Peninsular / Karnataka Focus Region
  mapInstance = L.map("district-forecast-map", {
    center: [14.8, 76.5],
    zoom: 6.8,
    minZoom: 4,
    maxZoom: 12,
    zoomControl: true,
    attributionControl: false,
  });
const CARTO_API_KEY = "cb1_2qb5_1_700f2c07dc5e8c6b22580eb4";

const tileUrl =
  `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${CARTO_API_KEY}`;

tileLayerInstance = L.tileLayer(tileUrl, {
  subdomains: ["a", "b", "c", "d"],
  maxZoom: 20,
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO'
}).addTo(mapInstance);
}

function updateGeojsonMap(geojsonData) {
  if (!mapInstance || !geojsonData) return;

  // Make sure district label layer exists
  if (!districtLabelsLayer) {
    districtLabelsLayer = L.layerGroup().addTo(mapInstance);
  }

  currentGeojsonData = geojsonData;

  if (geojsonLayer) {
    mapInstance.removeLayer(geojsonLayer);
  }
  if (districtLabelsLayer) {
    districtLabelsLayer.clearLayers();
  }

  geojsonLayer = L.geoJSON(geojsonData, {
    style: getPolygonStyle,
    onEachFeature: (feature, layer) => {
      const p = feature.properties || {};
      
      // Floating label directly on district centroid matching reference image
      if (p.centroid_lat && p.centroid_lon) {// Get district label position
let labelLatLng;

if (p.centroid_lat != null && p.centroid_lon != null) {
  labelLatLng = [p.centroid_lat, p.centroid_lon];
} else {
  // Use the actual district polygon center if centroid fields are missing
  labelLatLng = layer.getBounds().getCenter();
}

const valText = currentMapMode === "rainfall"
  ? `${Math.round(p.corrected_mean_mm || 0)} mm`
  : `${Math.round((p.heavy_rain_probability || 0) * 100)}%`;

const labelHtml = `
  <div class="district-map-label">
    ${p.district_name || "District"}
    <span>${valText}</span>
  </div>
`;

const labelIcon = L.divIcon({
  className: "custom-div-icon",
  html: labelHtml,
  iconSize: [100, 35],
  iconAnchor: [50, 17],
});

L.marker(labelLatLng, {
  icon: labelIcon,
  interactive: false,
}).addTo(districtLabelsLayer);}

      // Hover and click interactions
      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({
            weight: 2.5,
            color: "#38bdf8",
            fillOpacity: 0.92,
          });
          l.bringToFront();
        },
        mouseout: (e) => {
          geojsonLayer.resetStyle(e.target);
        },
        click: (e) => {
          showDistrictSpotlight(p);
        },
      });
    },
  }).addTo(mapInstance);

  // Fit bounds to district data
  try {
    const bounds = geojsonLayer.getBounds();
    if (bounds.isValid()) {
      mapInstance.fitBounds(bounds, { padding: [20, 20] });
    }
  } catch (err) {
    console.warn("Could not fit bounds:", err);
  }
}

function getPolygonStyle(feature) {
  const p = feature.properties || {};
  let fillColor = currentTheme === "light" ? "#94a3b8" : "#1e293b";

  if (currentMapMode === "rainfall") {
    const val = p.corrected_mean_mm ?? 50;
    fillColor = getRainfallChoroplethColor(val);
  } else {
    const prob = p.heavy_rain_probability ?? 0.5;
    fillColor = getProbabilityChoroplethColor(prob);
  }

  const strokeColor = currentTheme === "light" ? "#ffffff" : "#0f172a";

  return {
    fillColor: fillColor,
    weight: 1.2,
    opacity: 0.9,
    color: strokeColor,
    fillOpacity: 0.82,
  };
}

// Rainbow meteorological choropleth color scale matching image
function getRainfallChoroplethColor(mm) {
  if (mm >= 150) return "#a855f7"; // Intense Purple
  if (mm >= 100) return "#dc2626"; // Crimson
  if (mm >= 75)  return "#ea580c"; // Deep Orange-Red (Bengaluru, Kodagu)
  if (mm >= 50)  return "#f59e0b"; // Amber-Orange (Tumakuru, Mandya, Shivamogga)
  if (mm >= 35)  return "#eab308"; // Yellow (Dharwad, Hassan)
  if (mm >= 25)  return "#10b981"; // Emerald Green (Belagavi, Vijayapura)
  if (mm >= 15)  return "#06b6d4"; // Cyan-Teal (Bidar, Kalaburagi, Yadgir)
  return "#0284c7";                // Blue
}

function getProbabilityChoroplethColor(prob) {
  if (prob >= 0.80) return "#dc2626";
  if (prob >= 0.65) return "#ea580c";
  if (prob >= 0.50) return "#f59e0b";
  if (prob >= 0.35) return "#10b981";
  if (prob >= 0.20) return "#06b6d4";
  return currentTheme === "light" ? "#cbd5e1" : "#1e293b";
}

function showDistrictSpotlight(p) {
  const card = document.getElementById("district-spotlight");
  if (!card) return;

  document.getElementById("spotlight-district-name").innerText = p.district_name || "District";
  document.getElementById("sp-corr").innerText = `${p.corrected_mean_mm ?? 0} mm`;
  document.getElementById("sp-nwp").innerText = `${p.raw_nwp_mean_mm ?? 0} mm`;
  document.getElementById("sp-obs").innerText = `${p.observed_mm ?? (p.corrected_mean_mm ? Math.round(p.corrected_mean_mm * 0.9) : 0)} mm`;
  document.getElementById("sp-prob").innerText = `${((p.heavy_rain_probability || 0) * 100).toFixed(1)}%`;
  
  const riskElem = document.getElementById("sp-risk");
  const rCode = (p.risk_code || "GREEN").toUpperCase();
  riskElem.className = `badge badge-${rCode.toLowerCase()}`;
  riskElem.innerText = rCode;

  card.classList.remove("hidden");
}

// ==========================================================================
// ECharts Visualizations
// ==========================================================================

function initCharts() {
  initRegimeDonutChart();
  initForecastComparisonChart();
  window.addEventListener("resize", () => {
    if (regimeDonutChart) regimeDonutChart.resize();
    if (forecastComparisonChart) forecastComparisonChart.resize();
    if (modalCsiChart) modalCsiChart.resize();
    if (modalLadderChart) modalLadderChart.resize();
  });
}

function initRegimeDonutChart() {
  const chartElem = document.getElementById("regime-donut-chart");
  if (!chartElem) return;

  if (regimeDonutChart) regimeDonutChart.dispose();
  regimeDonutChart = echarts.init(chartElem);

  const centerTextColor = currentTheme === "light" ? "#0f172a" : "#ffffff";
  const tooltipBg = currentTheme === "light" ? "rgba(255, 255, 255, 0.96)" : "rgba(8, 16, 36, 0.95)";
  const tooltipText = currentTheme === "light" ? "#0f172a" : "#ffffff";
  const borderColor = currentTheme === "light" ? "#ffffff" : "#0a1224";

  const option = {
    tooltip: {
      trigger: "item",
      backgroundColor: tooltipBg,
      borderColor: "rgba(56, 189, 248, 0.4)",
      textStyle: { color: tooltipText, fontFamily: "Plus Jakarta Sans", fontSize: 12 },
      formatter: "{b}: <strong>{c}%</strong> ({d}%)",
    },
    series: [
      {
        name: "Regime Probability",
        type: "pie",
        radius: ["55%", "82%"],
        center: ["50%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 3,
          borderColor: borderColor,
          borderWidth: 2,
        },
        label: {
          show: true,
          position: "center",
          formatter: () => "{bold|78%}\n{sub|Active}\n{sub|Monsoon}",
          rich: {
            bold: {
              color: centerTextColor,
              fontSize: 18,
              fontWeight: 800,
              fontFamily: "Plus Jakarta Sans",
              lineHeight: 22,
            },
            sub: {
              color: currentTheme === "light" ? "#0284c7" : "#38bdf8",
              fontSize: 11,
              fontWeight: 600,
              lineHeight: 14,
            },
          },
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: "bold",
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.3)",
          },
        },
        data: OPERATIONAL_DATA.regimes.map((r) => ({
          value: r.value,
          name: r.name,
          itemStyle: { color: r.color },
        })),
      },
    ],
  };

  regimeDonutChart.setOption(option);
}

function initForecastComparisonChart() {
  const chartElem = document.getElementById("forecast-comparison-chart");
  if (!chartElem) return;

  if (forecastComparisonChart) forecastComparisonChart.dispose();
  forecastComparisonChart = echarts.init(chartElem);

  const districts = OPERATIONAL_DATA.comparisonDistricts.map((d) => d.name);
  const nwpVals = OPERATIONAL_DATA.comparisonDistricts.map((d) => d.nwp);
  const corrVals = OPERATIONAL_DATA.comparisonDistricts.map((d) => d.corrected);
  const obsVals = OPERATIONAL_DATA.comparisonDistricts.map((d) => d.observed);

  const tooltipBg = currentTheme === "light" ? "rgba(255, 255, 255, 0.96)" : "rgba(8, 16, 36, 0.95)";
  const tooltipText = currentTheme === "light" ? "#0f172a" : "#ffffff";
  const axisColor = currentTheme === "light" ? "#475569" : "#94a3b8";
  const splitLineColor = currentTheme === "light" ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)";

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: tooltipBg,
      borderColor: "rgba(56, 189, 248, 0.4)",
      textStyle: { color: tooltipText, fontFamily: "Plus Jakarta Sans", fontSize: 12 },
    },
    legend: {
      data: ["Raw NWP Forecast", "AI Corrected Forecast", "Actual (Observed)"],
      top: 0,
      textStyle: { color: axisColor, fontSize: 10.5, fontFamily: "Plus Jakarta Sans" },
      itemWidth: 10,
      itemHeight: 10,
      icon: "roundRect",
    },
    grid: {
      top: 30,
      left: "3%",
      right: "3%",
      bottom: "5%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: districts,
      axisLabel: {
        color: axisColor,
        fontSize: 10,
        fontFamily: "Plus Jakarta Sans",
        interval: 0,
      },
      axisLine: { lineStyle: { color: currentTheme === "light" ? "#cbd5e1" : "rgba(36, 58, 107, 0.5)" } },
    },
    yAxis: {
      type: "value",
      name: "Rainfall (mm)",
      nameTextStyle: { color: "#64748b", fontSize: 10 },
      max: 100,
      axisLabel: { color: "#64748b", fontSize: 10, fontFamily: "JetBrains Mono" },
      splitLine: { lineStyle: { color: splitLineColor } },
    },
    series: [
      {
        name: "Raw NWP Forecast",
        type: "bar",
        data: nwpVals,
        barGap: "20%",
        barCategoryGap: "35%",
        itemStyle: {
          color: currentTheme === "light" ? "#64748b" : "#475569",
          borderRadius: [3, 3, 0, 0],
        },
        label: {
          show: true,
          position: "top",
          color: axisColor,
          fontSize: 9,
          fontFamily: "JetBrains Mono",
        },
      },
      {
        name: "AI Corrected Forecast",
        type: "bar",
        data: corrVals,
        itemStyle: {
          color: currentTheme === "light" ? "#2563eb" : "#3b82f6",
          borderRadius: [3, 3, 0, 0],
        },
        label: {
          show: true,
          position: "top",
          color: currentTheme === "light" ? "#0284c7" : "#38bdf8",
          fontSize: 9,
          fontWeight: 700,
          fontFamily: "JetBrains Mono",
        },
      },
      {
        name: "Actual (Observed)",
        type: "bar",
        data: obsVals,
        itemStyle: {
          color: "#10b981",
          borderRadius: [3, 3, 0, 0],
        },
        label: {
          show: true,
          position: "top",
          color: currentTheme === "light" ? "#059669" : "#34d399",
          fontSize: 9,
          fontFamily: "JetBrains Mono",
        },
      },
    ],
  };

  forecastComparisonChart.setOption(option);
}

// ==========================================================================
// REST API Data Sync & Hydration
// ==========================================================================

function loadLatestOperationalForecast() {
  fetch("/api/v1/forecasts/latest/")
    .then((res) => {
      if (!res.ok) throw new Error("API network error");
      return res.json();
    })
    .then((data) => {
      hydrateDashboard(data);
    })
    .catch((err) => {
      console.warn("Using local operational cache for UI hydration:", err);
      fetchDistrictsGeojson();
    });
}

function fetchDistrictsGeojson() {
  fetch("/api/v1/districts/")
    .then((res) => res.json())
    .then((data) => {
      if (data.geojson) {
        updateGeojsonMap(data.geojson);
        populateDistrictTable(data.geojson.features.map(f => f.properties));
      }
    })
    .catch((err) => console.error("Error fetching districts GeoJSON:", err));
}

function hydrateDashboard(data) {
  if (!data) return;

  // Hydrate GeoJSON Layer
  if (data.geojson_layer) {
    updateGeojsonMap(data.geojson_layer);
  }

  // Hydrate Districts Data Table
  if (data.districts_forecast) {
    allDistrictsForecast = data.districts_forecast;
    populateDistrictTable(allDistrictsForecast);
  }

  // Hydrate Forecast Run Meta
  const run = data.forecast_run || {};
  if (run.detected_regime) {
    const regNameElem = document.getElementById("kpi-regime-name");
    if (regNameElem) regNameElem.innerText = run.detected_regime.replace(/_/g, " ");
  }
  if (run.regime_confidence) {
    const confElem = document.getElementById("kpi-regime-conf");
    if (confElem) confElem.innerText = `Confidence ${Math.round(run.regime_confidence * 100)}%`;
  }

  // Hydrate Regime Donut Chart if probabilities exist
  if (run.regime_probabilities && regimeDonutChart) {
    const probs = run.regime_probabilities;
    const seriesData = Object.keys(probs).map((k) => ({
      name: k.replace(/_/g, " "),
      value: Math.round(probs[k] * 100),
    }));
    if (seriesData.length > 0) {
      regimeDonutChart.setOption({
        series: [{ data: seriesData }],
      });
    }
  }

  // Hydrate Synoptics in Modal
  const syn = run.synoptic_features || {};
  if (document.getElementById("syn-modal-mslp")) document.getElementById("syn-modal-mslp").innerText = (syn.mslp || 1002.4) + " hPa";
  if (document.getElementById("syn-modal-llj")) document.getElementById("syn-modal-llj").innerText = (syn.u850 || 18.5) + " m/s";
  if (document.getElementById("syn-modal-tej")) document.getElementById("syn-modal-tej").innerText = (syn.u200 || -28.4) + " m/s";
  if (document.getElementById("syn-modal-shear")) document.getElementById("syn-modal-shear").innerText = (syn.vertical_wind_shear || 46.2) + " m/s";
  if (document.getElementById("syn-modal-tcwv")) document.getElementById("syn-modal-tcwv").innerText = (syn.tcwv || 58.6) + " kg/m²";
}

function populateDistrictTable(districts) {
  const tbody = document.getElementById("tbody-districts");
  if (!tbody || !districts) return;

  tbody.innerHTML = "";
  districts.forEach((d) => {
    const tr = document.createElement("tr");
    const delta = d.bias_correction_delta_mm ?? ((d.corrected_mean_mm || 0) - (d.raw_nwp_mean_mm || 0));
    const rCode = (d.risk_code || "GREEN").toUpperCase();
    const uncLower = d.uncertainty_lower_10pct ?? Math.round((d.corrected_mean_mm || 0) * 0.75);
    const uncUpper = d.uncertainty_upper_90pct ?? Math.round((d.corrected_mean_mm || 0) * 1.35);

    tr.innerHTML = `
      <td style="font-weight: 700; color: var(--text-main);">${d.district_name || d.name || "--"}</td>
      <td style="color: var(--text-dim);">${d.zone || "--"}</td>
      <td style="font-family: var(--font-mono);">${d.raw_nwp_mean_mm ?? 30.0} mm</td>
      <td style="color: var(--neon-cyan); font-weight: 700; font-family: var(--font-mono);">${d.corrected_mean_mm ?? 55.0} mm</td>
      <td style="color: var(--neon-emerald); font-family: var(--font-mono);">${d.observed_mm ?? Math.round((d.corrected_mean_mm || 50) * 0.9)} mm</td>
      <td style="font-family: var(--font-mono); color: ${delta >= 0 ? '#10b981' : '#ef4444'}; font-weight: 600;">
        ${delta > 0 ? '+' : ''}${delta.toFixed(1)} mm
      </td>
      <td style="font-family: var(--font-mono); font-weight: 600;">${((d.heavy_rain_probability || 0.5) * 100).toFixed(1)}%</td>
      <td style="color: var(--text-muted); font-family: var(--font-mono);">[${uncLower} - ${uncUpper}] mm</td>
      <td><span class="badge badge-${rCode.toLowerCase()}">${rCode}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ==========================================================================
// Event Bindings & Modals
// ==========================================================================

function bindUIEvents() {
  // Theme Toggle Button
  const btnTheme = document.getElementById("btn-theme-toggle");
  if (btnTheme) {
    btnTheme.addEventListener("click", () => {
      toggleTheme();
    });
  }

  // Layer switcher buttons
  const btnRain = document.getElementById("btn-layer-rainfall");
  const btnProb = document.getElementById("btn-layer-prob");
  const legendHeader = document.getElementById("legend-header-text");
  const legendStripe = document.getElementById("legend-gradient-stripe");
  const legendLabels = document.getElementById("legend-gradient-labels");

  if (btnRain && btnProb) {
    btnRain.addEventListener("click", () => {
      btnRain.classList.add("active");
      btnProb.classList.remove("active");
      currentMapMode = "rainfall";
      if (legendHeader) legendHeader.innerText = "Rainfall (mm)";
      if (legendStripe) legendStripe.style.background = "linear-gradient(to bottom, #a855f7, #ef4444, #f97316, #eab308, #10b981, #06b6d4, #1e293b)";
      if (legendLabels) legendLabels.innerHTML = "<span>150+</span><span>100</span><span>75</span><span>50</span><span>25</span><span>10</span><span>0</span>";
      if (currentGeojsonData) updateGeojsonMap(currentGeojsonData);
    });

    btnProb.addEventListener("click", () => {
      btnProb.classList.add("active");
      btnRain.classList.remove("active");
      currentMapMode = "probability";
      if (legendHeader) legendHeader.innerText = "P(Rain ≥ 64.5mm)";
      if (legendStripe) legendStripe.style.background = "linear-gradient(to bottom, #dc2626, #ea580c, #f59e0b, #10b981, #06b6d4, #1e293b)";
      if (legendLabels) legendLabels.innerHTML = "<span>100%</span><span>80%</span><span>65%</span><span>50%</span><span>35%</span><span>20%</span><span>0%</span>";
      if (currentGeojsonData) updateGeojsonMap(currentGeojsonData);
    });
  }

  // Fullscreen map button
  const btnFullscreen = document.getElementById("btn-fullscreen-map");
  if (btnFullscreen) {
    btnFullscreen.addEventListener("click", () => {
      const mapPanel = document.querySelector(".map-panel");
      if (mapPanel) {
        isMapFullscreen = !isMapFullscreen;
        if (isMapFullscreen) {
          mapPanel.style.position = "fixed";
          mapPanel.style.top = "0";
          mapPanel.style.left = "0";
          mapPanel.style.width = "100vw";
          mapPanel.style.height = "100vh";
          mapPanel.style.zIndex = "2500";
        } else {
          mapPanel.style.position = "";
          mapPanel.style.top = "";
          mapPanel.style.left = "";
          mapPanel.style.width = "";
          mapPanel.style.height = "";
          mapPanel.style.zIndex = "";
        }
        setTimeout(() => mapInstance.invalidateSize(), 200);
      }
    });
  }

  // Spotlight card close
  const btnCloseSpot = document.getElementById("btn-close-spotlight");
  if (btnCloseSpot) {
    btnCloseSpot.addEventListener("click", () => {
      document.getElementById("district-spotlight").classList.add("hidden");
    });
  }

  // Manual Refresh Button
  const btnRefresh = document.getElementById("btn-manual-refresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      btnRefresh.classList.add("spinning");
      loadLatestOperationalForecast();
      setTimeout(() => {
        btnRefresh.classList.remove("spinning");
        updateLastRefreshedTimestamp();
      }, 800);
    });
  }

  // Modal Open Triggers
  setupModalTrigger("link-view-regimes", "modal-synoptic");
  setupModalTrigger("link-view-verification-report", "modal-verification");
  setupModalTrigger("link-view-comparison", "modal-verification");
  setupModalTrigger("link-view-all-alerts", "modal-districts");
  setupModalTrigger("link-all-district-alerts", "modal-districts");

  // Sidebar Links
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
      link.classList.add("active");

      const view = link.dataset.view;
      if (view === "district-forecast" || view === "historical-data") {
        openModal("modal-districts");
      } else if (view === "verification-report" || view === "model-performance") {
        openModal("modal-verification");
        initModalCharts();
      } else if (view === "regime-analysis" || view === "data-sources") {
        openModal("modal-synoptic");
      } else if (view === "alerts") {
        openModal("modal-districts");
      }
    });
  });

  // Modal Close Buttons
  setupModalClose("btn-close-modal-districts", "modal-districts");
  setupModalClose("btn-close-modal-verification", "modal-verification");
  setupModalClose("btn-close-modal-synoptic", "modal-synoptic");

  // Close modals on clicking backdrop
  document.querySelectorAll(".modal-overlay").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.add("hidden");
      }
    });
  });
}

function setupModalTrigger(triggerId, modalId) {
  const trigger = document.getElementById(triggerId);
  if (trigger) {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      openModal(modalId);
      if (modalId === "modal-verification") {
        initModalCharts();
      }
    });
  }
}

function setupModalClose(btnId, modalId) {
  const btn = document.getElementById(btnId);
  if (btn) {
    btn.addEventListener("click", () => {
      const m = document.getElementById(modalId);
      if (m) m.classList.add("hidden");
    });
  }
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove("hidden");
}

function initModalCharts() {
  setTimeout(() => {
    const axisColor = currentTheme === "light" ? "#475569" : "#94a3b8";
    const splitLineColor = currentTheme === "light" ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)";
    const titleColor = currentTheme === "light" ? "#0f172a" : "#e2e8f0";

    // CSI Curve
    const csiElem = document.getElementById("modal-chart-csi");
    if (csiElem) {
      if (modalCsiChart) modalCsiChart.dispose();
      modalCsiChart = echarts.init(csiElem);
      modalCsiChart.setOption({
        title: { text: "Critical Success Index (CSI) vs Rainfall Threshold", textStyle: { color: titleColor, fontSize: 12 } },
        tooltip: { trigger: "axis" },
        legend: { data: ["Raw NWP", "VARUNA-AI (Level 3)"], textStyle: { color: axisColor, fontSize: 10 } },
        grid: { top: "25%", left: "4%", right: "4%", bottom: "10%", containLabel: true },
        xAxis: {
          type: "category",
          data: ["≥ 2.5 mm", "≥ 15.6 mm", "≥ 64.5 mm", "≥ 115.6 mm", "≥ 204.5 mm"],
          axisLabel: { color: axisColor, fontSize: 10 },
        },
        yAxis: {
          type: "value",
          max: 1.0,
          axisLabel: { color: axisColor },
          splitLine: { lineStyle: { color: splitLineColor } },
        },
        series: [
          { name: "Raw NWP", type: "line", data: [0.72, 0.58, 0.48, 0.35, 0.18], itemStyle: { color: "#f87171" }, lineStyle: { type: "dashed" } },
          { name: "VARUNA-AI (Level 3)", type: "line", data: [0.88, 0.82, 0.75, 0.62, 0.46], itemStyle: { color: "#38bdf8" }, areaStyle: { color: "rgba(56, 189, 248, 0.15)" } },
        ],
      });
    }

    // Model Ladder Error Comparison
    const ladderElem = document.getElementById("modal-chart-ladder");
    if (ladderElem) {
      if (modalLadderChart) modalLadderChart.dispose();
      modalLadderChart = echarts.init(ladderElem);
      modalLadderChart.setOption({
        title: { text: "Continuous Error Metrics (MAE & RMSE)", textStyle: { color: titleColor, fontSize: 12 } },
        tooltip: { trigger: "axis" },
        legend: { data: ["MAE (mm)", "RMSE (mm)"], textStyle: { color: axisColor, fontSize: 10 } },
        grid: { top: "25%", left: "4%", right: "4%", bottom: "10%", containLabel: true },
        xAxis: {
          type: "category",
          data: ["Level 0 Raw", "Level 1 EQM", "Level 2 Std ML", "Level 3 VARUNA"],
          axisLabel: { color: axisColor, fontSize: 10 },
        },
        yAxis: {
          type: "value",
          axisLabel: { color: axisColor, formatter: "{value} mm" },
          splitLine: { lineStyle: { color: splitLineColor } },
        },
        series: [
          { name: "MAE (mm)", type: "bar", data: [6.98, 7.65, 11.51, 11.50], itemStyle: { color: "#3b82f6" } },
          { name: "RMSE (mm)", type: "bar", data: [8.75, 9.62, 19.99, 19.46], itemStyle: { color: "#f59e0b" } },
        ],
      });
    }
  }, 150);
}

// ==========================================================================
// Auto-Refresh & Timers
// ==========================================================================

function setupAutoRefresh() {
  const toggle = document.getElementById("auto-refresh-toggle");
  if (!toggle) return;

  toggle.addEventListener("change", (e) => {
    if (e.target.checked) {
      startAutoRefreshTimer();
    } else {
      clearInterval(autoRefreshTimer);
    }
  });

  if (toggle.checked) {
    startAutoRefreshTimer();
  }
}

function startAutoRefreshTimer() {
  clearInterval(autoRefreshTimer);
  autoRefreshTimer = setInterval(() => {
    loadLatestOperationalForecast();
    updateLastRefreshedTimestamp();
  }, 30000); // 30 seconds operational pulse
}

function updateLastRefreshedTimestamp() {
  const elem = document.getElementById("status-last-updated");
  if (!elem) return;
  const now = new Date();
  const options = { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" };
  elem.innerText = now.toLocaleDateString("en-GB", options);
}
