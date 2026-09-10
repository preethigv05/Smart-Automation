/**
 * Dashboard Controller
 * Smart Resource Intelligence & Automation Platform (SIH 2026)
 */

let efficiencyChartInstance = null;
let utilizationChartInstance = null;
let currentDashboardData = null;
let showRawUnits = false;

async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard');
    if (!res.ok) throw new Error('Failed to load dashboard telemetry');
    const data = await res.json();
    currentDashboardData = data;

    // 1. Update KPI Metric Cards
    document.getElementById('kpi-total-resources').textContent = data.total_resources;
    document.getElementById('kpi-active-resources').textContent = data.active_resources;
    document.getElementById('kpi-utilization').textContent = `${data.avg_utilization_pct}%`;
    document.getElementById('kpi-wastage').textContent = data.wastage_count;
    document.getElementById('kpi-anomalies').textContent = data.active_anomalies;
    document.getElementById('kpi-actions').textContent = data.actions_performed;
    document.getElementById('kpi-available').textContent = data.available_resources;

    // 2. Render Efficiency Gauge & Breakdown
    renderEfficiencyGauge(data.efficiency);

    // 3. Render Resource Utilization Chart
    renderUtilizationChart(data.resources);

    // 4. Render Recent Insights
    renderRecentInsights(data.recent_insights);

    // 5. Render Recent Actions
    renderRecentActions(data.recent_actions);

  } catch(err) {
    console.error('Error loading dashboard:', err);
    showToast('Failed to refresh dashboard telemetry', 'danger');
  }
}

function renderEfficiencyGauge(eff) {
  const score = Math.round(eff.score || 0);
  const grade = eff.grade || 'B';
  const status = eff.status || 'Optimal';

  document.getElementById('efficiency-score-display').textContent = score;
  document.getElementById('efficiency-grade-display').textContent = `Grade ${grade}`;
  
  const statusBadge = document.getElementById('efficiency-status-badge');
  statusBadge.textContent = status;
  statusBadge.className = `badge px-3 py-2 fs-6 rounded-pill bg-${eff.badge_color || 'primary'}`;

  // Breakdown progress bars
  const b = eff.breakdown || {};
  const utilScore = b.utilization_health || 35;
  const anomScore = b.anomaly_health || 20;
  const wasteScore = b.wastage_health || 15;
  const autoScore = b.automation_bonus || 10;

  document.getElementById('score-util-val').textContent = `${utilScore}/40`;
  document.getElementById('score-util-bar').style.width = `${(utilScore / 40) * 100}%`;

  document.getElementById('score-anomaly-val').textContent = `${anomScore}/25`;
  document.getElementById('score-anomaly-bar').style.width = `${(anomScore / 25) * 100}%`;

  document.getElementById('score-waste-val').textContent = `${wasteScore}/20`;
  document.getElementById('score-waste-bar').style.width = `${(wasteScore / 20) * 100}%`;

  document.getElementById('score-auto-val').textContent = `${autoScore}/15`;
  document.getElementById('score-auto-bar').style.width = `${(autoScore / 15) * 100}%`;

  // Chart.js Gauge Doughnut
  const ctx = document.getElementById('efficiencyGaugeChart');
  if (!ctx) return;

  const color = score >= 80 ? '#10b981' : (score >= 65 ? '#2563eb' : (score >= 50 ? '#f59e0b' : '#ef4444'));

  if (efficiencyChartInstance) {
    efficiencyChartInstance.destroy();
  }

  efficiencyChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [color, '#e2e8f0'],
        borderWidth: 0,
        circumference: 240,
        rotation: 240,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '82%',
      plugins: {
        tooltip: { enabled: false }
      }
    }
  });
}

function renderUtilizationChart(resources) {
  const ctx = document.getElementById('resourceUtilizationChart');
  if (!ctx) return;

  const labels = resources.map(r => r.name);
  const pcts = resources.map(r => r.capacity > 0 ? Math.round((r.current_usage / r.capacity) * 100) : 0);
  const rawUsage = resources.map(r => r.current_usage);
  const capacities = resources.map(r => r.capacity);

  const colors = pcts.map(p => p > 85 ? '#ef4444' : (p > 70 ? '#f59e0b' : (p < 20 ? '#6366f1' : '#10b981')));

  if (utilizationChartInstance) {
    utilizationChartInstance.destroy();
  }

  const dataset = showRawUnits ? [{
    label: 'Current Usage',
    data: rawUsage,
    backgroundColor: '#3b82f6',
    borderRadius: 6
  }, {
    label: 'Total Capacity',
    data: capacities,
    backgroundColor: '#e2e8f0',
    borderRadius: 6
  }] : [{
    label: 'Utilization %',
    data: pcts,
    backgroundColor: colors,
    borderRadius: 6
  }];

  utilizationChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: dataset
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      scales: {
        x: {
          beginAtZero: true,
          max: showRawUnits ? undefined : 100,
          grid: { color: '#f1f5f9' },
          ticks: {
            callback: (val) => showRawUnits ? val : val + '%'
          }
        },
        y: {
          grid: { display: false },
          ticks: {
            font: { weight: '600', size: 11 }
          }
        }
      },
      plugins: {
        legend: { display: showRawUnits },
        tooltip: {
          callbacks: {
            label: (context) => {
              const res = resources[context.dataIndex];
              if (showRawUnits) {
                return `${context.dataset.label}: ${context.raw} ${res.unit}`;
              }
              return `Utilization: ${context.raw}% (${res.current_usage} / ${res.capacity} ${res.unit})`;
            }
          }
        }
      }
    }
  });
}

