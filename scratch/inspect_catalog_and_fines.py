import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    print("--- Categories and counts ---")
    res = s.run("""
        MATCH (c:Category)
        OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
        OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
        RETURN c.category_id AS cid, c.name AS name,
               count(DISTINCT b) AS book_titles_count,
               count(cp) AS all_copies_count,
               size([(b)-[:HAS_COPY]->(c1:Copy) WHERE c1.status <> 'Retired' AND c1.status <> 'Lost' | c1]) AS active_copies_count,
               size([(b)-[:HAS_COPY]->(c2:Copy) WHERE c2.status = 'Lost' | c2]) AS lost_copies_count
        ORDER BY c.category_id
    """)
    for r in res:
        print(dict(r))

    print("\n--- Copies and their statuses ---")
    res = s.run("MATCH (cp:Copy) RETURN cp.status AS status, count(cp) AS count")
    for r in res:
        print(dict(r))

    print("\n--- Loans and Fines summary ---")
    res = s.run("""
        MATCH (f:Fine)
        OPTIONAL MATCH (l:Loan)-[:HAS_FINE]->(f)
        OPTIONAL MATCH (u:User)-[:BORROWED]->(l)
        RETURN f.fine_id AS fine_id, f.fine_amount AS amount, f.payment_status AS status,
               u.username AS user, l.loan_id AS loan_id
        ORDER BY f.fine_id
    """)
    total_fines = 0.0
    for r in res:
        print(dict(r))
        total_fines += r["amount"]
    print(f"Total all fines: {total_fines}")

    res_unpaid = s.run("""
        MATCH (f:Fine {payment_status: 'Unpaid'})
        RETURN sum(f.fine_amount) AS unpaid_total
    """)
    print("Unpaid total fines:", res_unpaid.single()["unpaid_total"])
