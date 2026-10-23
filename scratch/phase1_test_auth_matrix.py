import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_phase1_auth_matrix():
    print("=================================================================")
    print("PHASE 1: AUTHENTICATION, ACCESS CONTROL & RBAC AUTHORIZATION MATRIX")
    print("=================================================================")
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    client = app.app.test_client()

    # -------------------------------------------------------------
    # 1. Unauthenticated Guest Access
    # -------------------------------------------------------------
    print("\n--- 1. Testing Unauthenticated Guest Access ---")
    protected_get_routes = [
        "/dashboard",
        "/books",
        "/catalog",
        "/category/1",
        "/issue_loan",
        "/loan_requests",
        "/manage_users",
        "/my_fines",
        "/recommendations",
        "/learning_paths",
        "/graph_visualizer",
        "/book_bridge",
        "/library_analytics",
        "/change_password",
        "/add_book",
        "/edit_book/1",
    ]

    for route in protected_get_routes:
        resp = client.get(route, follow_redirects=False)
        assert resp.status_code == 302, f"Expected 302 redirect for {route}, got {resp.status_code}"
        assert "/login" in resp.headers.get("Location", ""), f"Route {route} did not redirect to /login"
    print(f"[PASS] All {len(protected_get_routes)} protected GET routes safely redirected unauthenticated guests to /login.")

    protected_post_routes = [
        "/request_loan/1",
        "/return_book/1",
        "/pay_fine/1",
        "/report_lost/1",
        "/delete_loan/1",
        "/delete_user/9999",
        "/delete_book/9999",
        "/adjust_inventory/1",
    ]
    for route in protected_post_routes:
        resp = client.post(route, follow_redirects=False)
        assert resp.status_code == 302, f"Expected 302 redirect for POST {route}, got {resp.status_code}"
        assert "/login" in resp.headers.get("Location", ""), f"POST {route} did not redirect to /login"
    print(f"[PASS] All {len(protected_post_routes)} protected POST routes safely redirected unauthenticated guests to /login.")

    # -------------------------------------------------------------
    # 2. Login Flow with Existing Seed Accounts
    # -------------------------------------------------------------
    print("\n--- 2. Testing Live Authentication Flow with Role Accounts ---")
    roles_credentials = [
        ("Admin", "admin", "Admin@123"),
        ("Librarian", "librarian", "Librarian@123"),
        ("Staff", "staff", "Staff@123"),
        ("Student", "student", "Student@123")
    ]

    for expected_role, username, password in roles_credentials:
        resp = client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
        assert resp.status_code == 200, f"Login failed for {username}: status {resp.status_code}"
        html = resp.get_data(as_text=True)
        assert "Welcome back" in html or "Dashboard" in html, f"Login response did not show dashboard for {username}"
        # Logout
        client.get("/logout", follow_redirects=True)
        print(f"[PASS] Successful authentication for {expected_role} ('{username}').")

    # Invalid credentials
    resp = client.post("/login", data={"username": "admin", "password": "WrongPassword!99"}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Invalid username or password" in html
    print("[PASS] Invalid password rejected with error alert.")

    # -------------------------------------------------------------
    # 3. RBAC Permission Matrix Verification
    # -------------------------------------------------------------
    print("\n--- 3. Testing RBAC Permission Matrix for All 4 Roles ---")

    admin_only_routes = [
        ("/manage_users", "GET"),
        ("/delete_user/9999", "POST"),
        ("/delete_book/9999", "POST")
    ]

    staff_librarian_routes = [
        ("/issue_loan", "GET"),
        ("/loan_requests", "GET"),
        ("/add_book", "GET"),
        ("/edit_book/1", "GET"),
        ("/adjust_inventory/1", "POST"),
        ("/return_book/9999", "POST"),
        ("/pay_fine/9999", "POST"),
        ("/report_lost/9999", "POST"),
        ("/delete_loan/9999", "POST")
    ]

    roles_to_test = [
        ("Admin", 1, "admin"),
        ("Librarian", 2, "librarian"),
        ("Staff", 3, "staff"),
        ("Student", 6, "student")
    ]

    for role_name, uid, uname in roles_to_test:
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = uname
            sess["role"] = role_name
            sess["last_activity"] = time.time()

        print(f"\nVerifying RBAC for Role: {role_name}...")

        # Test Admin-only routes
        for path, method in admin_only_routes:
            if method == "GET":
                resp = client.get(path, follow_redirects=False)
            else:
                resp = client.post(path, follow_redirects=False)

            if role_name == "Admin":
                # Admin should NOT get 403
                assert resp.status_code != 403, f"Admin was blocked from {path}"
            else:
                # Non-admins MUST get 403
                assert resp.status_code == 403, f"Role {role_name} was NOT blocked from Admin route {path}! Got {resp.status_code}"
        print(f"[PASS] Admin-only route restrictions strictly verified for {role_name}.")

        # Test Staff & Librarian circulation routes
        for path, method in staff_librarian_routes:
            if method == "GET":
                resp = client.get(path, follow_redirects=False)
            else:
                resp = client.post(path, follow_redirects=False)

            if role_name in ["Admin", "Librarian"]:
                # Admin and Librarian allowed
                assert resp.status_code != 403, f"{role_name} was wrongly blocked from {path}"
            else:
                # Staff and Student MUST be blocked
                assert resp.status_code == 403, f"Patron role {role_name} accessed staff route {path}! Got {resp.status_code}"
        print(f"[PASS] Staff/Librarian circulation restrictions strictly verified for {role_name}.")

    # -------------------------------------------------------------
    # 4. Zombie Session Eviction & Inactivity Timeout
    # -------------------------------------------------------------
    print("\n--- 4. Testing Zombie Session Eviction and Timeout ---")
    # Test zombie session with deleted or non-existent user_id
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 999999 # Non-existent
        sess["username"] = "ghost_user"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302, "Ghost session was not redirected"
    assert "/login" in resp.headers.get("Location", "")
    with client.session_transaction() as sess:
        assert "user_id" not in sess, "Ghost session was not evicted"
    print("[PASS] Ghost/deleted user session automatically evicted by @login_required.")

    # Test idle timeout (>600s)
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time() - 650 # 10+ minutes ago

    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302, "Idle session was not redirected"
    assert "/login" in resp.headers.get("Location", "")
    with client.session_transaction() as sess:
        assert "user_id" not in sess, "Idle session was not cleared"
    print("[PASS] Session idle timeout (> 10 minutes) automatically cleared session.")

    print("\n=================================================================")
    print("PHASE 1 VERIFICATION COMPLETED: 100% PASSING")
    print("=================================================================")

if __name__ == "__main__":
    test_phase1_auth_matrix()
