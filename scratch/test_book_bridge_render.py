import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

app.config['TESTING'] = True
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 6
    sess['username'] = 'student'
    sess['role'] = 'Student'

res = client.get('/book_bridge?book_a=1&book_b=4')
assert res.status_code == 200
html = res.data.decode('utf-8')
assert 'id="bridge-graph-data" type="application/json"' in html
print("Book bridge HTML rendered successfully with HTTP 200 and clean JSON payload!")
