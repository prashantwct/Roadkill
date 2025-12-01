import os

# ---------------------------------------------------------
# 1. CREATE MAP TEMPLATE (Leaflet.js)
# ---------------------------------------------------------
map_html = """{% extends "base.html" %}
{% block content %}

<div class="card shadow-sm">
  <div class="card-body p-0">
    <div id="map" style="height: 600px; width: 100%; border-radius: 4px;"></div>
  </div>
</div>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

<script>
document.addEventListener("DOMContentLoaded", function() {
  
  // 1. Initialize Map (Centered on India approx, or dynamic)
  // We start zoomed out, usually bounds will auto-fit later
  var map = L.map('map').setView([20.5937, 78.9629], 5);

  // 2. Add OpenStreetMap Tiles (Free)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // 3. Add Markers from Database Data
  var markers = [];
  
  {% for c in carcasses %}
    {% if c.latitude and c.longitude %}
      var marker = L.marker([{{ c.latitude }}, {{ c.longitude }}]).addTo(map);
      
      // Popup Content
      var popupContent = `
        <div style="min-width: 150px;">
          <h6 class="mb-1 text-primary">{{ c.species or 'Unknown Species' }}</h6>
          <p class="mb-1 small"><strong>Code:</strong> {{ c.code }}</p>
          <p class="mb-1 small"><strong>Site:</strong> {{ c.site.code }}</p>
          <p class="mb-2 small text-muted">{{ c.datetime_found.strftime('%Y-%m-%d') }}</p>
          <a href="{{ url_for('view_carcass', carcass_id=c.id) }}" class="btn btn-sm btn-primary w-100 text-white">View Details</a>
        </div>
      `;
      
      marker.bindPopup(popupContent);
      markers.push(marker);
    {% endif %}
  {% endfor %}

  // 4. Auto-fit map to show all markers
  if (markers.length > 0) {
    var group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
});
</script>
{% endblock %}
"""

os.makedirs('templates', exist_ok=True)
with open('templates/map.html', 'w') as f:
    f.write(map_html)
print("✅ Created templates/map.html")


# ---------------------------------------------------------
# 2. INJECT ROUTE INTO APP.PY
# ---------------------------------------------------------
map_route_code = """
    # ---------------- MAP VIEW ----------------
    @app.route('/map')
    def map_view():
        # Get all carcasses that have GPS coordinates
        carcasses = Carcass.query.filter(
            Carcass.latitude.isnot(None), 
            Carcass.longitude.isnot(None)
        ).all()
        return render_template('map.html', carcasses=carcasses)
"""

with open('app.py', 'r') as f:
    content = f.read()

# We inject this before the Gunicorn entrypoint, inside register_routes
anchor = "# ========================\n# GUNICORN ENTRYPOINT"
if anchor in content and "/map" not in content:
    content = content.replace(anchor, map_route_code + "\n\n" + anchor)
    with open('app.py', 'w') as f:
        f.write(content)
    print("✅ Injected /map route into app.py")
else:
    print("⚠️ /map route already exists or anchor not found.")


# ---------------------------------------------------------
# 3. ADD 'MAP' LINK TO NAVBAR (base.html)
# ---------------------------------------------------------
# We look for the "Home" link and add "Map" right after it.
link_html = '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'map_view\') }}">Map</a></li>'

with open('templates/base.html', 'r') as f:
    base_html = f.read()

target = 'href="{{ url_for(\'index\') }}">Home</a></li>'
if 'href="{{ url_for(\'map_view\') }}"' not in base_html:
    if target in base_html:
        # Insert after Home
        base_html = base_html.replace(target, target + "\n        " + link_html)
        with open('templates/base.html', 'w') as f:
            f.write(base_html)
        print("✅ Added 'Map' tab to Navbar.")
    else:
        print("⚠️ Could not find Home link in Navbar to append Map link.")
else:
    print("⚠️ Map link already in Navbar.")

print("🎉 Map feature added! Restart your app.")
