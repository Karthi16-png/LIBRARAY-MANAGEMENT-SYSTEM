import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_session, format_bridge_node

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

def set_user_session(client, username):
    with get_session() as s:
        res = s.run("MATCH (u:User) WHERE toLower(u.username) = toLower($u) RETURN u.user_id AS uid, u.username AS uname, u.role AS role", u=username).single()
        assert res, f"User {username} not found in Neo4j"
        uid = res["uid"]
        uname = res["uname"]
        role = res["role"]

    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = uid
        sess["username"] = uname
        sess["role"] = role
    return uid, uname, role

def test_all():
    # ------------------------------------------------------------------------
    # 0. PRIVACY MASKING UNIT TESTS FOR FORMAT_BRIDGE_NODE
    # ------------------------------------------------------------------------
    print("=== 0. TESTING PRIVACY MASKING FOR USER & LOAN NODES ===")
    with get_session() as s:
        u_node = s.run("MATCH (u:User {role: 'Student'}) RETURN u LIMIT 1").single()["u"]
        l_node = s.run("MATCH (l:Loan) RETURN l LIMIT 1").single()["l"]

    # Student Masking
    u_stu, u_step_stu = format_bridge_node(u_node, 1, 3, "Student")
    assert u_stu["label"] == "Anonymous Reader"
    assert "Anonymous Reader" in u_stu["title"]
    assert u_stu["properties"] == {"role": "Reader", "status": "Anonymous Reader"}
    assert u_step_stu["name"] == "Anonymous Reader"
    assert u_node.get("username") not in str(u_stu)

    l_stu, l_step_stu = format_bridge_node(l_node, 2, 4, "Student")
    assert l_stu["label"] == "Circulation Link"
    assert "Circulation Link" in l_stu["title"]
    assert l_step_stu["name"] == "Circulation Link"

    # Staff Masking
    u_staff, _ = format_bridge_node(u_node, 1, 3, "Staff")
    assert u_staff["label"] == "Anonymous Reader"
    assert u_node.get("username") not in str(u_staff)

    l_staff, _ = format_bridge_node(l_node, 2, 4, "Staff")
    assert l_staff["label"] == "Circulation Link"

    # Admin & Librarian Unmasked Access
    u_admin, _ = format_bridge_node(u_node, 1, 3, "Admin")
    assert u_admin["label"] != "Anonymous Reader"
    assert u_node.get("username") in u_admin["label"] or u_node.get("username") in str(u_admin)

    l_admin, _ = format_bridge_node(l_node, 2, 4, "Admin")
    assert l_admin["label"] != "Circulation Link"

    u_lib, _ = format_bridge_node(u_node, 1, 3, "Librarian")
    assert u_lib["label"] != "Anonymous Reader"
    print("[PASS] Privacy masking unit tests verified successfully!")

    # ------------------------------------------------------------------------
    # 1. STUDENT ROLE RBAC & LAYOUT
    # ------------------------------------------------------------------------
    print("\n=== 1. TESTING STUDENT ACCOUNT (student) ===")
    uid, uname, role = set_user_session(client, 'student')
    res = client.get('/dashboard')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    
    # Test Topbar - exactly 2 buttons
    topbar_match = re.search(r'<div class="topbar-actions">(.*?)<span class="badge badge-info">', html, re.DOTALL)
    assert topbar_match, "Topbar actions div found"
    topbar_html = topbar_match.group(1)
    topbar_links = re.findall(r'<a href="([^"]+)" class="topbar-nav-btn[^"]*".*?<span>(.*?)</span>', topbar_html, re.DOTALL)
    print(f"Student Topbar Links count: {len(topbar_links)}")
    for href, text in topbar_links:
        print(f"  - {text.strip()} -> {href.strip()}")
    assert len(topbar_links) == 2, f"Expected 2 topbar links for Student, got {len(topbar_links)}"
    assert "/learning_paths" in topbar_links[0][0]
    assert "Learning Roadmaps" in topbar_links[0][1]
    assert "/recommendations" in topbar_links[1][0]
    assert "AI & Study Recs" in topbar_links[1][1]

    # Test Sidebar (Student has 4 KG links, but not Centrality Analytics)
    sidebar_part = html[:html.find('</aside>')]
    assert '/graph_visualizer' in sidebar_part
    assert '/recommendations' in sidebar_part
    assert '/book_bridge' in sidebar_part
    assert '/learning_paths' in sidebar_part
    assert '/library_analytics' not in sidebar_part
    print("[PASS] Student sidebar contains all permitted Knowledge Graph links!")

    # Test Recommendations page
    rec_res = client.get('/recommendations')
    assert rec_res.status_code == 200
    rec_html = rec_res.data.decode('utf-8')
    if '<div class="partners-section">' in rec_html:
        assert "Top Study Partners" in rec_html and "(Jaccard Graph Similarity)" not in rec_html
        print("[PASS] Student sees 'Top Study Partners' without (Jaccard Graph Similarity)")

    # Test /book_bridge & /api/book_bridge with :PREREQUISITE_FOR edge
    bridge_res = client.get('/api/book_bridge?book_a=1&book_b=4')
    assert bridge_res.status_code == 200
    bridge_data = bridge_res.get_json()
    assert bridge_data.get('found') is True
    print(f"[PASS] Student accessed /api/book_bridge: {bridge_data.get('degrees')} degrees of separation connecting Book 1 and 4 via :PREREQUISITE_FOR!")

    # ------------------------------------------------------------------------
    # 2. STAFF ROLE RBAC & LAYOUT
    # ------------------------------------------------------------------------
    print("\n=== 2. TESTING STAFF ACCOUNT (staff) ===")
    uid, uname, role = set_user_session(client, 'staff')
    res = client.get('/dashboard')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    # Test Topbar - exactly 2 buttons
    topbar_match = re.search(r'<div class="topbar-actions">(.*?)<span class="badge badge-info">', html, re.DOTALL)
    topbar_html = topbar_match.group(1)
    topbar_links = re.findall(r'<a href="([^"]+)" class="topbar-nav-btn[^"]*".*?<span>(.*?)</span>', topbar_html, re.DOTALL)
    print(f"Staff Topbar Links count: {len(topbar_links)}")
    for href, text in topbar_links:
        print(f"  - {text.strip()} -> {href.strip()}")
    assert len(topbar_links) == 2, f"Expected 2 topbar links for Staff, got {len(topbar_links)}"
    assert "/learning_paths" in topbar_links[0][0]
    assert "Learning Roadmaps" in topbar_links[0][1]
    assert "/library_analytics" in topbar_links[1][0]
    assert "Centrality Analytics" in topbar_links[1][1]

    # Test Sidebar (Staff has Centrality Analytics)
    sidebar_part = html[:html.find('</aside>')]
    assert '/library_analytics' in sidebar_part
    print("[PASS] Staff sidebar includes Centrality Analytics link!")

    # Test Recommendations page (Study Partners MUST BE HIDDEN for Staff)
    rec_res = client.get('/recommendations')
    assert rec_res.status_code == 200
    rec_html = rec_res.data.decode('utf-8')
    assert '<div class="partners-section">' not in rec_html, "Staff should NOT see study partners section"
    print("[PASS] Staff Recommendations: Study Partners section is successfully hidden from faculty view!")

    # ------------------------------------------------------------------------
    # 3. ADMIN ROLE RBAC & LAYOUT
    # ------------------------------------------------------------------------
    print("\n=== 3. TESTING ADMIN ACCOUNT (admin) ===")
    uid, uname, role = set_user_session(client, 'admin')
    res = client.get('/dashboard')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    # Test Topbar - exactly 2 buttons
    topbar_match = re.search(r'<div class="topbar-actions">(.*?)<span class="badge badge-info">', html, re.DOTALL)
    topbar_html = topbar_match.group(1)
    topbar_links = re.findall(r'<a href="([^"]+)" class="topbar-nav-btn[^"]*".*?<span>(.*?)</span>', topbar_html, re.DOTALL)
    print(f"Admin Topbar Links count: {len(topbar_links)}")
    for href, text in topbar_links:
        print(f"  - {text.strip()} -> {href.strip()}")
    assert len(topbar_links) == 2, f"Expected 2 topbar links for Admin, got {len(topbar_links)}"
    assert "/graph_visualizer" in topbar_links[0][0]
    assert "Live Graph Explorer" in topbar_links[0][1]
    assert "/library_analytics" in topbar_links[1][0]
    assert "Centrality Analytics" in topbar_links[1][1]

    # Test Recommendations page (Admin sees Student Cohort Study Pairs)
    rec_res = client.get('/recommendations')
    assert rec_res.status_code == 200
    rec_html = rec_res.data.decode('utf-8')
    if '<div class="partners-section">' in rec_html:
        assert "Student Cohort Study Pairs" in rec_html and "(Jaccard Graph Similarity)" not in rec_html
        print("[PASS] Admin sees 'Student Cohort Study Pairs' without (Jaccard Graph Similarity)!")

    print("\nALL RBAC, PRIVACY MASKING, AND TOPBAR DECLUTTERING TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_all()
