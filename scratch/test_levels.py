import sys
sys.path.insert(0, ".")
from app import get_session, rows

with get_session() as s:
    edge_res = s.run("MATCH (src:Book)-[r:PREREQUISITE_FOR]->(dst:Book) RETURN src.book_id AS source, dst.book_id AS target, r.difficulty_jump AS difficulty_jump, r.stage AS stage, coalesce(r.track, 'General') AS track")
    edge_rows = rows(edge_res)
    nodes_res = s.run("MATCH (b:Book) WHERE (b)-[:PREREQUISITE_FOR]-() OPTIONAL MATCH (prv:Book)-[:PREREQUISITE_FOR]->(b) WITH b, collect(DISTINCT prv.book_id) AS prereqs RETURN b.book_id AS book_id, b.title AS title, prereqs")
    book_nodes = rows(nodes_res)

    in_degrees = {b["book_id"]: len(b["prereqs"]) for b in book_nodes}
    levels = {b["book_id"]: 1 for b in book_nodes if in_degrees.get(b["book_id"], 0) == 0}

    for e in edge_rows:
        stage_str = e.get("stage", "")
        if "->" in stage_str and "Stage" in stage_str:
            try:
                dest_stage = int(stage_str.split("->")[-1].replace("Stage", "").strip())
                levels[e["target"]] = max(levels.get(e["target"], 1), dest_stage)
            except Exception:
                pass

    changed = True
    it = 0
    while changed and it < 10:
        changed = False
        it += 1
        for e in edge_rows:
            src_lvl = levels.get(e["source"])
            if src_lvl is not None:
                target_lvl = src_lvl + 1
                if levels.get(e["target"]) is None or levels[e["target"]] < target_lvl:
                    levels[e["target"]] = target_lvl
                    changed = True

    for b in book_nodes:
        print(f"{b['title']} -> Level {levels.get(b['book_id'])}")
    print("Max depth:", max(levels.values()))
