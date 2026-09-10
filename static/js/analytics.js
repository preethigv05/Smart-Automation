/**
 * Predictive Analytics Controller
 * Smart Resource Intelligence & Automation Platform (SIH 2026)
 */

let forecastChartInstance = null;
let comparativeChartInstance = null;
let allocationChartInstance = null;

async function loadAnalytics() {
  const resSelect = document.getElementById('analytics-resource-select');
  const horizonSelect = document.getElementById('analytics-horizon-select');

  const selectedResId = resSelect.value;
  const horizon = horizonSelect.value || 24;

  let url = `/api/analytics?horizon=${horizon}`;
  if (selectedResId) {
    url += `&resource_id=${selectedResId}`;
  }

  try {
    const res = await fetch(url);
    const data = await res.json();

    // Populate dropdown if first time
    if (resSelect.options.length <= 1) {
      resSelect.innerHTML = (data.resources || []).map(r => `
        <option value="${r.id}" ${r.id === data.selected_resource_id ? 'selected' : ''}>
          ${r.name} (${r.unit})
        </option>
      `).join('');
    }

    // 1. Update Forecast KPI Summary
    const f = data.forecast;
    const histVals = f.historical_values || [];
    const predVals = f.predicted_values || [];

    const currentLoad = histVals.length ? histVals[histVals.length - 1] : 0;
    const maxPred = predVals.length ? Math.max(...predVals) : 0;
    const minPred = predVals.length ? Math.min(...predVals) : 0;
    const maxPredIdx = predVals.indexOf(maxPred);
    const peakTime = maxPredIdx >= 0 ? f.future_timestamps[maxPredIdx] : '--';

    document.getElementById('kpi-current-load').textContent = currentLoad;
    document.getElementById('kpi-current-unit').textContent = `${f.unit || ''} (Current Telemetry)`;
    document.getElementById('kpi-projected-peak').textContent = maxPred;
    document.getElementById('kpi-peak-time').textContent = `Est. peak: ${peakTime}`;
    document.getElementById('kpi-projected-low').textContent = minPred;

    // 2. Render Main Forecast Time-Series Chart
    renderForecastChart(f);

    // 3. Render Comparative Utilization Matrix
    renderComparativeChart(data.comparisons || []);

    // 4. Render Allocation Pie Chart
    renderAllocationPie(data.resources || []);

  } catch(err) {
    console.error('Analytics load error:', err);
    showToast('Failed to load predictive analytics', 'danger');
  }
}

function renderForecastChart(f) {
  const ctx = document.getElementById('forecastChart');
  if (!ctx) return;

  const histTimes = f.historical_timestamps || [];
  const histVals = f.historical_values || [];
  const futTimes = f.future_timestamps || [];
  const predVals = f.predicted_values || [];
  const upper = f.upper_bound || [];
  const lower = f.lower_bound || [];

  const allLabels = [...histTimes, ...futTimes];

  // Align historical with nulls for future
  const histData = [...histVals, ...new Array(futTimes.length).fill(null)];

  // Align future forecast starting from last historical point
  const lastHistVal = histVals.length ? histVals[histVals.length - 1] : null;
  const predData = new Array(histVals.length - 1).fill(null).concat([lastHistVal, ...predVals]);
  const upperData = new Array(histVals.length - 1).fill(null).concat([lastHistVal, ...upper]);
  const lowerData = new Array(histVals.length - 1).fill(null).concat([lastHistVal, ...lower]);

  if (forecastChartInstance) {
    forecastChartInstance.destroy();
  }

  forecastChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical Actuals',
          data: histData,
          borderColor: '#2563eb',
          backgroundColor: '#2563eb',
          borderWidth: 2.5,
          tension: 0.3,
          pointRadius: 2,
          pointHoverRadius: 5
        },
        {
          label: 'AI Forecast Trajectory',
          data: predData,
          borderColor: '#ef4444',
          backgroundColor: '#ef4444',
          borderWidth: 2.5,
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '95% Confidence Upper Bound',
          data: upperData,
          borderColor: 'transparent',
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          fill: '+1',
          pointRadius: 0
        },
        {
          label: '95% Confidence Lower Bound',
          data: lowerData,
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            maxTicksLimit: 12,
            font: { size: 10 }
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          title: {
            display: true,
            text: f.unit || 'Units'
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            filter: (item) => !item.text.includes('Confidence')
          }
        }
      }
    }
  });
}

function renderComparativeChart(comparisons) {
  const ctx = document.getElementById('comparativeUtilChart');
  if (!ctx) return;

  const labels = comparisons.map(c => c.name);
  const currentPcts = comparisons.map(c => c.current_pct);
  const avg24hPcts = comparisons.map(c => c.avg_24h_pct);

  if (comparativeChartInstance) {
    comparativeChartInstance.destroy();
  }

  comparativeChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Current Utilization %',
          data: currentPcts,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        },
        {
          label: '24h Moving Avg %',
          data: avg24hPcts,
          backgroundColor: '#94a3b8',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 } }
        },
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: v => v + '%' }
        }
      }
    }
  });
}

function renderAllocationPie(resources) {
  const ctx = document.getElementById('allocationPieChart');
  if (!ctx) return;

  const labels = resources.map(r => r.name);
  const usages = resources.map(r => r.current_usage);
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899'];

  if (allocationChartInstance) {
    allocationChartInstance.destroy();
  }

  allocationChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: usages,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { boxWidth: 12, font: { size: 10 } }
        }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadAnalytics();

  document.getElementById('analytics-resource-select').addEventListener('change', loadAnalytics);
  document.getElementById('analytics-horizon-select').addEventListener('change', loadAnalytics);
});
