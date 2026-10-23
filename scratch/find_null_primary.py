import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import get_session

with get_session() as s:
    res = s.run("""
        MATCH (b1:Book), (b2:Book)
        WHERE b1.book_id < b2.book_id
        OPTIONAL MATCH p1 = shortestPath((b1)-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|HAS_COPY*1..5]-(b2))
        WITH b1, b2, p1
        WHERE p1 IS NULL
        RETURN count(*) AS null_primary_count
    """).single()
    print("Pairs with NULL primary path:", res["null_primary_count"])

    # If there are any, let's see them:
    res2 = s.run("""
        MATCH (b1:Book), (b2:Book)
        WHERE b1.book_id < b2.book_id
        OPTIONAL MATCH p1 = shortestPath((b1)-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|HAS_COPY*1..5]-(b2))
        WITH b1, b2, p1
        WHERE p1 IS NULL
        OPTIONAL MATCH p2 = shortestPath((b1)-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|PUBLISHED_BY|HAS_COPY|FOR_COPY|BORROWED|FOR_BOOK*1..10]-(b2))
        WHERE p2 IS NOT NULL
        RETURN b1.book_id AS id1, b1.title AS t1, b2.book_id AS id2, b2.title AS t2, [n IN nodes(p2) | labels(n)] AS lbls, [r IN relationships(p2) | type(r)] AS rels
        LIMIT 5
    """)
    for r in res2:
        print(f"Book {r['id1']} ('{r['t1']}') <-> Book {r['id2']} ('{r['t2']}'):")
        print("  Labels:", r['lbls'])
        print("  Rels:", r['rels'])
