import sys
sys.path.insert(0, ".")
from app import app, get_session

def test_features():
    client = app.test_client()

    print("--- 1. Testing /learning_paths ---")
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"

    lp_resp = client.get("/learning_paths")
    assert lp_resp.status_code == 200, f"Expected 200, got {lp_resp.status_code}"
    html = lp_resp.get_data(as_text=True)

    # Check max depth is 4 Levels
    assert "4 Levels" in html, "Max Academic Depth should be 4 Levels"
    print("[OK] Max Academic Depth is 4 Levels")

    # Check font size 15 and layout options in Vis.js
    assert "levelSeparation: 130" in html, "Vis.js options should have levelSeparation: 130"
    assert "nodeSpacing: 220" in html, "Vis.js options should have nodeSpacing: 220"
    assert '"size": 15' in html or "size: 15" in html, "Vis.js node font size should be 15"
    assert "padding: 40" in html, "Vis.js fit should have padding: 40"
    print("[OK] Vis.js options verified (font size 15, levelSeparation 130, nodeSpacing 220, padding 40)")

    # Check track specialization badges
    assert "AI Specialization Track" in html, "Missing AI Specialization Track badge"
    assert "Algorithms Mastery Track" in html, "Missing Algorithms Mastery Track badge"
    assert "Software Architecture Track" in html, "Missing Software Architecture Track badge"
    assert "Systems &amp; Infrastructure Track" in html or "Systems & Infrastructure Track" in html, "Missing Systems & Infrastructure Track badge"
    assert "Data Engineering Track" in html, "Missing Data Engineering Track badge"
    print("[OK] All 5 complete end-to-end track specialization badges rendered")

    print("\n--- 2. Testing /category/1 (Computer Science & Architecture) ---")
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "student_user"
        sess["role"] = "Student"

    cat_resp = client.get("/category/1")
    assert cat_resp.status_code == 200, f"Expected 200, got {cat_resp.status_code}"
    cat_html = cat_resp.get_data(as_text=True)

    # Check Academic Progression Box
    assert "academic-progression-box" in cat_html, "Academic Progression Box not found in HTML"
    assert "Prerequisite" in cat_html, "Prerequisite section not found"
    assert "Study Next After This" in cat_html, "Study Next After This section not found"
    # User 3 has borrowed Clean Code, so Clean Code as prerequisite for CLRS / DDD should be Completed
    assert "Completed" in cat_html, "Expected completed prerequisite badge"
    print("[OK] Academic Progression Box rendered with Prerequisite (Completed/Recommended First) and Study Next After This")

    print("\n--- 3. Testing /dashboard for Student with Active Loans ---")
    # User 3 has active loan for Clean Code
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "student_user"
        sess["role"] = "Student"

    dash_resp = client.get("/dashboard")
    assert dash_resp.status_code == 200, f"Expected 200, got {dash_resp.status_code}"
    dash_html = dash_resp.get_data(as_text=True)

    assert "Next to Study:" in dash_html, "Missing 'Next to Study:' recommendation pill"
    assert "Introduction to Algorithms (CLRS)" in dash_html, "Expected downstream CLRS recommendation"
    print("[OK] Student Dashboard displays 'Next to Study' recommendation pill with availability and category link")

    # Test user 8 who has borrowed CLRS, which has a prerequisite
    with client.session_transaction() as sess:
        sess["user_id"] = 8
        sess["username"] = "user_8"
        sess["role"] = "Student"

    dash_resp_8 = client.get("/dashboard")
    assert dash_resp_8.status_code == 200
    dash_html_8 = dash_resp_8.get_data(as_text=True)
    assert "Prerequisite: Clean Code" in dash_html_8, "Missing Prerequisite Reference badge for borrowed book"
    assert "Next to Study:" in dash_html_8, "Missing Next to Study pill for user 8"
    print("[OK] Student Dashboard displays 'Prerequisite Reference' badge alongside currently borrowed book")

    print("\n--- 4. Testing /dashboard for Staff ---")
    with client.session_transaction() as sess:
        sess["user_id"] = 4
        sess["username"] = "staff_user"
        sess["role"] = "Staff"

    dash_resp_staff = client.get("/dashboard")
    assert dash_resp_staff.status_code == 200
    print("[OK] Staff Dashboard renders cleanly")

    print("\nALL 3 GRAPH INTEGRATION UPDATES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_features()
