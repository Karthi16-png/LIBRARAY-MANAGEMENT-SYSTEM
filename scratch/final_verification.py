import re
import requests

BASE_URL = "http://127.0.0.1:5000"

def get_session_and_dash(username, password):
    s = requests.Session()
    resp = s.get(f"{BASE_URL}/login")
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text).group(1)
    s.post(f"{BASE_URL}/login", data={"csrf_token": token, "username": username, "password": password})
    dash = s.get(f"{BASE_URL}/dashboard")
    return s, dash

# 1. Test Student Dashboard
_, stu_dash = get_session_and_dash("student", "Student@1")
m_stu = re.search(r'Committed Books.*?(\d+)\s*/\s*3.*?(\d+)\s+Checked Out.*?(\d+)\s+Awaiting Pickup', stu_dash.text, re.DOTALL)
print(f"Student Committed: {m_stu.group(1)}/3 ({m_stu.group(2)} Checked Out, {m_stu.group(3)} Awaiting Pickup)")
assert m_stu.group(1) == "2", "Student committed should be 2"
assert "AI / Graph Recommendations" in stu_dash.text, "Student should see AI Recs"

# 2. Test Staff Dashboard
_, stf_dash = get_session_and_dash("staff", "Staff@123")
m_stf = re.search(r'Committed Books.*?(\d+)\s*/\s*3.*?(\d+)\s+Checked Out.*?(\d+)\s+Awaiting Pickup', stf_dash.text, re.DOTALL)
print(f"Staff Committed: {m_stf.group(1)}/3 ({m_stf.group(2)} Checked Out, {m_stf.group(3)} Awaiting Pickup)")
assert m_stf.group(1) == "1", "Staff committed should be 1"
assert "AI / Graph Recommendations" in stf_dash.text, "Staff should see AI Recs"

# 3. Test Admin Dashboard
_, adm_dash = get_session_and_dash("admin", "Admin@123")
assert "AI / Graph Recommendations" not in adm_dash.text, "Admin should NOT see AI Recs in topbar"
assert "AI Recommendations" not in adm_dash.text, "Admin should NOT see AI Recs in sidebar"
print("Admin: AI recommendations completely hidden from UI")

# 4. Test Librarian Dashboard
_, lib_dash = get_session_and_dash("librarian", "Lib@12345")
assert "AI / Graph Recommendations" not in lib_dash.text, "Librarian should NOT see AI Recs in topbar"
assert "AI Recommendations" not in lib_dash.text, "Librarian should NOT see AI Recs in sidebar"
print("Librarian: AI recommendations completely hidden from UI")

print("\n>>> ALL VALIDATIONS CONFIRMED 100% WORKING! <<<")
