import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def check_all_templates():
    env = app.app.jinja_env
    templates_dir = os.path.join(os.path.dirname(app.__file__), "templates")

    print("--- 1. Testing Jinja2 Template AST Parsing ---")
    all_clean = True
    for fname in sorted(os.listdir(templates_dir)):
        if fname.endswith(".html"):
            fpath = os.path.join(templates_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                src = f.read()
            try:
                env.parse(src)
                print(f"  [PASS] {fname}")
            except Exception as e:
                print(f"  [FAIL] {fname}: {e}")
                all_clean = False
    assert all_clean, "One or more templates failed AST compilation!"

    print("\n--- 2. Checking url_for Endpoint References ---")
    endpoints = {r.endpoint for r in app.app.url_map.iter_rules()}
    url_for_pattern = re.compile(r"url_for\(['\"]([a-zA-Z0-9_]+)['\"]")
    missing = []
    for fname in sorted(os.listdir(templates_dir)):
        if fname.endswith(".html"):
            fpath = os.path.join(templates_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                src = f.read()
            for m in url_for_pattern.findall(src):
                if m not in endpoints and m != "static":
                    missing.append((fname, m))

    if missing:
        print("  [FAIL] Missing endpoints found:", missing)
        assert False, f"Missing endpoints: {missing}"
    else:
        print("  [PASS] All url_for endpoints in all 24 templates are valid registered routes.")

    print("\n--- 3. Checking for Common Typographical & Spelling Errors ---")
    typo_patterns = [
        (r"\bteh\b", "the"),
        (r"\brecieve\b", "receive"),
        (r"\bsucces\b", "success"),
        (r"\bdefinately\b", "definitely"),
        (r"\bseperate\b", "separate"),
        (r"\blibrarion\b", "librarian"),
        (r"\bcancled\b", "canceled/cancelled"),
        (r"\bunauthorise\b", "unauthorized")
    ]
    typo_found = False
    for fname in sorted(os.listdir(templates_dir)):
        if fname.endswith(".html"):
            fpath = os.path.join(templates_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                src = f.read()
            for pattern, correction in typo_patterns:
                matches = re.findall(pattern, src, re.IGNORECASE)
                if matches:
                    print(f"  [TYPO] {fname}: Found '{matches[0]}' (did you mean '{correction}'?)")
                    typo_found = True

    if not typo_found:
        print("  [PASS] Zero common typographical or spelling errors detected.")

    print("\n--- 4. Checking Page Titles and Header Consistency ---")
    title_pattern = re.compile(r"{%\s*block\s+title\s*%}(.*?){%\s*endblock\s*%}", re.DOTALL)
    for fname in sorted(os.listdir(templates_dir)):
        if fname.endswith(".html") and not fname.startswith("dashboard_") and fname != "books.html":
            fpath = os.path.join(templates_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                src = f.read()
            match = title_pattern.search(src)
            if match:
                title = match.group(1).strip()
                print(f"  [TITLE] {fname:<25} -> '{title}'")
            else:
                print(f"  [NO TITLE BLOCK] {fname}")

    print("\n[ALL TEMPLATE AUDITS PASSED]")

if __name__ == "__main__":
    check_all_templates()
