import os, sys
sys.path.insert(0, os.path.abspath("."))
from app import get_session

with get_session() as s:
    for fid in [11, 12, 13]:
        res = s.run("MATCH (f:Fine {fine_id: $fid}) RETURN f, [(f)--(x) | [labels(x), properties(x)]] AS rels", fid=fid)
        for r in res:
            print(f"Fine #{fid}:", dict(r["f"]), "Connected to:", r["rels"])
