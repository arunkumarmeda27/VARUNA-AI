/**
 * VARUNA-AI: Operational Dashboard Frontend Engine
 * Handles Leaflet GIS map rendering, ECharts scientific visualizations, and REST API sync.
 */

let mapInstance = null;
let geojsonLayer = null;
let currentGeojsonData = null;
let currentLayerMode = "corrected"; // "corrected", "nwp", "probability", "risk", "delta"
let regimeChart = null;
let verificationChart = null;
let ladderChart = null;

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initCharts();
  bindEvents();
  loadLatestForecast();
  loadVerificationData();
});

function initMap() {
  // Center over central India
  mapInstance = L.map("map-container", {
    center: [21.5, 79.5],
    zoom: 5,
    minZoom: 4,
    maxZoom: 9,
  });

  // Dark CartoDB basemap for high-contrast scientific overlay
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://carto.com/">CartoDB</a> &copy; OpenStreetMap',
    subdomains: "abcd",
    maxZoom: 19,
  }).addTo(mapInstance);
}

function bindEvents() {
  // Layer switch buttons
  document.querySelectorAll(".map-layer-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".map-layer-btn").forEach((b) => b.classList.remove("active"));
      e.target.classList.add("active");
      currentLayerMode = e.target.dataset.layer;
      updateMapStyle();
      updateMapLegend();
    });
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

      e.target.classList.add("active");
      const targetPaneId = e.target.dataset.tab;
      const pane = document.getElementById(targetPaneId);
      if (pane) pane.classList.add("active");

      // Resize echarts upon tab display
      setTimeout(() => {
        if (verificationChart) verificationChart.resize();
        if (ladderChart) ladderChart.resize();
        if (regimeChart) regimeChart.resize();
      }, 100);
    });
  });

  // Run selection dropdown
  const runSelect = document.getElementById("forecast-run-select");
  if (runSelect) {
    runSelect.addEventListener("change", (e) => {
      loadForecastByRunId(e.target.value);
    });
  }
}

function loadLatestForecast() {
  fetch("/api/v1/forecasts/latest/")
    .then((res) => res.json())
    .then((data) => {
      renderForecastData(data);
    })
    .catch((err) => console.error("Error loading forecast:", err));
}

function loadForecastByRunId(runId) {
  fetch(`/api/v1/forecasts/${runId}/`)
    .then((res) => res.json())
    .then((data) => {
      renderForecastData(data);
    })
    .catch((err) => console.error("Error loading forecast by ID:", err));
}

function renderForecastData(data) {
  if (!data || !data.geojson_layer) return;

  currentGeojsonData = data.geojson_layer;
  updateMapLayer(currentGeojsonData);

  // Update regime probability chart
  const regProbs = data.forecast_run.regime_probabilities || {};
  updateRegimeChart(regProbs, data.forecast_run.detected_regime);

  // Update Synoptic indicators if available
  const syn = data.forecast_run.synoptic_features || {};
  if (document.getElementById("syn-mslp")) document.getElementById("syn-mslp").innerText = (syn.mslp || "--") + " hPa";
  if (document.getElementById("syn-llj")) document.getElementById("syn-llj").innerText = (syn.u850 || "--") + " m/s";
  if (document.getElementById("syn-tej")) document.getElementById("syn-tej").innerText = (syn.u200 || "--") + " m/s";
  if (document.getElementById("syn-shear")) document.getElementById("syn-shear").innerText = (syn.vertical_wind_shear || "--") + " m/s";
  if (document.getElementById("syn-tcwv")) document.getElementById("syn-tcwv").innerText = (syn.tcwv || "--") + " kg/m²";
  if (document.getElementById("syn-trough")) document.getElementById("syn-trough").innerText = (syn.monsoon_trough_lat || "--") + " °N";
}

