import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import oracledb
from app import app

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
client = app.test_client()

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

# Get an Admin and a Librarian user
cur.execute("SELECT User_ID, Username, Role FROM Users WHERE Role = 'Admin' AND ROWNUM = 1")
admin_user = cur.fetchone()

cur.execute("SELECT User_ID, Username, Role FROM Users WHERE Role = 'Librarian' AND ROWNUM = 1")
librarian_user = cur.fetchone()

cur.execute("SELECT COUNT(*) FROM Books")
total_books = cur.fetchone()[0]

print(f"Total books in DB: {total_books}")

for u in [admin_user, librarian_user]:
    user_id, username, role = u
    print(f"\nTesting /issue_loan for {role} ({username}, ID #{user_id})...")
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['username'] = username
        sess['role'] = role

    res = client.get('/issue_loan')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.data.decode('utf-8')

    assert '<select id="book_id"' in html, "book_id select dropdown missing"
    assert 'Select Book from Catalog' in html, "Select Book from Catalog label missing"
    assert 'book_quick_search' in html, "book_quick_search input missing"
    assert '<select id="borrower_username"' in html, "borrower_username select dropdown missing"
    assert '<select id="copy_select"' in html, "copy_select dropdown missing"
    
    # Check count of options rendered in book_id
    import re
    options = re.findall(r'<option[^>]*value="(\d+)"[^>]*data-avail="(\d+)"', html)
    print(f"  -> Found {len(options)} book options in book_id dropdown (total books in DB: {total_books})")
    assert len(options) == total_books, f"Expected {total_books} books in dropdown, found {len(options)}"

    # Check patron options
    patron_options = re.findall(r'<option[^>]*value="([^"]+)"[^>]*data-role="(staff|student)"', html)
    print(f"  -> Found {len(patron_options)} patron options in borrower_username dropdown")

# Test issuing loan by book_id fallback (when copy_id is empty or when copy_id is passed)
print("\nTesting POST /issue_loan with book_id...")
# Find a book with available copy
cur.execute("""
    SELECT bc.Book_ID, bc.Copy_ID
    FROM Book_Copies bc
    JOIN Books b ON bc.Book_ID = b.Book_ID
    WHERE bc.Status = 'Available' AND ROWNUM = 1
""")
avail_sample = cur.fetchone()
if avail_sample:
    sample_book_id, sample_copy_id = avail_sample
    print(f"Sample available book_id: {sample_book_id}, copy_id: {sample_copy_id}")
    
    # Find a clean student with 0 loans/fines
    cur.execute("""
        SELECT u.Username, u.User_ID
        FROM Users u
        WHERE u.Role = 'Student'
          AND u.Account_Status = 'Active'
          AND NOT EXISTS (SELECT 1 FROM Loans l WHERE l.Borrower_ID = u.User_ID AND l.Return_Date IS NULL)
          AND NOT EXISTS (SELECT 1 FROM Fines f JOIN Loans l ON f.Loan_ID = l.Loan_ID WHERE l.Borrower_ID = u.User_ID AND f.Payment_Status = 'Unpaid')
          AND ROWNUM = 1
    """)
    clean_stu = cur.fetchone()
    if clean_stu:
        stu_uname, stu_id = clean_stu
        print(f"Found clean student: {stu_uname} (ID #{stu_id})")
        
        with client.session_transaction() as sess:
            sess['user_id'] = librarian_user[0]
            sess['username'] = librarian_user[1]
            sess['role'] = 'Librarian'
            
        # Post with book_id only (simulating librarian choosing book from dropdown where JS might be disabled or copy_id omitted)
        res_post = client.post('/issue_loan', data={
            'book_id': sample_book_id,
            'borrower_username': stu_uname,
            'due_in_days': 14
        }, follow_redirects=True)
        assert res_post.status_code == 200
        post_html = res_post.data.decode('utf-8')
        import re
        flashes = re.findall(r'<div class="flash-alert[^>]*>(.*?)</div>', post_html, re.DOTALL)
        print("Flashed messages:", flashes)
        print("PASS: Successfully issued loan using book_id fallback resolution!")
        
        # Verify loan in DB and clean up
        cur.execute("SELECT Loan_ID, Copy_ID FROM Loans WHERE Borrower_ID = :bid AND Return_Date IS NULL", {"bid": stu_id})
        new_loan = cur.fetchone()
        assert new_loan is not None
        loan_id, issued_copy = new_loan
        print(f"Created loan #{loan_id} for copy #{issued_copy}")
        
        # Return the copy back to Available
        cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": loan_id})
        cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": issued_copy})
        conn.commit()
        print("Cleaned up test loan successfully.")

        # Also test with copy_id explicitly passed
        res_post2 = client.post('/issue_loan', data={
            'book_id': sample_book_id,
            'copy_id': sample_copy_id,
            'borrower_username': stu_uname,
            'due_in_days': 14
        }, follow_redirects=True)
        assert res_post2.status_code == 200
        post_html2 = res_post2.data.decode('utf-8')
        assert "Loan successfully created" in post_html2
        print("PASS: Successfully issued loan using explicit copy_id selection!")

        cur.execute("SELECT Loan_ID FROM Loans WHERE Borrower_ID = :bid AND Return_Date IS NULL", {"bid": stu_id})
        new_loan2 = cur.fetchone()
        assert new_loan2 is not None
        cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": new_loan2[0]})
        cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": sample_copy_id})
        conn.commit()
        print("Cleaned up explicit copy test loan successfully.")

print("\nALL ASSERTIONS PASSED SUCCESSFULLY!")
cur.close()
conn.close()
