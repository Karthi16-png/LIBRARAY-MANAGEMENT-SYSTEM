import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from app import app
import oracledb

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
c = app.test_client()

# Admin rejects 61
with c.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'Admin'
    sess['last_activity'] = datetime.now().timestamp()

res = c.post('/loan_requests', data={'request_id': '61', 'action': 'reject'}, follow_redirects=True)

# Now check Nithin
with c.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'
    sess['last_activity'] = datetime.now().timestamp()

res = c.get('/category/1')
html = res.data.decode('utf-8', errors='ignore')

lines = html.splitlines()
for i, l in enumerate(lines):
    if "Clean Code" in l:
        print("\n".join(lines[max(0, i-5):min(len(lines), i+55)]))
        break
