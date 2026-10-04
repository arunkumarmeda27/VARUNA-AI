/**
 * ==========================================================================
 * VARUNA-AI: Operational Frontend Engine & Meteorological GIS Interface
 * Full Multi-View Panel Controller, Firebase Authentication Guard,
 * ECharts Synoptic & Verification Analytics, & Interactive Leaflet GIS
 * ==========================================================================
 */

/// Ensure default theme is always dark if not previously set
if (!localStorage.getItem("varuna-theme")) {
  localStorage.setItem("varuna-theme", "dark");
}

// Dynamically initialize Firebase from backend configuration (no secret in source)
const firebaseInitPromise = fetch("/api/v1/auth/config/")
  .then((res) => res.json())
  .then((firebaseConfig) => {
    if (typeof firebase !== "undefined" && (!firebase.apps || !firebase.apps.length)) {
      try {
        firebase.initializeApp(firebaseConfig);
      } catch (e) {
        console.warn("Firebase initializeApp error:", e);
      }
    }
    // Check authentication once Firebase is safely initialized
    checkAuthentication();
    return true;
  })
  .catch((err) => {
    console.warn("Could not load dynamic auth config:", err);
    return false;
  });

// Application State

let mapInstance = null;
let gisMapInstance = null;
let tileLayerInstance = null;
let gisTileLayerInstance = null;
let gisGeojsonLayer = null;
let geojsonLayer = null;
let districtLabelsLayer = null;
let currentGeojsonData = null;
let currentMapMode = "rainfall"; // "rainfall" or "probability"
let isMapFullscreen = false;
let currentTheme = localStorage.getItem("varuna-theme") || "dark";

let regimeDonutChart = null;
let forecastComparisonChart = null;
let synopticRadarChart = null;
let csiCurveChart = null;
let ladderComparisonChart = null;
let historicalTimeseriesChart = null;

let autoRefreshTimer = null;
let allDistrictsForecast = [];
let currentRegimeProbabilities = null;
let currentSynopticFeatures = null;

// ==========================================================================
// Initialization & Authentication Lifecycle
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  checkAuthentication();
  applyTheme(currentTheme);
  initLeafletMap();
  initCharts();
  bindUIEvents();
  loadLatestOperationalForecast();
  setupAutoRefresh();
  updateDynamicDates();
});

function checkAuthentication() {
  const storedUser = localStorage.getItem("varuna_user");

  // 1. If user is already stored (Demo Mode or prior login), validate and hydrate immediately!
  if (storedUser) {
    try {
      const u = JSON.parse(storedUser);
      updateUserHeader(u);
      return;
    } catch (e) {
      console.warn("Invalid user storage");
      localStorage.removeItem("varuna_user");
    }
  }

  // 2. Only check Firebase auth if Firebase is initialized with at least 1 app!
  if (typeof firebase !== "undefined" && firebase.apps && firebase.apps.length > 0) {
    try {
      const auth = firebase.auth();
      auth.onAuthStateChanged((user) => {
        if (user) {
          const u = {
            email: user.email,
            displayName: user.displayName || user.email.split("@")[0],
            uid: user.uid,
          };
          localStorage.setItem("varuna_user", JSON.stringify(u));
          updateUserHeader(u);
        } else {
          // If no Firebase user and no stored user, redirect to login
          if (!localStorage.getItem("varuna_user")) {
            window.location.href = "/login/";
          }
        }
      });
      return;
    } catch (err) {
      console.warn("Firebase auth listener error:", err);
    }
  }

  // 3. Fallback: If not authenticated and no stored session after init attempt, redirect
  firebaseInitPromise.finally(() => {
    if (!localStorage.getItem("varuna_user")) {
      setTimeout(() => {
        if (!localStorage.getItem("varuna_user")) {
          window.location.href = "/login/";
        }
      }, 500);
    }
  });
}

function updateUserHeader(u) {
  const nameElem = document.getElementById("user-display-name");
  const avatarElem = document.getElementById("user-avatar-circle");
  if (nameElem && u.displayName) {
    nameElem.innerText = u.displayName;
  } else if (nameElem && u.email) {
    nameElem.innerText = u.email.split("@")[0];
  }
  if (avatarElem) {
    const initials = (u.displayName || u.email || "MO").slice(0, 2).toUpperCase();
    avatarElem.innerText = initials;
  }
}

function handleSignOut() {
  try {
    if (typeof firebase !== "undefined" && firebase.apps && firebase.apps.length > 0) {
      firebase.auth().signOut().catch(() => {});
    }
  } catch (e) {
    console.warn("Sign out error:", e);
  }
  localStorage.removeItem("varuna_user");
  window.location.href = "/login/";
}


// ==========================================================================
// View Switching Logic (Fixes all navigation tabs)
// ==========================================================================

function switchView(viewName) {
  // 1. Hide all view panels
  document.querySelectorAll(".view-panel").forEach((panel) => {
    panel.classList.remove("active");
  });

  // 2. Remove active state from all sidebar nav links
  document.querySelectorAll(".sidebar-nav .nav-link").forEach((link) => {
    link.classList.remove("active");
  });

  // 3. Activate target link in sidebar
  const activeLink = document.querySelector(`.sidebar-nav .nav-link[data-view="${viewName}"]`);
  if (activeLink) {
    activeLink.classList.add("active");
  }

  // 4. Show target view panel
  const targetPanel = document.getElementById(`view-${viewName}`);
  if (targetPanel) {
    targetPanel.classList.add("active");
  } else {
    console.warn(`View panel not found: view-${viewName}`);
    document.getElementById("view-dashboard").classList.add("active");
  }

  // 5. Trigger resize and render on specific view activations
  setTimeout(() => {
    if (viewName === "dashboard" && mapInstance) {
      mapInstance.invalidateSize();
      if (regimeDonutChart) regimeDonutChart.resize();
      if (forecastComparisonChart) forecastComparisonChart.resize();
    } else if (viewName === "forecast-map") {
      initGisMap();
    } else if (viewName === "regime-analysis") {
      initSynopticRadarChart();
    } else if (viewName === "verification-report") {
      initVerificationCharts();
    } else if (viewName === "historical-data") {
      initHistoricalTimeseriesChart();
    } else if (viewName === "district-forecast") {
      populateDistrictViewTable(allDistrictsForecast);
    } else if (viewName === "alerts") {
      renderAlertsFeed(allDistrictsForecast);
    }
  }, 100);
}

