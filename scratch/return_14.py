import re
import requests

BASE_URL = "http://127.0.0.1:5000"

s_admin = requests.Session()
resp = s_admin.get(f"{BASE_URL}/login")
token = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text).group(1)
s_admin.post(f"{BASE_URL}/login", data={"csrf_token": token, "username": "admin", "password": "Admin@123"})

dash = s_admin.get(f"{BASE_URL}/dashboard")
csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', dash.text).group(1)

ret = s_admin.post(f"{BASE_URL}/return_book/14", data={"csrf_token": csrf}, allow_redirects=True)
print("Return book 14 status:", ret.status_code)

s_staff = requests.Session()
resp_s = s_staff.get(f"{BASE_URL}/login")
token_s = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp_s.text).group(1)
s_staff.post(f"{BASE_URL}/login", data={"csrf_token": token_s, "username": "staff", "password": "Staff@123"})

staff_dash = s_staff.get(f"{BASE_URL}/dashboard")
m = re.search(r'Committed Books.*?(\d+)\s*/\s*3', staff_dash.text, re.DOTALL)
print("Staff committed count:", m.group(1) if m else "not found")
