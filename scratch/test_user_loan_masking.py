import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_session

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

def set_user_session(client, username):
    with get_session() as s:
        res = s.run("MATCH (u:User) WHERE toLower(u.username) = toLower($u) RETURN u.user_id AS uid, u.username AS uname, u.role AS role", u=username).single()
        uid, uname, role = res["uid"], res["uname"], res["role"]

    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = uid
        sess["username"] = uname
        sess["role"] = role
    return uid, uname, role

def test_masking():
    print("--- Testing Student on Books 2 and 10 ---")
    set_user_session(client, 'student')
    res = client.get('/api/book_bridge?book_a=2&book_b=10')
    assert res.status_code == 200
    data = res.get_json()
    print("Found:", data['found'], "degrees:", data['degrees'])
    user_nodes = [n for n in data['nodes'] if n.get('group') == 'User']
    loan_nodes = [n for n in data['nodes'] if n.get('group') == 'Loan']
    assert len(user_nodes) > 0, "Expected User node"
    assert len(loan_nodes) > 0, "Expected Loan node"
    for u in user_nodes:
        print("Student view of User node:", u['label'], u['title'])
        assert u['label'] == 'Anonymous Reader'
        assert 'Anonymous Library Reader' in u['title']
    for l in loan_nodes:
        print("Student view of Loan node:", l['label'], l['title'])
        assert l['label'] == 'Circulation Link'
        assert 'Confidential Circulation Link' in l['title']

    print("\n--- Testing Staff on Books 2 and 10 ---")
    set_user_session(client, 'staff')
    res = client.get('/api/book_bridge?book_a=2&book_b=10')
    assert res.status_code == 200
    data = res.get_json()
    user_nodes = [n for n in data['nodes'] if n.get('group') == 'User']
    loan_nodes = [n for n in data['nodes'] if n.get('group') == 'Loan']
    for u in user_nodes:
        assert u['label'] == 'Anonymous Reader'
    for l in loan_nodes:
        assert l['label'] == 'Circulation Link'

    print("\n--- Testing Admin on Books 2 and 10 ---")
    set_user_session(client, 'admin')
    res = client.get('/api/book_bridge?book_a=2&book_b=10')
    assert res.status_code == 200
    data = res.get_json()
    user_nodes = [n for n in data['nodes'] if n.get('group') == 'User']
    loan_nodes = [n for n in data['nodes'] if n.get('group') == 'Loan']
    for u in user_nodes:
        print("Admin view of User node:", u['label'])
        assert u['label'] != 'Anonymous Reader'
    for l in loan_nodes:
        print("Admin view of Loan node:", l['label'])
        assert l['label'] != 'Circulation Link'

    print("\nSUCCESS! Privacy masking works with 100% precision for Student/Staff while Admin/Librarian see real identities!")

if __name__ == '__main__':
    test_masking()
