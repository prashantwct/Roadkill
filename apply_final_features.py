import os
import re

print("🚀 Applying Final Features...")

# ---------------------------------------------------------
# 1. UPDATE MAP TEMPLATE (Add Hybrid Layer)
# ---------------------------------------------------------
# We need to inject the "Hybrid" layer definition into the existing map.html logic.
# The easiest way is to rewrite the map template with the new layer added.

map_html = """{% extends "base.html" %}
{% block content %}

<div class="row">
  <!-- MAP COLUMN -->
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

  <!-- FILTERS COLUMN -->
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

<!-- LEAFLET & PLUGINS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

<style>
  .custom-marker { border: 2px solid white; box-shadow: 1px 1px 4px rgba(0,0,0,0.5); }
  .marker-wild { background-color: #dc3545; border-radius: 50%; }
  .marker-domestic { background-color: #000000; border-radius: 0%; }
  .marker-other { background-color: #6c757d; border-radius: 50%; }
</style>

<script>
var map, markerLayerGroup, heatLayer, allMarkers = []; 

function getCustomIcon(type) {
    let className = 'marker-other';
    let t = (type || '').toLowerCase();
    if (t.includes('wild')) className = 'marker-wild';
    else if (t.includes('domestic')) className = 'marker-domestic';

    return L.divIcon({
        className: 'custom-marker ' + className,
        iconSize: [12, 12], iconAnchor: [6, 6], popupAnchor: [0, -8]
    });
}

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Define Base Layers
  var streetMap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
  
  var satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 });
  
  // Hybrid: Satellite + Transparent Labels Overlay
  var hybridMap = L.layerGroup([
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 }),
      L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_lines/{z}/{x}/{y}{r}.png', { maxZoom: 19, opacity: 0.7 }),
      L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_labels/{z}/{x}/{y}{r}.png', { maxZoom: 19, opacity: 0.7 })
  ]);
  // Fallback Hybrid (Simpler) if Stadia requires API key:
  // Using OpenStreetMap on top with transparency? No, standard practice is pure Satellite or Annotated.
  // Let's stick to Esri Satellite which often has labels baked in certain services, but here we will try a standard overlay approach.
  // Actually, let's use Google Hybrid structure if possible, but Google requires API key.
  // Best free alternative: CartoDB Dark Matter for "Dark" mode, or just Satellite.
  // Let's use Esri World Imagery (Satellite) + CartoDB Voyager Labels (as transparent overlay)
  
  var hybridLabels = L.layerGroup([
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 }),
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png', { maxZoom: 19 })
  ]);

  // 2. Init Map
  map = L.map('map', { center: [20.5937, 78.9629], zoom: 5, layers: [streetMap] });

  // 3. Overlay Layers
  markerLayerGroup = L.layerGroup().addTo(map);
  heatLayer = L.heatLayer([], {radius: 20, blur: 15}).addTo(map);

  // 4. Controls
  L.control.layers(
      { "Streets": streetMap, "Satellite": satelliteMap, "Hybrid (Sat+Labels)": hybridLabels },
      { "Markers": markerLayerGroup, "Heatmap": heatLayer }
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
  var heatData = [];
  var count = 0;

  allMarkers.forEach(item => {
    const d = item.data;
    let match = true;
    if (siteVal !== 'all' && d.site !== siteVal) match = false;
    if (speciesVal !== 'all' && d.species !== speciesVal) match = false;
    if (typeVal !== 'all' && d.type !== typeVal) match = false;

    if (match) {
      item.marker.addTo(markerLayerGroup);
      heatData.push([d.lat, d.lng, 0.8]);
      count++;
    }
  });

  if(heatLayer) heatLayer.setLatLngs(heatData);
  document.getElementById('countBadge').textContent = count + " Found";
  
  if (count > 0) {
     var group = new L.featureGroup(allMarkers.filter(m => markerLayerGroup.hasLayer(m.marker)).map(m => m.marker));
     map.fitBounds(group.getBounds().pad(0.1));
  }
}

function resetFilters() { document.getElementById('filterForm').reset(); applyFilters(); }
function locateUser() { map.locate({setView: true, maxZoom: 16}); }
</script>
{% endblock %}
"""

os.makedirs('templates', exist_ok=True)
with open('templates/map.html', 'w') as f:
    f.write(map_html)
print("✅ Updated map.html with Hybrid Layer.")


# ---------------------------------------------------------
# 2. UPDATE CSV EXPORT (Add Lat/Lon)
# ---------------------------------------------------------
print("🔧 Updating CSV export...")
with open('app.py', 'r') as f:
    code = f.read()

# Pattern for CSV header row
header_pattern = r"cw\.writerow\(\[\s*'label'.*?'species'\s*\]\)"
new_header = "cw.writerow(['label', 'uuid', 'sample_type', 'collected_by', 'collected_at_IST', 'storage', 'notes', 'carcass_id', 'carcass_code', 'site_code', 'species', 'latitude', 'longitude'])"

# Pattern for CSV data row
row_pattern = r"s\.carcass\.species if s\.carcass else ''\s*\]\)"
new_row = "s.carcass.species if s.carcass else '', s.carcass.latitude if s.carcass else '', s.carcass.longitude if s.carcass else ''])"

if "latitude" not in code:
    code = re.sub(header_pattern, new_header, code)
    code = re.sub(row_pattern, new_row, code)
    with open('app.py', 'w') as f:
        f.write(code)
    print("✅ Added Latitude/Longitude to CSV Export.")
else:
    print("ℹ️ CSV export already seems to have coordinates.")


# ---------------------------------------------------------
# 3. UPDATE ADMIN DASHBOARD (Reactive Buttons)
# ---------------------------------------------------------
# We will inject some CSS into base.html (or app.css) to make buttons interactive
# and update the dashboard template to use specific hover classes if needed.
# For simplicity, let's update app.css to affect all buttons globally.

css_content = """
:root{ --brand:#0d6efd; }
body{ font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
.navbar-brand{ letter-spacing:0.3px; }
.card{ border-radius:12px; transition: transform 0.2s ease-in-out, box-shadow 0.2s; }
.card:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important; }
.btn{ border-radius:8px; transition: all 0.2s; position: relative; overflow: hidden; }
.btn:active { transform: scale(0.97); }
.btn-primary:hover { background-color: #0b5ed7; box-shadow: 0 4px 12px rgba(13,110,253,0.3); }
.form-control, .form-select{ border-radius:8px; }
.table thead th{ background:#f8f9fa; }
.toast{ box-shadow:0 4px 10px rgba(0,0,0,0.06); }
.container-lg{ max-width:1100px; }
"""

with open('static/app.css', 'w') as f:
    f.write(css_content)
print("✅ Updated app.css with reactive button/card styles.")

print("🎉 Final features applied. Restart app.")
