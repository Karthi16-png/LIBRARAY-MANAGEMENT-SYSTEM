import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "staff"
        sess["role"] = "Staff"
        sess["logged_in"] = True

    res = client.get("/dashboard")
    html = res.get_data(as_text=True)
    idx = html.find("Clean Code")
    if idx != -1:
        print(html[idx-100:idx+1200])