function updateMapLayer(geojsonData) {
  if (geojsonLayer) {
    mapInstance.removeLayer(geojsonLayer);
  }

  geojsonLayer = L.geoJSON(geojsonData, {
    style: styleFeature,
    onEachFeature: (feature, layer) => {
      const props = feature.properties || {};
      const tooltipContent = `
        <div style="font-family: var(--font-mono); font-size: 11.5px;">
          <strong style="color: #38bdf8; font-size: 13px;">${props.district_name || "District"}</strong> (${props.state || ""})<br/>
          <hr style="border-color: #334d85; margin: 4px 0;"/>
          <strong>VARUNA Corrected:</strong> ${props.corrected_mean_mm ?? "--"} mm (Max: ${props.corrected_max_mm ?? "--"} mm)<br/>
          <strong>Raw NWP:</strong> ${props.raw_nwp_mean_mm ?? "--"} mm<br/>
          <strong>Bias Delta:</strong> <span style="color: ${props.bias_correction_delta_mm >= 0 ? '#34d399' : '#f87171'}">${props.bias_correction_delta_mm > 0 ? '+' : ''}${props.bias_correction_delta_mm ?? '--'} mm</span><br/>
          <strong>P(Rain &ge; 64.5mm):</strong> ${((props.heavy_rain_probability || 0) * 100).toFixed(1)}%<br/>
          <strong>80% Uncertainty:</strong> [${props.uncertainty_lower_10pct ?? "--"} - ${props.uncertainty_upper_90pct ?? "--"}] mm<br/>
          <strong>Risk:</strong> <span class="badge badge-${(props.risk_code || 'green').toLowerCase()}">${props.risk_code || "GREEN"}</span>
        </div>
      `;
      layer.bindTooltip(tooltipContent, { sticky: true, className: "custom-leaflet-tooltip" });

      layer.on("mouseover", (e) => {
        const l = e.target;
        l.setStyle({ weight: 3, color: "#38bdf8", fillOpacity: 0.85 });
      });
      layer.on("mouseout", (e) => {
        geojsonLayer.resetStyle(e.target);
      });
    },
  }).addTo(mapInstance);

  updateMapLegend();
}

function updateMapStyle() {
  if (geojsonLayer) {
    geojsonLayer.setStyle(styleFeature);
  }
}

function styleFeature(feature) {
  const p = feature.properties || {};
  let fillColor = "#334155";

  if (currentLayerMode === "corrected") {
    const val = p.corrected_mean_mm || 0;
    fillColor = getRainfallColor(val);
  } else if (currentLayerMode === "nwp") {
    const val = p.raw_nwp_mean_mm || 0;
    fillColor = getRainfallColor(val);
  } else if (currentLayerMode === "probability") {
    const prob = p.heavy_rain_probability || 0;
    fillColor = getProbabilityColor(prob);
  } else if (currentLayerMode === "risk") {
    const code = (p.risk_code || "GREEN").toUpperCase();
    if (code === "RED") fillColor = "#ef4444";
    else if (code === "ORANGE") fillColor = "#f97316";
    else if (code === "YELLOW") fillColor = "#eab308";
    else fillColor = "#10b981";
  } else if (currentLayerMode === "delta") {
    const delta = p.bias_correction_delta_mm || 0;
    fillColor = getDeltaColor(delta);
  }

  return {
    fillColor: fillColor,
    weight: 1.5,
    opacity: 1,
    color: "#475569",
    fillOpacity: 0.70,
  };
}

function getRainfallColor(val) {
  if (val < 2.5) return "#0284c7";      // Very light
  if (val < 15.6) return "#06b6d4";     // Light-Mod
  if (val < 64.5) return "#10b981";     // Mod-Heavy
  if (val < 115.6) return "#f59e0b";    // Heavy
  if (val < 204.5) return "#ea580c";    // Very Heavy
  return "#dc2626";                     // Extremely Heavy
}

function getProbabilityColor(prob) {
  if (prob < 0.20) return "#1e293b";
  if (prob < 0.40) return "#0369a1";
  if (prob < 0.60) return "#0d9488";
  if (prob < 0.80) return "#f59e0b";
  return "#e11d48";
}

function getDeltaColor(delta) {
  if (delta > 20) return "#059669";
  if (delta > 5) return "#10b981";
  if (delta >= -5) return "#475569";
  if (delta >= -20) return "#f97316";
  return "#ef4444";
}

