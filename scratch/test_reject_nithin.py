import sys
sys.path.insert(0, ".")
from datetime import datetime
from app import app
import re
import oracledb

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
c = app.test_client()

# Admin rejects REQ-57
with c.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'Admin'
    sess['last_activity'] = datetime.now().timestamp()

res = c.post('/loan_requests', data={'request_id': '57', 'action': 'reject'}, follow_redirects=True)
print("Admin reject status:", res.status_code)

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
cur.execute("SELECT Request_ID, Status FROM Loan_Requests WHERE Request_ID = 57")
print("REQ-57 in DB:", cur.fetchone())

cur.execute("SELECT Copy_ID, Status FROM Book_Copies WHERE Book_ID = 2")
print("Copies of Book 2 in DB:", cur.fetchall())

# Now Nithin logs in and views Category 1 (where Book 2 is)
with c.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'
    sess['last_activity'] = datetime.now().timestamp()

res_cat = c.get('/category/1')
html_cat = res_cat.data.decode('utf-8', errors='ignore')

# Check what Book 2 shows on category page
import re
# Find Clean Code card
cards = re.findall(r'<div class="book-card"[^>]*>(.*?)</div>\s*</div>\s*</div>', html_cat, re.DOTALL)
print(f"Found {len(cards)} book cards.")
for card in cards:
    if "Clean Code" in card:
        print("Clean Code card snippet:")
        for line in card.splitlines():
            if "badge" in line or "btn" in line or "Stock" in line or "Blocked" in line or "Request" in line:
                print("   ", line.strip())

# Now Nithin tries to request Book 2 again!
res_req = c.post('/request_loan/2', data={'category_id': 1}, follow_redirects=True)
html_req = res_req.data.decode('utf-8', errors='ignore')
print("Flash alerts on requesting Book 2 again:")
print(re.findall(r'<div class="flash-alert [^"]*">\s*(.*?)\s*</div>', html_req, re.DOTALL))

cur.execute("SELECT Request_ID, Status FROM Loan_Requests WHERE Borrower_ID = 31 AND Book_ID = 2 ORDER BY Request_ID DESC")
print("Nithin requests for Book 2 now in DB:", cur.fetchall())

conn.close()
