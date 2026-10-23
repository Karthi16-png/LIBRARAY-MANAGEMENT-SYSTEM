import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    res1 = s.run("""
        MATCH (f:Fine {payment_status: 'Unpaid'})
        RETURN coalesce(sum(f.fine_amount), 0) AS c
    """).single()["c"]
    print("Stat card query (data['unpaid_fines']):", res1)

    res2 = s.run("""
        MATCH (l:Loan)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
        MATCH (u:User)-[:BORROWED]->(l)
        OPTIONAL MATCH (l)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
        RETURN f.fine_id AS fine_id, f.fine_amount AS fine_amount,
               f.payment_status AS payment_status,
               u.username AS borrower_name, u.email AS borrower_email,
               coalesce(b.title, 'Archived/Deleted Title') AS book_title,
               l.loan_id AS loan_id, l.due_date AS due_date
        ORDER BY f.fine_amount DESC
    """)
    ledger_rows = list(res2)
    print("Ledger rows count:", len(ledger_rows))
    ledger_sum = 0.0
    for r in ledger_rows:
        print(f"  Fine #{r['fine_id']}: Rs. {r['fine_amount']} | User: {r['borrower_name']} | Title: {r['book_title']} | Loan: {r['loan_id']}")
        ledger_sum += r["fine_amount"]
    print(f"Ledger rows sum: Rs. {ledger_sum}")
    print(f"Discrepancy: Rs. {res1 - ledger_sum}")

    # Now let's check ALL Unpaid fines in the DB
    res3 = s.run("""
        MATCH (f:Fine {payment_status: 'Unpaid'})
        OPTIONAL MATCH (l:Loan)-[:HAS_FINE]->(f)
        OPTIONAL MATCH (u:User)-[:BORROWED]->(l)
        RETURN f.fine_id AS fid, f.fine_amount AS amt, f.loan_id AS f_lid, l.loan_id AS actual_lid, u.username AS uname
    """)
    print("\nAll Unpaid Fine Nodes:")
    for r in res3:
        print(dict(r))
