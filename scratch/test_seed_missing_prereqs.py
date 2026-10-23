import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    print("Checking missing edges:")
    s.run("""
        MATCH (b7:Book {book_id: 7}), (b1:Book {book_id: 1})
        MERGE (b7)-[r6:PREREQUISITE_FOR]->(b1)
        ON CREATE SET r6.difficulty_jump = 'Networking to Distributed Storage',
                      r6.stage = 'Stage 2 -> Stage 3',
                      r6.track = 'Data Engineering'
    """)
    s.run("""
        MATCH (b5:Book {book_id: 5}), (b1:Book {book_id: 1})
        MERGE (b5)-[r7:PREREQUISITE_FOR]->(b1)
        ON CREATE SET r7.difficulty_jump = 'Relational Theory to Distributed Scale',
                      r7.stage = 'Stage 1 -> Stage 3',
                      r7.track = 'Data Engineering'
    """)
    
    res = s.run("""
        MATCH (src:Book)-[r:PREREQUISITE_FOR]->(dst:Book)
        RETURN src.book_id AS src_id, src.title AS src_title,
               r.difficulty_jump AS jump, r.stage AS stage, r.track AS track,
               dst.book_id AS dst_id, dst.title AS dst_title
        ORDER BY src.book_id, dst.book_id
    """)
    print("Updated prerequisites:")
    for r in res:
        print(f"[{r['src_id']}] '{r['src_title']}' -> [{r['dst_id']}] '{r['dst_title']}' (track: {r['track']})")
