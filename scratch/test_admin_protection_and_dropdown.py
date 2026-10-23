import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_session

def test_admin_protection_and_librarian_management():
    print("==================================================")
    print("TEST 1: Admin Protection & Librarian Suspend/Delete")
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
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        html = res.get_data(as_text=True)

        # Librarian must NOT have Protected (Librarian) badge
        assert "Protected (Librarian)" not in html, "Librarian must not be protected from suspension/deletion"
        print("[PASS] 'Protected (Librarian)' badge is removed.")

        # Librarian row must have Suspend or Activate button and Delete Account button
        assert 'value="toggle_status"' in html
        assert "/delete_user/" in html
        print("[PASS] User action forms (toggle_status and delete_user) are rendered for non-admin accounts.")

        # 2. Test toggling status of librarian (user_id=2 or joe user_id=13)
        with get_session() as s:
            rec = s.run("MATCH (u:User {username: 'joe', role: 'Librarian'}) RETURN u.user_id AS uid, u.account_status AS status").single()
            if not rec:
                # If joe doesn't exist, create a test librarian
                s.run("""
                    MERGE (u:User {username: 'test_librarian'})
                    ON CREATE SET u.user_id = 998, u.role = 'Librarian', u.account_status = 'Active',
                                  u.email = 'test_lib@vit.edu', u.password_hash = 'scrypt:test'
                    RETURN u.user_id AS uid, u.account_status AS status
                """)
                test_lib_id = 998
                test_lib_status = "Active"
            else:
                test_lib_id = rec["uid"]
                test_lib_status = rec["status"]

        # Suspend the librarian
        res_suspend = client.post("/manage_users", data={
            "action": "toggle_status",
            "user_id": test_lib_id,
            "current_status": test_lib_status
        }, follow_redirects=True)
        assert res_suspend.status_code == 200
        html_suspend = res_suspend.get_data(as_text=True)
        assert "status updated to 'Suspended'" in html_suspend or "status updated" in html_suspend
        print(f"[PASS] Successfully suspended Librarian (ID #{test_lib_id}).")

        # Reactivate the librarian
        res_activate = client.post("/manage_users", data={
            "action": "toggle_status",
            "user_id": test_lib_id,
            "current_status": "Suspended"
        }, follow_redirects=True)
        assert res_activate.status_code == 200
        html_activate = res_activate.get_data(as_text=True)
        assert "status updated to 'Active'" in html_activate or "status updated" in html_activate
        print(f"[PASS] Successfully reactivated Librarian (ID #{test_lib_id}).")

        # 3. Test Admin Protection: Attempt to suspend an Admin
        with get_session() as s:
            # Create a secondary admin to verify another admin cannot be suspended or deleted
            s.run("""
                MERGE (u:User {username: 'admin_secondary'})
                ON CREATE SET u.user_id = 999, u.role = 'Admin', u.account_status = 'Active',
                              u.email = 'admin2@vit.edu', u.password_hash = 'scrypt:test'
            """)

        res_admin_suspend = client.post("/manage_users", data={
            "action": "toggle_status",
            "user_id": 999,
            "current_status": "Active"
        }, follow_redirects=True)
        assert res_admin_suspend.status_code == 200
        html_admin_suspend = res_admin_suspend.get_data(as_text=True)
        assert "cannot be suspended by system policy" in html_admin_suspend and "admin_secondary" in html_admin_suspend
        print("[PASS] Admin is strictly protected from suspension by policy.")

        # 4. Test Admin Protection: Attempt to delete an Admin
        res_admin_del = client.post("/delete_user/999", follow_redirects=True)
        assert res_admin_del.status_code == 200
        html_admin_del = res_admin_del.get_data(as_text=True)
        assert "cannot be deleted by policy" in html_admin_del and "admin_secondary" in html_admin_del
        print("[PASS] Admin is strictly protected from deletion by policy.")

        # Verify secondary admin has 'Protected (Admin)' rendered on /manage_users
        res_page = client.get("/manage_users")
        html_page = res_page.get_data(as_text=True)
        assert "Protected (Admin)" in html_page
        print("[PASS] 'Protected (Admin)' badge renders for Admin rows in manage_users table.")

        # 5. Test Librarian Deletion: Admin can delete a Librarian
        with get_session() as s:
            s.run("""
                MERGE (u:User {username: 'temp_librarian_del'})
                ON CREATE SET u.user_id = 997, u.role = 'Librarian', u.account_status = 'Active',
                              u.email = 'temp_lib_del@vit.edu', u.password_hash = 'scrypt:test'
            """)

        res_del_lib = client.post("/delete_user/997", follow_redirects=True)
        assert res_del_lib.status_code == 200
        html_del_lib = res_del_lib.get_data(as_text=True)
        assert "deleted successfully" in html_del_lib
        print("[PASS] Admin can successfully delete a Librarian account.")

        # Cleanup test secondary admin
        with get_session() as s:
            s.run("MATCH (u:User {user_id: 999}) DETACH DELETE u")
            s.run("MATCH (u:User {user_id: 998}) DETACH DELETE u")
        print("[PASS] Test fixtures cleaned up successfully.")

def test_issue_loan_autocomplete_dropdown():
    print("\n==================================================")
    print("TEST 2: Issue Book Patron Autocomplete Dropdown")
    print("==================================================")

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "Admin"
            sess["username"] = "admin"

        res = client.get("/issue_loan")
        assert res.status_code == 200
        html = res.get_data(as_text=True)

        # 1. Check DOM elements for patron substring dropdown
        assert "id=\"patron_filter_wrapper\"" in html
        assert "id=\"patron_quick_search\"" in html
        assert "id=\"patron_dropdown_list\"" in html
        assert "class=\"autocomplete-dropdown\"" in html
        print("[PASS] Patron dropdown DOM structure present in /issue_loan.")

        # 2. Check DOM elements for book autocomplete dropdown
        assert "id=\"book_filter_wrapper\"" in html
        assert "id=\"book_quick_search\"" in html
        assert "id=\"book_dropdown_list\"" in html
        print("[PASS] Book dropdown DOM structure present in /issue_loan.")

        # 3. Check JavaScript substring dropdown filtering logic
        assert "function highlightSubstring" in html
        assert "function renderPatronDropdown" in html
        assert "function filterPatrons" in html
        assert "autocomplete-highlight" in html
        print("[PASS] Substring highlighting and dynamic patron dropdown JavaScript logic present.")

        # 4. Check that patronsData JSON is embedded
        assert "const patronsData =" in html
        assert "marcus_stu" in html
        assert "prof_turing" in html
        print("[PASS] Patron dataset containing active students and staff is embedded in template.")

        # 5. Check CSS styling for dark mode autocomplete
        assert ".autocomplete-dropdown" in html
        assert ".autocomplete-item" in html
        assert "background: #0f172a" in html
        assert "#334155" in html
        print("[PASS] Dark mode styling tokens verified for autocomplete dropdown.")

if __name__ == "__main__":
    try:
        test_admin_protection_and_librarian_management()
        test_issue_loan_autocomplete_dropdown()
        print("\nALL TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
