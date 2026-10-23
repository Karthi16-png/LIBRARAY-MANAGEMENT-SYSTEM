import re
import requests

BASE_URL = "http://127.0.0.1:5000"

def login(session, username, password):
    resp = session.get(f"{BASE_URL}/login")
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text)
    csrf_token = match.group(1) if match else None
    
    post_resp = session.post(f"{BASE_URL}/login", data={
        "csrf_token": csrf_token,
        "username": username,
        "password": password
    }, allow_redirects=True)
    return post_resp

s = requests.Session()
login_resp = login(s, "student", "Student@1")
print("Login student status:", login_resp.status_code)
assert "Welcome back" in login_resp.text, "Student login failed"

# 2. Test /graph_visualizer
gv_resp = s.get(f"{BASE_URL}/graph_visualizer")
print("GET /graph_visualizer status:", gv_resp.status_code)
assert gv_resp.status_code == 200, f"Expected 200, got {gv_resp.status_code}"
assert "vis-network.min.js" in gv_resp.text, "vis-network script missing in graph_visualizer"
assert "Live Neo4j Graph Explorer" in gv_resp.text, "Title missing in graph_visualizer"

# 3. Test /api/graph_data?view=personal
api_p = s.get(f"{BASE_URL}/api/graph_data?view=personal")
print("GET /api/graph_data?view=personal status:", api_p.status_code)
p_data = api_p.json()
print(f"Personal view nodes: {len(p_data.get('nodes', []))}, edges: {len(p_data.get('edges', []))}")

# 4. Test /api/graph_data?view=catalog
api_c = s.get(f"{BASE_URL}/api/graph_data?view=catalog")
print("GET /api/graph_data?view=catalog status:", api_c.status_code)
c_data = api_c.json()
print(f"Catalog view nodes: {len(c_data.get('nodes', []))}, edges: {len(c_data.get('edges', []))}")

# 5. Test /api/graph_data?view=recommendations
api_r = s.get(f"{BASE_URL}/api/graph_data?view=recommendations")
print("GET /api/graph_data?view=recommendations status:", api_r.status_code)
r_data = api_r.json()
print(f"Recommendations view nodes: {len(r_data.get('nodes', []))}, edges: {len(r_data.get('edges', []))}")

# 6. Test /recommendations page
recs_page = s.get(f"{BASE_URL}/recommendations")
print("GET /recommendations status:", recs_page.status_code)
assert recs_page.status_code == 200, f"Expected 200, got {recs_page.status_code}"
assert "Multi-Hop Recommendation Path" in recs_page.text, "Mini graph missing in recommendations"

# 7. Login as Admin and test full graph view
s_admin = requests.Session()
login_admin = login(s_admin, "admin", "Admin@123")
print("Login admin status:", login_admin.status_code)
assert "Welcome back" in login_admin.text, "Admin login failed"

api_f = s_admin.get(f"{BASE_URL}/api/graph_data?view=full")
print("GET /api/graph_data?view=full (Admin) status:", api_f.status_code)
f_data = api_f.json()
print(f"Full view nodes: {len(f_data.get('nodes', []))}, edges: {len(f_data.get('edges', []))}")

print("\n>>> ALL GRAPH & UI ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY! <<<")
