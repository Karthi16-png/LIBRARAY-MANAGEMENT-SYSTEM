import sys
sys.path.insert(0, '.')
from app import app
import re

client = app.test_client()
with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

resp = client.get('/dashboard')
html = resp.data.decode('utf-8')

for match in re.finditer(r'#REQ-(\d+).*?<td class="book-title-cell">(.*?)</td>.*?<td>(.*?)</td>.*?<td>\s*(<span.*?>.*?</span>)\s*</td>', html, re.DOTALL):
    req_id, title, date, badge = match.groups()
    print(f"REQ #{req_id}: {title.strip()} | {date.strip()} | {badge.strip()}")
