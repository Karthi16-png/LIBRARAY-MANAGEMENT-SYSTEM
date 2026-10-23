import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    res = s.run("""
        MATCH (c:Category)
        OPTIONAL MATCH (c)<-[:BELONGS_TO]-(b:Book)
        OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
        RETURN c.category_id AS cid, c.name AS name,
               count(DISTINCT b) AS titles_count,
               count(DISTINCT CASE WHEN cp.status <> 'Retired' AND cp.status <> 'Lost' THEN cp ELSE null END) AS active_books_count,
               count(DISTINCT CASE WHEN cp.status = 'Lost' THEN cp ELSE null END) AS lost_books_count
        ORDER BY c.category_id
    """)
    for r in res:
        print(dict(r))
