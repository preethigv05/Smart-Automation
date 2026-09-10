/**
 * Resources Controller
 * Smart Resource Intelligence & Automation Platform (SIH 2026)
 */

let allResources = [];
let resourceModalInstance = null;
let viewModalInstance = null;

async function loadResourcesList() {
  const tbody = document.getElementById('resources-table-body');
  const countLabel = document.getElementById('resource-count-label');

  try {
    const res = await fetch('/api/resources');
    const data = await res.json();
    allResources = data.resources || [];

    renderResourcesTable();
  } catch(err) {
    console.error(err);
    tbody.innerHTML = '<tr><td colspan="7" class="text-danger text-center">Failed to load resource registry.</td></tr>';
  }
}

function renderResourcesTable() {
  const tbody = document.getElementById('resources-table-body');
  const countLabel = document.getElementById('resource-count-label');
  const search = document.getElementById('resource-search').value.toLowerCase().trim();
  const typeFilter = document.getElementById('filter-type').value;
  const statusFilter = document.getElementById('filter-status').value;

  const filtered = allResources.filter(r => {
    const matchesSearch = !search || r.name.toLowerCase().includes(search) || (r.location && r.location.toLowerCase().includes(search));
    const matchesType = !typeFilter || r.type === typeFilter;
    const matchesStatus = !statusFilter || r.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  countLabel.textContent = `Showing ${filtered.length} of ${allResources.length} assets`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-5 text-muted">No resources match the selected criteria.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(r => {
    const pct = r.utilization_pct || (r.capacity > 0 ? Math.round((r.current_usage / r.capacity) * 100) : 0);
    const barColor = pct > 85 ? 'bg-danger' : (pct > 70 ? 'bg-warning' : (pct < 20 ? 'bg-primary' : 'bg-success'));

    return `
      <tr>
        <td>
          <div class="fw-bold text-dark">${r.name}</div>
          <span class="font-monospace text-muted small">Asset ID: #${r.id}</span>
        </td>
        <td>
          <span class="badge bg-light text-dark border text-uppercase" style="font-size: 0.72rem;">${r.type}</span>
        </td>
        <td>
          <span class="text-muted small"><i class="bi bi-geo-alt me-1"></i>${r.location || 'Main Campus'}</span>
        </td>
        <td>
          <span class="fw-bold text-dark">${r.current_usage}</span> 
          <span class="small text-muted">/ ${r.capacity} ${r.unit}</span>
        </td>
        <td style="min-width: 140px;">
          <div class="d-flex align-items-center gap-2">
            <span class="small fw-semibold" style="width: 40px;">${pct}%</span>
            <div class="progress flex-grow-1 progress-thin">
              <div class="progress-bar ${barColor}" style="width: ${pct}%"></div>
            </div>
          </div>
        </td>
        <td>
          <span class="badge badge-status badge-${r.status.toLowerCase()}">${r.status}</span>
        </td>
        <td class="text-end">
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-info btn-view-res" data-id="${r.id}" title="View Asset Telemetry">
              <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-outline-primary btn-edit-res" data-id="${r.id}" title="Edit Configuration">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-outline-danger btn-del-res" data-id="${r.id}" title="Delete Resource">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Attach action buttons
  document.querySelectorAll('.btn-view-res').forEach(btn => {
    btn.addEventListener('click', () => viewResourceDetails(btn.dataset.id));
  });

  document.querySelectorAll('.btn-edit-res').forEach(btn => {
    btn.addEventListener('click', () => openEditResourceModal(btn.dataset.id));
  });

  document.querySelectorAll('.btn-del-res').forEach(btn => {
    btn.addEventListener('click', () => deleteResource(btn.dataset.id));
  });
}

function openAddResourceModal() {
  document.getElementById('resourceModalTitle').textContent = 'Add New Monitored Resource';
  document.getElementById('resourceForm').reset();
  document.getElementById('res-id').value = '';
}

function openEditResourceModal(id) {
  const r = allResources.find(item => item.id == id);
  if (!r) return;

  document.getElementById('resourceModalTitle').textContent = 'Edit Resource Configuration';
  document.getElementById('res-id').value = r.id;
  document.getElementById('res-name').value = r.name;
  document.getElementById('res-type').value = r.type;
  document.getElementById('res-capacity').value = r.capacity;
  document.getElementById('res-usage').value = r.current_usage;
  document.getElementById('res-unit').value = r.unit;
  document.getElementById('res-status').value = r.status;
  document.getElementById('res-location').value = r.location;

  if (!resourceModalInstance) {
    resourceModalInstance = new bootstrap.Modal(document.getElementById('resourceModal'));
  }
  resourceModalInstance.show();
}

async function viewResourceDetails(id) {
  const content = document.getElementById('view-res-content');
  if (!viewModalInstance) {
    viewModalInstance = new bootstrap.Modal(document.getElementById('viewResourceModal'));
  }
  viewModalInstance.show();

  content.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';

  try {
    const res = await fetch(`/api/resources/${id}`);
    const data = await res.json();
    const r = data.resource;
    const u = r.utilization || {};
    const a = r.anomaly_status || {};

    document.getElementById('view-res-name').textContent = `${r.name} (Telemetry Audit)`;

    content.innerHTML = `
      <div class="row g-3 mb-3">
        <div class="col-md-6">
          <div class="p-3 bg-light rounded-3 border">
            <div class="small text-muted fw-semibold">RESOURCE IDENTITY</div>
            <h5 class="fw-bold mb-1">${r.name}</h5>
            <div class="small text-secondary">Type: <span class="badge bg-light text-dark border">${r.type}</span></div>
            <div class="small text-secondary">Location: ${r.location}</div>
            <div class="small text-secondary">Health Status: <span class="badge badge-status badge-${r.status.toLowerCase()}">${r.status}</span></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3 bg-light rounded-3 border">
            <div class="small text-muted fw-semibold">TELEMETRY STATS (24H)</div>
            <div class="d-flex justify-content-between small py-1 border-bottom">
              <span>Current Usage:</span>
              <span class="fw-bold">${r.current_usage} ${r.unit} (${u.current_pct || 0}%)</span>
            </div>
            <div class="d-flex justify-content-between small py-1 border-bottom">
              <span>Total Capacity:</span>
              <span>${r.capacity} ${r.unit}</span>
            </div>
            <div class="d-flex justify-content-between small py-1 border-bottom">
              <span>24h Peak Usage:</span>
              <span>${u.peak_24h || r.current_usage} ${r.unit}</span>
            </div>
            <div class="d-flex justify-content-between small py-1">
              <span>24h Moving Average:</span>
              <span>${u.avg_24h || r.current_usage} ${r.unit}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="p-3 rounded-3 border ${a.is_anomaly ? 'bg-danger-subtle border-danger' : 'bg-success-subtle border-success'}">
        <div class="d-flex align-items-center gap-2 mb-1">
          <i class="bi ${a.is_anomaly ? 'bi-exclamation-octagon-fill text-danger' : 'bi-shield-check text-success'} fs-5"></i>
          <span class="fw-bold ${a.is_anomaly ? 'text-danger' : 'text-success'}">
            ${a.is_anomaly ? 'Statistical Anomaly Flagged' : 'Statistical Baseline Normal'}
          </span>
        </div>
        <div class="small text-dark">
          Calculated Z-Score: <strong>${a.z_score || 0.0}&sigma;</strong> &bull; 
          Baseline Mean: <strong>${a.baseline_mean || r.current_usage} ${r.unit}</strong> &bull; 
          Deviation: <strong>${a.pct_deviation || 0}%</strong>
        </div>
      </div>
    `;

  } catch(err) {
    content.innerHTML = '<div class="alert alert-danger">Failed to load resource details.</div>';
  }
}

async function deleteResource(id) {
  if (!confirm('Are you sure you want to delete this resource and all associated historical readings?')) return;

  try {
    const res = await fetch(`/api/resources/${id}`, { method: 'DELETE' });
    const data = await res.json();
    showToast(data.message, 'success');
    loadResourcesList();
  } catch(err) {
    showToast('Failed to delete resource', 'danger');
  }
}

// Form Submit (Create / Edit)
document.addEventListener('DOMContentLoaded', () => {
  resourceModalInstance = new bootstrap.Modal(document.getElementById('resourceModal'));
  loadResourcesList();

  const form = document.getElementById('resourceForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const id = document.getElementById('res-id').value;
    const payload = {
      name: document.getElementById('res-name').value.trim(),
      type: document.getElementById('res-type').value,
      capacity: parseFloat(document.getElementById('res-capacity').value),
      current_usage: parseFloat(document.getElementById('res-usage').value || 0),
      unit: document.getElementById('res-unit').value.trim(),
      status: document.getElementById('res-status').value,
      location: document.getElementById('res-location').value.trim()
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/resources/${id}` : '/api/resources';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        showToast(data.message, 'success');
        resourceModalInstance.hide();
        loadResourcesList();
      } else {
        showToast(data.error || 'Operation failed', 'danger');
      }
    } catch(err) {
      showToast('Network error while saving resource', 'danger');
    }
  });

  // Filters & Search
  document.getElementById('resource-search').addEventListener('input', renderResourcesTable);
  document.getElementById('filter-type').addEventListener('change', renderResourcesTable);
  document.getElementById('filter-status').addEventListener('change', renderResourcesTable);
});
