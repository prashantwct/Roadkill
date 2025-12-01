import os
import re

print("🔧 Starting Fixes...")

# ---------------------------------------------------------
# 1. FIX TIMESTAMP LOGIC IN APP.PY
# ---------------------------------------------------------
# Problem: The code adds +5:30 to the User's input time.
# Fix: Remove the timedelta addition for form inputs, keep it only for ist_now().

with open('app.py', 'r') as f:
    content = f.read()

# Fix 1: New Carcass Route
# Pattern: datetime.fromisoformat(dt) + timedelta(...)
# We want: datetime.fromisoformat(dt)
new_content = re.sub(
    r'datetime\.fromisoformat\(dt\) \+ timedelta\(hours=5, minutes=30\)', 
    'datetime.fromisoformat(dt)', 
    content
)

# Fix 2: New Sample Route
# Pattern: datetime.fromisoformat(collected_at_str) + timedelta(...)
new_content = re.sub(
    r'datetime\.fromisoformat\(collected_at_str\) \+ timedelta\(hours=5, minutes=30\)', 
    'datetime.fromisoformat(collected_at_str)', 
    new_content
)

if new_content != content:
    with open('app.py', 'w') as f:
        f.write(new_content)
    print("✅ Fixed app.py: Removed double timezone addition.")
else:
    print("ℹ️  app.py timestamps appear to be already fixed or patterns didn't match.")


# ---------------------------------------------------------
# 2. RE-GENERATE MAP TEMPLATE (Fix Heatmap)
# ---------------------------------------------------------
# We switch to a reliable CDN for Leaflet.heat and ensure the layer is initialized correctly.

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
              {% for site in all_sites %}
                <option value="{{ site }}">{{ site }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold">Species</label>
            <select id="speciesFilter" class="form-select form-select-sm" onchange="applyFilters()">
              <option value="all">All Species</option>
              {% for sp in all_species %}
                <option value="{{ sp }}">{{ sp }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold">Animal Type</label>
            <select id="typeFilter" class="form-select form-select-sm" onchange="applyFilters()">
              <option value="all">All Types</option>
              {% for t in all_types %}
                <option value="{{ t }}">{{ t }}</option>
              {% endfor %}
            </select>
          </div>

          <hr>
          <div class="d-grid">
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="resetFilters()">
              <i class="fa-solid fa-rotate-right me-1"></i> Reset Filters
            </button>
          </div>
        </form>

        <div class="mt-4 small">
           <strong>Legend:</strong>
           <div class="d-flex align-items-center mt-2">
             <span class="d-inline-block me-2" style="width:12px; height:12px; background:#dc3545; border-radius:50%; border:2px solid #fff; box-shadow:1px 1px 2px rgba(0,0,0,0.3);"></span>
             Wild Animal (Red Circle)
           </div>
           <div class="d-flex align-items-center mt-2">
             <span class="d-inline-block me-2" style="width:12px; height:12px; background:#000000; border:2px solid #fff; box-shadow:1px 1px 2px rgba(0,0,0,0.3);"></span>
             Domestic Animal (Black Square)
           </div>
           <div class="d-flex align-items-center mt-2">
             <span class="d-inline-block me-2" style="width:12px; height:12px; background:#6c757d; border-radius:50%; border:2px solid #fff; box-shadow:1px 1px 2px rgba(0,0,0,0.3);"></span>
             Unknown/Other
           </div>
        </div>

      </div>
    </div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js"></script>

<style>
  .custom-marker {
    border: 2px solid white;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.5);
  }
  .marker-wild { background-color: #dc3545; border-radius: 50%; }
  .marker-domestic { background-color: #000000; border-radius: 0%; }
  .marker-other { background-color: #6c757d; border-radius: 50%; }
</style>

<script>
var map;
var markerLayerGroup; 
var heatLayer;
var allMarkers = []; 

function getCustomIcon(type) {
    let className = 'marker-other';
    let t = (type || '').toLowerCase();
    if (t.includes('wild')) className = 'marker-wild';
    else if (t.includes('domestic')) className = 'marker-domestic';

    return L.divIcon({
        className: 'custom-marker ' + className,
        iconSize: [12, 12],
        iconAnchor: [6, 6],
        popupAnchor: [0, -8]
    });
}

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Base Layers
  var streetMap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
  var satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 });

  // 2. Init Map
  map = L.map('map', { center: [20.5937, 78.9629], zoom: 5, layers: [streetMap] });

  // 3. Init Layers
  markerLayerGroup = L.layerGroup().addTo(map);
  
  // Initialize Heatmap (Empty initially, added to map by default)
  // We use slightly larger radius for better visibility
  heatLayer = L.heatLayer([], {radius: 30, blur: 20, maxZoom: 17}).addTo(map);

  // 4. Controls
  L.control.layers(
      {"Streets": streetMap, "Satellite": satelliteMap},
      {"Markers": markerLayerGroup, "Heatmap": heatLayer}
  ).addTo(map);

  // 5. Load Data
  {% for c in carcasses %}
    {% if c.latitude and c.longitude %}
      var mData = {
        lat: {{ c.latitude }},
        lng: {{ c.longitude }},
        site: {{ c.site.code | tojson }},
        species: {{ (c.species or 'Unknown') | tojson }},
        type: {{ (c.animal_type or 'Unknown') | tojson }},
        dateStr: "{{ c.datetime_found.strftime('%Y-%m-%d') }}", 
        code: {{ c.code | tojson }},
        link: "{{ url_for('view_carcass', carcass_id=c.id) }}"
      };
      
      var icon = getCustomIcon(mData.type);
      
      var popupHtml = `
        <div class="p-1 text-center">
          <h6 class="mb-1 fw-bold text-primary">${mData.code}</h6>
          <div class="mb-2">
            <span class="badge bg-dark">${mData.type}</span><br>
            <span class="small text-muted">${mData.species}</span>
          </div>
          <a href="${mData.link}" class="btn btn-sm btn-outline-primary w-100 py-0">View</a>
        </div>
      `;
      
      var marker = L.marker([mData.lat, mData.lng], {icon: icon}).bindPopup(popupHtml);
      allMarkers.push({ marker: marker, data: mData });
    {% endif %}
  {% endfor %}

  applyFilters();
  
  map.on('locationfound', function(e) {
      L.circleMarker(e.latlng, {radius: 8, color: '#0d6efd', fillColor: '#0d6efd', fillOpacity: 1}).addTo(map).bindPopup("You").openPopup();
      L.circle(e.latlng, e.accuracy/2).addTo(map);
  });
});

