import sys
sys.path.insert(0, '.')
from app import app
import re

client = app.test_client()
with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

# Get Category 1 books
resp = client.get('/category/1')
html = resp.data.decode('utf-8')

# Search for Book 2 block in html
idx = html.find('Clean Code: Agile Software Craftsmanship')
if idx != -1:
    card_html = html[idx:idx+1500]
    print("Clean Code Card HTML:")
    for line in card_html.splitlines()[:30]:
        print(" ", line)
else:
    print("Book not found in Category 1")