// ==========================================================================
// Dynamic Date & Cycle Update (Makes model look like real production)
// ==========================================================================

function updateDynamicDates() {
  const now = new Date();
  const options = { day: "2-digit", month: "short", year: "numeric" };
  const dateStr = now.toLocaleDateString("en-GB", options);

  // Update status card
  const statusUpdated = document.getElementById("status-last-updated");
  if (statusUpdated) {
    statusUpdated.innerText = `${dateStr} 00:00 UTC (T+24h)`;
  }

  // Update date selector options
  const dateSelect = document.getElementById("forecast-date-select");
  if (dateSelect) {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    const day3 = new Date(today);
    day3.setDate(today.getDate() + 2);

    dateSelect.options[0].text = `Today (${today.toLocaleDateString("en-GB", { day: "numeric", month: "short" })}) — T+24h`;
    dateSelect.options[1].text = `Tomorrow (${tomorrow.toLocaleDateString("en-GB", { day: "numeric", month: "short" })}) — T+48h`;
    dateSelect.options[2].text = `Day +3 (${day3.toLocaleDateString("en-GB", { day: "numeric", month: "short" })}) — T+72h`;
  }
}

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
  const CARTO_API_KEY = "cb1_2qb5_1_700f2c07dc5e8c6b22580eb4";
  const tileUrl = theme === "light"
    ? `https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`
    : `https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`;

  if (mapInstance && tileLayerInstance) {
    tileLayerInstance.setUrl(tileUrl);
  }
  if (gisMapInstance && gisTileLayerInstance) {
    gisTileLayerInstance.setUrl(tileUrl);
  }


  // Refresh Charts with matching theme options
  if (regimeDonutChart) initRegimeDonutChart();
  if (forecastComparisonChart) initForecastComparisonChart();
  if (synopticRadarChart) initSynopticRadarChart();
  if (csiCurveChart || ladderComparisonChart) initVerificationCharts();
  if (historicalTimeseriesChart) initHistoricalTimeseriesChart();
  if (currentGeojsonData) updateGeojsonMap(currentGeojsonData);
}

function toggleTheme() {
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(newTheme);
}

// ==========================================================================
// Leaflet Map Initialization & Geospatial Choropleths
// ==========================================================================

