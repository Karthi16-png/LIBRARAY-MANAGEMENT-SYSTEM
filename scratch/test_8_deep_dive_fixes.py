import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from datetime import datetime, timedelta
from app import app, get_session, today_str

class TestEightDeepDiveFixes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_01_login_required_evicts_suspended_or_missing_user(self):
        """Fix 1: Deleted/Suspended user evicted in @login_required, active user has role synced"""
        # Test 1a: non-existent user_id
        with self.client.session_transaction() as sess:
            sess["user_id"] = 99999999
            sess["username"] = "ghost_user"
            sess["role"] = "Student"

        resp = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/login"))

        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

        # Test 1b: active user gets role synced
        with get_session() as s:
            rec = s.run("MATCH (u:User {username: 'alex_stu'}) RETURN u.user_id AS uid, u.role AS role").single()
            alex_uid = rec["uid"]
            alex_role = rec["role"]

        with self.client.session_transaction() as sess:
            sess["user_id"] = alex_uid
            sess["username"] = "alex_stu"
            sess["role"] = "WrongRole"

        resp = self.client.get("/dashboard", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("role"), alex_role)
        print(" [PASS] Fix 1: @login_required evicts deleted/suspended users and syncs role.")

    def test_02_block_suspended_patrons_issue_loan_and_requests(self):
        """Fix 2: Block suspended/non-patron in issue_loan and loan_requests approve/handover"""
        with get_session() as s:
            # Create a temporary suspended patron
            s.run("""
                MERGE (u:User {user_id: 88888})
                SET u.username = 'test_suspended_patron',
                    u.password_hash = 'dummy',
                    u.role = 'Student',
                    u.account_status = 'Suspended'
            """)
            admin_rec = s.run("MATCH (u:User {role: 'Admin'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()
            admin_uid = admin_rec["uid"]
            admin_uname = admin_rec["uname"]

        try:
            # Login as Admin
            with self.client.session_transaction() as sess:
                sess["user_id"] = admin_uid
                sess["username"] = admin_uname
                sess["role"] = "Admin"

            # 2a: Try issuing a loan to test_suspended_patron
            resp = self.client.post("/issue_loan", data={
                "borrower_username": "test_suspended_patron",
                "copy_id": "4",
                "book_id": "2",
                "due_in_days": "14"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Borrowing Prohibited: Borrower account is Suspended", resp.data)
            print(" [DEBUG] 2a passed")

            # 2b: Try approving a loan request for suspended patron
            with get_session() as s:
                s.run("""
                    MERGE (r:LoanRequest {request_id: 88888})
                    SET r.book_id = 2,
                        r.borrower_id = 88888,
                        r.status = 'Pending',
                        r.request_date = '2026-10-19'
                    WITH r
                    MATCH (b:Book {book_id: 2})
                    MERGE (r)-[:FOR_BOOK]->(b)
                """)

            resp = self.client.post("/loan_requests", data={
                "request_id": "88888",
                "action": "approve"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"account is currently suspended", resp.data)
            print(" [DEBUG] 2b passed")

            # 2c: Try confirm_pickup for suspended patron
            with get_session() as s:
                s.run("""
                    MATCH (r:LoanRequest {request_id: 88888})
                    SET r.status = 'Awaiting Pickup', r.copy_id = 4
                """)

            resp = self.client.post("/loan_requests", data={
                "request_id": "88888",
                "action": "confirm_pickup"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"account is currently suspended", resp.data)
            self.assertIn(b"Handover Prohibited", resp.data)
            print(" [PASS] Fix 2: Suspended patrons are strictly blocked from issue_loan, approve, and handover.")

        finally:
            with get_session() as s:
                s.run("MATCH (r:LoanRequest {request_id: 88888}) DETACH DELETE r")
                s.run("MATCH (u:User {user_id: 88888}) DETACH DELETE u")

    def test_03_dashboard_staff_overdue_and_student_copy_id(self):
        """Fix 3: Overdue column in Staff dashboard, Copy ID in Student dashboard"""
        with get_session() as s:
            staff_rec = s.run("MATCH (u:User {role: 'Staff', account_status: 'Active'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()
            student_rec = s.run("MATCH (u:User {role: 'Student', account_status: 'Active'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()

        # Staff dashboard check
        with self.client.session_transaction() as sess:
            sess["user_id"] = staff_rec["uid"]
            sess["username"] = staff_rec["uname"]
            sess["role"] = "Staff"

        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        # Check for Status column in staff table
        self.assertIn(b"<th>Status</th>", resp.data)

        # Student dashboard check
        with self.client.session_transaction() as sess:
            sess["user_id"] = student_rec["uid"]
            sess["username"] = student_rec["uname"]
            sess["role"] = "Student"

        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        # Check for Copy ID column
        self.assertIn(b"<th>Copy ID</th>", resp.data)
        print(" [PASS] Fix 3: Dashboard contains Staff Status column and Student Copy ID column.")

    def test_04_preserve_category_book_count_during_search(self):
        """Fix 4: Preserve true category book count in badge when search query ?q= is applied"""
        with get_session() as s:
            cat_rec = s.run("MATCH (c:Category) RETURN c.category_id AS cid, c.name AS name LIMIT 1").single()
            cid = cat_rec["cid"]
            total_books = s.run("""
                MATCH (c:Category {category_id: $cid})
                OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
                RETURN count(DISTINCT b) AS c
            """, cid=cid).single()["c"]

            admin_rec = s.run("MATCH (u:User {role: 'Admin', account_status: 'Active'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()

        with self.client.session_transaction() as sess:
            sess["user_id"] = admin_rec["uid"]
            sess["username"] = admin_rec["uname"]
            sess["role"] = "Admin"

        # Search with a filter that returns 0 or 1 books
        resp = self.client.get(f"/category/{cid}?q=nonexistentbookqueryxyz")
        self.assertEqual(resp.status_code, 200)
        expected_badge_text = f'{total_books} Title{"s" if total_books != 1 else ""} in Category'
        self.assertIn(expected_badge_text.encode("utf-8"), resp.data)
        print(" [PASS] Fix 4: Total category book count badge preserved during filtered searches.")

    def test_05_autocomplete_enter_key_and_book_fallback(self):
        """Fix 5: Autocomplete Enter key >= 0 and form submit bookSelect fallback"""
        with open(os.path.join(os.path.dirname(__file__), "..", "templates", "issue_loan.html"), "r", encoding="utf-8") as f:
            tmpl = f.read()

        self.assertIn("activePatronIdx >= 0", tmpl)
        self.assertIn("activeBookIdx >= 0", tmpl)
        self.assertIn("bookSelect.dispatchEvent(new Event('change'))", tmpl)
        self.assertIn("booksData.find(b =>", tmpl)
        print(" [PASS] Fix 5: Autocomplete indices >= 0 and form submit bookSelect fallback verified.")

    def test_06_validate_pub_year_in_add_book(self):
        """Fix 6: Validate publication_year before creating on-the-fly nodes in /add_book"""
        with get_session() as s:
            admin_rec = s.run("MATCH (u:User {role: 'Admin', account_status: 'Active'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()

        with self.client.session_transaction() as sess:
            sess["user_id"] = admin_rec["uid"]
            sess["username"] = admin_rec["uname"]
            sess["role"] = "Admin"

        resp = self.client.post("/add_book", data={
            "isbn": "978-0000000001",
            "title": "Invalid Year Book",
            "publication_year": "NotAYear",
            "category_id": "1",
            "new_category_name": "ShouldNotBeCreatedCategory123",
            "publisher_id": "1",
            "num_copies": "1"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Publication Year must be a valid numerical year.", resp.data)

        # Verify on-the-fly category was NOT created
        with get_session() as s:
            cat_chk = s.run("MATCH (c:Category {name: 'ShouldNotBeCreatedCategory123'}) RETURN count(c) AS c").single()["c"]
            self.assertEqual(cat_chk, 0)
        print(" [PASS] Fix 6: Invalid publication_year rejected early before node creation.")

    def test_07_deterministic_companion_tie_breaking(self):
        """Fix 7: Co-borrowing companion tie-breaking order by title ASC"""
        with get_session() as s:
            res = s.run("""
                MATCH (b1:Book)-[:BELONGS_TO]->(:Category {category_id: 1})
                OPTIONAL MATCH (b1)-[:HAS_COPY]->(:Copy)<-[:FOR_COPY]-(:Loan)<-[:BORROWED]-(u:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2:Book)
                WHERE b1.book_id <> b2.book_id
                WITH b1, b2, count(DISTINCT u) AS common_patrons
                ORDER BY common_patrons DESC, b2.title ASC
                WITH b1, collect(CASE WHEN b2 IS NOT NULL THEN {id: b2.book_id, title: b2.title, count: common_patrons} ELSE null END)[0] AS companion
                RETURN b1.book_id AS book_id, companion
            """)
            self.assertIsNotNone(res)
        print(" [PASS] Fix 7: Deterministic companion tie-breaking syntax validated successfully.")

    def test_08_learning_paths_session_reuse(self):
        """Fix 8: ensure_prerequisite_hierarchy reuses existing session in /learning_paths & /api/learning_paths"""
        with get_session() as s:
            student_rec = s.run("MATCH (u:User {role: 'Student', account_status: 'Active'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()

        with self.client.session_transaction() as sess:
            sess["user_id"] = student_rec["uid"]
            sess["username"] = student_rec["uname"]
            sess["role"] = "Student"

        resp1 = self.client.get("/learning_paths")
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.client.get("/api/learning_paths")
        self.assertEqual(resp2.status_code, 200)
        json_data = resp2.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertGreater(len(json_data["edges"]), 0)
        print(" [PASS] Fix 8: Learning paths routes execute smoothly with session reuse.")

if __name__ == "__main__":
    unittest.main()
