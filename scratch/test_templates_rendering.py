import os
import sys
sys.path.insert(0, os.path.abspath("."))
from app import app

def test_flask_template_rendering():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    template_dir = "templates"
    templates = [f for f in os.listdir(template_dir) if f.endswith(".html")]
    print(f"Testing all {len(templates)} templates inside Flask application context...")

    errors = []
    with app.test_request_context("/"):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = 1
                sess["username"] = "admin"
                sess["role"] = "Admin"
                sess["account_status"] = "Active"

            for t_name in sorted(templates):
                # Prepare mock context appropriate for each template
                ctx = {
                    "books": [],
                    "all_books": [],
                    "categories": [],
                    "category": {"category_id": 1, "name": "Computer Science", "section_code": "CS-01", "description": "CS books"},
                    "publishers": [],
                    "authors": [],
                    "users": [],
                    "patrons": [],
                    "available_copies": [],
                    "requests": [],
                    "awaiting_pickup": [],
                    "my_requests": [],
                    "active_loans": [],
                    "all_loans": [],
                    "overdue_loans": [],
                    "loans": [],
                    "fines": [],
                    "my_fines": [],
                    "top_authors": [],
                    "top_books": [],
                    "recommendations": [],
                    "study_partners": [],
                    "vis_nodes": [],
                    "vis_edges": [],
                    "book_nodes": [],
                    "edge_rows": [],
                    "stats": {"total_volumes": 0, "available_volumes": 0, "max_depth": 1, "total_edges": 0, "total_paths": 0},
                    "paths": [],
                    "metrics": {"nodes_count": 0, "rels_count": 0, "active_borrowers": 0, "active_loans": 0, "avg_degree": 0.0, "density_rating": "N/A"},
                    "book": {"book_id": 1, "title": "Test Book", "isbn": "1234567890", "publication_year": 2024, "category_id": 1, "category_name": "CS", "publisher_id": 1, "publisher_name": "Test Pub", "current_author_ids": [], "current_prereq_id": None, "current_next_id": None, "current_track": "CS"},
                    "data": {
                        "user": {"user_id": 1, "username": "admin", "role": "Admin", "account_status": "Active", "email": "admin@vit.edu"},
                        "active_loans": [],
                        "all_loans": [],
                        "overdue_loans": [],
                        "requests": [],
                        "my_requests": [],
                        "awaiting_pickup": [],
                        "pending_requests": [],
                        "fines": [],
                        "my_fines": [],
                        "active_fines": [],
                        "stats": {"total_books": 0, "available_books": 0, "active_loans": 0, "total_fines": 0.0, "total_users": 0}
                    },
                    "page": 1,
                    "total_pages": 1,
                    "total_books": 0,
                    "q": "",
                    "user_role": "Admin",
                    "username": "admin",
                    "user_id": 1,
                    "is_admin_view": True,
                    "admin_banner": "Admin View",
                    "degrees": 0,
                    "path_found": False,
                    "error_msg": None,
                    "path_nodes": [],
                    "path_edges": [],
                    "path_steps": [],
                    "book_a_id": None,
                    "book_b_id": None
                }

                try:
                    from flask import render_template
                    rendered = render_template(t_name, **ctx)
                    print(f"  [OK] {t_name} (length: {len(rendered)} bytes)")
                except Exception as e:
                    errors.append((t_name, str(e)))
                    print(f"  [FAIL] {t_name}: {e}")

    print(f"\nFinal Result: {len(templates) - len(errors)} passed, {len(errors)} failed.")
    return errors

if __name__ == "__main__":
    test_flask_template_rendering()
