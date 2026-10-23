"""
Neo4j AuraDB Seeding Script - VITCC Library Management System
Migrated from Oracle 21c to Neo4j Graph Database.
Seeds all 9 entity types with 10+ records each using explicit graph relationships.
"""

from neo4j import GraphDatabase
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

NEO4J_URI      = "neo4j+s://e7f1b8d0.databases.neo4j.io"
NEO4J_USERNAME = "e7f1b8d0"
NEO4J_PASSWORD = "ROzf6G2s6B2tP6C61ODmEGMbmG-pzeCq5KZgI6CmxHI"
NEO4J_DATABASE = "e7f1b8d0"


def run_seed():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    print("Connected to Neo4j AuraDB. Beginning comprehensive seeding...")

    with driver.session(database=NEO4J_DATABASE) as session:
        try:
            # =================================================================
            # WIPE existing data for a clean seed
            # =================================================================
            print("\n[0/9] Clearing existing graph data...")
            session.run("MATCH (n) DETACH DELETE n")
            print(" -> Graph cleared.")

            # =================================================================
            # 0.1 CREATE UNIQUENESS CONSTRAINTS
            # =================================================================
            print("\n[0.1] Ensuring schema uniqueness constraints...")
            constraints = [
                ("user_id_unique", "User", "user_id"),
                ("user_username_unique", "User", "username"),
                ("user_email_unique", "User", "email"),
                ("book_id_unique", "Book", "book_id"),
                ("book_isbn_unique", "Book", "isbn"),
                ("category_id_unique", "Category", "category_id"),
                ("publisher_id_unique", "Publisher", "publisher_id"),
                ("author_id_unique", "Author", "author_id"),
                ("copy_id_unique", "Copy", "copy_id"),
                ("loan_id_unique", "Loan", "loan_id"),
                ("fine_id_unique", "Fine", "fine_id"),
                ("request_id_unique", "LoanRequest", "request_id"),
            ]
            for c_name, label, prop in constraints:
                session.run(f"CREATE CONSTRAINT {c_name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE")
            print(" -> All 12 uniqueness constraints verified.")

            # =================================================================
            # 1. SEED USERS (11 users across all 4 RBAC roles)
            # =================================================================
            print("\n[1/9] Seeding Users...")
            users = [
                ("admin",        "Admin@123",   "admin@vit.edu",         "Admin"),
                ("librarian",    "Lib@12345",   "librarian@vit.edu",     "Librarian"),
                ("staff",        "Staff@123",   "staff@vit.edu",         "Staff"),
                ("prof_turing",  "Staff@123",   "turing@vit.edu",        "Staff"),
                ("prof_shannon", "Staff@123",   "shannon@vit.edu",       "Staff"),
                ("student",      "Student@1",   "student@vit.edu",       "Student"),
                ("alex_stu",     "Student@1",   "alex@vit.edu",          "Student"),
                ("priya_stu",    "Student@1",   "priya@vit.edu",         "Student"),
                ("rahul_stu",    "Student@1",   "rahul@vit.edu",         "Student"),
                ("emily_stu",    "Student@1",   "emily@vit.edu",         "Student"),
                ("marcus_stu",   "Student@1",   "marcus@vit.edu",        "Student"),
            ]

            for idx, u in enumerate(users, start=1):
                pw_hash = generate_password_hash(u[1])
                session.run("""
                    CREATE (u:User {
                        user_id: $uid,
                        username: $username,
                        password_hash: $pw,
                        email: $email,
                        role: $role,
                        account_status: 'Active'
                    })
                """, uid=idx, username=u[0], pw=pw_hash, email=u[2], role=u[3])

            result = session.run("MATCH (u:User) RETURN u.username AS username, u.user_id AS user_id")
            user_id_map = {r["username"]: r["user_id"] for r in result}
            print(f" -> Seeded {len(users)} users.")

            # =================================================================
            # 2. SEED CATEGORIES (10 records)
            # =================================================================
            print("[2/9] Seeding Categories...")
            categories = [
                ("Computer Science & AI",        "CS"),
                ("Physics & Astronomy",           "PHY"),
                ("Mathematics & Statistics",      "MAT"),
                ("Electrical Engineering",        "EE"),
                ("Mechanical Engineering",        "ME"),
                ("World History & Civilizations", "HIS"),
                ("Philosophy & Ethics",           "PHI"),
                ("Classical Literature",          "LIT"),
                ("Economics & Public Policy",     "ECO"),
                ("Data Architecture & Databases", "DB"),
            ]

            for idx, cat in enumerate(categories, start=1):
                session.run("""
                    CREATE (c:Category {
                        category_id: $cid,
                        name: $name,
                        section_code: $code
                    })
                """, cid=idx, name=cat[0], code=cat[1])

            result = session.run("MATCH (c:Category) RETURN c.name AS name, c.category_id AS cid")
            category_id_map = {r["name"]: r["cid"] for r in result}
            print(f" -> Seeded {len(categories)} categories.")

            # =================================================================
            # 3. SEED PUBLISHERS (10 records)
            # =================================================================
            print("[3/9] Seeding Publishers...")
            publishers = [
                ("O'Reilly Media",              "contact@oreilly.com"),
                ("Pearson Education",           "support@pearson.com"),
                ("MIT Press",                   "info@mitpress.mit.edu"),
                ("McGraw-Hill Education",       "help@mheducation.com"),
                ("Addison-Wesley Professional", "inquiries@addisonwesley.com"),
                ("Cambridge University Press",  "academic@cambridge.org"),
                ("Oxford University Press",     "custserv@oup.com"),
                ("Springer Nature",             "contact@springernature.com"),
                ("John Wiley & Sons",           "support@wiley.com"),
                ("Morgan Kaufmann",             "info@mkp.com"),
            ]

            for idx, pub in enumerate(publishers, start=1):
                session.run("""
                    CREATE (p:Publisher {
                        publisher_id: $pid,
                        name: $name,
                        contact_email: $email
                    })
                """, pid=idx, name=pub[0], email=pub[1])

            result = session.run("MATCH (p:Publisher) RETURN p.name AS name, p.publisher_id AS pid")
            publisher_id_map = {r["name"]: r["pid"] for r in result}
            print(f" -> Seeded {len(publishers)} publishers.")

            # =================================================================
            # 4. SEED AUTHORS (10 records)
            # =================================================================
            print("[4/9] Seeding Authors...")
            authors = [
                ("Donald",  "Knuth"),
                ("Martin",  "Fowler"),
                ("Robert",  "Martin"),
                ("Eric",    "Evans"),
                ("Abraham", "Silberschatz"),
                ("Andrew",  "Tanenbaum"),
                ("Thomas",  "Cormen"),
                ("Stuart",  "Russell"),
                ("Peter",   "Norvig"),
                ("Richard", "Feynman"),
            ]

            for idx, auth in enumerate(authors, start=1):
                session.run("""
                    CREATE (a:Author {
                        author_id: $aid,
                        first_name: $fn,
                        last_name: $ln
                    })
                """, aid=idx, fn=auth[0], ln=auth[1])

            result = session.run("""
                MATCH (a:Author)
                RETURN (a.first_name + ' ' + a.last_name) AS full_name, a.author_id AS aid
            """)
            author_id_map = {r["full_name"]: r["aid"] for r in result}
            print(f" -> Seeded {len(authors)} authors.")

            # =================================================================
            # 5. SEED BOOKS + graph relationships (10 records)
            # =================================================================
            print("[5/9] Seeding Books + graph relationships...")
            books = [
                ("978-1449373320", "Designing Data-Intensive Applications",     2017,
                 "Data Architecture & Databases", "O'Reilly Media",              ["Martin Fowler"]),
                ("978-0132350884", "Clean Code: Agile Software Craftsmanship",   2008,
                 "Computer Science & AI",         "Pearson Education",           ["Robert Martin"]),
                ("978-0262033848", "Introduction to Algorithms (CLRS)",          2009,
                 "Computer Science & AI",         "MIT Press",                   ["Thomas Cormen"]),
                ("978-0136042594", "Artificial Intelligence: A Modern Approach", 2020,
                 "Computer Science & AI",         "Pearson Education",           ["Stuart Russell", "Peter Norvig"]),
                ("978-0078022159", "Database System Concepts (7th Ed)",          2019,
                 "Data Architecture & Databases", "McGraw-Hill Education",       ["Abraham Silberschatz"]),
                ("978-0133591620", "Modern Operating Systems (4th Ed)",          2014,
                 "Computer Science & AI",         "Addison-Wesley Professional", ["Andrew Tanenbaum"]),
                ("978-0132126953", "Computer Networks (5th Ed)",                 2010,
                 "Computer Science & AI",         "Pearson Education",           ["Andrew Tanenbaum"]),
                ("978-0321125217", "Domain-Driven Design: Tackling Complexity",  2003,
                 "Computer Science & AI",         "Addison-Wesley Professional", ["Eric Evans"]),
                ("978-0201896831", "The Art of Computer Programming, Vol 1",     1997,
                 "Mathematics & Statistics",      "Addison-Wesley Professional", ["Donald Knuth"]),
                ("978-0465023820", "The Feynman Lectures on Physics",            2011,
                 "Physics & Astronomy",           "Addison-Wesley Professional", ["Richard Feynman"]),
            ]

            book_id_map = {}  # isbn -> book_id
            for idx, b in enumerate(books, start=1):
                isbn, title, year, cat_name, pub_name, auth_names = b
                cat_id = category_id_map.get(cat_name)
                pub_id = publisher_id_map.get(pub_name)

                session.run("""
                    CREATE (bk:Book {
                        book_id: $bid,
                        isbn: $isbn,
                        title: $title,
                        publication_year: $year,
                        category_id: $cat_id,
                        publisher_id: $pub_id
                    })
                """, bid=idx, isbn=isbn, title=title, year=year,
                     cat_id=cat_id, pub_id=pub_id)

                session.run("""
                    MATCH (bk:Book {book_id: $bid}), (c:Category {category_id: $cid})
                    CREATE (bk)-[:BELONGS_TO]->(c)
                """, bid=idx, cid=cat_id)

                session.run("""
                    MATCH (bk:Book {book_id: $bid}), (p:Publisher {publisher_id: $pid})
                    CREATE (bk)-[:PUBLISHED_BY]->(p)
                """, bid=idx, pid=pub_id)

                for a_name in auth_names:
                    a_id = author_id_map.get(a_name)
                    if a_id:
                        session.run("""
                            MATCH (a:Author {author_id: $aid}), (bk:Book {book_id: $bid})
                            CREATE (a)-[:WROTE]->(bk)
                        """, aid=a_id, bid=idx)

                book_id_map[isbn] = idx

            print(f" -> Seeded {len(books)} books.")

            # =================================================================
            # 6. SEED BOOK COPIES (2 per book = 20 copies)
            # =================================================================
            print("[6/9] Seeding Book Copies...")
            cid_counter = 1
            copy_rows = []

            for isbn, b_id in book_id_map.items():
                for condition in ["New", "Good"]:
                    session.run("""
                        CREATE (cp:Copy {
                            copy_id: $cid,
                            book_id: $bid,
                            status: 'Available',
                            condition: $cond
                        })
                    """, cid=cid_counter, bid=b_id, cond=condition)

                    session.run("""
                        MATCH (bk:Book {book_id: $bid}), (cp:Copy {copy_id: $cid})
                        CREATE (bk)-[:HAS_COPY]->(cp)
                    """, bid=b_id, cid=cid_counter)

                    copy_rows.append((cid_counter, b_id))
                    cid_counter += 1

            print(f" -> Seeded {len(copy_rows)} book copies.")

            # =================================================================
            # 7. SEED LOANS (12 scenarios)
            # =================================================================
            print("[7/9] Seeding Loans...")
            librarian_id = user_id_map.get("librarian", user_id_map.get("admin"))
            student_id   = user_id_map.get("student")
            alex_id      = user_id_map.get("alex_stu")
            priya_id     = user_id_map.get("priya_stu")
            rahul_id     = user_id_map.get("rahul_stu")
            staff_id     = user_id_map.get("staff")
            turing_id    = user_id_map.get("prof_turing")

            now = datetime.now()

            loan_configs = [
                (0,  student_id, 3,  -11, None),
                (1,  alex_id,   5,  -9,  None),
                (2,  staff_id,  7,  -7,  None),
                (3,  student_id, 25, 12,  1),   # Returned Oct 17, 2026 (11 days late = Rs. 110.00 Paid)
                (4,  rahul_id,  20,  6,  None),
                (5,  priya_id,  30, 16,  None),
                (6,  student_id, 31, 17,  14),  # Due Oct 1, returned Oct 4 (3 days late = Rs. 30.00 Paid)
                (7,  alex_id,   20,  10,  6),   # Returned 4 days late = Rs. 40.00 Unpaid
                (8,  turing_id, 15,  5,   2),   # Returned 3 days late = Rs. 30.00 Paid
                (9,  student_id, 40, 26,  20),
                (10, rahul_id,  35, 21,  14),
                (11, priya_id,  50, 36,  25),
                (12, staff_id,  22, 12,   7),   # Returned 5 days late = Rs. 50.00 Paid
            ]

            loans_list = []

            for loan_idx, cfg in enumerate(loan_configs, start=1):
                c_idx, b_id, issue_days, due_days, ret_days = cfg
                c_id = copy_rows[c_idx][0]

                issue_dt = now - timedelta(days=issue_days)
                due_dt   = now - timedelta(days=due_days)
                ret_dt   = (now - timedelta(days=ret_days)) if ret_days is not None else None

                session.run("""
                    CREATE (l:Loan {
                        loan_id: $lid,
                        copy_id: $cid,
                        borrower_id: $bid,
                        issued_by: $issby,
                        issue_date: $issue_date,
                        due_date: $due_date,
                        return_date: $return_date
                    })
                """, lid=loan_idx, cid=c_id, bid=b_id, issby=librarian_id,
                     issue_date=issue_dt.strftime("%Y-%m-%d"),
                     due_date=due_dt.strftime("%Y-%m-%d"),
                     return_date=ret_dt.strftime("%Y-%m-%d") if ret_dt else None)

                session.run("""
                    MATCH (u:User {user_id: $uid}), (l:Loan {loan_id: $lid})
                    CREATE (u)-[:BORROWED]->(l)
                """, uid=b_id, lid=loan_idx)

                session.run("""
                    MATCH (l:Loan {loan_id: $lid}), (cp:Copy {copy_id: $cid})
                    CREATE (l)-[:FOR_COPY]->(cp)
                """, lid=loan_idx, cid=c_id)

                session.run("""
                    MATCH (lib:User {user_id: $uid}), (l:Loan {loan_id: $lid})
                    CREATE (lib)-[:ISSUED]->(l)
                """, uid=librarian_id, lid=loan_idx)

                if ret_dt is None:
                    session.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Borrowed'", cid=c_id)

                loans_list.append((loan_idx, b_id, issue_dt, due_dt, ret_dt))

            print(f" -> Seeded {len(loans_list)} loans.")

            # =================================================================
            # 8. SEED FINES (10 records)
            # =================================================================
            print("[8/9] Seeding Fines...")
            fine_specs = [
                (3,  110.00, "Paid"),    # Loan #4 (Clean Code, returned 11 days late = Rs. 110 Paid)
                (4,   60.00, "Unpaid"),
                (5,  160.00, "Unpaid"),
                (9,   60.00, "Paid"),
                (10,  70.00, "Paid"),
                (11, 110.00, "Waived"),
                (6,   30.00, "Paid"),    # Loan #7 (AI, returned 3 days late = Rs. 30 Paid)
                (7,   40.00, "Unpaid"),
                (8,   30.00, "Paid"),
                (12,  50.00, "Paid"),    # Loan #13 (staff, returned 5 days late = Rs. 50 Paid)
            ]

            for fine_idx, spec in enumerate(fine_specs, start=1):
                loan_0idx, amount, status = spec
                l_id = loans_list[loan_0idx][0]
                l_ret_dt = loans_list[loan_0idx][4]
                pay_dt = (l_ret_dt.strftime("%Y-%m-%d") if l_ret_dt else "2026-10-17") if status == "Paid" else None
                col_by = librarian_id if status == "Paid" else None

                session.run("""
                    CREATE (f:Fine {
                        fine_id: $fid,
                        loan_id: $lid,
                        fine_amount: $amt,
                        payment_status: $status,
                        payment_date: $pay_date,
                        collected_by: $col_by
                    })
                """, fid=fine_idx, lid=l_id, amt=amount, status=status,
                     pay_date=pay_dt, col_by=col_by)

                session.run("""
                    MATCH (l:Loan {loan_id: $lid}), (f:Fine {fine_id: $fid})
                    CREATE (l)-[:HAS_FINE]->(f)
                """, lid=l_id, fid=fine_idx)

            print(f" -> Seeded {len(fine_specs)} fines.")

            # =================================================================
            # 9. SEED LOAN REQUESTS (10 records)
            # =================================================================
            print("[9/9] Seeding Loan Requests...")
            book_ids_list = list(book_id_map.values())

            request_specs = [
                ("emily_stu",    0, "Pending",         2),
                ("marcus_stu",   1, "Pending",         1),
                ("alex_stu",     2, "Pending",         5),  # CLRS copies 5 & 6 already borrowed; re-synced to Pending
                ("marcus_stu",   3, "Awaiting Pickup", 4),  # Eligible student in good standing
                ("rahul_stu",    4, "Fulfilled",       10),
                ("student",      5, "Fulfilled",       15),
                ("emily_stu",    6, "Rejected",         7),
                ("marcus_stu",   7, "Pending",          3),
                ("prof_turing",  8, "Fulfilled",        20),
                ("prof_shannon", 9, "Pending",           1),
            ]

            for req_idx, spec in enumerate(request_specs, start=1):
                uname, b_idx, status, days_ago = spec
                borrower_id = user_id_map.get(uname)
                b_id = book_ids_list[b_idx]
                req_date = now - timedelta(days=days_ago)

                # For Awaiting Pickup (e.g. Marcus REQ-4 for AI Book), assign available copy 8
                assigned_cid = 8 if req_idx == 4 and status == "Awaiting Pickup" else None

                session.run("""
                    CREATE (r:LoanRequest {
                        request_id: $rid,
                        book_id: $bid,
                        borrower_id: $borrower_id,
                        copy_id: $cid,
                        request_date: $rdate,
                        status: $status
                    })
                """, rid=req_idx, bid=b_id, borrower_id=borrower_id,
                     cid=assigned_cid,
                     rdate=req_date.strftime("%Y-%m-%d"), status=status)

                session.run("""
                    MATCH (u:User {user_id: $uid}), (r:LoanRequest {request_id: $rid})
                    CREATE (u)-[:REQUESTED]->(r)
                """, uid=borrower_id, rid=req_idx)

                session.run("""
                    MATCH (r:LoanRequest {request_id: $rid}), (bk:Book {book_id: $bid})
                    CREATE (r)-[:FOR_BOOK]->(bk)
                """, rid=req_idx, bid=b_id)

                if assigned_cid:
                    session.run("""
                        MATCH (cp:Copy {copy_id: $cid})
                        SET cp.status = 'Reserved'
                    """, cid=assigned_cid)
                    session.run("""
                        MATCH (r:LoanRequest {request_id: $rid}), (cp:Copy {copy_id: $cid})
                        CREATE (r)-[:RESERVED_COPY]->(cp)
                    """, rid=req_idx, cid=assigned_cid)

            print(f" -> Seeded {len(request_specs)} loan requests.")

            # =================================================================
            # 10. SEED ACADEMIC PREREQUISITES ([:PREREQUISITE_FOR])
            # =================================================================
            print("\n[10/10] Seeding Academic Prerequisite Hierarchy ([:PREREQUISITE_FOR])...")
            prereq_edges = [
                (2, 3, "Code Quality to Algorithms"),
                (3, 4, "Algorithms to Intelligent Systems"),
                (3, 9, "Algorithms to Theoretical Mastery"),
                (2, 8, "Clean Code to Domain Architecture"),
                (6, 7, "OS Internals to Network Protocols"),
                (7, 1, "Networking to Distributed Storage"),
                (5, 1, "Relational Theory to Distributed Scale"),
            ]
            for src_id, dst_id, jump in prereq_edges:
                session.run("""
                    MATCH (src:Book {book_id: $src_id}), (dst:Book {book_id: $dst_id})
                    MERGE (src)-[r:PREREQUISITE_FOR]->(dst)
                    SET r.difficulty_jump = $jump
                """, src_id=src_id, dst_id=dst_id, jump=jump)
            print(f" -> Seeded {len(prereq_edges)} prerequisite relationships.")

            print("\n[VERIFICATION] Node and Relationship counts:")
            for label in ["User", "Category", "Publisher", "Author", "Book", "Copy", "Loan", "Fine", "LoanRequest"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
                cnt = result.single()["cnt"]
                print(f"  Node {label}: {cnt}")

            rel_res = session.run("MATCH ()-[r:PREREQUISITE_FOR]->() RETURN count(r) AS cnt")
            print(f"  Relationship PREREQUISITE_FOR: {rel_res.single()['cnt']}")

            print("\n[SUCCESS] All 9 entity types and prerequisite roadmap seeded into Neo4j AuraDB!")
            print("\nLogin credentials:")
            print("  admin       / Admin@123")
            print("  librarian   / Lib@12345")
            print("  staff       / Staff@123")
            print("  student     / Student@1")

        except Exception as e:
            print(f"\n[ERROR] Seeding aborted: {e}")
            raise
        finally:
            driver.close()


if __name__ == "__main__":
    run_seed()
