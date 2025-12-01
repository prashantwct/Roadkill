import os
import re

# ---------------------------------------------------------
# 1. UPDATE TEMPLATE (Small Geometric Markers + Server Filters)
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
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

<style>
  .custom-marker {
    border: 2px solid white;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.5);
  }
  .marker-wild {
    background-color: #dc3545; /* Red */
    border-radius: 50%;
  }
  .marker-domestic {
    background-color: #000000; /* Black */
    border-radius: 0%; /* Square */
  }
  .marker-other {
    background-color: #6c757d; /* Grey */
    border-radius: 50%;
  }
</style>

<script>
var map;
var markerLayerGroup; 
var heatLayer;
var allMarkers = []; 

function getCustomIcon(type) {
    let className = 'marker-other';
    let t = (type || '').toLowerCase();

    if (t.includes('wild')) {
        className = 'marker-wild';
    } else if (t.includes('domestic')) {
        className = 'marker-domestic';
    }

    return L.divIcon({
        className: 'custom-marker ' + className,
        iconSize: [12, 12],    // Small size
        iconAnchor: [6, 6],    // Centered
        popupAnchor: [0, -8]
    });
}

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Base Layers
  var streetMap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
  var satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 });

  // 2. Init Map
  map = L.map('map', { center: [20.5937, 78.9629], zoom: 5, layers: [streetMap] });

  // 3. Layers
  markerLayerGroup = L.layerGroup().addTo(map);
  heatLayer = L.heatLayer([], {radius: 20, blur: 15}).addTo(map);

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
            <span class="badge bg-dark">${mData.type}</span>
            <br>
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
  
  // 6. User Location
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

  heatLayer.setLatLngs(heatData);
  document.getElementById('countBadge').textContent = count + " Found";
  
  if (count > 0) {
     var group = new L.featureGroup(allMarkers.filter(m => markerLayerGroup.hasLayer(m.marker)).map(m => m.marker));
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
print("✅ Updated templates/map.html")

# ---------------------------------------------------------
# 2. UPDATE APP.PY (Inject Full Filter Data)
# ---------------------------------------------------------
# We will use Regex to find the existing map_view function and replace it completely.

with open('app.py', 'r') as f:
    content = f.read()

# Define the new Route Function
new_route = """
    # ---------------- MAP VIEW ----------------
    @app.route('/map')
    def map_view():
        # 1. Get mappable carcasses for the map
        carcasses = Carcass.query.filter(
            Carcass.latitude.isnot(None), 
            Carcass.longitude.isnot(None)
        ).all()

        # 2. Get FULL unique lists for the dropdowns
        all_sites = sorted({s.code for s in Site.query.all()})
        
        # Use simple distinct queries
        all_species = [r[0] for r in db.session.query(Carcass.species).distinct().filter(Carcass.species.isnot(None)).all()]
        all_types = [r[0] for r in db.session.query(Carcass.animal_type).distinct().filter(Carcass.animal_type.isnot(None)).all()]
        
        all_species.sort()
        all_types.sort()

        return render_template('map.html', 
                               carcasses=carcasses, 
                               all_sites=all_sites, 
                               all_species=all_species, 
                               all_types=all_types)
"""

# Regex pattern to match the existing map_view function block
# Matches @app.route('/map') ... until the next @app.route or end of file
pattern = r"@app\.route\('/map'\).*?return render_template\('map\.html'.*?\)"

# Use re.DOTALL so . matches newlines
match = re.search(pattern, content, re.DOTALL)

if match:
    print("Found existing map route. Replacing...")
    # Replace the found block with our new code
    new_content = content.replace(match.group(0), new_route.strip())
    
    with open('app.py', 'w') as f:
        f.write(new_content)
    print("✅ Updated app.py map logic successfully.")
else:
    print("⚠️ Could not find existing map route to update. Appending new route...")
    # If strictly not found, append it (less ideal but works if clean)
    anchor = "# ========================\n# GUNICORN ENTRYPOINT"
    if anchor in content:
        new_content = content.replace(anchor, new_route + "\n\n" + anchor)
        with open('app.py', 'w') as f:
            f.write(new_content)
        print("✅ Appended new map route to app.py.")
    else:
        print("❌ Error: Could not find place to insert route.")

