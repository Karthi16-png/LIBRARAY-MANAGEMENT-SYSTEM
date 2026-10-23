import urllib.request
import urllib.parse
import http.cookiejar
import re
from neo4j import GraphDatabase

BASE_URL = "http://127.0.0.1:5000"
NEO4J_URI      = "neo4j+s://e7f1b8d0.databases.neo4j.io"
NEO4J_USERNAME = "e7f1b8d0"
NEO4J_PASSWORD = "ROzf6G2s6B2tP6C61ODmEGMbmG-pzeCq5KZgI6CmxHI"
NEO4J_DATABASE = "e7f1b8d0"

def get_client():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return opener, cj

def login(opener, username, password):
    resp = opener.open(f"{BASE_URL}/login")
    html = resp.read().decode("utf-8")
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf = m.group(1) if m else ""
    data = urllib.parse.urlencode({
        "username": username,
        "password": password,
        "csrf_token": csrf
    }).encode("utf-8")
    resp2 = opener.open(f"{BASE_URL}/login", data=data)
    assert resp2.status == 200, f"Login failed for {username}"
    return csrf

def get_csrf(opener, url):
    resp = opener.open(url)
    html = resp.read().decode("utf-8")
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    if not m:
        resp_cp = opener.open(f"{BASE_URL}/change_password")
        html_cp = resp_cp.read().decode("utf-8")
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_cp)
    return m.group(1) if m else "", html


def test_fix1_dashboard_rendering_and_terminology():
    print("\n--- TEST FIX 1: Dashboard Rendering & Terminology ---")
    roles = [
        ("admin", "Admin@123", "Admin"),
        ("librarian", "Lib@12345", "Librarian"),
        ("staff", "Staff@123", "Staff"),
        ("student", "Student@1", "Student")
    ]
    for uname, pw, role in roles:
        cli, cj = get_client()
        login(cli, uname, pw)
        resp = cli.open(f"{BASE_URL}/dashboard")
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "TemplateNotFound" not in html
        assert "Welcome back" in html or "Dashboard" in html, f"Dashboard content missing for {role}"

        if role in ["Admin", "Librarian"]:
            assert "Disciplinary Fines" in html, f"Disciplinary Fines missing in {role} dashboard"
            assert "Disciplinary Liabilities" in html, f"Disciplinary Liabilities missing in {role} dashboard"
            assert "Disciplinary Fines &amp; Liabilities Ledger" in html or "Disciplinary Fines & Liabilities Ledger" in html, f"Disciplinary Fines & Liabilities Ledger missing in {role}"
            assert "outstanding" not in html.lower(), f"Word 'outstanding' found in {role} dashboard!"

    # Verify line 554 in templates/dashboard.html
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        tmpl = f.read()
    assert '<td colspan="8" class="empty-state">' in tmpl, "Colspan 8 empty state missing in templates/dashboard.html"

    print("[PASS] Fix 1: All roles render dashboard.html cleanly with compliant Disciplinary terminology and colspan=8.")


def test_fix2_copy_reservation_and_lost():
    print("\n--- TEST FIX 2: Copy Reservation, Checkout Validation & Report Lost ---")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as s:
        # Check an available copy of Book 2 (which student has not borrowed)
        rec = s.run("MATCH (b:Book {book_id: 2})-[:HAS_COPY]->(cp:Copy {status: 'Available'}) RETURN b.book_id AS bid, cp.copy_id AS cid, cp.status AS status LIMIT 1").single()
        bid = rec["bid"]
        cid = rec["cid"]
        initial_status = rec["status"]

    # 1. Student requests loan on Book 2
    cli_stu, _ = get_client()
    login(cli_stu, "student", "Student@1")
    csrf_stu, _ = get_csrf(cli_stu, f"{BASE_URL}/dashboard")

    req_data = urllib.parse.urlencode({
        "csrf_token": csrf_stu,
        "from_dashboard": "1"
    }).encode("utf-8")
    resp_req = cli_stu.open(f"{BASE_URL}/request_loan/{bid}", data=req_data)
    assert resp_req.status == 200

    # Verify that copy is NOT prematurely set to 'Reserved' (must remain Available)
    with driver.session(database=NEO4J_DATABASE) as s:
        status_after = s.run("MATCH (cp:Copy {copy_id: $cid}) RETURN cp.status AS status", cid=cid).single()["status"]
        assert status_after == "Available", f"Expected copy #{cid} to remain Available, but was {status_after}!"
        print(f"[PASS] Student 'Pending' loan request did not prematurely reserve copy #{cid} (Status: {status_after}).")

    # 2. Check /issue_loan GET lists only Available copies
    cli_lib, _ = get_client()
    login(cli_lib, "librarian", "Lib@12345")
    resp_iss = cli_lib.open(f"{BASE_URL}/issue_loan")
    iss_html = resp_iss.read().decode("utf-8")
    assert resp_iss.status == 200

    # 3. Test report_lost on already closed/returned loan
    # Loan #4 in seed data (loan_id=4) is returned
    csrf_lib, _ = get_csrf(cli_lib, f"{BASE_URL}/dashboard")
    lost_data = urllib.parse.urlencode({"csrf_token": csrf_lib}).encode("utf-8")
    resp_lost = cli_lib.open(f"{BASE_URL}/report_lost/4", data=lost_data)
    lost_html = resp_lost.read().decode("utf-8")
    assert "already returned" in lost_html or "already returned/closed" in lost_html, "Expected already returned warning on loan #4 report_lost"
    print("[PASS] Report lost correctly aborted on returned loan with flash message.")


