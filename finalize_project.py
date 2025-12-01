import os
import re

print("🧹 Finalizing project code...")

# ---------------------------------------------------------
# 1. CLEAN APP.PY (Remove Photo Logic, Ensure Time Fix)
# ---------------------------------------------------------
with open('app.py', 'r') as f:
    content = f.read()

# A. Remove Photo Model Column
content = re.sub(r'\s+photo_path = db\.Column\(db\.String\(300\)\)', '', content)

# B. Remove Upload Config
content = re.sub(r'app\.config\[\'UPLOAD_FOLDER\'\] = .*?MB Limit', '', content, flags=re.DOTALL)

# C. Remove Photo Processing Logic in new_carcass
# We remove the block starting from "Photo Logic" to the Carcass() call
content = re.sub(r'# Photo Logic.*?photo_filename = unique_name', '', content, flags=re.DOTALL)

# D. Remove photo_path argument in Carcass()
content = re.sub(r'\s+photo_path=photo_filename,?', '', content)

# E. Ensure Timestamp Fix is Applied (Safety Check)
# Ensure we don't have the double timedelta
content = re.sub(
    r'datetime\.fromisoformat\(dt\) \+ timedelta\(hours=5, minutes=30\)', 
    'datetime.fromisoformat(dt)', 
    content
)
content = re.sub(
    r'datetime\.fromisoformat\(collected_at_str\) \+ timedelta\(hours=5, minutes=30\)', 
    'datetime.fromisoformat(collected_at_str)', 
    content
)

with open('app.py', 'w') as f:
    f.write(content)
print("✅ app.py cleaned (Photo logic removed, Timestamps verified).")

# ---------------------------------------------------------
# 2. CLEAN TEMPLATES
# ---------------------------------------------------------

# A. Clean new_carcass.html (Remove file input)
with open('templates/new_carcass.html', 'r') as f:
    html = f.read()

# Remove enctype
html = html.replace(' enctype="multipart/form-data"', '')
# Remove file input block
html = re.sub(r'.*?<div class="form-text">Optional\. Max size 5MB\.</div>\s+</div>', '', html, flags=re.DOTALL)

with open('templates/new_carcass.html', 'w') as f:
    f.write(html)
print("✅ templates/new_carcass.html cleaned.")

# B. Clean carcass.html (Remove photo display)
with open('templates/carcass.html', 'r') as f:
    html = f.read()

# Remove View Photo Badge
html = re.sub(r'.*?View Photo\s+</a>\s+{% endif %}', '', html, flags=re.DOTALL)
# Remove Photo Image Display
html = re.sub(r'.*?{% endif %}', '', html, flags=re.DOTALL)

with open('templates/carcass.html', 'w') as f:
    f.write(html)
print("✅ templates/carcass.html cleaned.")

print("🎉 Project is ready to push!")
