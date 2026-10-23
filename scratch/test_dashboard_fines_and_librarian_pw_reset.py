import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_session

def test_dashboard_fines_text():
    print("==================================================")
    print("TEST 1: Admin & Librarian Dashboard Fines Text")
    print("==================================================")

    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    with app.test_client() as client:
        # 1. Admin Dashboard
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "Admin"
            sess["username"] = "admin"

        res_admin = client.get("/dashboard")
        assert res_admin.status_code == 200
        html_admin = res_admin.get_data(as_text=True)

        assert "Disciplinary Liabilities" in html_admin, "Disciplinary Liabilities must appear in Admin dashboard"
        assert "Disciplinary Fine" in html_admin, "Disciplinary Fine must appear in Admin dashboard table header"
        assert "outstanding" not in html_admin.lower(), f"Word 'outstanding' must NOT appear in Admin dashboard!"
        print("[PASS] Admin dashboard: 'Disciplinary Liabilities' and 'Disciplinary Fine' present; 'outstanding' completely absent.")

        # 2. Librarian Dashboard
        with client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["role"] = "Librarian"
            sess["username"] = "librarian"

        res_lib = client.get("/dashboard")
        assert res_lib.status_code == 200
        html_lib = res_lib.get_data(as_text=True)

        assert "Disciplinary Liabilities" in html_lib, "Disciplinary Liabilities must appear in Librarian dashboard"
        assert "Disciplinary Fine" in html_lib, "Disciplinary Fine must appear in Librarian dashboard table header"
        assert "outstanding" not in html_lib.lower(), f"Word 'outstanding' must NOT appear in Librarian dashboard!"
        print("[PASS] Librarian dashboard: 'Disciplinary Liabilities' and 'Disciplinary Fine' present; 'outstanding' completely absent.")

def test_librarian_password_reset():
    print("\n==================================================")
    print("TEST 2: Admin Resetting Password for Librarian")
    print("==================================================")

    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    with app.test_client() as client:
        # 1. Login as Admin
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "Admin"
            sess["username"] = "admin"

        # Check /manage_users page
        res = client.get("/manage_users")
        assert res.status_code == 200
        html = res.get_data(as_text=True)

        # Librarian row must have Reset Password button
        assert "Reset password for librarian" in html or "Reset password for joe" in html or 'btn-reset-pw" title="Reset password for' in html
        print("[PASS] Reset Password button is rendered for Librarian row on /manage_users.")

        # 2. Create a test librarian or use joe (#13) to test reset password
        with get_session() as s:
            s.run("""
                MERGE (u:User {username: 'test_lib_reset'})
                ON CREATE SET u.user_id = 996, u.role = 'Librarian', u.account_status = 'Active',
                              u.email = 'test_lib_reset@vit.edu', u.password_hash = 'scrypt:oldpass'
            """)

        res_reset = client.post("/manage_users", data={
            "action": "reset_password",
            "user_id": 996
        }, follow_redirects=True)
        assert res_reset.status_code == 200
        html_reset = res_reset.get_data(as_text=True)

        assert "Password for Librarian &#39;test_lib_reset&#39; has been reset" in html_reset or "Password for Librarian 'test_lib_reset' has been reset" in html_reset
        assert "Test_lib_reset#Lib2026" in html_reset
        print("[PASS] Admin successfully reset Librarian password to temporary password (Test_lib_reset#Lib2026).")

        # 3. Test that Admin CANNOT reset an Admin password
        with get_session() as s:
            s.run("""
                MERGE (u:User {username: 'admin_test_reset'})
                ON CREATE SET u.user_id = 995, u.role = 'Admin', u.account_status = 'Active',
                              u.email = 'admin_test_reset@vit.edu', u.password_hash = 'scrypt:adminpass'
            """)

        res_reset_admin = client.post("/manage_users", data={
            "action": "reset_password",
            "user_id": 995
        }, follow_redirects=True)
        assert res_reset_admin.status_code == 200
        html_reset_admin = res_reset_admin.get_data(as_text=True)

        assert "Password reset via this panel is not permitted for Admin accounts" in html_reset_admin
        print("[PASS] Password reset for Admin accounts via the panel is prohibited.")

        # 4. Verify the librarian can authenticate with the newly reset password
        login_res = client.post("/login", data={
            "username": "test_lib_reset",
            "password": "Test_lib_reset#Lib2026"
        }, follow_redirects=False)
        assert login_res.status_code == 302, f"Expected 302 redirect on successful login, got {login_res.status_code}"
        print("[PASS] Librarian successfully authenticated with the newly reset password!")

        # Cleanup fixtures
        with get_session() as s:
            s.run("MATCH (u:User {user_id: 996}) DETACH DELETE u")
            s.run("MATCH (u:User {user_id: 995}) DETACH DELETE u")
        print("[PASS] Test fixtures cleaned up.")

if __name__ == "__main__":
    test_dashboard_fines_text()
    test_librarian_password_reset()
    print("\nALL TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")