function renderRecentInsights(insights) {
  const container = document.getElementById('recent-insights-list');
  if (!container) return;

  if (!insights || insights.length === 0) {
    container.innerHTML = '<div class="p-4 text-center text-muted small">No active anomalies or wastage identified.</div>';
    return;
  }

  container.innerHTML = insights.map(i => {
    let badgeClass = 'severity-low';
    let icon = 'bi-info-circle text-primary';
    if (i.severity === 'CRITICAL') {
      badgeClass = 'severity-critical';
      icon = 'bi-exclamation-octagon text-danger';
    } else if (i.severity === 'HIGH') {
      badgeClass = 'severity-high';
      icon = 'bi-exclamation-triangle text-warning';
    } else if (i.severity === 'MEDIUM') {
      badgeClass = 'severity-medium';
      icon = 'bi-exclamation-circle text-warning';
    }

    return `
      <div class="list-group-item p-3 border-0 border-bottom">
        <div class="d-flex align-items-center justify-content-between mb-1">
          <div class="d-flex align-items-center gap-2">
            <i class="bi ${icon} fs-5"></i>
            <span class="fw-bold text-dark small">${i.resource_name || 'System Asset'}</span>
            <span class="badge ${badgeClass} px-2 py-1" style="font-size: 0.68rem;">${i.severity}</span>
          </div>
          <span class="text-muted" style="font-size: 0.72rem;">${i.created_at}</span>
        </div>
        <p class="small text-secondary mb-1 ps-4">${i.description}</p>
        <div class="ps-4 small text-primary fw-medium"><i class="bi bi-arrow-right-short"></i> ${i.recommendation}</div>
      </div>
    `;
  }).join('');
}

function renderRecentActions(actions) {
  const container = document.getElementById('recent-actions-list');
  if (!container) return;

  if (!actions || actions.length === 0) {
    container.innerHTML = '<div class="p-4 text-center text-muted small">No recent automation actions.</div>';
    return;
  }

  container.innerHTML = actions.map(act => `
    <div class="list-group-item p-3 border-0 border-bottom">
      <div class="d-flex align-items-center justify-content-between mb-1">
        <div class="d-flex align-items-center gap-2">
          <i class="bi bi-cpu-fill text-success fs-5"></i>
          <span class="fw-bold text-dark small">${act.rule_name}</span>
          <span class="badge bg-success-subtle text-success px-2 py-1" style="font-size: 0.68rem;">${act.status}</span>
        </div>
        <span class="text-muted" style="font-size: 0.72rem;">${act.timestamp}</span>
      </div>
      <p class="small text-danger mb-1 ps-4 font-monospace" style="font-size: 0.75rem;">Trigger: ${act.trigger}</p>
      <div class="ps-4 small text-dark fw-medium"><i class="bi bi-check2 text-success me-1"></i>${act.action}</div>
    </div>
  `).join('');
}

// Event Listeners for Dashboard
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();

  // Unit toggle buttons
  const btnPct = document.getElementById('btn-chart-pct');
  const btnRaw = document.getElementById('btn-chart-raw');
  if (btnPct && btnRaw) {
    btnPct.addEventListener('click', () => {
      btnPct.classList.add('active');
      btnRaw.classList.remove('active');
      showRawUnits = false;
      if (currentDashboardData) renderUtilizationChart(currentDashboardData.resources);
    });

    btnRaw.addEventListener('click', () => {
      btnRaw.classList.add('active');
      btnPct.classList.remove('active');
      showRawUnits = true;
      if (currentDashboardData) renderUtilizationChart(currentDashboardData.resources);
    });
  }

  // Quick Action Buttons
  const btnAiScan = document.getElementById('btn-run-ai-scan');
  if (btnAiScan) {
    btnAiScan.addEventListener('click', async () => {
      btnAiScan.disabled = true;
      btnAiScan.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Scanning...';
      try {
        const res = await fetch('/api/insights/analyze', { method: 'POST' });
        const data = await res.json();
        showToast(`AI diagnostic finished: ${data.results.new_insights_count} insights generated`, 'success');
        loadDashboardData();
      } catch(err) {
        showToast('AI diagnostic failed', 'danger');
      } finally {
        btnAiScan.disabled = false;
        btnAiScan.innerHTML = '<i class="bi bi-search"></i> Run AI Anomaly Diagnostic';
      }
    });
  }

  const btnInjectAnomaly = document.getElementById('btn-inject-anomaly');
  if (btnInjectAnomaly) {
    btnInjectAnomaly.addEventListener('click', async () => {
      btnInjectAnomaly.disabled = true;
      btnInjectAnomaly.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Injecting...';
      try {
        const res = await fetch('/api/simulate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ with_anomaly: true })
        });
        showToast('Surge anomaly injected! AI flagged critical deviation.', 'warning');
        loadDashboardData();
      } catch(err) {
        showToast('Injection failed', 'danger');
      } finally {
        btnInjectAnomaly.disabled = false;
        btnInjectAnomaly.innerHTML = '<i class="bi bi-bug"></i> Inject Test Surge Spike';
      }
    });
  }

  const btnExecAuto = document.getElementById('btn-exec-automation');
  if (btnExecAuto) {
    btnExecAuto.addEventListener('click', async () => {
      btnExecAuto.disabled = true;
      btnExecAuto.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Executing...';
      try {
        const res = await fetch('/api/automation/run', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ force_simulation: true })
        });
        const data = await res.json();
        showToast(`Automation engine executed ${data.actions.length} closed-loop actions!`, 'success');
        loadDashboardData();
      } catch(err) {
        showToast('Automation execution failed', 'danger');
      } finally {
        btnExecAuto.disabled = false;
        btnExecAuto.innerHTML = '<i class="bi bi-play-circle"></i> Run Automation Engine';
      }
    });
  }
});
