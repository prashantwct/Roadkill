import os

# ---------------------------------------------------------
# ADVANCED MAP TEMPLATE (Icons + Heatmap + Filters)
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

        <div class="mt-4 small text-muted">
           <strong>Legend:</strong><br>
           <i class="fa-solid fa-dog text-danger"></i> Jackal/Dog<br>
           <i class="fa-solid fa-cat text-success"></i> Cat/Jungle Cat<br>
           <i class="fa-solid fa-cow text-primary"></i> Cattle/Buffalo<br>
           <i class="fa-solid fa-paw text-secondary"></i> Others
        </div>

      </div>
    </div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

<style>
  .custom-div-icon {
    background: transparent;
    border: none;
  }
  .marker-pin {
    width: 30px;
    height: 30px;
    border-radius: 50% 50% 50% 0;
    background: #fff;
    position: absolute;
    transform: rotate(-45deg);
    left: 50%;
    top: 50%;
    margin: -15px 0 0 -15px;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
    text-align: center;
    line-height: 30px;
  }
  .marker-pin::after {
      content: '';
      width: 24px;
      height: 24px;
      margin: 3px 0 0 3px;
      background: #fff;
      position: absolute;
      border-radius: 50%;
      left: 0; 
      top: 0;
  }
  .marker-icon {
      position: absolute;
      width: 100%;
      font-size: 16px;
      line-height: 30px; 
      text-align: center;
      margin-top: -15px; /* centering adjustment */
      z-index: 10;
  }
</style>

<script>
var map;
var userMarker;
var allMarkers = []; 
var markerLayerGroup; // Layer for individual pins
var heatLayer;        // Layer for heatmap
var layerControl;

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Base Maps
  var streetMap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: 'OpenStreetMap'
  });
  
  var satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19, attribution: 'Esri'
  });

  // 2. Init Map
  map = L.map('map', {
      center: [20.5937, 78.9629], 
      zoom: 5,
      layers: [streetMap] // Default layer
  });

  // 3. Init Overlay Layers
  markerLayerGroup = L.layerGroup().addTo(map);
  heatLayer = L.heatLayer([], {radius: 25, blur: 15, maxZoom: 12}); // Start empty, will fill later

  // 4. Layer Control (Top Right)
  var baseMaps = {
      "Streets": streetMap,
      "Satellite": satelliteMap
  };
  var overlayMaps = {
      "Individual Markers": markerLayerGroup,
      "Heatmap (Hotspots)": heatLayer
  };
  L.control.layers(baseMaps, overlayMaps).addTo(map);

  // 5. Load Data
  var data = [];
  {% for c in carcasses %}
    {% if c.latitude and c.longitude %}
      data.push({
        lat: {{ c.latitude }},
        lng: {{ c.longitude }},
        site: {{ c.site.code | tojson }},
        species: {{ (c.species or 'Unknown') | tojson }},
        type: {{ (c.animal_type or 'Unknown') | tojson }},
        dateStr: "{{ c.datetime_found.strftime('%Y-%m-%d') }}", 
        code: {{ c.code | tojson }},
        link: "{{ url_for('view_carcass', carcass_id=c.id) }}"
      });
    {% endif %}
  {% endfor %}

  // 6. Create Markers
  data.forEach(d => {
      var icon = getAnimalIcon(d.species);
      
      var popupHtml = `
        <div class="p-1">
          <h6 class="mb-1 fw-bold text-primary">${d.code}</h6>
          <div class="mb-2">
            <span class="badge bg-secondary">${d.species}</span>
            <span class="badge bg-light text-dark border">${d.type}</span>
          </div>
          <div class="small mb-2 text-muted">Found: ${d.dateStr}</div>
          <a href="${d.link}" class="btn btn-sm btn-outline-primary w-100 mt-2">View</a>
        </div>
      `;
      
      var marker = L.marker([d.lat, d.lng], {icon: icon}).bindPopup(popupHtml);
      
      allMarkers.push({ marker: marker, data: d });
  });

  // 7. Setup & Apply Filters
  populateDropdowns();
  applyFilters();

  // 8. User Location
  map.on('locationfound', function(e) {
      if (userMarker) map.removeLayer(userMarker);
      userMarker = L.marker(e.latlng).addTo(map)
          .bindPopup("You are here").openPopup();
      L.circle(e.latlng, e.accuracy/2).addTo(map);
  });
});