function updateMapLegend() {
  const legendBox = document.getElementById("map-legend-content");
  if (!legendBox) return;

  if (currentLayerMode === "corrected" || currentLayerMode === "nwp") {
    legendBox.innerHTML = `
      <span>Precipitation (mm/24h):</span>
      <div class="legend-scale">
        <span class="legend-color-box" style="background:#0284c7"></span> &lt;2.5
        <span class="legend-color-box" style="background:#06b6d4"></span> 2.5-15.6
        <span class="legend-color-box" style="background:#10b981"></span> 15.6-64.5
        <span class="legend-color-box" style="background:#f59e0b"></span> 64.5-115.6
        <span class="legend-color-box" style="background:#ea580c"></span> 115.6-204.5
        <span class="legend-color-box" style="background:#dc2626"></span> &ge;204.5
      </div>
    `;
  } else if (currentLayerMode === "probability") {
    legendBox.innerHTML = `
      <span>P(Rain &ge; 64.5mm):</span>
      <div class="legend-scale">
        <span class="legend-color-box" style="background:#1e293b"></span> &lt;20%
        <span class="legend-color-box" style="background:#0369a1"></span> 20-40%
        <span class="legend-color-box" style="background:#0d9488"></span> 40-60%
        <span class="legend-color-box" style="background:#f59e0b"></span> 60-80%
        <span class="legend-color-box" style="background:#e11d48"></span> &ge;80%
      </div>
    `;
  } else if (currentLayerMode === "risk") {
    legendBox.innerHTML = `
      <span>IMD Alert Code:</span>
      <div class="legend-scale">
        <span class="legend-color-box" style="background:#10b981"></span> Green (No Warning)
        <span class="legend-color-box" style="background:#eab308"></span> Yellow (Watch)
        <span class="legend-color-box" style="background:#f97316"></span> Orange (Alert)
        <span class="legend-color-box" style="background:#ef4444"></span> Red (Warning)
      </div>
    `;
  } else {
    legendBox.innerHTML = `
      <span>Bias Correction Delta (mm):</span>
      <div class="legend-scale">
        <span class="legend-color-box" style="background:#ef4444"></span> Underforecasted Raw
        <span class="legend-color-box" style="background:#475569"></span> Minimal Shift
        <span class="legend-color-box" style="background:#059669"></span> Enhanced Convective Peak
      </div>
    `;
  }
}

function initCharts() {
  const regElem = document.getElementById("regime-chart-container");
  if (regElem) {
    regimeChart = echarts.init(regElem);
  }

  const verifElem = document.getElementById("verification-chart-container");
  if (verifElem) {
    verificationChart = echarts.init(verifElem);
  }

  const ladderElem = document.getElementById("ladder-chart-container");
  if (ladderElem) {
    ladderChart = echarts.init(ladderElem);
  }
}

function updateRegimeChart(probDict, activeRegime) {
  if (!regimeChart) return;

  const regimes = Object.keys(probDict);
  const values = regimes.map((r) => (probDict[r] * 100).toFixed(1));

  const option = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, formatter: "{b}: {c}%" },
    grid: { top: "10%", left: "3%", right: "8%", bottom: "5%", containLabel: true },
    xAxis: {
      type: "value",
      max: 100,
      axisLabel: { color: "#94a3b8", formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#1e293b" } },
    },
    yAxis: {
      type: "category",
      data: regimes.map(r => r.replace(/_/g, " ")),
      axisLabel: { color: "#e2e8f0", fontSize: 11 },
      axisLine: { lineStyle: { color: "#334d85" } },
    },
    series: [
      {
        name: "Probability",
        type: "bar",
        data: values,
        itemStyle: {
          color: (params) => {
            const rawReg = regimes[params.dataIndex];
            return rawReg.toUpperCase() === (activeRegime || "").toUpperCase().replace(/ /g, "_")
              ? "#38bdf8"
              : "#334d85";
          },
          borderRadius: [0, 4, 4, 0],
        },
      },
    ],
  };

  regimeChart.setOption(option);
}

function loadVerificationData() {
  fetch("/api/v1/verification/")
    .then((res) => res.json())
    .then((data) => {
      renderVerificationCharts(data);
    })
    .catch((err) => console.error("Error loading verification benchmarks:", err));
}

