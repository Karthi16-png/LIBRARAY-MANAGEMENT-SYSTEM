import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import get_session, today_str

with get_session() as s:
    today = today_str()
    res = s.run("""
        MATCH (u:User)
        WHERE u.role IN ['Student','Staff'] AND u.account_status = 'Active'
        RETURN u.user_id AS user_id, u.username AS username,
               u.role AS role, u.email AS email,
               size([(u)-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'}) | f]) AS unpaid_fines_count,
               size([(u)-[:BORROWED]->(ol:Loan) WHERE ol.return_date IS NULL AND ol.due_date < $today | ol]) AS overdue_count
        ORDER BY u.role ASC, u.username ASC
    """, today=today).data()
    for r in res:
        has_block = (r["unpaid_fines_count"] > 0 or r["overdue_count"] > 0)
        print(f"{r['username']} ({r['role']}) - Fines count: {r['unpaid_fines_count']}, Overdue count: {r['overdue_count']}, Block: {has_block}")
