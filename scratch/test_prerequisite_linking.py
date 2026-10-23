import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from app import app, get_session

class TestPrerequisiteLinking(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        with get_session() as s:
            admin_rec = s.run("MATCH (u:User {role: 'Admin', account_status: 'Active'}) RETURN u.user_id AS uid, u.username AS uname LIMIT 1").single()
            self.admin_uid = admin_rec["uid"]
            self.admin_uname = admin_rec["uname"]

    def test_01_get_add_book_renders_curriculum_section(self):
        """GET /add_book populates all_books with category & level metadata in prerequisite selects"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_uid
            sess["username"] = self.admin_uname
            sess["role"] = "Admin"

        resp = self.client.get("/add_book")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")

        self.assertIn("Academic Curriculum & Prerequisite Links (Neo4j Graph)", html)
        self.assertIn('name="prereq_book_id"', html)
        self.assertIn('name="next_book_id"', html)
        self.assertIn('name="curriculum_track"', html)
        self.assertIn("Auto-Detect Prerequisite from Same Category", html)
        self.assertIn("Level", html)
        print(" [PASS] Step 1: GET /add_book renders Academic Curriculum section with metadata.")

    def test_02_post_add_book_with_auto_detect_prerequisite(self):
        """POST /add_book with prereq_book_id='auto' auto-detects foundational book in Category 1"""
        test_isbn = "978-8888880001"
        test_title = "Automated Test AI Principles"

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_uid
            sess["username"] = self.admin_uname
            sess["role"] = "Admin"

        try:
            resp = self.client.post("/add_book", data={
                "isbn": test_isbn,
                "title": test_title,
                "publication_year": "2025",
                "category_id": "1",  # Computer Science & AI
                "num_copies": "1",
                "prereq_book_id": "auto",
                "next_book_id": "",
                "curriculum_track": "auto"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Verify in Neo4j that book was created and linked from Book 2 (Clean Code - foundational)
            with get_session() as s:
                rec = s.run("""
                    MATCH (new_b:Book {isbn: $isbn})
                    OPTIONAL MATCH (pre:Book)-[r:PREREQUISITE_FOR]->(new_b)
                    RETURN new_b.book_id AS bid, new_b.title AS title,
                           pre.book_id AS pre_id, pre.title AS pre_title,
                           r.difficulty_jump AS jump, r.stage AS stage, r.track AS track
                """, isbn=test_isbn).single()

                self.assertIsNotNone(rec)
                self.assertEqual(rec["title"], test_title)
                self.assertEqual(rec["pre_id"], 2)  # Clean Code has in_degree 0 in Category 1
                self.assertEqual(rec["jump"], "Category Progression")
                self.assertEqual(rec["stage"], "Stage 1 -> Stage 2")
                self.assertIn(rec["track"], ["Software Engineering", "Artificial Intelligence"])
                print(f" [PASS] Step 2: Auto-detect successfully linked foundational book #2 -> new book with track '{rec['track']}'.")

        finally:
            with get_session() as s:
                s.run("""
                    MATCH (b:Book {isbn: $isbn})
                    OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
                    DETACH DELETE cp, b
                """, isbn=test_isbn)

    def test_03_post_add_book_with_manual_prereq_and_next_step(self):
        """POST /add_book with specific prereq and next step creates both edges with tracks"""
        test_isbn = "978-8888880002"
        test_title = "Intermediate Distributed Architectures"

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_uid
            sess["username"] = self.admin_uname
            sess["role"] = "Admin"

        try:
            # Prereq: Book 5 (Database System Concepts), Next: Book 1 (Designing Data-Intensive Apps)
            resp = self.client.post("/add_book", data={
                "isbn": test_isbn,
                "title": test_title,
                "publication_year": "2024",
                "category_id": "10",  # Data Architecture & Databases
                "num_copies": "1",
                "prereq_book_id": "5",
                "next_book_id": "1",
                "curriculum_track": "Data Engineering"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with get_session() as s:
                rec = s.run("""
                    MATCH (new_b:Book {isbn: $isbn})
                    OPTIONAL MATCH (pre:Book)-[r_in:PREREQUISITE_FOR]->(new_b)
                    OPTIONAL MATCH (new_b)-[r_out:PREREQUISITE_FOR]->(nxt:Book)
                    RETURN new_b.book_id AS bid,
                           pre.book_id AS pre_id, r_in.track AS in_track,
                           nxt.book_id AS nxt_id, r_out.track AS out_track
                """, isbn=test_isbn).single()

                self.assertIsNotNone(rec)
                self.assertEqual(rec["pre_id"], 5)
                self.assertEqual(rec["in_track"], "Data Engineering")
                self.assertEqual(rec["nxt_id"], 1)
                self.assertEqual(rec["out_track"], "Data Engineering")
                print(" [PASS] Step 3: Manual prerequisite (5 -> new -> 1) registered with Data Engineering track.")

        finally:
            with get_session() as s:
                s.run("""
                    MATCH (b:Book {isbn: $isbn})
                    OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
                    DETACH DELETE cp, b
                """, isbn=test_isbn)

    def test_04_get_edit_book_preselects_existing_links(self):
        """GET /edit_book/<book_id> preselects current incoming/outgoing links and excludes self"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_uid
            sess["username"] = self.admin_uname
            sess["role"] = "Admin"

        # Book 3 (CLRS) has prereq Book 2 and next Book 4
        resp = self.client.get("/edit_book/3")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")

        self.assertIn("Edit Book &amp; Academic Learning Links", html)
        self.assertIn('value="2" data-category-id="1" selected', html)
        self.assertIn('value="4" data-category-id="1" selected', html)
        # Excludes self (Book 3 option should NOT exist in dropdowns)
        self.assertNotIn('value="3" data-category-id="1"', html)
        print(" [PASS] Step 4: GET /edit_book/3 pre-selects prereq #2 and next #4, excluding self.")

    def test_05_post_edit_book_rewires_edges(self):
        """POST /edit_book/<book_id> clears old edges and rewires updated prerequisite links"""
        # Create a temporary book to edit without touching production seeds
        test_isbn = "978-8888880003"
        test_title = "Temporary Edit Test Title"

        with get_session() as s:
            s.run("""
                MERGE (b:Book {book_id: 77777})
                SET b.title = $title, b.isbn = $isbn, b.publication_year = 2024, b.category_id = 1
                WITH b
                MATCH (c:Category {category_id: 1})
                MERGE (b)-[:BELONGS_TO]->(c)
                WITH b
                MATCH (p:Book {book_id: 2})
                MERGE (p)-[:PREREQUISITE_FOR {difficulty_jump: 'Old Jump', stage: 'Stage 1', track: 'Software Engineering'}]->(b)
            """, title=test_title, isbn=test_isbn)

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin_uid
            sess["username"] = self.admin_uname
            sess["role"] = "Admin"

        try:
            # Change prerequisite to Book 6 and set Next to Book 7 with Systems & Infrastructure track
            resp = self.client.post("/edit_book/77777", data={
                "title": "Updated Edit Test Title",
                "isbn": test_isbn,
                "publication_year": "2024",
                "category_id": "1",
                "prereq_book_id": "6",
                "next_book_id": "7",
                "curriculum_track": "Systems & Infrastructure"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with get_session() as s:
                rec = s.run("""
                    MATCH (b:Book {book_id: 77777})
                    OPTIONAL MATCH (pre:Book)-[r_in:PREREQUISITE_FOR]->(b)
                    OPTIONAL MATCH (b)-[r_out:PREREQUISITE_FOR]->(nxt:Book)
                    RETURN pre.book_id AS pre_id, r_in.track AS in_track,
                           nxt.book_id AS nxt_id, r_out.track AS out_track
                """).single()

                self.assertIsNotNone(rec)
                self.assertEqual(rec["pre_id"], 6)  # Old #2 was deleted, #6 merged
                self.assertEqual(rec["in_track"], "Systems & Infrastructure")
                self.assertEqual(rec["nxt_id"], 7)
                self.assertEqual(rec["out_track"], "Systems & Infrastructure")
                print(" [PASS] Step 5: POST /edit_book/77777 rewires incoming #6 and outgoing #7.")

        finally:
            with get_session() as s:
                s.run("MATCH (b:Book {book_id: 77777}) DETACH DELETE b")

if __name__ == "__main__":
    unittest.main()