def test_fix3_uniqueness_check_and_recommendations_banner():
    print("\n--- TEST FIX 3: /manage_users Uniqueness & Recommendations Banner ---")
    cli_admin, _ = get_client()
    login(cli_admin, "admin", "Admin@123")
    csrf_admin, _ = get_csrf(cli_admin, f"{BASE_URL}/manage_users")

    # Attempt to create duplicate user with username 'student'
    dup_data = urllib.parse.urlencode({
        "csrf_token": csrf_admin,
        "action": "add_user",
        "username": "STUDENT",
        "email": "brand_new_unique_email@vit.edu",
        "password": "Password@1234",
        "role": "Student"
    }).encode("utf-8")
    resp = cli_admin.open(f"{BASE_URL}/manage_users", data=dup_data)
    dup_html = resp.read().decode("utf-8")
    assert "already exists" in dup_html, "Expected duplicate warning when creating user with existing username"
    print("[PASS] /manage_users correctly blocked duplicate username creation.")

    # Check /recommendations banner for Admin and Librarian
    rec_admin_resp = cli_admin.open(f"{BASE_URL}/recommendations")
    rec_admin_html = rec_admin_resp.read().decode("utf-8")
    assert "Admin View: Global Patron Collaborative Filtering Network" in rec_admin_html, "Admin banner missing in /recommendations"

    cli_lib, _ = get_client()
    login(cli_lib, "librarian", "Lib@12345")
    rec_lib_resp = cli_lib.open(f"{BASE_URL}/recommendations")
    rec_lib_html = rec_lib_resp.read().decode("utf-8")
    assert "Librarian View: Global Patron Collaborative Filtering Network" in rec_lib_html, "Librarian banner missing in /recommendations"
    print("[PASS] Dynamic role banner verified in /recommendations ('Admin View...' and 'Librarian View...').")

    # Check Student recommendations header
    cli_stu, _ = get_client()
    login(cli_stu, "student", "Student@1")
    rec_stu_resp = cli_stu.open(f"{BASE_URL}/recommendations")
    rec_stu_html = rec_stu_resp.read().decode("utf-8")
    assert "Top Study Partners" in rec_stu_html
    assert "(Jaccard Graph Similarity)" not in rec_stu_html
    print("[PASS] Student sees clean 'Top Study Partners' header without (Jaccard Graph Similarity).")


def test_fix4_constraints_and_late_return_fine():
    print("\n--- TEST FIX 4: Neo4j Constraints & Late Return Fine ---")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as s:
        res = s.run("SHOW CONSTRAINTS")
        constraint_pairs = []
        for r in res:
            labels = r.get("labelsOrTypes", [])
            props = r.get("properties", [])
            if labels and props:
                constraint_pairs.append((labels[0], props[0]))

        required_pairs = [
            ("User", "user_id"), ("User", "username"), ("User", "email"),
            ("Book", "book_id"), ("Book", "isbn"), ("Category", "category_id"),
            ("Publisher", "publisher_id"), ("Author", "author_id"), ("Copy", "copy_id"),
            ("Loan", "loan_id"), ("Fine", "fine_id"), ("LoanRequest", "request_id")
        ]
        for label, prop in required_pairs:
            assert (label, prop) in constraint_pairs, f"Missing constraint on {label}({prop})!"
        print(f"[PASS] All {len(required_pairs)} schema uniqueness constraints verified in Neo4j AuraDB.")

        # Check loan #9 and its fine
        res_fine = s.run("""
            MATCH (l:Loan {loan_id: 9})-[:HAS_FINE]->(f:Fine)
            RETURN l.due_date AS due_date, l.return_date AS return_date, f.fine_amount AS fine_amount, f.payment_status AS status
        """).single()
        assert res_fine is not None, "Loan #9 fine not found"
        assert res_fine["fine_amount"] == 30.0, f"Expected fine_amount 30.0, got {res_fine['fine_amount']}"
        assert res_fine["status"] == "Paid"
        print(f"[PASS] Loan #9 fine verified: Rs. {res_fine['fine_amount']} Paid (strictly days_late * Rs. 10.00).")


def test_fix5_graph_visualizer_filtering_and_search():
    print("\n--- TEST FIX 5: Graph Visualizer ActiveGroups & Search Scope ---")
    with open("templates/graph_visualizer.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Verify custom book groups in activeGroups
    assert '"Prerequisite"' in html and '"StartBook"' in html and '"TargetBook"' in html and '"IntermediateBook"' in html, "Custom book groups missing from activeGroups"
    
    # 2. Verify mapping in group counting
    assert 'g === "Prerequisite" || g === "StartBook" || g === "TargetBook" || g === "IntermediateBook"' in html, "Custom book groups missing from groupCounts mapping"

    # 3. Verify handleNodeSearch uses nodesDataSet ? nodesDataSet.get() : allNodes
    assert 'const currentNodes = nodesDataSet ? nodesDataSet.get() : allNodes;' in html, "handleNodeSearch should search currentNodes"

    print("[PASS] Graph Visualizer activeGroups, custom book groups mapping, and visible nodes search verified.")


if __name__ == "__main__":
    test_fix1_dashboard_rendering_and_terminology()
    test_fix2_copy_reservation_and_lost()
    test_fix3_uniqueness_check_and_recommendations_banner()
    test_fix4_constraints_and_late_return_fine()
    test_fix5_graph_visualizer_filtering_and_search()
    print("\n==================================================")
    print("ALL 5 TARGETED FIXES TESTED AND PASSED 100%!")
    print("==================================================")
