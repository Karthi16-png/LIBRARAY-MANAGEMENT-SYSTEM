import os
import sys
from datetime import datetime, date
from neo4j import GraphDatabase

NEO4J_URI      = "neo4j+s://e7f1b8d0.databases.neo4j.io"
NEO4J_USERNAME = "e7f1b8d0"
NEO4J_PASSWORD = "ROzf6G2s6B2tP6C61ODmEGMbmG-pzeCq5KZgI6CmxHI"
NEO4J_DATABASE = "e7f1b8d0"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def serialize_val(v):
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if hasattr(v, 'iso_format'):
        return v.iso_format()
    if hasattr(v, 'to_native'):
        native = v.to_native()
        if hasattr(native, 'isoformat'):
            return native.isoformat()
        return str(native)
    if isinstance(v, (int, float, bool, str)):
        return v
    return str(v)

def node_to_dict(n):
    labels = list(n.labels)
    primary_label = labels[0] if labels else "Node"
    raw_props = dict(n)
    props = {k: serialize_val(v) for k, v in raw_props.items() if k != "password_hash"}
    
    # Human readable label for vis.js
    if primary_label == "Book":
        title = props.get("title", f"Book #{props.get('book_id')}")
        display_label = title if len(title) <= 24 else title[:22] + "..."
    elif primary_label == "User":
        display_label = f"👤 {props.get('username')} ({props.get('role', 'User')})"
    elif primary_label == "Author":
        display_label = f"✍️ {props.get('first_name', '')} {props.get('last_name', '')}".strip()
    elif primary_label == "Category":
        display_label = f"📁 {props.get('name', 'Category')}"
    elif primary_label == "Publisher":
        display_label = f"🏢 {props.get('name', 'Publisher')}"
    elif primary_label == "Copy":
        display_label = f"📖 Copy #{props.get('copy_id')} [{props.get('status', 'Available')}]"
    elif primary_label == "Loan":
        display_label = f"⏱️ Loan #{props.get('loan_id')} [{props.get('status', 'Active')}]"
    elif primary_label == "Fine":
        display_label = f"⚠️ Fine #{props.get('fine_id')}: Rs.{props.get('fine_amount')}"
    elif primary_label == "LoanRequest":
        display_label = f"📩 Req #{props.get('request_id')} [{props.get('status')}]"
    else:
        display_label = f"{primary_label}"

    return {
        "id": n.element_id,
        "label": display_label,
        "group": primary_label,
        "title": f"<b>{primary_label}</b><br/>" + "<br/>".join([f"<b>{k}:</b> {v}" for k, v in list(props.items())[:6]]),
        "properties": props
    }

with driver.session(database=NEO4J_DATABASE) as s:
    result = s.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 5")
    nodes = {}
    edges = []
    for record in result:
        n = record["n"]
        m = record["m"]
        r = record["r"]
        if n.element_id not in nodes:
            nodes[n.element_id] = node_to_dict(n)
        if m.element_id not in nodes:
            nodes[m.element_id] = node_to_dict(m)
        edges.append({
            "id": r.element_id,
            "from": n.element_id,
            "to": m.element_id,
            "label": r.type,
            "title": f"Relationship: :{r.type}",
            "arrows": "to"
        })
    print(f"Success! Processed {len(nodes)} nodes, {len(edges)} edges.")
    print("Sample node:", list(nodes.values())[0])
    print("Sample edge:", edges[0])