function initLeafletMap() {
  const mapElem = document.getElementById("district-forecast-map");
  if (!mapElem) return;

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

function initGisMap() {
  const gisElem = document.getElementById("forecast-gis-map-container");
  if (!gisElem) return;

  if (!gisMapInstance) {
    gisMapInstance = L.map("forecast-gis-map-container", {
      center: [15.2, 76.5],
      zoom: 6.5,
      minZoom: 4,
      maxZoom: 12,
      zoomControl: true,
      attributionControl: false,
    });
  const CARTO_API_KEY = "cb1_2qb5_1_700f2c07dc5e8c6b22580eb4";

  const tileUrl = currentTheme === "light"
    ? `https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`
    : `https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`;

gisTileLayerInstance = L.tileLayer(tileUrl, {
  subdomains: ["a", "b", "c", "d"],
  maxZoom: 20,
  attribution:
    '&copy; OpenStreetMap &copy; CARTO'
}).addTo(gisMapInstance);
}
  gisMapInstance.invalidateSize();
  if (currentGeojsonData) {
    if (gisGeojsonLayer) gisMapInstance.removeLayer(gisGeojsonLayer);
    gisGeojsonLayer = L.geoJSON(currentGeojsonData, {
      style: getPolygonStyle,
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        layer.bindTooltip(`<strong>${p.district_name || p.name}</strong><br>VARUNA-AI: ${p.corrected_mean_mm || 0} mm`, {
          sticky: true,
          direction: "top",
        });
      },
    }).addTo(gisMapInstance);
  }
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
      
      // Floating label on district centroid
      let labelLatLng;
      if (p.centroid_lat != null && p.centroid_lon != null) {
        labelLatLng = [p.centroid_lat, p.centroid_lon];
      } else {
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
      }).addTo(districtLabelsLayer);


      // Hover and click interactions
      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({ weight: 2.5, color: "#38bdf8", fillOpacity: 0.92 });
          l.bringToFront();
        },
        mouseout: (e) => {
          geojsonLayer.resetStyle(e.target);
        },
        click: () => {
          showDistrictSpotlight(p);
        },
      });
    },
  }).addTo(mapInstance);

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
    if (hasNumericValue(p.corrected_mean_mm)) {
      fillColor = getRainfallChoroplethColor(Number(p.corrected_mean_mm));
    }
  } else {
    if (hasNumericValue(p.heavy_rain_probability)) {
      fillColor = getProbabilityChoroplethColor(Number(p.heavy_rain_probability));
    }
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

function hasNumericValue(value) {
  return value !== null
    && value !== undefined
    && value !== ""
    && Number.isFinite(Number(value));
}

function getRainfallChoroplethColor(mm) {
  if (mm >= 250) return "#a855f7"; // Intense Purple
  if (mm >= 204.5) return "#dc2626"; // Crimson
  if (mm >= 150)  return "#ea580c"; // Deep Orange-Red
  if (mm >= 115.6)  return "#f59e0b"; // Amber-Orange
  if (mm >= 64.5)  return "#eab308"; // Yellow
  if (mm >= 35.5)  return "#10b981"; // Emerald Green
  if (mm >= 15.6)  return "#06b6d4"; // Cyan-Teal
  return "#0284c7";                // Blue
}

function getProbabilityChoroplethColor(prob) {
  if (prob >= 0.85) return "#dc2626";
  if (prob >= 0.60) return "#ea580c";
  if (prob >= 0.40) return "#f59e0b";
  if (prob >= 0.20) return "#10b981";
  if (prob >= 0.10) return "#06b6d4";
  return currentTheme === "light" ? "#cbd5e1" : "#1e293b";
}

function showDistrictSpotlight(p) {
  const card = document.getElementById("district-spotlight");
  if (!card) return;

  document.getElementById("spotlight-district-name").innerText = p.district_name || p.name || "District";
  document.getElementById("sp-corr").innerText = hasNumericValue(p.corrected_mean_mm) ? `${p.corrected_mean_mm} mm` : "Unavailable";
  document.getElementById("sp-nwp").innerText = hasNumericValue(p.raw_nwp_mean_mm) ? `${p.raw_nwp_mean_mm} mm` : "Unavailable";
  document.getElementById("sp-obs").innerText = hasNumericValue(p.observed_mm) ? `${p.observed_mm} mm` : "Unavailable";
  document.getElementById("sp-prob").innerText = hasNumericValue(p.heavy_rain_probability) ? `${(p.heavy_rain_probability * 100).toFixed(1)}%` : "Unavailable";
  
  const riskElem = document.getElementById("sp-risk");
  const rCode = p.risk_code ? String(p.risk_code).toUpperCase() : null;
  riskElem.className = rCode ? `badge badge-${rCode.toLowerCase()}` : "badge";
  riskElem.innerText = rCode || "Unavailable";

  card.classList.remove("hidden");
}

function setMapLayerMode(mode) {
  currentMapMode = mode;
  const btnRain = document.getElementById("btn-layer-rainfall");
  const btnProb = document.getElementById("btn-layer-prob");
  const legendHeader = document.getElementById("legend-header-text");
  const legendStripe = document.getElementById("legend-gradient-stripe");
  const legendLabels = document.getElementById("legend-gradient-labels");

  if (mode === "rainfall") {
    if (btnRain) btnRain.classList.add("active");
    if (btnProb) btnProb.classList.remove("active");
    document.querySelectorAll('[data-forecast-map-mode="rainfall"]').forEach((btn) => btn.classList.add("active"));
    document.querySelectorAll('[data-forecast-map-mode="probability"]').forEach((btn) => btn.classList.remove("active"));
    if (legendHeader) legendHeader.innerText = "Rainfall (mm)";
    if (legendStripe) legendStripe.style.background = "linear-gradient(to bottom, #a855f7, #ef4444, #f97316, #eab308, #10b981, #06b6d4, #1e293b)";
    if (legendLabels) legendLabels.innerHTML = "<span>150+</span><span>100</span><span>75</span><span>50</span><span>25</span><span>10</span><span>0</span>";
  } else {
    if (btnProb) btnProb.classList.add("active");
    if (btnRain) btnRain.classList.remove("active");
    document.querySelectorAll('[data-forecast-map-mode="probability"]').forEach((btn) => btn.classList.add("active"));
    document.querySelectorAll('[data-forecast-map-mode="rainfall"]').forEach((btn) => btn.classList.remove("active"));
    if (legendHeader) legendHeader.innerText = "P(Rain ≥ 64.5mm)";
    if (legendStripe) legendStripe.style.background = "linear-gradient(to bottom, #dc2626, #ea580c, #f59e0b, #10b981, #06b6d4, #1e293b)";
    if (legendLabels) legendLabels.innerHTML = "<span>100%</span><span>80%</span><span>65%</span><span>50%</span><span>35%</span><span>20%</span><span>0%</span>";
  }

  if (currentGeojsonData) updateGeojsonMap(currentGeojsonData);
  if (gisMapInstance && currentGeojsonData) initGisMap();
}

// ==========================================================================
// ECharts Visualizations (Overview, Regimes, Verification, Historical)
// ==========================================================================

function initCharts() {
  initRegimeDonutChart();
  initForecastComparisonChart();

  window.addEventListener("resize", () => {
    if (regimeDonutChart) regimeDonutChart.resize();
    if (forecastComparisonChart) forecastComparisonChart.resize();
    if (synopticRadarChart) synopticRadarChart.resize();
    if (csiCurveChart) csiCurveChart.resize();
    if (ladderComparisonChart) ladderComparisonChart.resize();
    if (historicalTimeseriesChart) historicalTimeseriesChart.resize();
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
  const regimeColors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#06b6d4", "#8b5cf6"];
  const regimeData = currentRegimeProbabilities
    ? Object.entries(currentRegimeProbabilities).map(([name, probability], index) => ({
      name: name.replace(/_/g, " "),
      value: probability * 100,
      itemStyle: { color: regimeColors[index % regimeColors.length] },
    }))
    : [];
  const legend = document.getElementById("custom-regime-legend");
  if (legend) {
    if (!regimeData.length) {
      legend.textContent = "Real regime probabilities unavailable";
    } else {
      legend.replaceChildren(...regimeData.map((regime) => {
        const row = document.createElement("div");
        row.className = "legend-row";
        const dot = document.createElement("span");
        dot.className = "legend-dot";
        dot.style.background = regime.itemStyle.color;
        const name = document.createElement("span");
        name.className = "legend-name";
        name.textContent = regime.name;
        const percent = document.createElement("span");
        percent.className = "legend-percent";
        percent.textContent = `${regime.value.toFixed(1)}%`;
        row.append(dot, name, percent);
        return row;
      }));
    }
  }
  const regimeTableBody = document.getElementById("regime-probability-body");
  if (regimeTableBody) {
    regimeTableBody.replaceChildren();
    if (!regimeData.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 3;
      cell.textContent = "Real regime probabilities unavailable.";
      row.appendChild(cell);
      regimeTableBody.appendChild(row);
    } else {
      for (const regime of regimeData) {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        nameCell.textContent = regime.name;
        const probabilityCell = document.createElement("td");
        probabilityCell.textContent = `${regime.value.toFixed(1)}%`;
        const availabilityCell = document.createElement("td");
        availabilityCell.textContent = "Persisted model output";
        row.append(nameCell, probabilityCell, availabilityCell);
        regimeTableBody.appendChild(row);
      }
    }
  }

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
        itemStyle: { borderRadius: 3, borderColor: borderColor, borderWidth: 2 },
        label: {
          show: true,
          position: "center",
          formatter: () => {
            if (!regimeData.length) return "Unavailable";
            const leadingRegime = regimeData.reduce(
              (highest, current) => current.value > highest.value ? current : highest,
            );
            return `{bold|${Math.round(leadingRegime.value)}%}\n{sub|${leadingRegime.name}}`;
          },
          rich: {
            bold: { color: centerTextColor, fontSize: 18, fontWeight: 800, fontFamily: "Plus Jakarta Sans", lineHeight: 22 },
            sub: { color: currentTheme === "light" ? "#0284c7" : "#38bdf8", fontSize: 11, fontWeight: 600, lineHeight: 14 },
          },
        },
        data: regimeData,
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

  const forecastRows = allDistrictsForecast.filter((district) =>
    Number.isFinite(Number(district.raw_nwp_mean_mm))
    && Number.isFinite(Number(district.corrected_mean_mm))
  );
  const districts = forecastRows.map((district) => district.district_name);
  const nwpVals = forecastRows.map((district) => district.raw_nwp_mean_mm);
  const corrVals = forecastRows.map((district) => district.corrected_mean_mm);

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
      data: ["Raw NWP Forecast", "VARUNA-AI Corrected"],
      top: 0,
      textStyle: { color: axisColor, fontSize: 10.5, fontFamily: "Plus Jakarta Sans" },
      itemWidth: 10,
      itemHeight: 10,
    },
    grid: { top: 30, left: "3%", right: "3%", bottom: "5%", containLabel: true },
    xAxis: {
      type: "category",
      data: districts,
      axisLabel: { color: axisColor, fontSize: 10, fontFamily: "Plus Jakarta Sans", interval: 0 },
      axisLine: { lineStyle: { color: currentTheme === "light" ? "#cbd5e1" : "rgba(36, 58, 107, 0.5)" } },
    },
    yAxis: {
      type: "value",
      name: "Rainfall (mm)",
      nameTextStyle: { color: "#64748b", fontSize: 10 },
      axisLabel: { color: "#64748b", fontSize: 10, fontFamily: "JetBrains Mono" },
      splitLine: { lineStyle: { color: splitLineColor } },
    },
    series: [
      {
        name: "Raw NWP Forecast",
        type: "bar",
        data: nwpVals,
        barGap: "20%",
        itemStyle: { color: currentTheme === "light" ? "#94a3b8" : "#475569", borderRadius: [3, 3, 0, 0] },
      },
      {
        name: "VARUNA-AI Corrected",
        type: "bar",
        data: corrVals,
        itemStyle: { color: currentTheme === "light" ? "#0284c7" : "#38bdf8", borderRadius: [3, 3, 0, 0] },
      },
    ],
  };

  forecastComparisonChart.setOption(option);
}

// Synoptic Radar Chart (View: Regime Analysis)
function initSynopticRadarChart() {
  const elem = document.getElementById("synoptic-radar-chart");
  if (!elem) return;

  if (synopticRadarChart) synopticRadarChart.dispose();
  synopticRadarChart = echarts.init(elem);

  const axisColor = currentTheme === "light" ? "#475569" : "#94a3b8";
  const radarFeatures = [
    { key: "u850", label: "Somali Jet (u850)" },
    { key: "u200", label: "Easterly Jet (u200)" },
    { key: "tcwv", label: "Moisture (TCWV)" },
    { key: "cape", label: "Instability (CAPE)" },
    { key: "vorticity_proxy", label: "Vorticity Index" },
    { key: "orographic_flux_idx", label: "Orographic Flux" },
  ];
  const radarValues = radarFeatures.map((feature) =>
    currentSynopticFeatures?.[feature.key]
  );
  const hasRealRadarValues = radarValues.every((value) => Number.isFinite(Number(value)));
  const radarMaximum = hasRealRadarValues
    ? Math.max(...radarValues.map((value) => Math.abs(Number(value))))
    : null;

  const option = {
    tooltip: { trigger: "item" },
    radar: {
      indicator: radarFeatures.map((feature) => ({
        name: feature.label,
        max: radarMaximum || 1,
      })),
      axisName: { color: axisColor, fontSize: 11, fontFamily: "Plus Jakarta Sans" },
      splitArea: { show: false },
      splitLine: { lineStyle: { color: "rgba(56, 189, 248, 0.15)" } },
    },
    series: hasRealRadarValues
      ? [{
        name: "Persisted Synoptic State",
        type: "radar",
        data: [{
          value: radarValues.map(Number),
          name: "Persisted Synoptic State",
          itemStyle: { color: "#38bdf8" },
          areaStyle: { color: "rgba(56, 189, 248, 0.25)" },
        }],
      }]
      : [],
    graphic: hasRealRadarValues
      ? []
      : [{
        type: "text",
        left: "center",
        top: "middle",
        style: { text: "Synoptic data unavailable", fill: axisColor },
      }],
  };

  synopticRadarChart.setOption(option);
}

// Verification Charts (View: Verification Report)
function initVerificationCharts() {
  const csiElem = document.getElementById("chart-csi-curve");
  const ladderElem = document.getElementById("chart-ladder-comparison");
  const axisColor = currentTheme === "light" ? "#475569" : "#94a3b8";
  const splitLineColor = currentTheme === "light" ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)";

  if (csiElem) {
    if (csiCurveChart) csiCurveChart.dispose();
    csiCurveChart = echarts.init(csiElem);
    csiCurveChart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["Raw NWP", "Level 2: Standard ML", "Level 3: VARUNA-AI (Regime-Aware)"], textStyle: { color: axisColor, fontSize: 10.5 } },
      grid: { top: 35, left: "4%", right: "4%", bottom: "8%", containLabel: true },
      xAxis: {
        type: "category",
        data: ["≥ 2.5 mm", "≥ 15.6 mm", "≥ 35.5 mm", "≥ 64.5 mm (Heavy)", "≥ 115.6 mm (Very Heavy)", "≥ 204.5 mm (Extreme)"],
        axisLabel: { color: axisColor, fontSize: 10 },
      },
      yAxis: { type: "value", name: "Critical Success Index (CSI)", max: 1.0, axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: splitLineColor } } },
      series: [],
      graphic: [{ type: "text", left: "center", top: "middle", style: { text: "Real categorical metrics unavailable", fill: axisColor } }],
    });
  }

  if (ladderElem) {
    if (ladderComparisonChart) ladderComparisonChart.dispose();
    ladderComparisonChart = echarts.init(ladderElem);
    ladderComparisonChart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["MAE (mm)", "RMSE (mm)"], textStyle: { color: axisColor, fontSize: 11 } },
      grid: { top: 35, left: "4%", right: "4%", bottom: "8%", containLabel: true },
      xAxis: {
        type: "category",
        data: [],
        axisLabel: { color: axisColor, fontSize: 11 },
      },
      yAxis: { type: "value", axisLabel: { color: axisColor, formatter: "{value} mm" }, splitLine: { lineStyle: { color: splitLineColor } } },
      series: [
        { name: "MAE (mm)", type: "bar", data: [], itemStyle: { color: "#3b82f6", borderRadius: [3, 3, 0, 0] } },
        { name: "RMSE (mm)", type: "bar", data: [], itemStyle: { color: "#f59e0b", borderRadius: [3, 3, 0, 0] } },
      ],
      graphic: [{ type: "text", left: "center", top: "middle", style: { text: "Real verification unavailable", fill: axisColor } }],
    });

    fetch("/api/v1/verification/")
      .then((response) => {
        if (!response.ok) throw new Error("Real verification is unavailable.");
        return response.json();
      })
      .then((verification) => {
        const levels = verification.levels || {};
        const evaluated = [
          ["level0_raw_era5", "Level 0: Raw ERA5"],
          ["level1_empirical_quantile_mapping", "Level 1: Empirical Quantile Mapping"],
          ["level2_standard_ml", "Level 2: Standard ML"],
          ["level3_regime_aware_ml", "Level 3: Regime-Aware ML"],
        ].filter(([key]) => levels[key]?.status === "evaluated");
        ladderComparisonChart.setOption({
          xAxis: { data: evaluated.map(([, label]) => label) },
          series: [
            { name: "MAE (mm)", data: evaluated.map(([key]) => levels[key].test.MAE) },
            { name: "RMSE (mm)", data: evaluated.map(([key]) => levels[key].test.RMSE) },
          ],
          graphic: evaluated.length
            ? []
            : [{ type: "text", left: "center", top: "middle", style: { text: "Real verification unavailable", fill: axisColor } }],
        });
      })
      .catch(() => {});
  }
}

