import os
import sys
import re

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_session

def test_template_contents():
    print("--- 1. Testing templates/category_books.html ---")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tmpl_path = os.path.join(base_dir, "templates", "category_books.html")

    with open(tmpl_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. De-duplicate Graph Sections
    assert "academic-progression-box" not in html, "Found duplicate 'academic-progression-box' in category_books.html"
    assert "Study Next After This" not in html, "Found duplicate 'Study Next After This' section in category_books.html"
    assert "prereq-paired-badge" in html, "Compact 'prereq-paired-badge' must remain present"
    assert "next-step-paired-badge" in html, "Compact 'next-step-paired-badge' must remain present"
    assert "Requires:" in html, "Compact inline 'Requires:' pill must be present"
    assert "Unlocks:" in html, "Compact inline 'Unlocks:' pill must be present"
    print("[PASS] Item 1: Duplicate bottom sections removed, compact inline pills preserved")

    # 2. Fix Text Truncation in Badges
    assert re.search(r'\.frequently-paired-text\s*{[^}]*white-space:\s*normal', html), ".frequently-paired-text must have 'white-space: normal;'"
    assert re.search(r'\.frequently-paired-text\s*{[^}]*word-break:\s*break-word', html), ".frequently-paired-text must have 'word-break: break-word;'"
    assert not re.search(r'\.frequently-paired-text\s*{[^}]*white-space:\s*nowrap', html), ".frequently-paired-text must NOT have 'white-space: nowrap;'"
    assert not re.search(r'\.frequently-paired-text\s*{[^}]*text-overflow:\s*ellipsis', html), ".frequently-paired-text must NOT have 'text-overflow: ellipsis;'"

    assert re.search(r'\.frequently-paired-badge\s*{[^}]*align-items:\s*flex-start', html), ".frequently-paired-badge must have align-items: flex-start"
    assert re.search(r'\.prereq-paired-badge\s*{[^}]*align-items:\s*flex-start', html), ".prereq-paired-badge must have align-items: flex-start"
    assert re.search(r'\.next-step-paired-badge\s*{[^}]*align-items:\s*flex-start', html), ".next-step-paired-badge must have align-items: flex-start"
    print("[PASS] Item 2: Pill badges updated with natural text wrapping and flex-start alignment")

def test_category_route():
    print("\n--- 2. Testing /category/<id> route rendering with Flask client ---")
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["user_id"] = 10
        sess["username"] = "karthik"
        sess["role"] = "Student"
        sess["logged_in"] = True

    # Test category 1 (Computer Science & AI)
    res = client.get("/category/1")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    rendered_html = res.get_data(as_text=True)

    assert "academic-progression-box" not in rendered_html
    assert "Study Next After This" not in rendered_html
    assert "white-space: normal" in rendered_html
    assert "word-break: break-word" in rendered_html
    assert "Requires:" in rendered_html or "Unlocks:" in rendered_html
    print("[PASS] /category/1 renders cleanly without duplicate sections and with text-wrap styles")

if __name__ == "__main__":
    test_template_contents()
    test_category_route()
    print("\nALL CATEGORY BOOKS FIXES VERIFIED SUCCESSFULLY!")
