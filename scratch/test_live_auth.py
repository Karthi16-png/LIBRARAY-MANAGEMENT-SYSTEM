import urllib.request
import urllib.parse
import http.cookiejar
import re

BASE_URL = "http://127.0.0.1:5000"

users_to_test = [
    ("karthik", "Student123!"),
    ("admin", "Admin123!"),
    ("librarian", "Librarian123!"),
    ("staff", "Staff123!"),
    ("student", "Student123!"),
]

for username, password in users_to_test:
    cj = http.cookiejar.CookieJar()
    
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), NoRedirect)
    
    # 1. Fetch login page for CSRF token
    resp = opener.open(f"{BASE_URL}/login")
    html = resp.read().decode('utf-8')
    match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
    csrf_token = match.group(1) if match else ""
    
    # 2. Submit credentials
    payload = {
        "username": username,
        "password": password,
        "csrf_token": csrf_token
    }
    encoded = urllib.parse.urlencode(payload).encode('utf-8')
    post_req = urllib.request.Request(f"{BASE_URL}/login", data=encoded, method="POST")
    
    try:
        res = opener.open(post_req)
        print(f"FAILED for {username}: Status {res.status}")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302):
            loc = e.headers.get("Location")
            print(f"SUCCESS for {username}: Redirected to {loc}")
        else:
            print(f"FAILED for {username}: HTTPError {e.code}")

# Verify karthik dashboard
session_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
dash_resp = session_opener.open(f"{BASE_URL}/dashboard")
dash_html = dash_resp.read().decode('utf-8')
print("Dashboard Status:", dash_resp.status)
print("Contains 'karthik':", 'karthik' in dash_html)
print("Contains Loans table:", 'loan' in dash_html.lower())

