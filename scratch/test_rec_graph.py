import sys
sys.path.insert(0, ".")
from app import get_session, format_graph_node

with get_session() as s:
    target_uid = 6 # Student user
    target_label = "You (student)"
    nodes = {}
    edges = []

    res = s.run("""
        MATCH (me:User {user_id: $uid})-[:BORROWED]->(l1:Loan)-[:FOR_COPY]->(cp1:Copy)<-[:HAS_COPY]-(b1:Book)-[:BELONGS_TO]->(cat:Category)
        MATCH (other:User)-[:BORROWED]->(l2:Loan)-[:FOR_COPY]->(cp2:Copy)<-[:HAS_COPY]-(b2:Book)-[:BELONGS_TO]->(cat)
        WHERE other.user_id <> $uid AND other.role = 'Student'
          AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2)
        RETURN me, b1, other, b2, cat
        LIMIT 10
    """, uid=target_uid)

    def add_synth_edge(from_id, to_id, label):
        eid = f"rec_{from_id}_{to_id}_{label}"
        if eid not in [e["id"] for e in edges]:
            edges.append({
                "id": eid,
                "from": from_id,
                "to": to_id,
                "label": label,
                "title": label,
                "arrows": "to",
                "font": {"size": 10, "align": "middle", "background": "#0f172a", "color": "#94A3B8"}
            })

    for rec in res:
        me = rec["me"]
        b1 = rec["b1"]
        other = rec["other"]
        b2 = rec["b2"]
        cat = rec["cat"]

        if me.element_id not in nodes:
            n = format_graph_node(me, custom_label=f"⭐ {target_label}", custom_group="CurrentUser")
            n["level"] = 0
            nodes[me.element_id] = n
        if b1.element_id not in nodes:
            n = format_graph_node(b1, custom_label=f"📖 Read:\n{b1.get('title')}", custom_group="SharedBook")
            n["level"] = 1
            nodes[b1.element_id] = n
        if cat and cat.element_id not in nodes:
            n = format_graph_node(cat, custom_label=f"📁 Category:\n{cat.get('name')}", custom_group="Category")
            n["level"] = 1
            nodes[cat.element_id] = n
        if other.element_id not in nodes:
            n = format_graph_node(other, custom_label=f"👥 Peer:\n{other.get('username')}", custom_group="PeerUser")
            n["level"] = 2
            nodes[other.element_id] = n
        if b2.element_id not in nodes:
            n = format_graph_node(b2, custom_label=f"✨ Recommended:\n{b2.get('title')}", custom_group="RecommendedBook")
            n["level"] = 3
            nodes[b2.element_id] = n

        # Sequential multi-hop flow: Level 0 -> Level 1 -> Level 2 -> Level 3
        add_synth_edge(me.element_id, b1.element_id, "borrowed")
        if cat:
            add_synth_edge(me.element_id, cat.element_id, "shared")
            add_synth_edge(cat.element_id, other.element_id, "shared")
        add_synth_edge(b1.element_id, other.element_id, "shared")
        add_synth_edge(other.element_id, b2.element_id, "recommends")

    print(f"Total nodes: {len(nodes)}")
    for n in nodes.values():
        clean_lbl = n['label'].replace('\n', ' ').encode('ascii', 'replace').decode('ascii')
        print(f"  Level {n['level']}: {clean_lbl} (group: {n['group']})")
    print(f"\nTotal edges: {len(edges)}")
    for e in edges:
        from_n = nodes[e['from']]
        to_n = nodes[e['to']]
        print(f"  [{e['label']}] L{from_n['level']} ({from_n['group']}) -> L{to_n['level']} ({to_n['group']})")
