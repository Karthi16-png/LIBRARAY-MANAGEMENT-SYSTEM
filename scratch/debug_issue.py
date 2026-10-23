import re
import requests

BASE_URL = "http://127.0.0.1:5000"

s = requests.Session()
resp = s.get(f"{BASE_URL}/login")
token = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text).group(1)
s.post(f"{BASE_URL}/login", data={"csrf_token": token, "username": "admin", "password": "Admin@123"})

issue_page = s.get(f"{BASE_URL}/issue_loan")
token2 = re.search(r'name="csrf_token"\s+value="([^"]+)"', issue_page.text).group(1)

post_resp = s.post(f"{BASE_URL}/issue_loan", data={
    "csrf_token": token2,
    "copy_id": 11,
    "borrower_id": 6,
    "due_in_days": 14
}, allow_redirects=True)

for m in re.finditer(r'<div class="flash-alert[^"]*">(.*?)</div>', post_resp.text, re.DOTALL):
    print("FLASH:", m.group(1).strip())