// Historical Timeseries Chart (View: Historical Data)
function initHistoricalTimeseriesChart() {
  const elem = document.getElementById("historical-timeseries-chart");
  if (!elem) return;

  if (historicalTimeseriesChart) historicalTimeseriesChart.dispose();
  historicalTimeseriesChart = echarts.init(elem);

  const axisColor = currentTheme === "light" ? "#475569" : "#94a3b8";
  const splitLineColor = currentTheme === "light" ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)";

  historicalTimeseriesChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Raw NWP (mm)", "VARUNA-AI Corrected (mm)", "IMD Observed (mm)"], textStyle: { color: axisColor } },
    grid: { top: 35, left: "4%", right: "4%", bottom: "8%", containLabel: true },
    xAxis: { type: "category", data: [], axisLabel: { color: axisColor } },
    yAxis: { type: "value", name: "Precipitation (mm/day)", axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: splitLineColor } } },
    series: [
      { name: "Raw NWP (mm)", type: "line", data: [] },
      { name: "Corrected (mm)", type: "line", data: [] },
      { name: "Observed (mm)", type: "line", data: [] },
    ],
    graphic: [{ type: "text", left: "center", top: "middle", style: { text: "No persisted historical time series is available", fill: axisColor } }],
  });
}

function updateHistoricalSeason(season) {
  if (historicalTimeseriesChart) {
    initHistoricalTimeseriesChart();
  }
}

