import os

# ---------------------------------------------------------
# UPDATE MAP TEMPLATE WITH USER LOCATION
# ---------------------------------------------------------
map_html = """{% extends "base.html" %}
{% block content %}

<div class="card shadow-sm">
  <div class="card-header bg-white d-flex justify-content-between align-items-center">
    <h5 class="mb-0"><i class="fa-solid fa-map me-2"></i> Carcass Map</h5>
    <button class="btn btn-sm btn-primary" onclick="locateUser()">
      <i class="fa-solid fa-location-crosshairs me-1"></i> My Location
    </button>
  </div>
  <div class="card-body p-0">
    <div id="map" style="height: 600px; width: 100%;"></div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

<script>
var map;
var userMarker;

document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Initialize Map
  map = L.map('map').setView([20.5937, 78.9629], 5);

  // 2. Add OpenStreetMap Tiles
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  // 3. Add Carcass Markers
  var markers = [];
  
  {% for c in carcasses %}
    {% if c.latitude and c.longitude %}
      var marker = L.marker([{{ c.latitude }}, {{ c.longitude }}]).addTo(map);
      
      var popupContent = `
        <div style="min-width: 150px;">
          <h6 class="mb-1 text-primary">{{ c.species or 'Unknown' }}</h6>
          <span class="badge bg-secondary mb-2">{{ c.animal_type or 'Unknown Type' }}</span>
          <p class="mb-1 small"><strong>Site:</strong> {{ c.site.code }}</p>
          <p class="mb-2 small text-muted">{{ c.datetime_found.strftime('%Y-%m-%d') }}</p>
          <a href="{{ url_for('view_carcass', carcass_id=c.id) }}" class="btn btn-sm btn-outline-primary w-100">View</a>
        </div>
      `;
      
      marker.bindPopup(popupContent);
      markers.push(marker);
    {% endif %}
  {% endfor %}

  // 4. Fit bounds if markers exist
  if (markers.length > 0) {
    var group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
});

// 5. User Location Function
function locateUser() {
  map.locate({setView: true, maxZoom: 16});
}

// 6. Handle Location Found
// Leaflet fires 'locationfound' when it successfully gets the user's GPS
// We wait for the map to initialize, then attach the listener.
// Since 'map' is var, we can attach it after DOM load or inside.
// Best to attach it inside DOMContentLoaded or via map.on calls if map is global.
// Let's attach it inside the init block above? 
// Actually, since 'map' is global var declared at top, we can attach listeners here 
// BUT map isn't assigned until DOMContentLoaded runs.
// So we'll move the listener logic INTO the DOMContentLoaded block below.

document.addEventListener("DOMContentLoaded", function() {
    map.on('locationfound', function(e) {
        var radius = e.accuracy;

        if (userMarker) {
            map.removeLayer(userMarker);
        }

        userMarker = L.marker(e.latlng).addTo(map)
            .bindPopup("You are within " + radius + " meters from this point").openPopup();

        L.circle(e.latlng, radius).addTo(map);
    });

    map.on('locationerror', function(e) {
        alert("Location access denied or unavailable.");
    });
});
</script>
{% endblock %}
"""

os.makedirs('templates', exist_ok=True)
with open('templates/map.html', 'w') as f:
    f.write(map_html)

print("✅ Updated templates/map.html with user location feature.")
print("🎉 Done! Refresh the Map page.")
