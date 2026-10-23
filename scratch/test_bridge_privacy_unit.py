import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import get_session, format_bridge_node

with get_session() as s:
    u_node = s.run("MATCH (u:User {role: 'Student'}) RETURN u LIMIT 1").single()["u"]
    l_node = s.run("MATCH (l:Loan) RETURN l LIMIT 1").single()["l"]
    b_node = s.run("MATCH (b:Book) RETURN b LIMIT 1").single()["b"]

print("=== 1. Testing format_bridge_node for Student ===")
u_dict_stu, u_step_stu = format_bridge_node(u_node, 1, 3, "Student")
print("User node for Student:", u_dict_stu)
print("User step for Student:", u_step_stu)
assert u_dict_stu["label"] == "Anonymous Reader"
assert "Anonymous Reader" in u_dict_stu["title"]
assert u_dict_stu["properties"] == {"role": "Reader", "status": "Anonymous Reader"}
assert u_step_stu["name"] == "Anonymous Reader"
assert u_node.get("username") not in str(u_dict_stu)
assert u_node.get("username") not in str(u_step_stu)

l_dict_stu, l_step_stu = format_bridge_node(l_node, 2, 4, "Student")
print("Loan node for Student:", l_dict_stu)
print("Loan step for Student:", l_step_stu)
assert l_dict_stu["label"] == "Circulation Link"
assert "Circulation Link" in l_dict_stu["title"]
assert l_step_stu["name"] == "Circulation Link"

print("\n=== 2. Testing format_bridge_node for Staff ===")
u_dict_staff, u_step_staff = format_bridge_node(u_node, 1, 3, "Staff")
assert u_dict_staff["label"] == "Anonymous Reader"
assert u_node.get("username") not in str(u_dict_staff)

l_dict_staff, l_step_staff = format_bridge_node(l_node, 2, 4, "Staff")
assert l_dict_staff["label"] == "Circulation Link"

print("\n=== 3. Testing format_bridge_node for Admin & Librarian ===")
u_dict_admin, u_step_admin = format_bridge_node(u_node, 1, 3, "Admin")
print("User node for Admin:", u_dict_admin)
assert u_dict_admin["label"] != "Anonymous Reader"
assert u_node.get("username") in u_dict_admin["label"] or u_node.get("username") in str(u_dict_admin)

l_dict_admin, l_step_admin = format_bridge_node(l_node, 2, 4, "Admin")
print("Loan node for Admin:", l_dict_admin)
assert l_dict_admin["label"] != "Circulation Link"

u_dict_lib, _ = format_bridge_node(u_node, 1, 3, "Librarian")
assert u_dict_lib["label"] != "Anonymous Reader"

print("\nALL FORMAT_BRIDGE_NODE PRIVACY MASKING UNIT TESTS PASSED!")