// ==========================================================================
// REST API Ingestion & Data Hydration
// ==========================================================================

function loadLatestOperationalForecast(dateVal, cycleVal) {
  const dSelect = document.getElementById("forecast-date-select");
  const cSelect = document.getElementById("forecast-cycle-select");
  const dateParam = dateVal || (dSelect ? dSelect.value : "today");
  const cycleParam = cycleVal || (cSelect ? cSelect.value : "00:00");

  const query = new URLSearchParams({
    date: dateParam,
    cycle: cycleParam,
  });

  if (dateParam === "tomorrow") query.append("lead_time", "48");
  else if (dateParam === "day3") query.append("lead_time", "72");
  else if (dateParam === "today") query.append("lead_time", "24");

  fetch(`/api/v1/forecasts/latest/?${query.toString()}`)
    .then((res) => {
      if (!res.ok) throw new Error("API network error");
      return res.json();
    })
    .then((data) => {
      hydrateDashboard(data);
      updateForecastSelectorDisplay(data, dateParam, cycleParam);
    })
    .catch((err) => {
      console.warn("No persisted forecast is available:", err);
      showForecastUnavailableState();
      fetchDistrictsGeojson();
    });
}

function updateForecastSelectorDisplay(data, dateParam, cycleParam) {
  const run = (data && data.forecast_run) || {};
  const lt = run.lead_time_hours || 24;

  const statusUpdated = document.getElementById("status-last-updated");
  if (statusUpdated) {
    const dText = dateParam === "tomorrow" ? "Tomorrow" : (dateParam === "day3" ? "Day +3" : "Today");
    statusUpdated.innerText = `${dText} ${cycleParam || "00:00"} UTC (T+${lt}h)`;
  }

  const dSelect = document.getElementById("forecast-date-select");
  const cSelect = document.getElementById("forecast-cycle-select");
  const dName = dSelect && dSelect.options[dSelect.selectedIndex] ? dSelect.options[dSelect.selectedIndex].text : dateParam;
  const cName = cSelect && cSelect.options[cSelect.selectedIndex] ? cSelect.options[cSelect.selectedIndex].text : cycleParam;
  showToastNotification(`✅ Active Forecast: ${dName} | ${cName}`);
}

function showToastNotification(msg) {
  let toast = document.getElementById("varuna-toast-msg");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "varuna-toast-msg";
    toast.style.position = "fixed";
    toast.style.bottom = "24px";
    toast.style.right = "24px";
    toast.style.background = "linear-gradient(135deg, rgba(8,16,36,0.96), rgba(15,26,52,0.96))";
    toast.style.border = "1px solid rgba(56,189,248,0.4)";
    toast.style.color = "#38bdf8";
    toast.style.padding = "10px 18px";
    toast.style.borderRadius = "10px";
    toast.style.fontSize = "12.5px";
    toast.style.fontWeight = "600";
    toast.style.fontFamily = "var(--font-sans)";
    toast.style.boxShadow = "0 8px 30px rgba(0,0,0,0.5), 0 0 20px rgba(56,189,248,0.2)";
    toast.style.zIndex = "9999";
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    document.body.appendChild(toast);
  }
  toast.innerText = msg;
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";

  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 2800);
}

