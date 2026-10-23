import os
import sys
import re

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_session

def test_template_contents():
    print("--- 1. Testing templates/dashboard.html and templates/base.html ---")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dash_path = os.path.join(base_dir, "templates", "dashboard.html")
    base_path = os.path.join(base_dir, "templates", "base.html")

    with open(dash_path, "r", encoding="utf-8") as f:
        dash_html = f.read()

    with open(base_path, "r", encoding="utf-8") as f:
        base_html = f.read()

    # 1. Check Table Header Clipping & table-responsive
    assert ".table-responsive" in dash_html, "dashboard.html must define .table-responsive in CSS"
    assert "min-width: 780px" in dash_html or "min-width:" in dash_html, ".data-table must have min-width defined"
    
    # Verify the 3 tables have table-responsive
    assert re.search(r'Active Borrowers Ledger.*?<div class="[^"]*table-responsive[^"]*">', dash_html, re.DOTALL), "Active Borrowers Ledger must have table-responsive wrapper"
    assert re.search(r'Overdue Borrowers Watchlist.*?<div class="[^"]*table-responsive[^"]*">', dash_html, re.DOTALL), "Overdue Borrowers Watchlist must have table-responsive wrapper"
    assert re.search(r'Outstanding Disciplinary Liabilities.*?<div class="[^"]*table-responsive[^"]*">', dash_html, re.DOTALL), "Outstanding Disciplinary Liabilities must have table-responsive wrapper"
    print("[PASS] Item 1: All 3 admin tables have table-responsive wrapper and min-width CSS")

    # 2. Check Standardize Request Status Badge
    assert "Collected &amp; Issued" not in dash_html, "Found old 'Collected & Issued' badge in dashboard.html"
    assert "Collected & Issued" not in dash_html, "Found old 'Collected & Issued' badge in dashboard.html"
    assert '<span class="badge badge-success">Fulfilled</span>' in dash_html, "Expected '<span class=\"badge badge-success\">Fulfilled</span>' in dashboard.html"
    print("[PASS] Item 2: Request status badge standardized to 'Fulfilled'")

    # 3. Check Prerequisite Badges Clickable
    assert re.search(r'<a href="[^"]*category_books[^"]*"[^>]*>\s*<span class="badge"[^>]*>.*?Prerequisite:.*?</span>\s*</a>', dash_html, re.DOTALL), "Prerequisite pill must be wrapped in a link"
    print("[PASS] Item 3: Prerequisite badges are wrapped in hyperlinks to catalog/category")

    # 4. Check Pad Flash Banners in base.html
    assert "padding-right: 1.5rem" in base_html, "base.html .flash-alert must have 'padding-right: 1.5rem'"
    print("[PASS] Item 4: Flash alerts in base.html have padding-right: 1.5rem")

def test_routes_rendering():
    print("\n--- 2. Testing /dashboard routes rendering with Flask test client ---")
    client = app.test_client()

    # Test Admin Dashboard
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["logged_in"] = True

    res = client.get("/dashboard")
    assert res.status_code == 200, f"Admin dashboard returned status {res.status_code}"
    html = res.get_data(as_text=True)

    assert "Active Borrowers Ledger" in html
    assert "table-responsive" in html
    assert "Collected & Issued" not in html
    print("[PASS] Admin dashboard renders with table-responsive wrappers")

    # Test Student Dashboard (karthik)
    with client.session_transaction() as sess:
        sess["user_id"] = 10
        sess["username"] = "karthik"
        sess["role"] = "Student"
        sess["logged_in"] = True

    res = client.get("/dashboard")
    assert res.status_code == 200, f"Student dashboard returned status {res.status_code}"
    html = res.get_data(as_text=True)

    assert "My Active Loans" in html
    assert "table-responsive" in html
    assert "Collected & Issued" not in html
    if "Prerequisite:" in html:
        assert re.search(r'<a href="[^"]*category[^"]*"[^>]*>\s*<span class="badge"[^>]*>.*?Prerequisite:', html, re.DOTALL), "Rendered student prerequisite badge must be wrapped in <a>"
        print("[PASS] Student dashboard renders clickable prerequisite badges")
    else:
        print("[INFO] Student user has no active loans with prerequisites currently in DB")

    # Test Flash Banner
    with client.session_transaction() as sess:
        sess["user_id"] = 10
        sess["username"] = "karthik"
        sess["role"] = "Student"
        sess["logged_in"] = True

    # Call a route that flashes a message, or check base template inclusion
    res = client.get("/books")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "padding-right: 1.5rem" in html, "Rendered page head contains .flash-alert padding-right: 1.5rem"
    print("[PASS] Flash alert banner CSS padding-right: 1.5rem verified on rendered page")

if __name__ == "__main__":
    test_template_contents()
    test_routes_rendering()
    print("\nALL 4 DASHBOARD ADJUSTMENTS VERIFIED SUCCESSFULLY!")
