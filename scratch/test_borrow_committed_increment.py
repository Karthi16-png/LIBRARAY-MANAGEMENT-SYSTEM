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

s_student = requests.Session()
login(s_student, "student", "Student@1")

dash1 = s_student.get(f"{BASE_URL}/dashboard")
m1 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash1.text, re.DOTALL)
initial_committed = int(m1.group(1)) if m1 else None
print(f"Initial student committed books: {initial_committed} / 3")
assert initial_committed == 2, f"Expected 2, got {initial_committed}"

# Find an available copy to issue
s_admin = requests.Session()
login(s_admin, "admin", "Admin@123")
issue_page = s_admin.get(f"{BASE_URL}/issue_loan")
csrf_admin = re.search(r'name="csrf_token"\s+value="([^"]+)"', issue_page.text).group(1)

# Copy #11 is for Modern Operating Systems (4th Ed), which student has not borrowed
target_cid = 11
print(f"Target copy to issue: {target_cid}")

# Issue copy to student (borrower_id = 6)
issue_post = s_admin.post(f"{BASE_URL}/issue_loan", data={
    "csrf_token": csrf_admin,
    "copy_id": target_cid,
    "borrower_id": 6,
    "due_in_days": 14
}, allow_redirects=True)
print("Issue loan response status:", issue_post.status_code)

# Check student dashboard again!
dash2 = s_student.get(f"{BASE_URL}/dashboard")
m2 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash2.text, re.DOTALL)
new_committed = int(m2.group(1)) if m2 else None
print(f"Post-borrow student committed books: {new_committed} / 3")
assert new_committed == 3, f"Expected 3 after borrowing, got {new_committed}"

# Find the newly created loan id to return it
loan_ids = re.findall(r'#LN-(\d+)', dash2.text)
print(f"Student active loan IDs on dashboard: {loan_ids}")
latest_lid = loan_ids[0]

# Return book as admin/librarian
ret_post = s_admin.post(f"{BASE_URL}/return_book/{latest_lid}", data={
    "csrf_token": csrf_admin
}, allow_redirects=True)
print("Return book status:", ret_post.status_code)

# Check student dashboard again!
dash3 = s_student.get(f"{BASE_URL}/dashboard")
m3 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash3.text, re.DOTALL)
final_committed = int(m3.group(1)) if m3 else None
print(f"Post-return student committed books: {final_committed} / 3")
assert final_committed == 2, f"Expected 2 after returning, got {final_committed}"

print("\n>>> VERIFIED: COMMITTED BOOKS INCREASES ON BORROW AND DECREASES ON RETURN! <<<")
