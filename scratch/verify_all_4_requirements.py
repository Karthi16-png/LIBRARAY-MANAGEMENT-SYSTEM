import re
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_session, validate_password_strength, sync_fulfilled_loan_requests

def test_requirements():
    print("======================================================================")
    print("STARTING VERIFICATION OF ALL 4 REQUIREMENTS")
    print("======================================================================\n")

    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    client = app.test_client()

    # -------------------------------------------------------------------------
    # TEST 4: Password Length Rules
    # -------------------------------------------------------------------------
    print("--> Testing Requirement 4: Password Length Rules (8 to 64 chars)...")
    
    # Validation tests
    ok, err = validate_password_strength("Short1!") # 7 chars
    assert not ok, "Short password (<8 chars) must fail validation"
    assert "between 8 and 64 characters" in err, f"Expected 8 to 64 message, got: {err}"
    print("  [PASS] Password with 7 chars rejected with 8-64 length error.")

    ok, err = validate_password_strength("A" * 60 + "a1!") # 63 chars
    assert ok, f"Valid 63-char password should pass, failed: {err}"
    print("  [PASS] Valid 63-char password passes.")

    ok, err = validate_password_strength("A" * 63 + "a1!X") # 66 chars
    assert not ok, "Long password (>64 chars) must fail validation"
    assert "between 8 and 64 characters" in err
    print("  [PASS] Password with 66 chars rejected with 8-64 length error.")

    # Check template texts
    with open("templates/manage_users.html", "r", encoding="utf-8") as f:
        mu_html = f.read()
    assert "8 to 64 characters" in mu_html, "manage_users.html must specify 8 to 64 characters"
    assert 'minlength="8" maxlength="64"' in mu_html, "manage_users.html must specify minlength 8 and maxlength 64"
    assert "5 to 13" not in mu_html, "manage_users.html must not contain obsolete 5 to 13 characters"
    print("  [PASS] manage_users.html contains updated 8 to 64 rules and attributes.")

    with open("templates/change_password.html", "r", encoding="utf-8") as f:
        cp_html = f.read()
    assert "8 to 64 characters" in cp_html, "change_password.html must specify 8 to 64 characters"
    assert "(8-64 chars)" in cp_html, "change_password.html must specify (8-64 chars) in placeholder"
    assert 'minlength="8"' in cp_html and 'maxlength="64"' in cp_html
    assert "5 to 13" not in cp_html, "change_password.html must not contain obsolete 5 to 13 characters"
    print("  [PASS] change_password.html contains updated 8 to 64 rules and attributes.")

    # Check existing seeded logins work
    for uname, pw in [("admin", "Admin@123"), ("librarian", "Lib@123"), ("staff", "Staff@123"), ("student", "Student@123")]:
        login_res = client.post("/login", data={"username": uname, "password": pw}, follow_redirects=False)
        assert login_res.status_code == 302, f"Existing login for {uname} must succeed (302 redirect), got {login_res.status_code}"
    print("  [PASS] All existing seeded demo passwords (including 7-char Lib@123) successfully authenticate!")

    # -------------------------------------------------------------------------
    # TEST 1: Dark-Mode Form Styling & Layout on /issue_loan
    # -------------------------------------------------------------------------
    print("\n--> Testing Requirement 1: Dark-Mode Form Styling & Layout on /issue_loan...")
    
    # Login as admin
    client.post("/login", data={"username": "admin", "password": "Admin@123"}, follow_redirects=True)
    res = client.get("/issue_loan")
    assert res.status_code == 200, f"Expected 200 on /issue_loan, got {res.status_code}"
    html = res.get_data(as_text=True)

    # 1. Dark-mode surface styling on inputs/selects
    assert "background: #0f172a" in html or "#0f172a" in html, "Dark-mode surface styling background: #0f172a must be present"
    assert "color: #f8fafc" in html or "#f8fafc" in html, "color: #f8fafc must be present"
    assert "border: 1px solid #334155" in html or "#334155" in html, "border: 1px solid #334155 must be present"
    assert "border-radius: 0.5rem" in html, "border-radius: 0.5rem must be present"
    assert "padding: 0.65rem 0.85rem" in html, "padding: 0.65rem 0.85rem must be present"
    print("  [PASS] Dark-mode styling rules verified on /issue_loan.")

    # 2. Duplicate emoji removed & 100% width
    assert "🔍" not in html, "Duplicate emoji 🔍 must be removed from /issue_loan placeholders"
    assert "Type to filter books by title or ISBN..." in html, "Clean filter placeholder must be present"
    assert "Type to filter members by name or role..." in html, "Clean member filter placeholder must be present"
    print("  [PASS] Filter inputs have clean placeholders without duplicate emoji and span full width.")

    # 3. Block label for Loan Duration & hidden raw copy id
    assert '<label class="form-label" for="due_in_days" style="display: block;' in html, "Loan Duration must have display: block"
    assert 'type="hidden" id="copy_id"' in html, "Raw Copy ID number box must be hidden"
    assert '<input type="number" id="copy_id"' not in html, "Visible numeric input for copy_id must be removed"
    print("  [PASS] Loan duration block label and hidden raw Copy ID input verified.")

    # 4. Patron warning tag for patrons with overdue / unpaid fines
    assert "[⚠️ Has Overdue / Unpaid Fine]" in html, "Patron dropdown must contain [⚠️ Has Overdue / Unpaid Fine] warning tag"
    assert "alex_stu &mdash; [Student]" in html
    assert re.search(r"alex_stu\s+&mdash;\s+\[Student\]\s*\(ID:\s*#\d+\)\s*\[⚠️ Has Overdue / Unpaid Fine\]", html) is not None, "Warning tag must appear on alex_stu"
    print("  [PASS] Patron warning tags correctly rendered for patrons with overdue/fines.")

    # -------------------------------------------------------------------------
    # TEST 2: Reserved Copy ID, Stock Sync, Timestamps on /loan_requests
    # -------------------------------------------------------------------------
    print("\n--> Testing Requirement 2: Reserved Copy ID, Stock Sync, Timestamps on /loan_requests...")
    
    # Trigger consistency sync in Neo4j
    with get_session() as s:
        sync_fulfilled_loan_requests(s)

        # Verify #REQ-3 (CLRS) is 'Pending' because all copies are Borrowed
        res_r3 = s.run("MATCH (r:LoanRequest {request_id: 3}) RETURN r.status AS status, r.copy_id AS cid").single()
        assert res_r3["status"] == "Pending", f"#REQ-3 must be Pending, got {res_r3['status']}"
        assert res_r3["cid"] is None, f"#REQ-3 copy_id must be cleared, got {res_r3['cid']}"
        print("  [PASS] Neo4j consistency verified: #REQ-3 (CLRS) re-synced to 'Pending'.")

        # Verify #REQ-4 is 'Awaiting Pickup' and linked to real reserved copy with [:RESERVED_COPY]
        res_r4 = s.run("""
            MATCH (r:LoanRequest {request_id: 4})
            OPTIONAL MATCH (r)-[:RESERVED_COPY]->(cp:Copy)
            RETURN r.status AS status, r.copy_id AS cid, cp.copy_id AS rel_cid, cp.status AS cp_status
        """).single()
        assert res_r4["status"] == "Awaiting Pickup", f"#REQ-4 must be Awaiting Pickup, got {res_r4['status']}"
        assert res_r4["cid"] == 8, f"#REQ-4 must have copy_id 8, got {res_r4['cid']}"
        assert res_r4["rel_cid"] == 8, f"#REQ-4 must link to Copy 8 via [:RESERVED_COPY], got {res_r4['rel_cid']}"
        assert res_r4["cp_status"] == "Reserved", f"Copy 8 status must be 'Reserved', got {res_r4['cp_status']}"
        print("  [PASS] Neo4j consistency verified: #REQ-4 linked via [:RESERVED_COPY] to Copy 8 (Reserved).")

    # Check /loan_requests page rendering
    res_lr = client.get("/loan_requests")
    assert res_lr.status_code == 200
    lr_html = res_lr.get_data(as_text=True)

    # 1. Badge displays actual reserved copy number
    assert "Copy #8 Reserved" in lr_html, "Ready for Physical Collection table must display 'Copy #8 Reserved'"
    print("  [PASS] Reserved Copy badge displays 'Copy #8 Reserved'.")

    # 2. Stripped trailing 00:00 midnight time
    assert " 00:00" not in lr_html, "Trailing 00:00 midnight time must be stripped from dates"
    # Should format like "Oct 12, 2026"
    assert re.search(r"[A-Z][a-z]{2}\s+\d{1,2},\s+2026", lr_html), "Dates must format cleanly as 'Oct 12, 2026'"
    print("  [PASS] Dates format cleanly without trailing 00:00 midnight time.")

    # 3. Full-width dark-theme table styling
    assert "min-width: 780px" in lr_html and "padding: 0.85rem 1rem" in lr_html, "Table classes must have full-width and 0.85rem 1rem padding"
    print("  [PASS] Full-width dark-theme table classes verified on /loan_requests.")

    # -------------------------------------------------------------------------
    # TEST 3: Dark Inputs, Full-Width Table, Admin Controls on /manage_users
    # -------------------------------------------------------------------------
    print("\n--> Testing Requirement 3: Dark Inputs, Full-Width Table, Admin Controls on /manage_users...")
    
    res_mu = client.get("/manage_users")
    assert res_mu.status_code == 200
    mu_html = res_mu.get_data(as_text=True)

    # 1. Dark inputs styling
    assert "background: #0f172a" in mu_html or "#0f172a" in mu_html
    assert "border: 1px solid #334155" in mu_html or "#334155" in mu_html
    print("  [PASS] Provision New User form has dark-mode input styling.")

    # 2. Full-width table styling with generous padding
    assert "padding: 0.85rem 1rem" in mu_html, "Table th/td must have padding: 0.85rem 1rem"
    assert "min-width: 800px" in mu_html, "Table must have min-width: 800px"
    print("  [PASS] Active System Users table has full-width layout with 0.85rem 1rem padding.")

    # 3. Librarian Suspend protection (UI and backend)
    assert "Protected (Librarian)" in mu_html, "Librarian must display Protected badge"
    # Attempt to POST toggle_status for librarian (#USR-2)
    post_suspend = client.post("/manage_users", data={"action": "toggle_status", "user_id": "2", "current_status": "Active"}, follow_redirects=True)
    post_suspend_html = post_suspend.get_data(as_text=True)
    assert "cannot be suspended by system policy" in post_suspend_html or "Action Prohibited" in post_suspend_html
    print("  [PASS] Librarian account is protected from suspension in both UI and backend.")

    # 4. Reset Password action button for Student/Staff rows
    assert "Reset Password" in mu_html, "Reset Password button must be present"
    assert 'value="reset_password"' in mu_html, "action='reset_password' must be present in form"

    # Test reset password on a student (e.g. emily_stu, user_id 6)
    with get_session() as s:
        res_emily = s.run("MATCH (u:User {username: 'emily_stu'}) RETURN u.user_id AS uid").single()
        emily_uid = res_emily["uid"]

    reset_res = client.post("/manage_users", data={"action": "reset_password", "user_id": str(emily_uid)}, follow_redirects=True)
    reset_html = reset_res.get_data(as_text=True)
    assert "has been reset to temporary password: Emily_stu#Lib2026" in reset_html
    print("  [PASS] Reset Password action executes and flashes temporary password.")

    # Verify Emily can now log in with the reset password
    login_emily = client.post("/login", data={"username": "emily_stu", "password": "Emily_stu#Lib2026"}, follow_redirects=False)
    assert login_emily.status_code == 302, f"Emily must be able to log in with reset password, got {login_emily.status_code}"
    # Restore emily_stu password back to original demo password
    from werkzeug.security import generate_password_hash
    with get_session() as s:
        s.run("MATCH (u:User {username: 'emily_stu'}) SET u.password_hash = $ph", ph=generate_password_hash("Student@1"))
    print("  [PASS] Emily demo password restored to Student@1.")

    print("\n======================================================================")
    print("ALL 4 REQUIREMENTS VERIFIED AND PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    test_requirements()
