import re
import requests

BASE_URL = "http://127.0.0.1:5000"

def login(session, username, password):
    resp = session.get(f"{BASE_URL}/login")
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text).group(1)
    session.post(f"{BASE_URL}/login", data={"csrf_token": token, "username": username, "password": password})

s_student = requests.Session()
login(s_student, "student", "Student@1")

dash1 = s_student.get(f"{BASE_URL}/dashboard")
m1 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash1.text, re.DOTALL)
print(f"Step 1: Student starting committed count: {m1.group(1)} / 3")
assert int(m1.group(1)) == 2

# Admin logs in to pay student fines
s_admin = requests.Session()
login(s_admin, "admin", "Admin@123")
dash_adm = s_admin.get(f"{BASE_URL}/dashboard")
token_adm = re.search(r'name="csrf_token"\s+value="([^"]+)"', dash_adm.text).group(1)

s_admin.post(f"{BASE_URL}/pay_fine/1", data={"csrf_token": token_adm}, allow_redirects=True)
s_admin.post(f"{BASE_URL}/pay_fine/10", data={"csrf_token": token_adm}, allow_redirects=True)
print("Step 2: Admin collected/recorded payment for student fines #1 and #10.")

# Admin issues Copy #11 (Modern Operating Systems) to student (uid=6)
s_admin = requests.Session()
login(s_admin, "admin", "Admin@123")
issue_p = s_admin.get(f"{BASE_URL}/issue_loan")
token_a = re.search(r'name="csrf_token"\s+value="([^"]+)"', issue_p.text).group(1)

issue_post = s_admin.post(f"{BASE_URL}/issue_loan", data={
    "csrf_token": token_a,
    "copy_id": 11,
    "borrower_id": 6,
    "due_in_days": 14
}, allow_redirects=True)
print("Step 3: Issued Copy #11 to Student.")
for m in re.finditer(r'<div class="flash-alert[^"]*">(.*?)</div>', issue_post.text, re.DOTALL):
    print("FLASH:", m.group(1).strip())

# Check student dashboard!
dash2 = s_student.get(f"{BASE_URL}/dashboard")
m2 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash2.text, re.DOTALL)
print(f"Step 4: Post-borrow Student committed count: {m2.group(1)} / 3")
assert int(m2.group(1)) == 3, f"Expected 3, got {m2.group(1)}"

# Return loan as admin
dash_admin = s_admin.get(f"{BASE_URL}/dashboard")
token_adm = re.search(r'name="csrf_token"\s+value="([^"]+)"', dash_admin.text).group(1)
loan_ids = re.findall(r'#LN-(\d+)', dash2.text)
latest_lid = loan_ids[0]

s_admin.post(f"{BASE_URL}/return_book/{latest_lid}", data={"csrf_token": token_adm}, allow_redirects=True)
print(f"Step 5: Returned loan #{latest_lid}.")

# Check student dashboard again!
dash3 = s_student.get(f"{BASE_URL}/dashboard")
m3 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash3.text, re.DOTALL)
print(f"Step 6: Post-return Student committed count: {m3.group(1)} / 3")
assert int(m3.group(1)) == 2, f"Expected 2, got {m3.group(1)}"

print("\n>>> SUCCESS: Student Committed Books increases to 3 on borrow, and decreases to 2 on return! <<<")
