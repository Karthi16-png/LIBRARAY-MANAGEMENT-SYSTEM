import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import app, get_session, ensure_prerequisite_hierarchy

with app.test_request_context():
    with get_session() as s:
        ensure_prerequisite_hierarchy(s)
        res = s.run("""
            MATCH path = (root:Book)-[:PREREQUISITE_FOR*1..4]->(target:Book)
            WHERE NOT ()-[:PREREQUISITE_FOR]->(root) AND NOT (target)-[:PREREQUISITE_FOR]->()
            RETURN [n IN nodes(path) | {id: n.book_id, title: n.title}] AS nodes_in_path,
                   length(path) AS depth,
                   [r IN relationships(path) | {jump: r.difficulty_jump, track: r.track, stage: r.stage}] AS edges_in_path
        """)
        paths = list(res)
        print(f"Total end-to-end paths: {len(paths)}")
        for i, p in enumerate(paths, 1):
            titles = " -> ".join([n["title"] for n in p["nodes_in_path"]])
            print(f"Path {i} ({p['depth']} hops): {titles}")

        nodes_res = s.run("""
            MATCH (b:Book)
            WHERE (b)-[:PREREQUISITE_FOR]-()
            OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
            OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
            OPTIONAL MATCH (b)-[:PREREQUISITE_FOR]->(nxt:Book)
            OPTIONAL MATCH (prv:Book)-[:PREREQUISITE_FOR]->(b)
            WITH b, cat,
                 collect(DISTINCT a.first_name + ' ' + a.last_name) AS authors,
                 collect(DISTINCT prv.book_id) AS prereqs,
                 collect(DISTINCT nxt.book_id) AS unlocks
            RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                   coalesce(cat.category_id, b.category_id, 1) AS category_id,
                   coalesce(cat.name, 'General') AS category_name,
                   size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_copies,
                   size([(b)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies,
                   prereqs, unlocks
            ORDER BY book_id
        """)
        books = list(nodes_res)
        print(f"\nTotal books in roadmap: {len(books)}")
        for b in books:
            print(f"[{b['book_id']}] {b['title']} (Cat #{b['category_id']}: {b['category_name']}) - prereqs: {b['prereqs']}, unlocks: {b['unlocks']}")
