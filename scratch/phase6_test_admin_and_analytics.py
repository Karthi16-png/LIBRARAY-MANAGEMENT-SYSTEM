import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_phase6_admin_and_analytics():
    print("=================================================================")
    print("PHASE 6: USER ADMINISTRATION, SYSTEM ANALYTICS & PATRON FINES")
    print("=================================================================")
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    client = app.app.test_client()

    # 1. Access Control for /manage_users
    print("\n--- 1. Testing /manage_users RBAC Authorization ---")
    roles = [
        ("Student", 6, 403),
        ("Staff", 3, 403),
        ("Librarian", 2, 403),
        ("Admin", 1, 200)
    ]

    for rname, uid, expected_code in roles:
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = rname.lower()
            sess["role"] = rname
            sess["last_activity"] = time.time()

        resp = client.get("/manage_users")
        assert resp.status_code == expected_code, f"Role {rname} expected {expected_code}, got {resp.status_code}"
        print(f"[PASS] Role {rname} correctly received HTTP {resp.status_code} for /manage_users.")

    # 2. User Lifecycle Management (Create, Suspend, Reactivate, Reset Password, Delete)
    print("\n--- 2. Testing User Lifecycle Management via Admin ---")
    # Set session as Admin
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    # Clean up any leftover test user
    with app.get_session() as s:
        s.run("MATCH (u:User {username: 'p6_test_user'}) DETACH DELETE u")

    # Step A: Provision new Student user
    create_payload = {
        "action": "add_user",
        "username": "p6_test_user",
        "email": "p6_test_user@vit.edu",
        "password": "Password123!",
        "role": "Student"
    }
    resp = client.post("/manage_users", data=create_payload, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "p6_test_user" in html
    assert "created successfully" in html
    print("[PASS] Successfully created new user 'p6_test_user' with Student role.")

    # Get created user ID
    with app.get_session() as s:
        rec = s.run("MATCH (u:User {username: 'p6_test_user'}) RETURN u.user_id AS uid, u.account_status AS status").single()
        assert rec is not None
        p6_uid = rec["uid"]
        assert rec["status"] == "Active"

    # Step B: Suspend account
    toggle_payload = {
        "action": "toggle_status",
        "user_id": str(p6_uid),
        "current_status": "Active"
    }
    resp = client.post("/manage_users", data=toggle_payload, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "status updated to" in html and "Suspended" in html

    with app.get_session() as s:
        status = s.run("MATCH (u:User {user_id: $uid}) RETURN u.account_status AS status", uid=p6_uid).single()["status"]
        assert status == "Suspended"
    print(f"[PASS] Successfully suspended user #{p6_uid}.")

    # Step C: Verify suspended user cannot login
    client.get("/logout")
    resp = client.post("/login", data={"username": "p6_test_user", "password": "Password123!"}, follow_redirects=True)
    login_html = resp.get_data(as_text=True)
    assert "suspended" in login_html.lower()
    print("[PASS] Suspended account correctly blocked from logging into the portal.")

    # Re-authenticate as Admin
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    # Step D: Reactivate account
    toggle_payload["current_status"] = "Suspended"
    resp = client.post("/manage_users", data=toggle_payload, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "status updated to" in html and "Active" in html
    print(f"[PASS] Successfully reactivated user #{p6_uid}.")

    # Step E: Reset Password
    reset_payload = {
        "action": "reset_password",
        "user_id": str(p6_uid)
    }
    resp = client.post("/manage_users", data=reset_payload, follow_redirects=True)
    assert resp.status_code == 200
    expected_temp_pw = "P6_test_user#Lib2026"
    assert expected_temp_pw in resp.get_data(as_text=True)
    print(f"[PASS] Admin reset password: generated temporary password '{expected_temp_pw}'.")

    # Step F: Verify login with temporary password
    client.get("/logout")
    resp = client.post("/login", data={"username": "p6_test_user", "password": expected_temp_pw}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Dashboard" in resp.get_data(as_text=True)
    print("[PASS] Authenticated successfully using generated temporary password.")

    # Re-authenticate as Admin
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    # Step G: Protection against Admin Self-Deletion
    resp = client.post("/delete_user/1", follow_redirects=True)
    assert "Cannot delete your own Admin account" in resp.get_data(as_text=True)
    print("[PASS] Self-deletion protection verified: Admin cannot delete own account.")

    # Step H: Delete the test user
    resp = client.post(f"/delete_user/{p6_uid}", follow_redirects=True)
    assert resp.status_code == 200
    assert "deleted successfully" in resp.get_data(as_text=True)

    with app.get_session() as s:
        check = s.run("MATCH (u:User {user_id: $uid}) RETURN u", uid=p6_uid).single()
        assert check is None
    print(f"[PASS] Successfully deleted user #{p6_uid}. Database integrity verified.")

    # 3. System Analytics (/library_analytics)
    print("\n--- 3. Testing Library Analytics Across All Roles ---")
    analytics_roles = [
        ("Student", 6, 302),    # Student redirected with warning
        ("Staff", 3, 200),      # Staff allowed
        ("Librarian", 2, 200),  # Librarian allowed
        ("Admin", 1, 200)       # Admin allowed
    ]

    for rname, uid, expected_code in analytics_roles:
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = rname.lower()
            sess["role"] = rname
            sess["last_activity"] = time.time()

        resp = client.get("/library_analytics")
        assert resp.status_code == expected_code, f"Analytics for {rname} expected {expected_code}, got {resp.status_code}"
        if expected_code == 200:
            html = resp.get_data(as_text=True)
            assert "Graph Analytics" in html or "Centrality" in html or "Top Influencer" in html
        print(f"[PASS] Role {rname} handled correctly for /library_analytics (HTTP {expected_code}).")

    # 4. Personal Fine Ledgers (/my_fines)
    print("\n--- 4. Testing Patron Fine Ledgers Across All Roles ---")
    fine_roles = ["Student", "Staff", "Librarian", "Admin"]
    uids = [6, 3, 2, 1]

    for rname, uid in zip(fine_roles, uids):
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = rname.lower()
            sess["role"] = rname
            sess["last_activity"] = time.time()

        resp = client.get("/my_fines")
        assert resp.status_code == 200, f"/my_fines failed for {rname}: {resp.status_code}"
        html = resp.get_data(as_text=True)
        assert "Financial Statements" in html or "Fine Ledger" in html
        print(f"[PASS] /my_fines successfully rendered without error for {rname}.")

    print("\n=================================================================")
    print("PHASE 6 VERIFICATION COMPLETED: 100% PASSING")
    print("=================================================================")

if __name__ == "__main__":
    test_phase6_admin_and_analytics()
