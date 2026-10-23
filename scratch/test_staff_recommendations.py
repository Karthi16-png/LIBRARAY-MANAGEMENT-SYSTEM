import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import get_session

with get_session() as s:
    uid = 3
    res = s.run("""
        MATCH (me:User {user_id: $uid})-[:BORROWED|REQUESTED]->()-[:FOR_COPY|FOR_BOOK]->()-[:HAS_COPY*0..1]-(b1:Book)
        MATCH path = (b1)-[r:BELONGS_TO|WROTE|PREREQUISITE_FOR*1..2]-(b2:Book)
        WHERE b1.book_id <> b2.book_id
          AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2)
          AND NOT (me)-[:REQUESTED]->(:LoanRequest)-[:FOR_BOOK]->(b2)
        RETURN me.username AS me, b1.title AS b1, [n IN nodes(path) | labels(n)[0] + ': ' + coalesce(n.name, n.first_name + ' ' + n.last_name, n.title)] AS path_nodes, b2.title AS b2
        LIMIT 10
    """, uid=uid).data()
    for r in res:
        print(r)
