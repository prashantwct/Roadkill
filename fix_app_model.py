import os

print("🔧 Fixing Carcass model in app.py...")

with open('app.py', 'r') as f:
    code = f.read()

# The missing line we need to add
missing_col = "animal_type = db.Column(db.String(50))"

# The anchor line we look for to insert after
anchor = "species = db.Column(db.String(140))"

if anchor in code and missing_col not in code:
    # Add the column right after 'species'
    new_code = code.replace(anchor, anchor + "\n    " + missing_col)
    
    with open('app.py', 'w') as f:
        f.write(new_code)
    print("✅ Success: Added 'animal_type' to Carcass model.")
elif missing_col in code:
    print("ℹ️  'animal_type' already exists in the model.")
else:
    print("⚠️  Could not find the anchor line 'species = ...'. Please check app.py manually.")
