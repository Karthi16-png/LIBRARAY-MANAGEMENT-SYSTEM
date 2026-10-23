import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
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

res = c.get('/category/1')
html = res.data.decode('utf-8', errors='ignore')

# Print lines containing Clean Code
lines = html.splitlines()
for i, l in enumerate(lines):
    if "Clean Code" in l:
        print("\n".join(lines[max(0, i-5):min(len(lines), i+45)]))
        break
