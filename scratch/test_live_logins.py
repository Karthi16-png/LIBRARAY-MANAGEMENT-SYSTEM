import urllib.request
import urllib.parse
import http.cookiejar
import re

users = [
    ('admin', 'Admin@123'),
    ('librarian', 'Lib@12345'),
    ('librarian', 'Lib@123'),
    ('staff', 'Staff@123'),
    ('student', 'Student@1'),
    ('student', 'Student@123'),
]

for uname, pw in users:
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    resp = opener.open('http://127.0.0.1:5000/login')
    html = resp.read().decode('utf-8')
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf = m.group(1) if m else ''
    data = urllib.parse.urlencode({'username': uname, 'password': pw, 'csrf_token': csrf}).encode('utf-8')
    try:
        login_resp = opener.open('http://127.0.0.1:5000/login', data=data)
        final_url = login_resp.geturl()
        cookies = {c.name: c.value for c in cj}
        print(f"{uname} with {pw} -> {final_url} (cookies: {list(cookies.keys())})")
    except Exception as e:
        print(f"{uname} with {pw} -> error: {e}")
