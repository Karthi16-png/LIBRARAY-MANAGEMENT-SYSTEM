import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import get_session

with get_session() as s:
    uid = 3
    res = s.run("""
        MATCH (me:User {user_id: $uid})-[:BORROWED|REQUESTED]->()-[:FOR_COPY|FOR_BOOK]->()-[:HAS_COPY*0..1]-(b1:Book)
        MATCH path = (b1)-[r:BELONGS_TO|WROTE|PREREQUISITE_FOR*1..2]-(rec:Book)
        WHERE rec.book_id <> b1.book_id
          AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(rec)
          AND NOT (me)-[:REQUESTED]->(:LoanRequest)-[:FOR_BOOK]->(rec)
        RETURN me, b1, nodes(path) AS p_nodes, relationships(path) AS p_rels, rec
        LIMIT 10
    """, uid=uid)
    for row in res:
        p_nodes = row["p_nodes"]
        p_rels = row["p_rels"]
        labels_str = [list(n.labels)[0] for n in p_nodes]
        print("Path len:", len(p_nodes), labels_str)
        for rel in p_rels:
            print("  rel:", rel.type)
