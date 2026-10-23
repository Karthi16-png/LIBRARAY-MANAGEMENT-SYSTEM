import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    # 1. Clean up orphaned fines
    res = s.run("""
        MATCH (f:Fine)
        WHERE NOT (f)<-[:HAS_FINE]-(:Loan)
        RETURN f.fine_id AS fid, f.fine_amount AS amt, f.loan_id AS lid
    """)
    orphaned = list(res)
    print(f"Found {len(orphaned)} orphaned fines to delete:")
    for o in orphaned:
        print(f"  Deleting orphaned fine #{o['fid']} (Rs. {o['amt']}, mock loan {o['lid']})")
    
    del_res = s.run("""
        MATCH (f:Fine)
        WHERE NOT (f)<-[:HAS_FINE]-(:Loan)
        DETACH DELETE f
    """)
    print("Orphaned fines deleted successfully.")

    # 2. Verify remaining fines
    res_f = s.run("""
        MATCH (f:Fine {payment_status: 'Unpaid'})
        MATCH (l:Loan)-[:HAS_FINE]->(f)
        MATCH (u:User)-[:BORROWED]->(l)
        RETURN f.fine_id AS fid, f.fine_amount AS amt, u.username AS user, l.loan_id AS lid
    """)
    rem = list(res_f)
    print(f"\nRemaining Unpaid Fines in Ledger ({len(rem)}):")
    total = 0.0
    for r in rem:
        print(f"  Fine #{r['fid']}: Rs. {r['amt']} (User: {r['user']}, Loan: {r['lid']})")
        total += r["amt"]
    print(f"Total Unpaid Fines in Ledger: Rs. {total}")
