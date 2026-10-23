import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app import app, next_id, get_session

def run_comprehensive_error_proofing():
    print("=" * 80)
    print("STARTING COMPREHENSIVE CODE AUDIT & ERROR-PROOFING VALIDATION SUITE")
    print("=" * 80)

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    passed = 0
    failed = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}: {details}")

    # ------------------------------------------------------------------------
    # 1. Test next_id Whitelist and Error Proofing
    # ------------------------------------------------------------------------
    print("\n--- Test Suite 1: next_id Whitelist Validation & Boundary Handling ---")
    with get_session() as s:
        try:
            next_bid = next_id(s, "Book", "book_id")
            assert_test("Valid label 'Book' and id_field 'book_id'", isinstance(next_bid, int) and next_bid > 0)
        except Exception as e:
            assert_test("Valid label 'Book' and id_field 'book_id'", False, str(e))

        try:
            next_id(s, "MaliciousLabel", "book_id")
            assert_test("Invalid label rejected with ValueError", False, "Should have raised ValueError")
        except ValueError:
            assert_test("Invalid label rejected with ValueError", True)
        except Exception as e:
            assert_test("Invalid label rejected with ValueError", False, f"Unexpected exception: {e}")

        try:
            next_id(s, "Book", "malicious_field; DROP TABLE")
            assert_test("Invalid id_field rejected with ValueError", False, "Should have raised ValueError")
        except ValueError:
            assert_test("Invalid id_field rejected with ValueError", True)
        except Exception as e:
            assert_test("Invalid id_field rejected with ValueError", False, f"Unexpected exception: {e}")

    # ------------------------------------------------------------------------
    # 2. Test Client Requests Across All 4 RBAC Roles
    # ------------------------------------------------------------------------
    print("\n--- Test Suite 2: Multi-Role HTTP Route Verification & Resilience ---")
    with app.test_client() as client:
        # A. Unauthenticated Redirection
        res = client.get("/dashboard")
        assert_test("Unauthenticated /dashboard redirects to /login (302)", res.status_code == 302 and "/login" in res.headers.get("Location", ""))

        # B. Admin Session Routes
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "Admin"
            sess["account_status"] = "Active"

        res = client.get("/dashboard")
        assert_test("Admin /dashboard returns HTTP 200", res.status_code == 200)

        res = client.get("/catalog")
        assert_test("Admin /catalog returns HTTP 200", res.status_code == 200)

        res = client.get("/category/1")
        assert_test("Admin /category/1 returns HTTP 200", res.status_code == 200)

        # Boundary page test (invalid page string, negative page)
        res = client.get("/category/1?page=invalid&q=algo")
        assert_test("Admin /category/1?page=invalid handles malformed page smoothly (HTTP 200)", res.status_code == 200)

        res = client.get("/category/1?page=-5")
        assert_test("Admin /category/1?page=-5 clamps page smoothly (HTTP 200)", res.status_code == 200)

        res = client.get("/manage_users")
        assert_test("Admin /manage_users returns HTTP 200", res.status_code == 200)

        res = client.get("/loan_requests")
        assert_test("Admin /loan_requests returns HTTP 200", res.status_code == 200)

        res = client.get("/recommendations")
        assert_test("Admin /recommendations returns HTTP 200 (Global Cohort View)", res.status_code == 200)

        res = client.get("/library_analytics")
        assert_test("Admin /library_analytics returns HTTP 200", res.status_code == 200)

        res = client.get("/learning_paths")
        assert_test("Admin /learning_paths returns HTTP 200", res.status_code == 200)

        res = client.get("/api/learning_paths")
        assert_test("Admin /api/learning_paths returns valid JSON HTTP 200", res.status_code == 200 and res.is_json)

        res = client.get("/book_bridge")
        assert_test("Admin /book_bridge returns HTTP 200", res.status_code == 200)

        res = client.get("/api/book_bridge?book_a=1&book_b=2")
        assert_test("Admin /api/book_bridge with valid books returns JSON HTTP 200", res.status_code == 200 and res.is_json)

        res = client.get("/api/book_bridge?book_a=1&book_b=1")
        assert_test("Admin /api/book_bridge with identical books returns HTTP 400", res.status_code == 400)

        res = client.get("/api/graph_data?view=full")
        assert_test("Admin /api/graph_data?view=full returns JSON HTTP 200", res.status_code == 200 and res.is_json)

        res = client.get("/api/graph_data?view=circulation")
        assert_test("Admin /api/graph_data?view=circulation returns JSON HTTP 200", res.status_code == 200 and res.is_json)

        # C. Librarian Session Routes
        with client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "librarian"
            sess["role"] = "Librarian"
            sess["account_status"] = "Active"

        res = client.get("/dashboard")
        assert_test("Librarian /dashboard returns HTTP 200", res.status_code == 200)

        res = client.get("/manage_users")
        assert_test("Librarian /manage_users is Access Denied (HTTP 403)", res.status_code == 403)

        res = client.get("/loan_requests")
        assert_test("Librarian /loan_requests returns HTTP 200", res.status_code == 200)

        res = client.get("/recommendations")
        assert_test("Librarian /recommendations returns HTTP 200", res.status_code == 200)

        # D. Staff Session Routes
        with client.session_transaction() as sess:
            sess["user_id"] = 3
            sess["username"] = "staff"
            sess["role"] = "Staff"
            sess["account_status"] = "Active"

        res = client.get("/dashboard")
        assert_test("Staff /dashboard returns HTTP 200", res.status_code == 200)

        res = client.get("/manage_users")
        assert_test("Staff /manage_users is Access Denied (HTTP 403)", res.status_code == 403)

        res = client.get("/recommendations")
        assert_test("Staff /recommendations returns HTTP 200 (Faculty Content Traversal)", res.status_code == 200)

        res = client.get("/api/graph_data?view=full")
        assert_test("Staff /api/graph_data?view=full is role-downgraded to catalog safely (HTTP 200)", res.status_code == 200 and res.json.get("view") == "catalog")

        # E. Student Session Routes
        with client.session_transaction() as sess:
            sess["user_id"] = 6
            sess["username"] = "student"
            sess["role"] = "Student"
            sess["account_status"] = "Active"

        res = client.get("/dashboard")
        assert_test("Student /dashboard returns HTTP 200", res.status_code == 200)

        res = client.get("/my_fines")
        assert_test("Student /my_fines returns HTTP 200", res.status_code == 200)

        res = client.get("/recommendations")
        assert_test("Student /recommendations returns HTTP 200 (Peer Jaccard Matchmaker)", res.status_code == 200)

        res = client.get("/library_analytics")
        assert_test("Student /library_analytics redirects to /dashboard with warning (302)", res.status_code == 302 and "/dashboard" in res.headers.get("Location", ""))

    # ------------------------------------------------------------------------
    # 3. Test Form Input Boundary Handling & Error Proofing
    # ------------------------------------------------------------------------
    print("\n--- Test Suite 3: Malformed Form Boundary Inputs & Edge Cases ---")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "Admin"
            sess["account_status"] = "Active"

        # A. delete_book with malformed category_id
        res = client.post("/delete_book/999999", data={"category_id": "malicious_string_not_int"})
        assert_test("delete_book with non-int category_id handled safely without 500 (HTTP 302)", res.status_code == 302)

        # B. adjust_inventory with non-numeric quantity
        res = client.post("/adjust_inventory/1", data={"action": "increase", "quantity": "invalid_qty"})
        assert_test("adjust_inventory with invalid quantity rejects with flash (HTTP 302)", res.status_code == 302)

        # C. adjust_inventory with negative quantity
        res = client.post("/adjust_inventory/1", data={"action": "increase", "quantity": "-5"})
        assert_test("adjust_inventory with negative quantity rejects with flash (HTTP 302)", res.status_code == 302)

        # D. issue_loan with invalid due_in_days
        res = client.post("/issue_loan", data={"borrower_username": "student", "book_id": "1", "due_in_days": "not_a_day"})
        assert_test("issue_loan with invalid due_in_days rejects with flash (HTTP 302)", res.status_code == 302)

        # E. issue_loan with out-of-range due_in_days (e.g. 999 days)
        res = client.post("/issue_loan", data={"borrower_username": "student", "book_id": "1", "due_in_days": "999"})
        assert_test("issue_loan with 999 days rejects with flash (HTTP 302)", res.status_code == 302)

        # F. delete_user with self user_id
        res = client.post("/delete_user/1")
        assert_test("delete_user preventing self-deletion (HTTP 302)", res.status_code == 302)

    print("\n" + "=" * 80)
    print(f"VERIFICATION COMPLETED: {passed} PASSED, {failed} FAILED.")
    print("=" * 80)
    return failed == 0

if __name__ == "__main__":
    success = run_comprehensive_error_proofing()
    sys.exit(0 if success else 1)
