import sys
sys.path.insert(0, '.')
from app import app
import re

client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

# Get dashboard to extract CSRF token
resp = client.get('/dashboard')
html = resp.data.decode('utf-8')
csrf_match = re.search(r'name="csrf_token" value="(.*?)"', html)
csrf_token = csrf_match.group(1) if csrf_match else ''

# Submit Request Again for Book 2 from Dashboard
post_resp = client.post('/request_loan/2', data={
    'csrf_token': csrf_token,
    'from_dashboard': '1'
}, follow_redirects=True)

post_html = post_resp.data.decode('utf-8')
print('Post response status code:', post_resp.status_code)

alerts = re.findall(r'<div class="alert.*?">(.*?)</div>', post_html, re.DOTALL)
print('Flash alerts:', [re.sub(r'<.*?>', '', a).strip() for a in alerts])

# Inspect updated dashboard requests
matches = list(re.finditer(r'#REQ-(\d+).*?<td class="book-title-cell">(.*?)</td>.*?<td>(.*?)</td>.*?<td>\s*(<span.*?>.*?</span>)\s*</td>\s*<td>(.*?)</td>', post_html, re.DOTALL))
print(f"\nTop 3 requests after re-requesting:")
for m in matches[:3]:
    req_id, title, date, badge, action = m.groups()
    badge_clean = re.sub(r'<.*?>', '', badge).strip()
    action_clean = 'Request Again' if 'Request Again' in action else re.sub(r'<.*?>', '', action).strip()
    print(f'REQ #{req_id}: {title.strip()} | Status: {badge_clean} | Action: {action_clean}')