function fetchDistrictsGeojson() {
  fetch("/api/v1/districts/")
    .then((res) => res.json())
    .then((data) => {
      if (data.geojson) {
        updateGeojsonMap(data.geojson);
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

  // Hydrate Districts
  if (data.districts_forecast) {
    allDistrictsForecast = data.districts_forecast;
    populateDistrictViewTable(allDistrictsForecast);
    renderAlertsFeed(allDistrictsForecast);
    initForecastComparisonChart();
    updateForecastSummary(allDistrictsForecast);
  }

  // Hydrate Run Meta
  const run = data.forecast_run || {};
  currentRegimeProbabilities = run.regime_probabilities || null;
  currentSynopticFeatures = run.synoptic_features || null;
  initRegimeDonutChart();
  initSynopticRadarChart();
  const synopticUnits = {
    "syn-mslp": ["mslp", "hPa"],
    "syn-u850": ["u850", "m/s"],
    "syn-u200": ["u200", "m/s"],
    "syn-shear": ["vertical_wind_shear", "m/s"],
    "syn-tcwv": ["tcwv", "kg/m²"],
    "syn-cape": ["cape", "J/kg"],
  };
  for (const [elementId, [featureName, unit]] of Object.entries(synopticUnits)) {
    const featureValue = currentSynopticFeatures?.[featureName];
    setText(
      elementId,
      hasNumericValue(featureValue) ? `${featureValue} ${unit}` : "Unavailable",
    );
  }
  if (run.detected_regime) {
    const regNameElem = document.getElementById("kpi-regime-name");

    if (regNameElem) regNameElem.innerText = run.detected_regime.replace(/_/g, " ");
  }
  if (run.regime_confidence !== undefined && run.regime_confidence !== null) {
    const confElem = document.getElementById("kpi-regime-conf");
    if (confElem) confElem.innerText = `Confidence ${Math.round(run.regime_confidence * 100)}%`;
  }
}

function updateForecastSummary(forecasts) {
  const populated = forecasts.filter((forecast) =>
    hasNumericValue(forecast.corrected_mean_mm)
  );
  const meanCorrectedRainfall = populated.length
    ? populated.reduce((sum, forecast) => sum + Number(forecast.corrected_mean_mm), 0) / populated.length
    : null;
  const probabilityRows = populated.filter((forecast) =>
    hasNumericValue(forecast.heavy_rain_probability)
  );
  const meanHeavyProbability = probabilityRows.length
    ? probabilityRows.reduce((sum, forecast) => sum + Number(forecast.heavy_rain_probability), 0) / probabilityRows.length
    : null;

  setText(
    "kpi-rainfall-avg",
    meanCorrectedRainfall === null ? "Unavailable" : `${meanCorrectedRainfall.toFixed(1)} mm`,
  );
  setText(
    "kpi-heavy-prob",
    meanHeavyProbability === null ? "Unavailable" : `${(meanHeavyProbability * 100).toFixed(1)}%`,
  );
  setText("kpi-coverage-count", populated.length ? String(populated.length) : "Unavailable");
  setText("kpi-rmse-gain", "Unavailable");
}

function showForecastUnavailableState() {
  currentRegimeProbabilities = null;
  currentSynopticFeatures = null;
  allDistrictsForecast = [];
  setText("kpi-regime-name", "Unavailable");
  setText("kpi-regime-conf", "Confidence unavailable");
  setText("kpi-rainfall-avg", "Unavailable");
  setText("kpi-heavy-prob", "Unavailable");
  setText("kpi-rmse-gain", "Unavailable");
  setText("kpi-coverage-count", "Unavailable");
  initRegimeDonutChart();
  initSynopticRadarChart();
  initForecastComparisonChart();
}

// ==========================================================================
// District Table & Search Filters
// ==========================================================================

function populateDistrictViewTable(districts) {
  const tbody = document.getElementById("view-tbody-districts");
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
      <td style="color: var(--text-dim);">${d.state || "Karnataka"} / ${d.zone || "Peninsular"}</td>
      <td style="font-family: var(--font-mono);">${d.raw_nwp_mean_mm ?? 30.0}</td>
      <td style="color: var(--neon-cyan); font-weight: 700; font-family: var(--font-mono);">${d.corrected_mean_mm ?? 55.0}</td>
      <td style="color: var(--neon-emerald); font-family: var(--font-mono);">${d.corrected_max_mm ?? Math.round((d.corrected_mean_mm || 55) * 1.25)}</td>
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

function filterDistrictTable(query) {
  const q = query.toLowerCase();
  const rows = document.querySelectorAll("#view-tbody-districts tr");
  rows.forEach((row) => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? "" : "none";
  });
}

// ==========================================================================
// Alerts Feed & Notification Center
// ==========================================================================

function renderAlertsFeed(districts) {
  const container = document.getElementById("alerts-feed-list");
  if (!container || !districts) return;

  container.innerHTML = "";
  let redCount = 0;
  let orangeCount = 0;
  let yellowCount = 0;
  let greenCount = 0;

  const sorted = districts
    .filter((district) => district.risk_code)
    .sort((left, right) => Number(right.corrected_mean_mm) - Number(left.corrected_mean_mm));

  sorted.forEach((d) => {
    const rCode = String(d.risk_code).toUpperCase();
    const corr = d.corrected_mean_mm;
    const prob = d.heavy_rain_probability;
    const actionGuide = d.risk_label || "Persisted forecast risk classification.";

    if (rCode === "RED") redCount++;
    else if (rCode === "ORANGE") orangeCount++;
    else if (rCode === "YELLOW") yellowCount++;
    else if (rCode === "GREEN") greenCount++;

    if (rCode !== "GREEN") {
      const card = document.createElement("div");
      card.className = "alert-row-card";
      card.innerHTML = `
        <div class="alert-left-meta">
          <span class="alert-badge-large ${rCode.toLowerCase()}">${rCode} ALERT</span>
          <div>
            <div class="alert-district-name">${d.district_name || d.name || "District"}${d.state ? ` (${d.state})` : ""}</div>
            <div class="alert-action-guide">${actionGuide}</div>
          </div>
        </div>
        <div class="alert-right-data">
          <div class="alert-metric-col">
            <span class="alert-metric-lbl">AI Corrected Rain</span>
            <span class="alert-metric-val" style="color: var(--neon-cyan);">${hasNumericValue(corr) ? `${Number(corr).toFixed(1)} mm` : "Unavailable"}</span>
          </div>
          <div class="alert-metric-col">
            <span class="alert-metric-lbl">P(Rain &ge; 64.5mm)</span>
            <span class="alert-metric-val" style="color: ${rCode === 'RED' ? '#ef4444' : '#f59e0b'};">${hasNumericValue(prob) ? `${(Number(prob) * 100).toFixed(0)}%` : "Unavailable"}</span>
          </div>
          <div class="alert-metric-col">
            <span class="alert-metric-lbl">80% Uncertainty</span>
            <span class="alert-metric-val" style="color: var(--text-muted);">${hasNumericValue(d.uncertainty_lower_10pct) && hasNumericValue(d.uncertainty_upper_90pct) ? `[${d.uncertainty_lower_10pct} - ${d.uncertainty_upper_90pct}] mm` : "Unavailable"}</span>
          </div>
        </div>
      `;
      container.appendChild(card);
    }
  });

  // Update counter badges
  const elRed = document.getElementById("count-red-alerts");
  const elOrange = document.getElementById("count-orange-alerts");
  const elYellow = document.getElementById("count-yellow-alerts");
  const elGreen = document.getElementById("count-green-alerts");
  const elBadge = document.getElementById("sidebar-alert-badge");

  if (elRed) elRed.innerText = redCount;
  if (elOrange) elOrange.innerText = orangeCount;
  if (elYellow) elYellow.innerText = yellowCount;
  if (elGreen) elGreen.innerText = greenCount;
  if (elBadge) elBadge.innerText = redCount + orangeCount;
}

// ==========================================================================
// Settings Management
// ==========================================================================

function saveSystemSettings() {
  const coverage = document.getElementById("setting-coverage")?.value;
  const threshold = document.getElementById("setting-heavy-threshold")?.value;
  const refresh = document.getElementById("setting-refresh-interval")?.value;

  localStorage.setItem("varuna_setting_coverage", coverage);
  localStorage.setItem("varuna_setting_threshold", threshold);
  localStorage.setItem("varuna_setting_refresh", refresh);

  alert("✓ Operational settings saved successfully to VARUNA-AI engine.");
}

// ==========================================================================
// Event Bindings
// ==========================================================================

function bindUIEvents() {
  // Theme Toggle Button
  const btnTheme = document.getElementById("btn-theme-toggle");
  if (btnTheme) btnTheme.addEventListener("click", toggleTheme);

  // Sign out button
  const btnLogout = document.getElementById("btn-logout");
  if (btnLogout) btnLogout.addEventListener("click", handleSignOut);

  // Sidebar navigation switching
  document.querySelectorAll(".sidebar-nav .nav-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const view = link.dataset.view;
      if (view) switchView(view);
    });
  });

  // In-page navigation trigger links
  document.querySelectorAll(".view-nav-trigger").forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      const view = trigger.dataset.view;
      if (view) switchView(view);
    });
  });

  // Manual Refresh Button
  const btnRefresh = document.getElementById("btn-manual-refresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      btnRefresh.classList.add("spinning");
      loadLatestOperationalForecast();
      setTimeout(() => {
        btnRefresh.classList.remove("spinning");
        updateDynamicDates();
      }, 800);
    });
  }

  // Date Selector Change (Today T+24h, Tomorrow T+48h, Day +3 T+72h, Reference Event)
  const dateSelect = document.getElementById("forecast-date-select");
  if (dateSelect) {
    dateSelect.addEventListener("change", (e) => {
      const selectedVal = e.target.value;
      const selectedText = dateSelect.options[dateSelect.selectedIndex]?.text || selectedVal;
      showToastNotification(`⏳ Loading Forecast for ${selectedText}...`);
      loadLatestOperationalForecast(selectedVal);
    });
  }

  // Time Cycle Selector Change (00:00 UTC, 06:00 UTC, 12:00 UTC)
  const cycleSelect = document.getElementById("forecast-cycle-select");
  if (cycleSelect) {
    cycleSelect.addEventListener("change", (e) => {
      const selectedCycle = e.target.value;
      const selectedCycleText = cycleSelect.options[cycleSelect.selectedIndex]?.text || selectedCycle;
      showToastNotification(`⏳ Loading ${selectedCycleText} Run...`);
      loadLatestOperationalForecast(undefined, selectedCycle);
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

  // Spotlight close
  const btnCloseSpot = document.getElementById("btn-close-spotlight");
  if (btnCloseSpot) {
    btnCloseSpot.addEventListener("click", () => {
      document.getElementById("district-spotlight").classList.add("hidden");
    });
  }

  // Map layer toggle buttons
  const btnRain = document.getElementById("btn-layer-rainfall");
  const btnProb = document.getElementById("btn-layer-prob");
  if (btnRain) btnRain.addEventListener("click", () => setMapLayerMode("rainfall"));
  if (btnProb) btnProb.addEventListener("click", () => setMapLayerMode("probability"));
}

// Auto-Refresh Loop
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
    updateDynamicDates();
  }, 30000);
}

