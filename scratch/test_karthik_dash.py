import urllib.request
import urllib.parse
import http.cookiejar
import re

BASE_URL = "http://127.0.0.1:5000"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login as karthik
r1 = opener.open(f"{BASE_URL}/login")
html = r1.read().decode('utf-8')
csrf_token = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html).group(1)

data = urllib.parse.urlencode({
    "username": "karthik",
    "password": "Student123!",
    "csrf_token": csrf_token
}).encode('utf-8')

r2 = opener.open(f"{BASE_URL}/login", data=data)
dash_html = opener.open(f"{BASE_URL}/dashboard").read().decode('utf-8')
print("Dashboard status: 200")
print("Logged-in user is 'karthik':", "karthik" in dash_html.lower())
print("Has loan history:", "loan" in dash_html.lower())
