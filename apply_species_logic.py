import os

# ---------------------------------------------------------
# 1. DEFINE NEW TEMPLATES WITH JAVASCRIPT LOGIC
# ---------------------------------------------------------

# NEW CARCASS TEMPLATE
new_carcass_html = """{% extends "base.html" %}
{% block content %}

<div class="row justify-content-center mt-3">
  <div class="col-lg-8">
    <div class="card shadow-sm p-4">

      <h3 class="mb-3">
        <i class="fa-solid fa-skull-crossbones me-2"></i>
        Report Carcass
      </h3>

      <form method="POST">

        <div class="mb-3">
          <label class="form-label">Site</label>
          <select name="site_id" class="form-select" required>
            <option value="">Select site...</option>
            {% for s in sites %}
              <option value="{{ s.id }}" {% if site_id == s.id %} selected {% endif %}>
                {{ s.code }} — {{ s.name }}
              </option>
            {% endfor %}
          </select>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label">Animal Type</label>
            <select name="animal_type" id="animalType" class="form-select" onchange="updateSpeciesOptions()" required>
              <option value="Unknown">Unknown</option>
              <option value="Wild Animal">Wild Animal</option>
              <option value="Domestic Animal">Domestic Animal</option>
            </select>
          </div>

          <div class="col-md-6 mb-3">
            <label class="form-label">Species</label>
            
            <select name="species_select" id="speciesSelect" class="form-select" onchange="checkSpeciesOther()">
              </select>

            <div id="speciesCustomDiv" class="mt-2" style="display:none;">
              <input name="species_custom" id="speciesCustomInput" class="form-control" placeholder="Type species name...">
            </div>
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Date & Time Found</label>
          <input name="datetime" class="form-control" placeholder="YYYY-MM-DDTHH:MM:SS">
          <div class="form-text">Auto-filled with current local time.</div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label">Latitude</label>
            <input name="latitude" class="form-control" placeholder="Auto-filled">
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label">Longitude</label>
            <input name="longitude" class="form-control" placeholder="Auto-filled">
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Notes</label>
          <textarea name="notes" class="form-control" rows="3" placeholder="Optional notes"></textarea>
        </div>

        <button class="btn btn-primary w-100">
          <i class="fa-solid fa-check me-1"></i>
          Save Carcass
        </button>

      </form>

    </div>
  </div>
</div>

<script>
const speciesMap = {
  "Wild Animal": ["Jackal", "Jungle Cat", "Civet", "Other"],
  "Domestic Animal": ["Cattle", "Dog", "Buffalo", "Cat", "Other"],
  "Unknown": ["Unknown", "Other"]
};

function updateSpeciesOptions() {
  const typeSelect = document.getElementById('animalType');
  const speciesSelect = document.getElementById('speciesSelect');
  const type = typeSelect.value;
  const options = speciesMap[type] || ["Unknown", "Other"];

  speciesSelect.innerHTML = "";
  options.forEach(opt => {
    const el = document.createElement("option");
    el.value = opt;
    el.textContent = opt;
    speciesSelect.appendChild(el);
  });
  
  checkSpeciesOther();
}

function checkSpeciesOther() {
  const speciesSelect = document.getElementById('speciesSelect');
  const customDiv = document.getElementById('speciesCustomDiv');
  const customInput = document.getElementById('speciesCustomInput');

  if (speciesSelect.value === 'Other') {
    customDiv.style.display = 'block';
    customInput.required = true;
  } else {
    customDiv.style.display = 'none';
    customInput.required = false;
    customInput.value = ""; 
  }
}

// Initialize on load
document.addEventListener("DOMContentLoaded", function() {
  updateSpeciesOptions();
});
</script>

{% endblock %}
"""