// --- HELPER: Get Icon based on Species ---
function getAnimalIcon(species) {
    let iconClass = 'fa-paw';
    let color = '#6c757d'; // Default Grey

    const s = species.toLowerCase();

    if (s.includes('jackal') || s.includes('dog')) {
        iconClass = 'fa-dog';
        color = '#dc3545'; // Red
    } else if (s.includes('cat') || s.includes('leopard') || s.includes('tiger')) {
        iconClass = 'fa-cat';
        color = '#198754'; // Green
    } else if (s.includes('cow') || s.includes('cattle') || s.includes('buffalo')) {
        iconClass = 'fa-cow';
        color = '#0d6efd'; // Blue
    } else if (s.includes('civet')) {
        iconClass = 'fa-mask'; // Distinctive for civet
        color = '#fd7e14'; // Orange
    }

    // Return HTML for custom marker
    // We construct a "Pin" shape using CSS and place the font-awesome icon inside
    const html = `
      <div style="position:relative;">
        <div class="marker-pin" style="background:${color};"></div>
        <i class="fa-solid ${iconClass} marker-icon" style="color:white;"></i>
      </div>`;

    return L.divIcon({
        className: 'custom-div-icon',
        html: html,
        iconSize: [30, 42],
        iconAnchor: [15, 42],
        popupAnchor: [0, -35]
    });
}

function populateDropdowns() {
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
  while (select.options.length > 1) select.remove(1);
  Array.from(setObj).sort().forEach(val => {
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = val;
    select.appendChild(opt);
  });
}

function applyFilters() {
  const siteVal = document.getElementById('siteFilter').value;
  const speciesVal = document.getElementById('speciesFilter').value;
  const typeVal = document.getElementById('typeFilter').value;
  const startVal = document.getElementById('dateStart').value;
  const endVal = document.getElementById('dateEnd').value;
  const startDate = startVal ? new Date(startVal) : null;
  const endDate = endVal ? new Date(endVal) : null;

  // Clear current visible layers
  markerLayerGroup.clearLayers();
  
  // Prepare heatmap data array: [lat, lng, intensity]
  var heatData = [];
  var count = 0;

  allMarkers.forEach(item => {
    const d = item.data;
    let match = true;
    
    if (siteVal !== 'all' && d.site !== siteVal) match = false;
    if (speciesVal !== 'all' && d.species !== speciesVal) match = false;
    if (typeVal !== 'all' && d.type !== typeVal) match = false;
    if (match && (startDate || endDate)) {
      const itemDate = new Date(d.dateStr);
      if (startDate && itemDate < startDate) match = false;
      if (endDate && itemDate > endDate) match = false;
    }

    if (match) {
      // Add to Marker Layer
      item.marker.addTo(markerLayerGroup);
      
      // Add to Heatmap Data
      heatData.push([d.lat, d.lng, 0.8]); // 0.8 is intensity
      count++;
    }
  });

  // Update Heatmap Layer
  heatLayer.setLatLngs(heatData);

  document.getElementById('countBadge').textContent = count + " Found";

  // Auto-fit bounds
  if (count > 0) {
    const latLngs = allMarkers
      .filter(m => markerLayerGroup.hasLayer(m.marker))
      .map(m => m.marker.getLatLng());
    if (latLngs.length > 0) map.fitBounds(L.latLngBounds(latLngs).pad(0.1));
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

print("✅ Updated map.html with Advanced Icons and Heatmap.")