function applyFilters() {
  const siteVal = document.getElementById('siteFilter').value;
  const speciesVal = document.getElementById('speciesFilter').value;
  const typeVal = document.getElementById('typeFilter').value;

  markerLayerGroup.clearLayers();
  var heatData = []; // Array of [lat, lng, intensity]
  var count = 0;

  allMarkers.forEach(item => {
    const d = item.data;
    let match = true;
    if (siteVal !== 'all' && d.site !== siteVal) match = false;
    if (speciesVal !== 'all' && d.species !== speciesVal) match = false;
    if (typeVal !== 'all' && d.type !== typeVal) match = false;

    if (match) {
      item.marker.addTo(markerLayerGroup);
      // Heatmap needs numeric lat/lng
      heatData.push([d.lat, d.lng, 1.0]); 
      count++;
    }
  });

  // Update HeatLayer data
  if(heatLayer) {
    heatLayer.setLatLngs(heatData);
  }

  document.getElementById('countBadge').textContent = count + " Found";
  
  if (count > 0) {
     var visibleMarkers = allMarkers.filter(m => markerLayerGroup.hasLayer(m.marker)).map(m => m.marker);
     var group = new L.featureGroup(visibleMarkers);
     map.fitBounds(group.getBounds().pad(0.1));
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

print("✅ Fixed templates/map.html: Updated Heatmap config & CDN.")
print("🎉 Done! Restart your app to apply changes.")
