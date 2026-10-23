"""
Comprehensive Database Seeding Script for Oracle 21c Enterprise Library System
Ensures:
1. Every table in the schema has sample records if empty (COUNT == 0).
2. All patron users (Students and Staff) have sample activity across Loans, Fines, and Loan_Requests.
3. All constraints (domain validation, check constraints, foreign keys) are strictly respected.
"""

import oracledb
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def seed_database():
    conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
    cursor = conn.cursor()
    print("=================================================================")
    print("ORACLE 21c SEEDING ENGINE: Populating Tables and All User Records")
    print("=================================================================")

    try:
        # =====================================================================
        # 1. TABLE: USERS
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Users")
        users_count = cursor.fetchone()[0]
        print(f"\n[1/11] Checking USERS table (Current rows: {users_count})...")

        # Standard baseline users with vit.edu institutional domain
        sample_users = [
            ("admin", "Admin123!", "admin@vit.edu", "Admin"),
            ("librarian", "Librarian123!", "librarian@vit.edu", "Librarian"),
            ("staff", "Staff123!", "staff@vit.edu", "Staff"),
            ("prof_turing", "Staff123!", "turing@vit.edu", "Staff"),
            ("prof_shannon", "Staff123!", "shannon@vit.edu", "Staff"),
            ("student", "Student123!", "student@vit.edu", "Student"),
            ("alex_stu", "Student123!", "alex@vit.edu", "Student"),
            ("priya_stu", "Student123!", "priya@vit.edu", "Student"),
            ("rahul_stu", "Student123!", "rahul@vit.edu", "Student"),
            ("emily_stu", "Student123!", "emily@vit.edu", "Student"),
            ("marcus_stu", "Student123!", "marcus@vit.edu", "Student"),
            ("nithin", "Student123!", "nithin@vit.edu", "Student"),
            ("joe", "Student123!", "joe@vit.edu", "Student"),
        ]

        # Always ensure 'Archived Patron' (ID 0) exists
        cursor.execute("SELECT COUNT(*) FROM Users WHERE User_ID = 0")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO Users (User_ID, Username, Password_Hash, Email, Role, Account_Status)
                VALUES (0, 'Archived Patron', 'archived_placeholder', 'archived@vit.edu', 'Student', 'Suspended')
            """)
            print(" -> Created System Account 'Archived Patron' (User_ID = 0).")

        merge_user_sql = """
            MERGE INTO Users u
            USING (SELECT :username AS uname FROM dual) d
            ON (LOWER(u.Username) = LOWER(d.uname))
            WHEN MATCHED THEN
                UPDATE SET u.Password_Hash = :pw, u.Email = :email, u.Role = :role, u.Account_Status = 'Active'
            WHEN NOT MATCHED THEN
                INSERT (Username, Password_Hash, Email, Role, Account_Status)
                VALUES (:username, :pw, :email, :role, 'Active')
        """
        for uname, pwd, email, role in sample_users:
            cursor.execute(merge_user_sql, {
                "username": uname,
                "pw": generate_password_hash(pwd),
                "email": email,
                "role": role
            })
        conn.commit()

        cursor.execute("SELECT User_ID, Username, Role FROM Users WHERE User_ID != 0 ORDER BY User_ID")
        all_active_users = cursor.fetchall()
        user_id_map = {row[1].lower(): row[0] for row in all_active_users}
        admin_id = user_id_map.get("admin", 1)
        librarian_id = user_id_map.get("librarian", admin_id)
        print(f" -> Active Users populated. Total count: {len(all_active_users)}")

        # =====================================================================
        # 2. TABLE: CATEGORIES
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Categories")
        cat_count = cursor.fetchone()[0]
        print(f"\n[2/11] Checking CATEGORIES table (Current rows: {cat_count})...")
        if cat_count == 0:
            sample_categories = [
                ("Computer Science & AI", "CS"),
                ("Physics & Astronomy", "PHY"),
                ("Mathematics & Statistics", "MAT"),
                ("Electrical Engineering", "EE"),
                ("Mechanical Engineering", "ME"),
                ("World History & Civilizations", "HIS"),
                ("Philosophy & Ethics", "PHI"),
                ("Classical Literature", "LIT"),
                ("Economics & Public Policy", "ECO"),
                ("Data Architecture & Databases", "DB")
            ]
            for cname, code in sample_categories:
                cursor.execute("INSERT INTO Categories (Name, Section_Code) VALUES (:name, :code)", {
                    "name": cname, "code": code
                })
            conn.commit()
            print(f" -> Seeded {len(sample_categories)} sample categories.")
        else:
            print(" -> Table already populated.")

        cursor.execute("SELECT Category_ID, Name FROM Categories")
        all_categories = cursor.fetchall()
        first_cat_id = all_categories[0][0]

        # =====================================================================
        # 3. TABLE: PUBLISHERS
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Publishers")
        pub_count = cursor.fetchone()[0]
        print(f"\n[3/11] Checking PUBLISHERS table (Current rows: {pub_count})...")
        if pub_count == 0:
            sample_publishers = [
                ("O'Reilly Media", "contact@oreilly.com"),
                ("Pearson Education", "support@pearson.com"),
                ("MIT Press", "info@mitpress.mit.edu"),
                ("McGraw-Hill Education", "help@mheducation.com"),
                ("Addison-Wesley Professional", "inquiries@addisonwesley.com")
            ]
            for pname, email in sample_publishers:
                cursor.execute("INSERT INTO Publishers (Name, Contact_Email) VALUES (:name, :email)", {
                    "name": pname, "email": email
                })
            conn.commit()
            print(f" -> Seeded {len(sample_publishers)} sample publishers.")
        else:
            print(" -> Table already populated.")

        cursor.execute("SELECT Publisher_ID FROM Publishers")
        first_pub_id = cursor.fetchone()[0]

        # =====================================================================
        # 4. TABLE: AUTHORS
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Authors")
        auth_count = cursor.fetchone()[0]
        print(f"\n[4/11] Checking AUTHORS table (Current rows: {auth_count})...")
        if auth_count == 0:
            sample_authors = [
                ("Donald", "Knuth"),
                ("Martin", "Fowler"),
                ("Robert", "Martin"),
                ("Thomas", "Cormen"),
                ("Stuart", "Russell")
            ]
            for fn, ln in sample_authors:
                cursor.execute("INSERT INTO Authors (First_Name, Last_Name) VALUES (:fn, :ln)", {
                    "fn": fn, "ln": ln
                })
            conn.commit()
            print(f" -> Seeded {len(sample_authors)} sample authors.")
        else:
            print(" -> Table already populated.")

        cursor.execute("SELECT Author_ID FROM Authors")
        all_author_ids = [r[0] for r in cursor.fetchall()]

        # =====================================================================
        # 5. TABLE: BOOKS
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Books")
        books_count = cursor.fetchone()[0]
        print(f"\n[5/11] Checking BOOKS table (Current rows: {books_count})...")
        if books_count == 0:
            sample_books = [
                ("978-0132350884", "Clean Code: Agile Software Craftsmanship", 2008),
                ("978-0262033848", "Introduction to Algorithms (CLRS)", 2009),
                ("978-1449373320", "Designing Data-Intensive Applications", 2017),
                ("978-0136042594", "Artificial Intelligence: A Modern Approach", 2020),
                ("978-0201896831", "The Art of Computer Programming, Vol 1", 1997)
            ]
            for isbn, title, yr in sample_books:
                cursor.execute("""
                    INSERT INTO Books (ISBN, Title, Publication_Year, Category_ID, Publisher_ID)
                    VALUES (:isbn, :title, :yr, :cid, :pid)
                """, {"isbn": isbn, "title": title, "yr": yr, "cid": first_cat_id, "pid": first_pub_id})
            conn.commit()
            print(f" -> Seeded {len(sample_books)} sample books.")
        else:
            print(" -> Table already populated.")

        cursor.execute("SELECT Book_ID, Title FROM Books")
        all_books = cursor.fetchall()

        # =====================================================================
        # 6. TABLE: BOOK_AUTHORS
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Book_Authors")
        ba_count = cursor.fetchone()[0]
        print(f"\n[6/11] Checking BOOK_AUTHORS table (Current rows: {ba_count})...")
        if ba_count == 0 and all_books and all_author_ids:
            for b in all_books:
                b_id = b[0]
                a_id = all_author_ids[b_id % len(all_author_ids)]
                cursor.execute("""
                    INSERT INTO Book_Authors (Book_ID, Author_ID)
                    VALUES (:bid, :aid)
                """, {"bid": b_id, "aid": a_id})
            conn.commit()
            print(" -> Seeded Book_Authors relationships.")
        else:
            print(" -> Table already populated.")

        # =====================================================================
        # 7. TABLE: BOOK_COPIES
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Book_Copies")
        copies_count = cursor.fetchone()[0]
        print(f"\n[7/11] Checking BOOK_COPIES table (Current rows: {copies_count})...")
        if copies_count < len(all_books) * 3:
            # Ensure at least 3 physical copies per book
            for b in all_books:
                b_id = b[0]
                cursor.execute("SELECT COUNT(*) FROM Book_Copies WHERE Book_ID = :bid", {"bid": b_id})
                c_cnt = cursor.fetchone()[0]
                needed = max(0, 3 - c_cnt)
                for _ in range(needed):
                    cursor.execute("""
                        INSERT INTO Book_Copies (Book_ID, Status, Condition)
                        VALUES (:bid, 'Available', 'Good')
                    """, {"bid": b_id})
            conn.commit()
            print(" -> Added physical copies to ensure abundant inventory.")
        else:
            print(" -> Table already populated with sufficient copies.")

        cursor.execute("SELECT Copy_ID, Book_ID, Status FROM Book_Copies ORDER BY Copy_ID")
        all_copies = cursor.fetchall()

        # =====================================================================
        # 8 & 9. TABLE: LOANS & FINES (Populating Activity for ALL Users)
        # =====================================================================
        print("\n[8/11 & 9/11] Checking LOANS and FINES per user...")
        now = datetime.now()

        # Filter patron users (Students and Staff)
        cursor.execute("SELECT User_ID, Username, Role FROM Users WHERE Role IN ('Student', 'Staff') AND User_ID != 0 ORDER BY User_ID")
        patrons = cursor.fetchall()

        for p_uid, p_uname, p_role in patrons:
            # Check user loans
            cursor.execute("SELECT COUNT(*) FROM Loans WHERE Borrower_ID = :p_uid", {"p_uid": p_uid})
            user_loans_count = cursor.fetchone()[0]

            if user_loans_count == 0:
                # Assign a past completed loan so user history is rich without blocking new borrowing
                cursor.execute("SELECT Copy_ID FROM Book_Copies WHERE Status = 'Available' AND ROWNUM = 1")
                avail_copy = cursor.fetchone()
                if avail_copy:
                    c_id = avail_copy[0]
                    issue_dt = now - timedelta(days=25)
                    due_dt = now - timedelta(days=11)
                    ret_dt = now - timedelta(days=8) # returned late by 3 days

                    new_loan_id_var = cursor.var(oracledb.NUMBER)
                    cursor.execute("""
                        INSERT INTO Loans (Copy_ID, Borrower_ID, Issued_By, Issue_Date, Due_Date, Return_Date)
                        VALUES (:copy_id, :borrower_id, :issued_by, :issue_date, :due_date, :return_date)
                        RETURNING Loan_ID INTO :lid
                    """, {
                        "copy_id": c_id,
                        "borrower_id": p_uid,
                        "issued_by": librarian_id,
                        "issue_date": issue_dt,
                        "due_date": due_dt,
                        "return_date": ret_dt,
                        "lid": new_loan_id_var
                    })
                    loan_id = int(new_loan_id_var.getvalue()[0])
                    print(f" -> Created historical loan #{loan_id} for patron '{p_uname}' ({p_role}).")

                    # Check fines for this patron
                    cursor.execute("""
                        SELECT COUNT(*) FROM Fines f
                        JOIN Loans l ON f.Loan_ID = l.Loan_ID
                        WHERE l.Borrower_ID = :p_uid
                    """, {"p_uid": p_uid})
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO Fines (Loan_ID, Fine_Amount, Payment_Status, Payment_Date, Collected_By)
                            VALUES (:lid, 30.00, 'Paid', SYSDATE, :cid)
                        """, {"lid": loan_id, "cid": admin_id})
                        print(f"    -> Added paid sample fine statement for patron '{p_uname}'.")
            else:
                # User already has loans, check if user has at least one fine entry
                cursor.execute("""
                    SELECT COUNT(*) FROM Fines f
                    JOIN Loans l ON f.Loan_ID = l.Loan_ID
                    WHERE l.Borrower_ID = :p_uid
                """, {"p_uid": p_uid})
                if cursor.fetchone()[0] == 0:
                    cursor.execute("SELECT Loan_ID FROM Loans WHERE Borrower_ID = :p_uid AND ROWNUM = 1", {"p_uid": p_uid})
                    target_loan = cursor.fetchone()
                    if target_loan:
                        cursor.execute("""
                            INSERT INTO Fines (Loan_ID, Fine_Amount, Payment_Status, Payment_Date, Collected_By)
                            VALUES (:lid, 20.00, 'Paid', SYSDATE, :cid)
                        """, {"lid": target_loan[0], "cid": admin_id})
                        print(f" -> Added paid sample fine statement for patron '{p_uname}'.")
        conn.commit()

        # =====================================================================
        # 10. TABLE: LOAN_REQUESTS (Ensure Queue records for ALL Users)
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Loan_Requests")
        total_requests = cursor.fetchone()[0]
        print(f"\n[10/11] Checking LOAN_REQUESTS table (Current rows: {total_requests})...")

        for p_uid, p_uname, p_role in patrons:
            cursor.execute("SELECT COUNT(*) FROM Loan_Requests WHERE Borrower_ID = :p_uid", {"p_uid": p_uid})
            user_req_count = cursor.fetchone()[0]

            if user_req_count == 0 and all_books:
                # Select a book for the request
                target_book_id = all_books[(p_uid + 1) % len(all_books)][0]

                # Check if this user already holds or requested this book
                cursor.execute("""
                    SELECT COUNT(*) FROM Loan_Requests
                    WHERE Borrower_ID = :p_uid AND Book_ID = :bid
                """, {"p_uid": p_uid, "bid": target_book_id})
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO Loan_Requests (Book_ID, Borrower_ID, Request_Date, Status)
                        VALUES (:bid, :p_uid, SYSDATE - 1, 'Fulfilled')
                    """, {"bid": target_book_id, "p_uid": p_uid})
                    print(f" -> Added fulfilled sample queue request for patron '{p_uname}'.")
        conn.commit()

        # =====================================================================
        # 11. TABLE: AUDIT_LOGS
        # =====================================================================
        cursor.execute("SELECT COUNT(*) FROM Audit_Logs")
        audit_count = cursor.fetchone()[0]
        print(f"\n[11/11] Checking AUDIT_LOGS table (Current rows: {audit_count})...")
        if audit_count == 0:
            sample_logs = [
                ("SYSTEM_BOOTSTRAP", "System", "admin", "Enterprise Library System initialization and security audit baseline established."),
                ("USER_AUDIT", "student", "admin", "Account standing verified and cleared for circulation privileges."),
                ("LEDGER_RECONCILE", "Finance", "admin", "Overdue penalty rates verified against university financial guidelines.")
            ]
            for action, tgt, actor, details in sample_logs:
                cursor.execute("""
                    INSERT INTO Audit_Logs (Action_Type, Target_User, Performed_By, Log_Date, Details)
                    VALUES (:action, :target, :actor, SYSDATE, :details)
                """, {"action": action, "target": tgt, "actor": actor, "details": details})
            conn.commit()
            print(f" -> Seeded {len(sample_logs)} baseline Audit_Logs entries.")
        else:
            print(" -> Table already populated.")

        print("\n=================================================================")
        print("SUMMARY: Final Record Counts Across All Application Tables")
        print("=================================================================")
        tables = [
            "Users", "Categories", "Publishers", "Authors", "Books",
            "Book_Authors", "Book_Copies", "Loans", "Fines", "Loan_Requests", "Audit_Logs"
        ]
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            print(f" - {t:<15}: {cnt:>4} rows")
        print("=================================================================")
        print("[SUCCESS] All tables and all users verified and populated!")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Database seeding failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_database()
