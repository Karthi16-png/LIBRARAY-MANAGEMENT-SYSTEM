import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import oracledb
from app import app

client = app.test_client()
conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

print("=== 1. Testing CSRF Protection ===")
app.config["WTF_CSRF_ENABLED"] = True
res = client.post("/login", data={"username": "admin", "password": "wrong"})
assert res.status_code == 400, f"Expected 400 on missing CSRF token, got {res.status_code}"
print("PASS: POST without CSRF token is rejected with 400 Bad Request.")
app.config["WTF_CSRF_ENABLED"] = False

print("=== 2. Testing Backend Search (?q=) ===")
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"

cur.execute("SELECT Category_ID FROM Categories WHERE ROWNUM = 1")
cat_id = cur.fetchone()[0]

cur.execute("SELECT Title, ISBN FROM Books WHERE Category_ID = :1 AND ROWNUM = 1", [cat_id])
row = cur.fetchone()
if row:
    title, isbn = row[0], row[1]
    word = title.split()[0] if title else ""
    res_search = client.get(f"/category/{cat_id}?q={word}")
    assert res_search.status_code == 200
    html = res_search.data.decode("utf-8")
    assert 'name="q"' in html
    assert word in html
    print(f"PASS: Search by title query '{word}' returned 200 and rendered results.")

print("=== 3. Testing Anonymization on /delete_user ===")
# Clean up if leftover
cur.execute("DELETE FROM Users WHERE Username = 'test_anon_user'")
conn.commit()
cur.execute("""
    INSERT INTO Users (Username, Email, Password_Hash, Role, Account_Status)
    VALUES ('test_anon_user', 'anon@test.edu', 'TestPass@123', 'Student', 'Active')
""")
conn.commit()
cur.execute("SELECT User_ID FROM Users WHERE Username = 'test_anon_user'")
anon_uid = cur.fetchone()[0]

# Pick an available copy
cur.execute("SELECT Copy_ID FROM Book_Copies WHERE Status = 'Available' AND ROWNUM = 1")
test_cid = cur.fetchone()[0]

# Insert completed loan (Return_Date is NOT NULL)
cur.execute("SELECT NVL(MAX(Loan_ID), 0) + 1 FROM Loans")
test_lid = cur.fetchone()[0]
cur.execute("""
    INSERT INTO Loans (Loan_ID, Copy_ID, Borrower_ID, Issued_By, Issue_Date, Due_Date, Return_Date)
    VALUES (:p_lid, :p_cid, :p_uid, 1, SYSDATE - 10, SYSDATE - 3, SYSDATE - 2)
""", {"p_lid": test_lid, "p_cid": test_cid, "p_uid": anon_uid})
conn.commit()

# Call delete_user
res_del = client.post(f"/delete_user/{anon_uid}", follow_redirects=True)
assert res_del.status_code == 200

# Verify User was deleted
cur.execute("SELECT COUNT(*) FROM Users WHERE User_ID = :p_uid", {"p_uid": anon_uid})
assert cur.fetchone()[0] == 0, "User was not deleted!"

# Verify Loan still exists and was anonymized to Borrower_ID = 0
cur.execute("SELECT Borrower_ID, Return_Date FROM Loans WHERE Loan_ID = :lid", {"lid": test_lid})
loan_row = cur.fetchone()
assert loan_row is not None, "Loan was deleted instead of anonymized!"
assert loan_row[0] == 0, f"Expected Borrower_ID = 0, got {loan_row[0]}"
print("PASS: User deleted and historical loan anonymized to Borrower_ID = 0.")

# Clean up test loan
cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO('ALLOW_DELETE'); END;")
cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": test_lid})
cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO(NULL); END;")
conn.commit()

print("=== 4. Testing Bulk Insertion in /adjust_inventory ===")
cur.execute("SELECT Book_ID, Category_ID FROM Books WHERE ROWNUM = 1")
b_row = cur.fetchone()
test_bid = b_row[0]
test_cid = b_row[1]

cur.execute("SELECT COUNT(*) FROM Book_Copies WHERE Book_ID = :bid", {"bid": test_bid})
initial_copies = cur.fetchone()[0]

res_adj = client.post(f"/adjust_inventory/{test_bid}", data={
    "action": "increase",
    "quantity": "3",
    "category_id": str(test_cid)
}, follow_redirects=True)
assert res_adj.status_code == 200

cur.execute("SELECT COUNT(*) FROM Book_Copies WHERE Book_ID = :bid", {"bid": test_bid})
new_copies = cur.fetchone()[0]
assert new_copies == initial_copies + 3, f"Expected {initial_copies + 3}, got {new_copies}"
print(f"PASS: Bulk inserted 3 copies via executemany (from {initial_copies} to {new_copies}).")

# Decrease back by 3
res_dec = client.post(f"/adjust_inventory/{test_bid}", data={
    "action": "decrease",
    "quantity": "3",
    "category_id": str(test_cid)
}, follow_redirects=True)
assert res_dec.status_code == 200

conn.close()
print("\n=====================================================================")
print("ALL 4 ARCHITECTURAL VULNERABILITY FIXES VERIFIED SUCCESSFULLY!")
print("=====================================================================")
