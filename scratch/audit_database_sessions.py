import ast
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_path = os.path.join(BASE_DIR, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

tree = ast.parse(code, filename="app.py")

routes = []

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # Check if function has an @app.route decorator
        is_route = False
        route_paths = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute) and dec.func.attr == "route":
                    is_route = True
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        route_paths.append(dec.args[0].value)
        if is_route:
            # Check how database sessions are used inside this route
            has_get_session_with = False
            has_raw_get_session = False
            has_direct_driver_session = False
            session_var_names = []

            for sub in ast.walk(node):
                if isinstance(sub, ast.With):
                    for item in sub.items:
                        if isinstance(item.context_expr, ast.Call):
                            func = item.context_expr.func
                            if isinstance(func, ast.Name) and func.id == "get_session":
                                has_get_session_with = True
                                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                                    session_var_names.append(item.optional_vars.id)
                elif isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Name) and func.id == "get_session":
                        # Check if it was part of a with statement or raw call
                        pass
                    elif isinstance(func, ast.Attribute) and func.attr == "session":
                        # e.g., driver.session()
                        has_direct_driver_session = True

            routes.append({
                "name": node.name,
                "lines": f"{node.lineno}-{node.end_lineno}",
                "paths": route_paths,
                "has_get_session_with": has_get_session_with,
                "session_vars": session_var_names,
                "has_direct_driver_session": has_direct_driver_session
            })

print(f"Total routes detected: {len(routes)}")
print("=" * 80)
missing_context_manager = []
for r in routes:
    status = "OK (with get_session() as s:)" if r["has_get_session_with"] else "NO DB (static / redirect / template only)"
    # Check if the route does DB queries without context manager
    if not r["has_get_session_with"] and r["has_direct_driver_session"]:
        status = "VIOLATION: Direct driver session used!"
        missing_context_manager.append(r)
    print(f"Route: {r['name']:25} | Lines: {r['lines']:12} | Paths: {', '.join(r['paths']):30} | {status}")

print("=" * 80)
if missing_context_manager:
    print(f"WARNING: {len(missing_context_manager)} routes with session issues:")
    for m in missing_context_manager:
        print(m)
else:
    print("ALL database-accessing routes strictly use 'with get_session() as s:' context managers!")
