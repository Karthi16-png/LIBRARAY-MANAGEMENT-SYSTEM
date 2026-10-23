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

print("==================================================")
print("TEST 1: Student Dashboard & AI Recs Visibility")
print("==================================================")
s_student = requests.Session()
login(s_student, "student", "Student@1")
dash_stu = s_student.get(f"{BASE_URL}/dashboard")
assert dash_stu.status_code == 200
assert "Committed Books" in dash_stu.text, "Committed Books stat label missing for Student"
assert "2 / 3" in dash_stu.text, f"Expected '2 / 3' committed books for student, not found in:\n{dash_stu.text[dash_stu.text.find('Committed Books'):dash_stu.text.find('Committed Books')+200]}"
assert "2 Checked Out" in dash_stu.text, "Expected '2 Checked Out' for student"
assert "AI / Graph Recommendations" in dash_stu.text, "AI recommendations should be visible to student"

recs_stu = s_student.get(f"{BASE_URL}/recommendations")
assert recs_stu.status_code == 200, f"Student should access /recommendations, got {recs_stu.status_code}"
print("PASS: Student Dashboard displays Committed Books (2 / 3) and AI Recommendations is visible & accessible!")

print("\n==================================================")
print("TEST 2: Staff Dashboard & AI Recs Visibility")
print("==================================================")
s_staff = requests.Session()
login(s_staff, "staff", "Staff@123")
dash_stf = s_staff.get(f"{BASE_URL}/dashboard")
assert dash_stf.status_code == 200
assert "Committed Books" in dash_stf.text, "Committed Books stat label missing for Staff"
assert "1 / 3" in dash_stf.text, f"Expected '1 / 3' committed books for staff, not found in:\n{dash_stf.text[dash_stf.text.find('Committed Books'):dash_stf.text.find('Committed Books')+200]}"
assert "1 Checked Out" in dash_stf.text, "Expected '1 Checked Out' for staff"
assert "AI / Graph Recommendations" in dash_stf.text, "AI recommendations should be visible to staff"

recs_stf = s_staff.get(f"{BASE_URL}/recommendations")
assert recs_stf.status_code == 200, f"Staff should access /recommendations, got {recs_stf.status_code}"
print("PASS: Staff Dashboard displays Committed Books (1 / 3) and AI Recommendations is visible & accessible!")

print("\n==================================================")
print("TEST 3: Admin - AI Recs Hidden & Blocked")
print("==================================================")
s_admin = requests.Session()
login(s_admin, "admin", "Admin@123")
dash_adm = s_admin.get(f"{BASE_URL}/dashboard")
assert dash_adm.status_code == 200
assert "AI / Graph Recommendations" not in dash_adm.text, "AI Recommendations button should NOT be in topbar for Admin"
assert "AI Recommendations" not in dash_adm.text, "AI Recommendations link should NOT be in sidebar for Admin"

recs_adm = s_admin.get(f"{BASE_URL}/recommendations", allow_redirects=False)
assert recs_adm.status_code == 302, f"Admin access to /recommendations should redirect with 302, got {recs_adm.status_code}"
print("PASS: Admin does NOT see AI recommendations in navbar, sidebar, or dashboard, and direct URL access redirects!")

print("\n==================================================")
print("TEST 4: Librarian - AI Recs Hidden & Blocked")
print("==================================================")
s_lib = requests.Session()
login(s_lib, "librarian", "Lib@12345")
dash_lib = s_lib.get(f"{BASE_URL}/dashboard")
assert dash_lib.status_code == 200
assert "AI / Graph Recommendations" not in dash_lib.text, "AI Recommendations button should NOT be in topbar for Librarian"
assert "AI Recommendations" not in dash_lib.text, "AI Recommendations link should NOT be in sidebar for Librarian"

recs_lib = s_lib.get(f"{BASE_URL}/recommendations", allow_redirects=False)
assert recs_lib.status_code == 302, f"Librarian access to /recommendations should redirect with 302, got {recs_lib.status_code}"
print("PASS: Librarian does NOT see AI recommendations in navbar, sidebar, or dashboard, and direct URL access redirects!")

print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
