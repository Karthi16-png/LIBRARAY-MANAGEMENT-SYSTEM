import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_phase3_catalog_and_books():
    print("=================================================================")
    print("PHASE 3: CATALOG, CATEGORIES & BOOK ACTIONS FOR ALL 4 ROLES")
    print("=================================================================")
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    client = app.app.test_client()

    # 1. /catalog Role-based Views
    print("\n--- 1. Testing /catalog for Each Role ---")
    roles = [
        ("Admin", 1, True),
        ("Librarian", 2, True),
        ("Staff", 3, False),
        ("Student", 6, False)
    ]

    for role_name, uid, should_have_add_book in roles:
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = role_name.lower()
            sess["role"] = role_name
            sess["last_activity"] = time.time()

        resp = client.get("/catalog")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        # Check "Register New Book"
        if should_have_add_book:
            assert "Register New Book" in html, f"{role_name} expected to see 'Register New Book' button on /catalog"
        else:
            assert "Register New Book" not in html, f"{role_name} should NOT see 'Register New Book' button on /catalog"

        # Check unique title count renders (e.g. "6 Titles")
        assert "Titles" in html or "Title" in html
        print(f"[PASS] /catalog validated for {role_name} (Add Book button: {should_have_add_book}).")

    # 2. /category/<id> Role-based Buttons & Controls
    print("\n--- 2. Testing /category/1 Controls for Each Role ---")
    for role_name, uid, _ in roles:
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = role_name.lower()
            sess["role"] = role_name
            sess["last_activity"] = time.time()

        resp = client.get("/category/1")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        if role_name == "Admin":
            assert "/edit_book/" in html
            assert "/adjust_inventory/" in html
            assert "/delete_book/" in html
        elif role_name == "Librarian":
            assert "/edit_book/" in html
            assert "/adjust_inventory/" in html
            assert "/delete_book/" not in html, "Librarian should NOT have delete_book action"
        else: # Staff or Student
            assert "/edit_book/" not in html, f"{role_name} should NOT have edit_book action"
            assert "/adjust_inventory/" not in html, f"{role_name} should NOT have adjust_inventory action"
            assert "/delete_book/" not in html, f"{role_name} should NOT have delete_book action"

        print(f"[PASS] /category/1 UI controls properly isolated for {role_name}.")

    # 3. Search & Filter Testing on /category/1
    print("\n--- 3. Testing Search & Filtering on /category/1 ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    # Search by Title in Category 1
    resp = client.get("/category/1?q=Clean+Code")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Clean Code: Agile Software Craftsmanship" in html
    assert "Modern Operating Systems" not in html
    print("[PASS] Title search in Category 1 accurately filtered results.")

    # Search by ISBN in Category 1
    resp = client.get("/category/1?q=9780132350884")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Clean Code" in html
    assert "Modern Operating Systems" not in html
    print("[PASS] ISBN search in Category 1 accurately filtered results.")

    # Search by Author in Category 1
    resp = client.get("/category/1?q=Robert+Martin")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Clean Code" in html
    assert "Modern Operating Systems" not in html
    print("[PASS] Author search in Category 1 accurately filtered results.")

    # Search in Category 10 (Data Architecture & Databases)
    resp = client.get("/category/10?q=Designing+Data-Intensive")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Designing Data-Intensive Applications" in html
    print("[PASS] Category 10 search accurately returned DDIA.")

    # Search with no matches
    resp = client.get("/category/1?q=NonExistentQueryXYZ123456")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "No books match your search" in html or "No Books Found" in html or "empty-state" in html or "Showing <strong>0</strong>" in html
    print("[PASS] No-match search displays clean zero results state.")

    # 4. Strict Backend Route Authorization for Book Operations
    print("\n--- 4. Testing Backend Book Action Authorization ---")
    # Non-admin / non-librarian attempting /adjust_inventory
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 6
        sess["username"] = "student"
        sess["role"] = "Student"
        sess["last_activity"] = time.time()

    resp = client.post("/adjust_inventory/1", data={"action": "increase", "quantity": 1})
    assert resp.status_code == 403, f"Expected 403 for student adjust_inventory, got {resp.status_code}"

    resp = client.get("/add_book")
    assert resp.status_code == 403, f"Expected 403 for student add_book, got {resp.status_code}"

    resp = client.get("/edit_book/1")
    assert resp.status_code == 403, f"Expected 403 for student edit_book, got {resp.status_code}"

    resp = client.post("/delete_book/1")
    assert resp.status_code == 403, f"Expected 403 for student delete_book, got {resp.status_code}"

    # Librarian attempting delete_book (Admin-only)
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 2
        sess["username"] = "librarian"
        sess["role"] = "Librarian"
        sess["last_activity"] = time.time()

    resp = client.post("/delete_book/1")
    assert resp.status_code == 403, f"Expected 403 for librarian delete_book, got {resp.status_code}"

    print("[PASS] Book management endpoints strictly protected by RBAC.")

    print("\n=================================================================")
    print("PHASE 3 VERIFICATION COMPLETED: 100% PASSING")
    print("=================================================================")

if __name__ == "__main__":
    test_phase3_catalog_and_books()
