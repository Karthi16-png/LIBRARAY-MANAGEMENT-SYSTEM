import sys
sys.path.insert(0, ".")
from datetime import datetime
from app import app
import re

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
c = app.test_client()

with c.session_transaction() as sess:
    sess['user_id'] = 32
    sess['username'] = 'joe'
    sess['role'] = 'Student'
    sess['last_activity'] = datetime.now().timestamp()

res = c.post('/request_loan/3', data={'category_id': 1}, follow_redirects=False)
print("Status:", res.status_code, "Location:", res.headers.get("Location"))
res2 = c.get(res.headers.get("Location"))
print("Final Status:", res2.status_code)
html = res2.data.decode("utf-8", errors="ignore")
print("Page title/heading:", re.findall(r'<title>(.*?)</title>', html))
print("Flash message:", re.findall(r'<div class="flash-alert [^"]*">\s*(.*?)\s*</div>', html, re.DOTALL))