# EDIT CARCASS TEMPLATE (With Pre-fill Logic)
edit_carcass_html = """{% extends "base.html" %}
{% block content %}

<div class="row justify-content-center">
  <div class="col-lg-6">
    <div class="card shadow-sm p-4">

      <h3 class="mb-3">Edit Carcass {{ c.code }}</h3>

      <form method="POST">

        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label">Animal Type</label>
            <select name="animal_type" id="animalType" class="form-select" onchange="updateSpeciesOptions()">
              <option value="Unknown" {% if c.animal_type == 'Unknown' %}selected{% endif %}>Unknown</option>
              <option value="Wild Animal" {% if c.animal_type == 'Wild Animal' %}selected{% endif %}>Wild Animal</option>
              <option value="Domestic Animal" {% if c.animal_type == 'Domestic Animal' %}selected{% endif %}>Domestic Animal</option>
            </select>
          </div>

          <div class="col-md-6 mb-3">
            <label class="form-label">Species</label>
            <select name="species_select" id="speciesSelect" class="form-select" onchange="checkSpeciesOther()">
              </select>
            
            <div id="speciesCustomDiv" class="mt-2" style="display:none;">
              <input name="species_custom" id="speciesCustomInput" class="form-control" placeholder="Type species name...">
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-6 mb-3">
             <label class="form-label">Latitude</label>
             <input name="latitude" class="form-control" value="{{ c.latitude }}">
          </div>
          <div class="col-6 mb-3">
             <label class="form-label">Longitude</label>
             <input name="longitude" class="form-control" value="{{ c.longitude }}">
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Notes</label>
          <textarea name="notes" class="form-control" rows="3">{{ c.notes }}</textarea>
        </div>

        <button class="btn btn-success w-100">Update Carcass</button>
        <a href="{{ url_for('view_carcass', carcass_id=c.id) }}" class="btn btn-link w-100 mt-2">Cancel</a>
      </form>

    </div>
  </div>
</div>

<script>
const speciesMap = {
  "Wild Animal": ["Jackal", "Jungle Cat", "Civet", "Other"],
  "Domestic Animal": ["Cattle", "Dog", "Buffalo", "Cat", "Other"],
  "Unknown": ["Unknown", "Other"]
};

function updateSpeciesOptions() {
  const typeSelect = document.getElementById('animalType');
  const speciesSelect = document.getElementById('speciesSelect');
  const type = typeSelect.value;
  const options = speciesMap[type] || ["Unknown", "Other"];

  // Save selection if trying to persist, otherwise just reset
  speciesSelect.innerHTML = "";
  options.forEach(opt => {
    const el = document.createElement("option");
    el.value = opt;
    el.textContent = opt;
    speciesSelect.appendChild(el);
  });
  
  checkSpeciesOther();
}

function checkSpeciesOther() {
  const speciesSelect = document.getElementById('speciesSelect');
  const customDiv = document.getElementById('speciesCustomDiv');
  const customInput = document.getElementById('speciesCustomInput');

  if (speciesSelect.value === 'Other') {
    customDiv.style.display = 'block';
    customInput.required = true;
  } else {
    customDiv.style.display = 'none';
    customInput.required = false;
  }
}

// Initialization Logic to handle saved data
document.addEventListener("DOMContentLoaded", function() {
  const savedSpecies = "{{ c.species }}";
  
  // 1. Populate dropdown based on the loaded Animal Type
  updateSpeciesOptions();
  
  const speciesSelect = document.getElementById('speciesSelect');
  const customInput = document.getElementById('speciesCustomInput');

  // 2. Try to select the saved species in the dropdown
  let found = false;
  for(let i=0; i<speciesSelect.options.length; i++){
    if(speciesSelect.options[i].value === savedSpecies){
      speciesSelect.selectedIndex = i;
      found = true;
      break;
    }
  }
  
  // 3. If not found in list (and not empty), it must be a custom "Other" value
  if(!found && savedSpecies && savedSpecies !== 'None') {
    speciesSelect.value = 'Other';
    checkSpeciesOther(); // Show the input
    customInput.value = savedSpecies;
  }
});
</script>

{% endblock %}
"""

os.makedirs('templates', exist_ok=True)
with open('templates/new_carcass.html', 'w') as f: f.write(new_carcass_html)
with open('templates/edit_carcass.html', 'w') as f: f.write(edit_carcass_html)
print("✅ Updated HTML templates.")

# ---------------------------------------------------------
# 2. UPDATE APP.PY LOGIC TO HANDLE "OTHER" INPUT
# ---------------------------------------------------------

with open('app.py', 'r') as f:
    code = f.read()

# Logic to inject for calculating the final species string
# It checks if dropdown is 'Other', if so uses the text input.
new_species_logic = "(request.form.get('species_custom') if request.form.get('species_select') == 'Other' else request.form.get('species_select'))"

# 1. Update NEW CARCASS route
# Look for: species=request.form.get('species') ... or similar from previous edits
# We'll replace the line entirely to be safe.
if "species=request.form.get('species')" in code:
    code = code.replace(
        "species=request.form.get('species')",
        f"species={new_species_logic}"
    )
elif "species=species" in code: # From previous apply_animal_type.py
    # If using variable from previous edit, we replace the variable assignment if possible
    # Easier: Replace the variable usage inside the Carcass(...) constructor
    # Current state likely: species=species, where species comes from form
    # Let's target the variable assignment in 'new_carcass' if it exists
    pass 

# Actually, the most robust way given previous edits is to just look for the form getter 
# because we might have variables like `species = request.form.get('species')`
code = code.replace("request.form.get('species')", new_species_logic)

# 2. Update EDIT CARCASS route
# In edit_carcass, we might have: c.species = request.form.get('species')
# The replacement above handles this too because it targets the string "request.form.get('species')" globally.

# However, we need to be careful not to break other things.
# Let's refine.

with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Fix the NEW CARCASS and EDIT CARCASS logic
    if "request.form.get('species')" in line:
        # Replace simple get with the conditional logic
        line = line.replace(
            "request.form.get('species')", 
            new_species_logic
        )
    
    # Check if we accidentally replaced it in a way that creates double logic
    # (e.g. if previous script did something complex). 
    # But generally "request.form.get('species')" is the key signature.
    
    new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Updated app.py species logic.")
print("🎉 Done! Restart the app.")