function renderVerificationCharts(vData) {
  if (!vData || !vData.categorical_metrics) return;

  // 1. Categorical CSI vs Threshold Chart
  const thresholds = [2.5, 15.6, 64.5, 115.6, 204.5];
  const cats = vData.categorical_metrics;

  const rawNwpCSI = thresholds.map((t) => {
    const item = cats.find((c) => c.Threshold_mm === t && c.Model === "Raw_NWP");
    return item ? item.CSI : 0;
  });

  const varunaCSI = thresholds.map((t) => {
    const item = cats.find((c) => c.Threshold_mm === t && c.Model.includes("VARUNA"));
    return item ? item.CSI : 0;
  });

  if (verificationChart) {
    const verifOption = {
      title: { text: "Critical Success Index (CSI / Threat Score)", textStyle: { color: "#e2e8f0", fontSize: 13 } },
      tooltip: { trigger: "axis" },
      legend: { data: ["Raw NWP", "VARUNA-AI (Regime-Aware)"], textStyle: { color: "#94a3b8" }, right: 10 },
      grid: { top: "20%", left: "4%", right: "4%", bottom: "10%", containLabel: true },
      xAxis: {
        type: "category",
        data: thresholds.map((t) => `≥ ${t} mm`),
        axisLabel: { color: "#94a3b8" },
        axisLine: { lineStyle: { color: "#334d85" } },
      },
      yAxis: {
        type: "value",
        max: 1.0,
        axisLabel: { color: "#94a3b8" },
        splitLine: { lineStyle: { color: "#1e293b" } },
      },
      series: [
        {
          name: "Raw NWP",
          type: "line",
          data: rawNwpCSI,
          itemStyle: { color: "#f87171" },
          lineStyle: { width: 2, type: "dashed" },
        },
        {
          name: "VARUNA-AI (Regime-Aware)",
          type: "line",
          data: varunaCSI,
          itemStyle: { color: "#38bdf8" },
          lineStyle: { width: 3 },
          areaStyle: { color: "rgba(56, 189, 248, 0.15)" },
        },
      ],
    };
    verificationChart.setOption(verifOption);
  }

  // 2. Model Ladder Continuous Error Comparison
  if (ladderChart && vData.continuous_metrics) {
    const cm = vData.continuous_metrics;
    const ladderModels = ["Raw NWP", "Level 1 EQM", "Level 2 Std ML", "Level 3 VARUNA"];
    const maeData = [
      cm.Raw_NWP?.MAE || 8.76,
      cm.Level1_Quantile_Mapping?.MAE || 5.71,
      cm.Level2_Standard_ML?.MAE || 5.40,
      cm.VARUNA_AI_Level3_Regime_Aware?.MAE || 5.42,
    ];
    const rmseData = [
      cm.Raw_NWP?.RMSE || 16.89,
      cm.Level1_Quantile_Mapping?.RMSE || 8.96,
      cm.Level2_Standard_ML?.RMSE || 9.68,
      cm.VARUNA_AI_Level3_Regime_Aware?.RMSE || 9.98,
    ];

    const ladderOption = {
      title: { text: "Model Ladder Continuous Error (MAE & RMSE)", textStyle: { color: "#e2e8f0", fontSize: 13 } },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: { data: ["MAE (mm)", "RMSE (mm)"], textStyle: { color: "#94a3b8" }, right: 10 },
      grid: { top: "20%", left: "4%", right: "4%", bottom: "10%", containLabel: true },
      xAxis: {
        type: "category",
        data: ladderModels,
        axisLabel: { color: "#94a3b8" },
        axisLine: { lineStyle: { color: "#334d85" } },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#94a3b8", formatter: "{value} mm" },
        splitLine: { lineStyle: { color: "#1e293b" } },
      },
      series: [
        {
          name: "MAE (mm)",
          type: "bar",
          data: maeData,
          itemStyle: { color: "#3b82f6" },
        },
        {
          name: "RMSE (mm)",
          type: "bar",
          data: rmseData,
          itemStyle: { color: "#f59e0b" },
        },
      ],
    };
    ladderChart.setOption(ladderOption);
  }
}
