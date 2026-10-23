import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    print("--- PREREQUISITE_FOR relationships in DB ---")
    res = s.run("""
        MATCH (src:Book)-[r:PREREQUISITE_FOR]->(dst:Book)
        RETURN src.book_id AS src_id, src.title AS src_title,
               r.difficulty_jump AS jump, r.stage AS stage, r.track AS track,
               dst.book_id AS dst_id, dst.title AS dst_title
        ORDER BY src.book_id, dst.book_id
    """)
    rows = list(res)
    print(f"Total prerequisite relationships: {len(rows)}")
    for r in rows:
        print(f"[{r['src_id']}] '{r['src_title']}' ---> [{r['dst_id']}] '{r['dst_title']}' | stage={r['stage']}, track={r['track']}, jump={r['jump']}")

    print("\n--- All Books and whether they are in roadmap ---")
    res_b = s.run("""
        MATCH (b:Book)
        OPTIONAL MATCH (b)-[r:PREREQUISITE_FOR]-()
        RETURN b.book_id AS bid, b.title AS title, count(r) AS degree
        ORDER BY b.book_id
    """)
    for b in res_b:
        print(f"[{b['bid']}] '{b['title']}' - degree: {b['degree']}")
