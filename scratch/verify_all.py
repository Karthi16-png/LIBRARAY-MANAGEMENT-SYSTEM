import sys
sys.path.insert(0, '.')
from app import app
import re

client = app.test_client()

# 1. Test student dashboard
with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

resp = client.get('/dashboard')
html = resp.data.decode('utf-8')
print('=== STUDENT DASHBOARD REQUESTS ===')
matches = list(re.finditer(r'#REQ-(\d+).*?<td class="book-title-cell">(.*?)</td>.*?<td>(.*?)</td>.*?<td>\s*(<span.*?>.*?</span>)\s*</td>\s*<td>(.*?)</td>', html, re.DOTALL))
print(f"Found {len(matches)} requests rendered in table")
for m in matches:
    req_id, title, date, badge, action = m.groups()
    badge_clean = re.sub(r'<.*?>', '', badge).strip()
    action_clean = 'Request Again Button Present' if 'Request Again' in action else re.sub(r'<.*?>', '', action).strip()
    print(f'REQ #{req_id}: {title.strip()} | Status: {badge_clean} | Action: {action_clean}')

# 2. Test category books search by author
resp_cat = client.get('/category/1?q=Martin')
html_cat = resp_cat.data.decode('utf-8')
print('\n=== CATEGORY 1 SEARCH BY AUTHOR (Martin) ===')
if 'Clean Code: Agile Software Craftsmanship' in html_cat:
    print('SUCCESS: Found Clean Code by author Martin!')
else:
    print('FAILED: Clean Code NOT found!')

# 3. Test issue_loan page dropdown
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'Admin'

resp_issue = client.get('/issue_loan')
html_issue = resp_issue.data.decode('utf-8')
print('\n=== ISSUE LOAN PAGE PATRON DROPDOWN ===')
if 'patron_select' in html_issue and '[Student]' in html_issue:
    print('SUCCESS: patron_select with [Student] and [Staff] found in issue_loan.html!')
    # Print sample options
    options = re.findall(r'<option value=".*?">.*?</option>', html_issue)
    print(f"Sample dropdown options ({len(options)} total):")
    for opt in options[:5]:
        print("  ", opt)
else:
    print('FAILED: Dropdown not found in issue_loan.html')
