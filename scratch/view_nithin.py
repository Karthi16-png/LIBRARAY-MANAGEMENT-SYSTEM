import sys
sys.path.insert(0, ".")
from datetime import datetime
from app import app
import re

app.config['TESTING'] = True
c = app.test_client()
with c.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'
    sess['last_activity'] = datetime.now().timestamp()
res = c.get('/dashboard')
html = res.data.decode('utf-8', errors='ignore')
print("ROWS IN NITHIN DASHBOARD:")
for row in re.findall(r'<tr>\s*<td[^>]*>(#REQ-\d+)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td>\s*<span class="badge [^"]*">(.*?)</span>', html):
    print(" ", row)
