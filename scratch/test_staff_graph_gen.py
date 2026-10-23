import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import get_session, format_graph_node

with get_session() as s:
    uid = 3
    nodes = {}
    edges = []

    def add_synth_edge(from_id, to_id, label):
        eid = f"rec_{from_id}_{to_id}_{label}"
        if eid not in [e["id"] for e in edges]:
            edges.append({
                "id": eid, "from": from_id, "to": to_id, "label": label,
                "title": label, "arrows": "to",
                "font": {"size": 10, "align": "middle", "background": "#0f172a", "color": "#94A3B8"}
            })

    target_label = "You (staff)"
    res = s.run("""
        MATCH (me:User {user_id: $uid})-[:BORROWED|REQUESTED]->()-[:FOR_COPY|FOR_BOOK]->()-[:HAS_COPY*0..1]-(b1:Book)
        MATCH path = (b1)-[r:BELONGS_TO|WROTE|PREREQUISITE_FOR*1..2]-(rec:Book)
        WHERE rec.book_id <> b1.book_id
          AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(rec)
          AND NOT (me)-[:REQUESTED]->(:LoanRequest)-[:FOR_BOOK]->(rec)
        RETURN me, b1, nodes(path) AS p_nodes, relationships(path) AS p_rels, rec
        LIMIT 15
    """, uid=uid)

    for row in res:
        me = row["me"]
        b1 = row["b1"]
        rec = row["rec"]
        p_nodes = row["p_nodes"]
        p_rels = row["p_rels"]

        # Level 0
        if me.element_id not in nodes:
            n = format_graph_node(me, custom_label=f"⭐ {target_label}", custom_group="CurrentUser")
            n["level"] = 0
            nodes[me.element_id] = n

        # Level 1
        if b1.element_id not in nodes:
            n = format_graph_node(b1, custom_label=f"📖 Borrowed:\n{b1.get('title')}", custom_group="SharedBook")
            n["level"] = 1
            nodes[b1.element_id] = n

        add_synth_edge(me.element_id, b1.element_id, "borrowed")

        # Level 2 (intermediate)
        inter_id = None
        if len(p_nodes) == 3:
            inter = p_nodes[1]
            inter_id = inter.element_id
            if inter_id not in nodes:
                labels = list(inter.labels)
                if "Category" in labels:
                    n = format_graph_node(inter, custom_label=f"📁 Category:\n{inter.get('name')}", custom_group="Category")
                elif "Author" in labels:
                    n = format_graph_node(inter, custom_label=f"✍️ Author:\n{inter.get('first_name','')} {inter.get('last_name','')}", custom_group="Author")
                else:
                    n = format_graph_node(inter, custom_label=f"🔗 Prerequisite:\n{inter.get('title')}", custom_group="Prerequisite")
                n["level"] = 2
                nodes[inter_id] = n
            add_synth_edge(b1.element_id, inter_id, "shared")
        else:
            # direct relationship between b1 and rec (e.g. PREREQUISITE_FOR)
            rel_type = p_rels[0].type if p_rels else "PREREQUISITE_FOR"
            synth_node_id = f"synth_prereq_{b1.element_id}_{rec.element_id}"
            if synth_node_id not in nodes:
                nodes[synth_node_id] = {
                    "id": synth_node_id,
                    "label": "🔗 Prerequisite\nPath",
                    "group": "Prerequisite",
                    "level": 2,
                    "title": "Prerequisite Academic Pathway"
                }
            inter_id = synth_node_id
            add_synth_edge(b1.element_id, inter_id, "requires" if rel_type == "PREREQUISITE_FOR" else "shared")

        # Level 3 (Recommended Book)
        if rec.element_id not in nodes:
            n = format_graph_node(rec, custom_label=f"✨ Recommended:\n{rec.get('title')}", custom_group="RecommendedBook")
            n["level"] = 3
            nodes[rec.element_id] = n

        if inter_id:
            add_synth_edge(inter_id, rec.element_id, "recommends")

    print(f"Total nodes: {len(nodes)}, Total edges: {len(edges)}")
    for nid, node in nodes.items():
        print(f"  Level {node.get('level')}: {node.get('label')[:35]} (group: {node.get('group')})")
    for e in edges[:5]:
        print(f"  Edge: {e['from']} -> {e['to']} [{e['label']}]")
