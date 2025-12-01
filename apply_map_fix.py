import os

# ---------------------------------------------------------
# 1. CREATE ROBUST MAP TEMPLATE
# ---------------------------------------------------------
map_html = """{% extends "base.html" %}
{% block content %}

<div class="card shadow-sm">
  <div class="card-header bg-white d-flex justify-content-between align-items-center">
    <h5 class="mb-0"><i class="fa-solid fa-map-location-dot me-2"></i> Carcass & Sample Map</h5>
    <button class="btn btn-sm btn-primary" onclick="locateUser()">
      <i class="fa-solid fa-location-arrow me-1"></i> My Location
    </button>
  </div>
  <div class="card-body p-0">
    <div id="map" style="height: 75vh; width: 100%;"></div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
var map;
var userMarker;

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Init Map
  map = L.map('map').setView([20.5937, 78.9629], 5); // Default center (India)

  // 2. Tile Layer
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  // 3. Add Markers
  var markers = [];
  
  {% for c in carcasses %}
    {% if c.latitude and c.longitude %}
      var lat = {{ c.latitude }};
      var lng = {{ c.longitude }};
      
      // Create Marker
      var marker = L.marker([lat, lng]).addTo(map);
      
      // Build Popup Content
      var popupHtml = `
        <div class="p-1">
          <h6 class="mb-1 fw-bold text-primary">{{ c.code }}</h6>
          <div class="mb-2">
            <span class="badge bg-secondary">{{ c.species or 'Unknown' }}</span>
            <span class="badge bg-light text-dark border">{{ c.site.code }}</span>
          </div>
          
          <div class="small mb-2 text-muted">
            Found: {{ c.datetime_found.strftime('%Y-%m-%d') }}
          </div>

          <div class="border-top pt-2 mb-2">
            <strong>Samples ({{ c.samples|length }}):</strong>
            <ul class="ps-3 mb-0 small">
              {% for s in c.samples %}
                <li>{{ s.sample_type or 'Unknown' }} <span class="text-muted">({{ s.label|truncate(10, True, '...') }})</span></li>
              {% else %}
                <li class="text-muted fst-italic">No samples</li>
              {% endfor %}
            </ul>
          </div>

          <a href="{{ url_for('view_carcass', carcass_id=c.id) }}" class="btn btn-sm btn-outline-primary w-100 mt-2">View Full Details</a>
        </div>
      `;
      
      marker.bindPopup(popupHtml);
      markers.push(marker);
    {% endif %}
  {% endfor %}

  // 4. Auto-fit Bounds
  if (markers.length > 0) {
    var group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
});

// User Location Logic
function locateUser() {
  map.locate({setView: true, maxZoom: 16});
}

// Listeners for Location
document.addEventListener("DOMContentLoaded", function() {
    // We attach listeners to the map object after it's created
    // A small timeout ensures map var is ready, though DOMContentLoaded usually handles seq correctly
    setTimeout(() => {
        if(!map) return;
        
        map.on('locationfound', function(e) {
            var radius = e.accuracy;
            if (userMarker) map.removeLayer(userMarker);
            
            userMarker = L.marker(e.latlng).addTo(map)
                .bindPopup("You are within " + Math.round(radius) + " meters of this point").openPopup();
            
            L.circle(e.latlng, radius).addTo(map);
        });

        map.on('locationerror', function(e) {
            alert("Could not access location: " + e.message);
        });
    }, 500);
});
</script>
{% endblock %}
"""

os.makedirs('templates', exist_ok=True)
with open('templates/map.html', 'w') as f:
    f.write(map_html)
print("✅ Re-created templates/map.html")


# ---------------------------------------------------------
# 2. INJECT ROUTE INTO APP.PY
# ---------------------------------------------------------
# We need to make sure we import 'joinedload' if we want optimization, 
# but for simplicity we will rely on lazy loading or standard access.

map_route_code = """
    # ---------------- MAP VIEW ----------------
    @app.route('/map')
    def map_view():
        # Filter carcasses that actually have GPS data
        carcasses = Carcass.query.filter(
            Carcass.latitude.isnot(None), 
            Carcass.longitude.isnot(None)
        ).all()
        return render_template('map.html', carcasses=carcasses)
"""

with open('app.py', 'r') as f:
    content = f.read()

# Only inject if not present
if "def map_view():" not in content:
    # Inject before the Gunicorn entry point
    anchor = "# ========================\n# GUNICORN ENTRYPOINT"
    if anchor in content:
        content = content.replace(anchor, map_route_code + "\n\n" + anchor)
        with open('app.py', 'w') as f:
            f.write(content)
        print("✅ Injected /map route into app.py")
    else:
        print("⚠️ Could not find injection anchor in app.py")
else:
    print("ℹ️ /map route already exists.")


# ---------------------------------------------------------
# 3. ENSURE NAVBAR LINK
# ---------------------------------------------------------
link_html = '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'map_view\') }}">Map</a></li>'
with open('templates/base.html', 'r') as f:
    base_html = f.read()

target = 'href="{{ url_for(\'index\') }}">Home</a></li>'
if 'href="{{ url_for(\'map_view\') }}"' not in base_html:
    if target in base_html:
        base_html = base_html.replace(target, target + "\n        " + link_html)
        with open('templates/base.html', 'w') as f:
            f.write(base_html)
        print("✅ Added 'Map' tab to Navbar.")
else:
    print("ℹ️ Map link already in Navbar.")

print("🎉 Fix applied. Restart your app!")