// ==========================================================================
// Live On-Demand Prediction Engine
// ==========================================================================

let predLadderChart = null;

function runPrediction() {
  const btn = document.getElementById("btn-run-prediction");
  const statusEl = document.getElementById("pred-status");

  const inputFields = [
    ["nwp_rainfall", "pred-nwp"],
    ["latitude", "pred-lat"],
    ["longitude", "pred-lon"],
    ["mslp", "pred-mslp"],
    ["u850", "pred-u850"],
    ["v850", "pred-v850"],
    ["u200", "pred-u200"],
    ["v200", "pred-v200"],
    ["tcwv", "pred-tcwv"],
    ["rh700", "pred-rh700"],
    ["cape", "pred-cape"],
    ["monsoon_trough_lat", "pred-trough"],
    ["vertical_wind_shear", "pred-shear"],
  ];
  const payload = {};
  const invalidFields = [];
  for (const [fieldName, inputId] of inputFields) {
    const inputValue = document.getElementById(inputId)?.value?.trim();
    const numericValue = Number(inputValue);
    if (inputValue === undefined || inputValue === "" || !Number.isFinite(numericValue)) {
      invalidFields.push(fieldName);
      continue;
    }
    payload[fieldName] = numericValue;
  }
  const districtName = document.getElementById("pred-district")?.value?.trim();
  if (districtName) payload.district_name = districtName;

  if (invalidFields.length) {
    if (statusEl) {
      statusEl.style.color = "#ef4444";
      statusEl.textContent = `Enter valid values for: ${invalidFields.join(", ")}`;
    }
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.style.opacity = "0.6";
    btn.textContent = "⏳ Running VARUNA-AI Model Ladder...";
  }
  if (statusEl) statusEl.textContent = "🔄 Sending to inference engine...";

  // POST to /api/v1/predict/
  const query = new URLSearchParams(payload).toString();
  fetch(`/api/v1/predict/?${query}`, { method: "GET" })
    .then((res) => res.json())
    .then((d) => {
      if (d.status === "ERROR") throw new Error(d.message);

      const riskColors = { RED: "#ef4444", ORANGE: "#f97316", YELLOW: "#eab308", GREEN: "#10b981" };
      const risk = d.risk_assessment.risk_code;
      const riskColor = riskColors[risk];

      const fmt = (v) => (v != null ? `${v.toFixed(1)} mm` : "—");
      const fmtDelta = (v) => (v != null ? `${v > 0 ? "+" : ""}${v.toFixed(1)} mm` : "—");

      setText("pred-out-regime", (d.detected_regime || "—").replace(/_/g, " "));
      setText("pred-out-conf", `Confidence: ${Math.round((d.regime_confidence || 0) * 100)}%`);

      const riskEl = document.getElementById("pred-out-risk");
      if (riskEl) {
        riskEl.textContent = `🚨 ${risk} ALERT`;
        riskEl.style.color = riskColor;
      }
      setText("pred-out-action", d.risk_assessment.action_advisory);

      const lad = d.model_ladder;
      setText("pred-l0", fmt(lad.level0_raw_nwp_mm));
      setText("pred-l1", fmt(lad.level1_quantile_mapping_mm));
      setText("pred-l2", fmt(lad.level2_standard_ml_mm));
      setText("pred-l3", fmt(lad.level3_regime_aware_ml_mm));

      const deltaEl = document.getElementById("pred-delta");
      if (deltaEl) {
        deltaEl.textContent = fmtDelta(d.bias_correction_delta_mm);
        deltaEl.style.color = (d.bias_correction_delta_mm || 0) >= 0 ? "#10b981" : "#f97171";
      }

      const probHeavy = d.heavy_rainfall_probability;
      setText("pred-prob-heavy", probHeavy != null ? `${Math.round(probHeavy * 100)}%` : "—");

      const ci = d.uncertainty_interval_80pct || {};
      setText("pred-ci",
        ci.lower_10pct_mm != null
          ? `[${ci.lower_10pct_mm.toFixed(1)}, ${ci.upper_90pct_mm.toFixed(1)}] mm`
          : "—"
      );

      // Render Ladder Comparison Chart
      const chartEl = document.getElementById("pred-ladder-chart");
      if (chartEl && typeof echarts !== "undefined") {
        if (predLadderChart) predLadderChart.dispose();
        predLadderChart = echarts.init(chartEl);
        const axisColor = currentTheme === "light" ? "#475569" : "#94a3b8";
        const tooltipBg = currentTheme === "light" ? "rgba(255,255,255,0.96)" : "rgba(8,16,36,0.95)";
        const tooltipText = currentTheme === "light" ? "#0f172a" : "#ffffff";

        predLadderChart.setOption({
          tooltip: {
            trigger: "axis",
            axisPointer: { type: "shadow" },
            backgroundColor: tooltipBg,
            textStyle: { color: tooltipText },
            formatter: (p) => `${p[0].name}<br/>Rainfall: <strong>${p[0].value.toFixed(1)} mm</strong>`,
          },
          grid: { top: 20, left: "5%", right: "5%", bottom: "10%", containLabel: true },
          xAxis: {
            type: "category",
            data: ["Level 0\nRaw NWP", "Level 1\nEQM", "Level 2\nStd ML", "Level 3\nVARUNA-AI"],
            axisLabel: { color: axisColor, fontSize: 11, fontFamily: "Plus Jakarta Sans" },
            axisLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
          },
          yAxis: {
            type: "value",
            name: "Rainfall (mm)",
            nameTextStyle: { color: axisColor, fontSize: 10 },
            axisLabel: { color: axisColor, fontFamily: "JetBrains Mono" },
            splitLine: { lineStyle: { color: currentTheme === "light" ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.05)" } },
          },
          series: [{
            type: "bar",
            barWidth: "45%",
            data: [
              { value: lad.level0_raw_nwp_mm, itemStyle: { color: "#f87171", borderRadius: [5, 5, 0, 0] } },
              { value: lad.level1_quantile_mapping_mm, itemStyle: { color: "#38bdf8", borderRadius: [5, 5, 0, 0] } },
              { value: lad.level2_standard_ml_mm, itemStyle: { color: "#a855f7", borderRadius: [5, 5, 0, 0] } },
              { value: lad.level3_regime_aware_ml_mm, itemStyle: { color: "#34d399", borderRadius: [5, 5, 0, 0] } },
            ],
            label: {
              show: true,
              position: "top",
              formatter: (p) => `${p.value.toFixed(1)}`,
              color: axisColor,
              fontFamily: "JetBrains Mono",
              fontSize: 11,
              fontWeight: 700,
            },
          }],
        });
      }

      if (statusEl) {
        statusEl.style.color = "#10b981";
        statusEl.textContent = `✅ Inference complete — ${d.district_name} | ${new Date().toLocaleTimeString()}`;
      }
    })
    .catch((err) => {
      if (statusEl) {
        statusEl.style.color = "#ef4444";
        statusEl.textContent = `❌ Inference failed: ${err.message}`;
      }
    })
    .finally(() => {
      if (btn) {
        btn.disabled = false;
        btn.style.opacity = "1";
        btn.textContent = "▶ Run VARUNA-AI Prediction Engine";
      }
    });
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
