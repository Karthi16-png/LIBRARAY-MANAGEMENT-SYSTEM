import re
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import app

flask_endpoints = set(app.app.view_functions.keys())
flask_endpoints.add('static')

print(f"Registered Flask endpoints ({len(flask_endpoints)}):")
for ep in sorted(flask_endpoints):
    print(f"  - {ep}")

print("\n--- Checking url_for in app.py ---")
with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
    app_code = f.read()

app_url_fors = set(re.findall(r"url_for\([\"']([a-zA-Z0-9_]+)[\"']", app_code))
missing_in_app = app_url_fors - flask_endpoints
if missing_in_app:
    print(f"FAILED: Found invalid endpoints in app.py: {missing_in_app}")
else:
    print("PASSED: All url_for references in app.py match valid Flask routes.")

print("\n--- Checking url_for in all templates ---")
template_dir = os.path.join(BASE_DIR, "templates")
missing_in_templates = {}
for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith(".html"):
            fpath = os.path.join(root, file)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            matches = re.findall(r"url_for\([\"']([a-zA-Z0-9_]+)[\"']", content)
            for m in matches:
                if m not in flask_endpoints:
                    if m not in missing_in_templates:
                        missing_in_templates[m] = []
                    missing_in_templates[m].append(file)

if missing_in_templates:
    print(f"FAILED: Found invalid endpoints in templates: {missing_in_templates}")
else:
    print("PASSED: All url_for references in all templates match valid Flask routes.")
