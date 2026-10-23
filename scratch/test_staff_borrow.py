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

s_staff = requests.Session()
login(s_staff, "staff", "Staff@123")

dash1 = s_staff.get(f"{BASE_URL}/dashboard")
m1 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash1.text, re.DOTALL)
initial_committed = int(m1.group(1)) if m1 else None
print(f"Initial staff committed books: {initial_committed} / 3")
assert initial_committed == 1, f"Expected 1, got {initial_committed}"

# Admin logs in to issue Copy #11 to staff (borrower_id=3)
s_admin = requests.Session()
login(s_admin, "admin", "Admin@123")
issue_page = s_admin.get(f"{BASE_URL}/issue_loan")
csrf_admin = re.search(r'name="csrf_token"\s+value="([^"]+)"', issue_page.text).group(1)

issue_post = s_admin.post(f"{BASE_URL}/issue_loan", data={
    "csrf_token": csrf_admin,
    "copy_id": 11,
    "borrower_id": 3,
    "due_in_days": 14
}, allow_redirects=True)
print("Issue loan response status:", issue_post.status_code)
for m in re.finditer(r'<div class="flash-alert[^"]*">(.*?)</div>', issue_post.text, re.DOTALL):
    print("FLASH:", m.group(1).strip())

# Check staff dashboard again!
dash2 = s_staff.get(f"{BASE_URL}/dashboard")
m2 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash2.text, re.DOTALL)
new_committed = int(m2.group(1)) if m2 else None
print(f"Post-borrow staff committed books: {new_committed} / 3")
assert new_committed == 2, f"Expected 2 after borrowing, got {new_committed}"

# Return the copy so state is restored
loan_ids = re.findall(r'<td style="font-family: var\(--font-mono\);">#(\d+)</td>', dash2.text)
print("Active loans for staff:", loan_ids)
latest_lid = loan_ids[0] if loan_ids else 14

ret_post = s_admin.post(f"{BASE_URL}/return_book/{latest_lid}", data={
    "csrf_token": csrf_admin
}, allow_redirects=True)
print("Return book status:", ret_post.status_code)

# Check staff dashboard again
dash3 = s_staff.get(f"{BASE_URL}/dashboard")
m3 = re.search(r'Committed Books.*?(\d+)\s*/\s*3', dash3.text, re.DOTALL)
final_committed = int(m3.group(1)) if m3 else None
print(f"Post-return staff committed books: {final_committed} / 3")
assert final_committed == 1, f"Expected 1 after returning, got {final_committed}"

print("\n>>> FULL STAFF BORROW & RETURN VERIFIED: COUNT INCREMENTED FROM 1 TO 2, THEN BACK TO 1! <<<")
