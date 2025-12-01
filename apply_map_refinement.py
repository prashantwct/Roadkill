import os

# ---------------------------------------------------------
# 1. UPDATE APP.PY (Pass ALL filter options)
# ---------------------------------------------------------
# We need to fetch distinct lists for Sites, Species, and Types
# and pass them to the map template so the dropdowns are always full.

map_route_logic = """
    # ---------------- MAP VIEW ----------------
    @app.route('/map')
    def map_view():
        # 1. Get mappable carcasses
        carcasses = Carcass.query.filter(
            Carcass.latitude.isnot(None), 
            Carcass.longitude.isnot(None)
        ).all()

        # 2. Get FULL lists for filters (distinct values)
        # We use a helper set comprehension to ensure uniqueness
        all_sites = sorted({s.code for s in Site.query.all()})
        
        # SQLAlchemy distinct queries for strings
        # (Handling potential NULLs with filter)
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

with open('app.py', 'r') as f:
    code = f.read()

# Replace the old simple map_view with the new robust one
# We look for the function definition and replace the block
if "@app.route('/map')" in code:
    # A bit risky to replace by string matching a large block, 
    # so we'll look for the specific signature and replace the function body?
    # Actually, your file is small enough. Let's just swap the route block.
    # We will assume the previous script inserted it before the Gunicorn entrypoint.
    
    # We'll just append imports if missing, but we assume they are there.
    # To be safe, let's just overwrite the whole file's map_view section if we can identify it.
    
    # Simpler approach: We will just rewrite the map_view function using a unique marker.
    # The previous script used "@app.route('/map')\n    def map_view():"
    
    start_marker = "@app.route('/map')"
    end_marker = "return render_template('map.html', carcasses=carcasses)"
    
    if start_marker in code and end_marker in code:
        # Construct the new code block
        # We need to be careful with indentation in app.py
        # typically 4 spaces.
        
        # Let's just "Patch" it by replacing the simple return line with the complex logic
        # This is safer than replacing the whole block blindly.
        
        old_return = "return render_template('map.html', carcasses=carcasses)"
        
        new_logic = """
        # Get Filter Options
        all_sites = sorted({s.code for s in Site.query.all()})
        all_species = [r[0] for r in db.session.query(Carcass.species).distinct().filter(Carcass.species.isnot(None)).all()]
        all_types = [r[0] for r in db.session.query(Carcass.animal_type).distinct().filter(Carcass.animal_type.isnot(None)).all()]
        all_species.sort()
        all_types.sort()

        return render_template('map.html', carcasses=carcasses, all_sites=all_sites, all_species=all_species, all_types=all_types)
        """
        
        code = code.replace(old_return, new_logic.strip())
        
        with open('app.py', 'w') as f:
            f.write(code)
        print("✅ Updated app.py to send full filter lists.")
    else:
        print("⚠️ Could not find exact map_view pattern to patch. Logic might be different.")
else:
    print("⚠️ /map route not found in app.py. Please run previous map script first.")


# ---------------------------------------------------------
# 2. UPDATE TEMPLATE (Robust Markers + Full Filters)
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
           <strong>Legend:</strong><br>
           <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png" height="18"> Jackal/Dog (Wild)<br>
           <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png" height="18"> Cat/Leopard<br>
           <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png" height="18"> Cattle/Domestic<br>
           <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png" height="18"> Others
        </div>

      </div>
    </div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

<script>
var map;
var markerLayerGroup; 
var heatLayer;
var allMarkers = []; 

// ICONS (Using standard colored images - 100% reliable)
var redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});
var greenIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});
var blueIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});
var greyIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});

function getIcon(species, type) {
    if (!species) return greyIcon;
    var s = species.toLowerCase();
    
    if (s.includes('jackal') || s.includes('dog') || s.includes('civet')) return redIcon;
    if (s.includes('cat') || s.includes('leopard') || s.includes('tiger')) return greenIcon;
    if (s.includes('cattle') || s.includes('buffalo') || s.includes('cow')) return blueIcon;
    
    return greyIcon;
}

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Base Layers
  var streetMap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
  var satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 });

  // 2. Init Map
  map = L.map('map', { center: [20.5937, 78.9629], zoom: 5, layers: [streetMap] });

  // 3. Overlay Layers
  markerLayerGroup = L.layerGroup().addTo(map);
  heatLayer = L.heatLayer([], {radius: 25, blur: 15}).addTo(map); // Heatmap on by default? Or remove .addTo(map) to hide

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
      
      var icon = getIcon(mData.species, mData.type);
      
      var popupHtml = `
        <div class="p-1">
          <h6 class="mb-1 fw-bold text-primary">${mData.code}</h6>
          <span class="badge bg-secondary mb-2">${mData.species}</span>
          <br>
          <a href="${mData.link}" class="btn btn-sm btn-outline-primary w-100 mt-2">View</a>
        </div>
      `;
      
      var marker = L.marker([mData.lat, mData.lng], {icon: icon}).bindPopup(popupHtml);
      
      allMarkers.push({ marker: marker, data: mData });
    {% endif %}
  {% endfor %}

  applyFilters();
  
  // 6. User Location
  map.on('locationfound', function(e) {
      L.marker(e.latlng).addTo(map).bindPopup("You").openPopup();
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

print("✅ Updated map.html with Robust Images and Full Filter Lists.")
