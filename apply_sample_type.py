import os

# ---------------------------------------------------------
# 1. DEFINE NEW HTML TEMPLATES
# ---------------------------------------------------------

# OPTIONS LIST for injection into JS
sample_options = [
    "Nasal Swab", "Oral Swab", "Rectal Swab", 
    "Brain Swab", "Brain Tissue", "Lung Tissue", "Liver Tissue", 
    "Urinary Bladder Swab", "Urinary Bladder Tissue", "Other"
]

# NEW SAMPLE TEMPLATE
new_sample_html = """{% extends "base.html" %}
{% block content %}

<div class="row justify-content-center mt-3">
  <div class="col-lg-7">

    <div class="card shadow-sm p-4">

      <h3 class="mb-3">
        <i class="fa-solid fa-vial me-2"></i>
        New Sample for Carcass {{ c.code }}
      </h3>

      <p class="text-muted">
        Species: <strong>{{ c.species }}</strong> •
        Site: <strong>{{ c.site.code }}</strong>
      </p>

      <form method="POST">

        <div class="mb-3">
          <label class="form-label">Sample Type</label>
          <select name="sample_type_select" id="sampleTypeSelect" class="form-select" onchange="checkSampleTypeOther()" required>
            <option value="">Select type...</option>
            {% for opt in options %}
              <option value="{{ opt }}">{{ opt }}</option>
            {% endfor %}
          </select>

          <div id="sampleTypeCustomDiv" class="mt-2" style="display:none;">
            <input name="sample_type_custom" id="sampleTypeCustomInput" class="form-control" placeholder="Specify sample type...">
          </div>
        </div>

        <input type="hidden" name="collected_at">

        <div class="mb-3">
          <label class="form-label">Collected By</label>
          <input name="collected_by" class="form-control" value="{{ current_user.username }}" readonly>
        </div>

        <div class="mb-3">
          <label class="form-label">Storage</label>
          <input name="storage" class="form-control" placeholder="e.g. -80°C freezer">
        </div>

        <div class="mb-3">
          <label class="form-label">Notes</label>
          <textarea name="notes" class="form-control" rows="3" placeholder="Optional"></textarea>
        </div>

        <div class="d-grid gap-2">
          <button type="submit" name="action" value="add_more" class="btn btn-primary">
            <i class="fa-solid fa-plus me-1"></i> Add Another Sample
          </button>
          <button type="submit" name="action" value="finish" class="btn btn-success">
            <i class="fa-solid fa-check me-1"></i> Finish
          </button>
        </div>

      </form>

    </div>
  </div>
</div>

<script>
function checkSampleTypeOther() {
  const select = document.getElementById('sampleTypeSelect');
  const customDiv = document.getElementById('sampleTypeCustomDiv');
  const customInput = document.getElementById('sampleTypeCustomInput');

  if (select.value === 'Other') {
    customDiv.style.display = 'block';
    customInput.required = true;
  } else {
    customDiv.style.display = 'none';
    customInput.required = false;
    customInput.value = "";
  }
}
</script>

{% endblock %}
""".replace("{% for opt in options %}", "{% for opt in " + str(sample_options) + " %}")


# EDIT SAMPLE TEMPLATE
edit_sample_html = """{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-lg-6">
    <div class="card shadow-sm p-4">
      <h3>Edit Sample {{ s.label }}</h3>
      <form method="POST">
        
        <div class="mb-3">
          <label class="form-label">Sample Type</label>
          <select name="sample_type_select" id="sampleTypeSelect" class="form-select" onchange="checkSampleTypeOther()" required>
            <option value="">Select type...</option>
            {% for opt in options %}
              <option value="{{ opt }}">{{ opt }}</option>
            {% endfor %}
          </select>

          <div id="sampleTypeCustomDiv" class="mt-2" style="display:none;">
            <input name="sample_type_custom" id="sampleTypeCustomInput" class="form-control" placeholder="Specify sample type...">
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label">Storage</label>
          <input name="storage" class="form-control" value="{{ s.storage }}">
        </div>
        <div class="mb-3">
          <label class="form-label">Notes</label>
          <textarea name="notes" class="form-control" rows="3">{{ s.notes }}</textarea>
        </div>
        <button class="btn btn-success w-100">Update Sample</button>
        <a href="{{ url_for('view_sample', sample_id=s.id) }}" class="btn btn-link w-100 mt-2">Cancel</a>
      </form>
    </div>
  </div>
</div>

<script>
function checkSampleTypeOther() {
  const select = document.getElementById('sampleTypeSelect');
  const customDiv = document.getElementById('sampleTypeCustomDiv');
  const customInput = document.getElementById('sampleTypeCustomInput');

  if (select.value === 'Other') {
    customDiv.style.display = 'block';
    customInput.required = true;
  } else {
    customDiv.style.display = 'none';
    customInput.required = false;
  }
}

document.addEventListener("DOMContentLoaded", function() {
  const savedType = "{{ s.sample_type }}";
  const select = document.getElementById('sampleTypeSelect');
  const customInput = document.getElementById('sampleTypeCustomInput');

  let found = false;
  for(let i=0; i<select.options.length; i++){
    if(select.options[i].value === savedType){
      select.selectedIndex = i;
      found = true;
      break;
    }
  }

  // If the saved type isn't in the list (and isn't empty), it's a custom 'Other'
  if(!found && savedType && savedType !== 'None') {
    select.value = 'Other';
    checkSampleTypeOther();
    customInput.value = savedType;
  }
});
</script>
{% endblock %}
""".replace("{% for opt in options %}", "{% for opt in " + str(sample_options) + " %}")


os.makedirs('templates', exist_ok=True)
with open('templates/new_sample.html', 'w') as f: f.write(new_sample_html)
with open('templates/edit_sample.html', 'w') as f: f.write(edit_sample_html)
print("✅ Updated sample templates with dropdowns.")

# ---------------------------------------------------------
# 2. UPDATE APP.PY LOGIC
# ---------------------------------------------------------

with open('app.py', 'r') as f:
    code = f.read()

# Logic: If 'Other' is selected in dropdown, take the value from custom input.
new_sample_logic = "(request.form.get('sample_type_custom') if request.form.get('sample_type_select') == 'Other' else request.form.get('sample_type_select'))"

# We replace "request.form.get('sample_type')" which appears in both new_sample and edit_sample routes
# This is safe because we changed the HTML input name to 'sample_type_select'
if "request.form.get('sample_type')" in code:
    code = code.replace(
        "request.form.get('sample_type')", 
        new_sample_logic
    )
    with open('app.py', 'w') as f:
        f.write(code)
    print("✅ Updated app.py sample logic.")
else:
    print("⚠️ app.py not updated (logic might already exist).")

print("🎉 Done! Restart the app.")
