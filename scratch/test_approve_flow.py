import sys
sys.path.insert(0, '.')
from app import app
import re

client = app.test_client()

# Admin logs in
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'Admin'

resp = client.get('/loan_requests')
html = resp.data.decode('utf-8')
csrf_match = re.search(r'name="csrf_token" value="(.*?)"', html)
csrf_token = csrf_match.group(1) if csrf_match else ''

# Admin approves REQ #63
post_resp = client.post('/loan_requests', data={
    'csrf_token': csrf_token,
    'request_id': 63,
    'action': 'approve'
}, follow_redirects=True)
print('Admin approve response code:', post_resp.status_code)

# Student checks dashboard
with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

dash_resp = client.get('/dashboard')
dash_html = dash_resp.data.decode('utf-8')

for m in re.finditer(r'#REQ-63.*?<td class="book-title-cell">(.*?)</td>.*?<td>(.*?)</td>.*?<td>\s*(<span.*?>.*?</span>)\s*</td>\s*<td>(.*?)</td>', dash_html, re.DOTALL):
    title, date, badge, action = m.groups()
    badge_clean = re.sub(r'<.*?>', '', badge).strip()
    action_clean = re.sub(r'<.*?>', '', action).strip()
    print(f'REQ #63 on Student Dashboard: Status = "{badge_clean}" | Action = "{action_clean}"')
