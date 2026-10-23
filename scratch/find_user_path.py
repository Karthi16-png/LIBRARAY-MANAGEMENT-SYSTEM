import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import get_session

with get_session() as s:
    res = s.run("""
        MATCH (b1:Book), (b2:Book)
        WHERE b1.book_id < b2.book_id
        MATCH p = shortestPath((b1:Book)-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|PUBLISHED_BY|HAS_COPY|FOR_COPY|BORROWED|FOR_BOOK*1..10]-(b2:Book))
        WHERE any(n IN nodes(p) WHERE 'User' IN labels(n))
        RETURN b1.book_id AS id1, b2.book_id AS id2, [n IN nodes(p) | labels(n)] AS lbls, [r IN relationships(p) | type(r)] AS rels
        LIMIT 5
    """)
    records = list(res)
    print("Found count:", len(records))
    for r in records:
        print(f"Books {r['id1']} <-> {r['id2']}:")
        print("  Labels:", r['lbls'])
        print("  Rels:", r['rels'])
