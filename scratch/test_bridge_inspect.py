import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import get_session

pairs = [(1, 5), (2, 4), (1, 4), (1, 2)]
with get_session() as s:
    for a, b in pairs:
        res = s.run("""
            MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|HAS_COPY*1..5]-(b2:Book {book_id: $id2}))
            RETURN p
        """, id1=a, id2=b)
        rec = res.single()
        if not (rec and rec['p']):
            res = s.run("""
                MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|PUBLISHED_BY|HAS_COPY|FOR_COPY|BORROWED|FOR_BOOK*1..10]-(b2:Book {book_id: $id2}))
                RETURN p
            """, id1=a, id2=b)
            rec = res.single()
        p = rec['p']
        print(f"=== Book {a} to Book {b} ===")
        for idx, n in enumerate(p.nodes):
            val = n.get('title') or n.get('name') or n.get('username')
            print(f"  Node {idx}: {list(n.labels)[0]} - {val}")
        for idx, r in enumerate(p.relationships):
            s_name = r.start_node.get('title') or r.start_node.get('name')
            e_name = r.end_node.get('title') or r.end_node.get('name')
            print(f"  Rel {idx}: {r.type} from {list(r.start_node.labels)[0]} ({s_name}) to {list(r.end_node.labels)[0]} ({e_name})")
