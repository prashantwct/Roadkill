import os

# ---------------------------------------------------------
# UPDATE MAP TEMPLATE WITH FILTERS & LOCATION
# ---------------------------------------------------------
map_html = """{% extends "base.html" %}
{% block content %}

<div class="row">
  <div class="col-lg-9 order-lg-2 mb-3">
    <div class="card shadow-sm h-100">
      <div class="card-header bg-white d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><i class="fa-solid fa-map-location-dot me-2"></i> Interactive Map</h5>
        
        <div class="d-flex gap-2">
           <span id="countBadge" class="badge bg-secondary d-flex align-items-center">Loading...</span>
           <button class="btn btn-sm btn-primary" onclick="locateUser()">
             <i class="fa-solid fa-location-crosshairs me-1"></i> Me
           </button>
        </div>
      </div>
      <div class="card-body p-0">
        <div id="map" style="height: 75vh; width: 100%;"></div>
      </div>
    </div>
  </div>

  <div class="col-lg-3 order-lg-1 mb-3">
    <div class="card shadow-sm border-0">
      <div class="card-header bg-light fw-bold">
        <i class="fa-solid fa-filter me-2"></i> Filters
      </div>
      <div class="card-body">
        
        <form id="filterForm">
          <div class="mb-3">
            <label class="form-label small fw-bold">Site</label>
            <select id="siteFilter" class="form-select form-select-sm" onchange="applyFilters()">
              <option value="all">All Sites</option>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold">Species</label>
            <select id="speciesFilter" class="form-select form-select-sm" onchange="applyFilters()">
              <option value="all">All Species</option>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold">Animal Type</label>
            <select id="typeFilter" class="form-select form-select-sm" onchange="applyFilters()">
              <option value="all">All Types</option>
            </select>
          </div>

          <hr>

          <div class="mb-3">
            <label class="form-label small fw-bold">Date Range</label>
            <input type="date" id="dateStart" class="form-control form-control-sm mb-2" onchange="applyFilters()">
            <input type="date" id="dateEnd" class="form-control form-control-sm" onchange="applyFilters()">
          </div>

          <div class="d-grid">
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="resetFilters()">
              <i class="fa-solid fa-rotate-right me-1"></i> Reset
            </button>
          </div>

        </form>

      </div>
    </div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
var map;
var userMarker;
var allMarkers = []; // Store marker objects and their data
var layerGroup;      // Group to hold visible markers

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Init Map
  map = L.map('map').setView([20.5937, 78.9629], 5);
  layerGroup = L.layerGroup().addTo(map);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  // 2. Load Markers from Jinja
  // We construct a JS object for every carcass
  {% for c in carcasses %}
    {% if c.latitude and c.longitude %}
      
      var mData = {
        lat: {{ c.latitude }},
        lng: {{ c.longitude }},
        site: "{{ c.site.code }}",
        species: "{{ c.species or 'Unknown' }}",
        type: "{{ c.animal_type or 'Unknown' }}",
        dateStr: "{{ c.datetime_found.strftime('%Y-%m-%d') }}", // YYYY-MM-DD
        popup: `
          <div class="p-1">
            <h6 class="mb-1 fw-bold text-primary">{{ c.code }}</h6>
            <div class="mb-2">
              <span class="badge bg-secondary">{{ c.species or 'Unknown' }}</span>
              <span class="badge bg-light text-dark border">{{ c.site.code }}</span>
            </div>
            <div class="small mb-2 text-muted">Found: {{ c.datetime_found.strftime('%Y-%m-%d') }}</div>
            <a href="{{ url_for('view_carcass', carcass_id=c.id) }}" class="btn btn-sm btn-outline-primary w-100 mt-2">View</a>
          </div>
        `
      };
      
      var leafletMarker = L.marker([mData.lat, mData.lng]).bindPopup(mData.popup);
      
      allMarkers.push({
        marker: leafletMarker,
        data: mData
      });

    {% endif %}
  {% endfor %}

  // 3. Populate Dropdowns Dynamically
  populateDropdowns();

  // 4. Show All Markers Initially
  applyFilters();

  // 5. User Location Listeners
  map.on('locationfound', function(e) {
      var radius = e.accuracy;
      if (userMarker) map.removeLayer(userMarker);
      userMarker = L.marker(e.latlng).addTo(map)
          .bindPopup("You are within " + Math.round(radius) + " meters").openPopup();
      L.circle(e.latlng, radius).addTo(map);
  });
  map.on('locationerror', e => alert(e.message));
});

function populateDropdowns() {
  // Extract unique values
  const sites = new Set();
  const species = new Set();
  const types = new Set();

  allMarkers.forEach(item => {
    sites.add(item.data.site);
    species.add(item.data.species);
    types.add(item.data.type);
  });

  addOptions('siteFilter', sites);
  addOptions('speciesFilter', species);
  addOptions('typeFilter', types);
}

function addOptions(id, setObj) {
  const select = document.getElementById(id);
  // Sort and append
  Array.from(setObj).sort().forEach(val => {
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = val;
    select.appendChild(opt);
  });
}

function applyFilters() {
  // Get current values
  const siteVal = document.getElementById('siteFilter').value;
  const speciesVal = document.getElementById('speciesFilter').value;
  const typeVal = document.getElementById('typeFilter').value;
  
  const startVal = document.getElementById('dateStart').value;
  const endVal = document.getElementById('dateEnd').value;
  
  const startDate = startVal ? new Date(startVal) : null;
  const endDate = endVal ? new Date(endVal) : null;

  // Clear current map layer
  layerGroup.clearLayers();
  let count = 0;

  // Filter and add
  allMarkers.forEach(item => {
    const d = item.data;
    
    // Check Logic
    let match = true;
    if (siteVal !== 'all' && d.site !== siteVal) match = false;
    if (speciesVal !== 'all' && d.species !== speciesVal) match = false;
    if (typeVal !== 'all' && d.type !== typeVal) match = false;

    // Date check
    if (match && (startDate || endDate)) {
      const itemDate = new Date(d.dateStr);
      if (startDate && itemDate < startDate) match = false;
      if (endDate && itemDate > endDate) match = false;
    }

    if (match) {
      item.marker.addTo(layerGroup);
      count++;
    }
  });

  // Update Badge
  document.getElementById('countBadge').textContent = count + " Found";

  // Auto-fit bounds if we have visible markers
  if (count > 0) {
    // Collect LatLngs of visible markers
    const latLngs = allMarkers
      .filter(m => layerGroup.hasLayer(m.marker))
      .map(m => m.marker.getLatLng());
    
    if (latLngs.length > 0) {
       map.fitBounds(L.latLngBounds(latLngs).pad(0.1));
    }
  }
}

function resetFilters() {
  document.getElementById('filterForm').reset();
  applyFilters();
}

function locateUser() {
  map.locate({setView: true, maxZoom: 16});
}
</script>
{% endblock %}
"""

os.makedirs('templates', exist_ok=True)
with open('templates/map.html', 'w') as f:
    f.write(map_html)

print("✅ Updated templates/map.html with Filters sidebar.")
print("🎉 Done! Refresh the Map page to use filters.")
