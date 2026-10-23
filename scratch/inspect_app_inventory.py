import sys
import os
import inspect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def inspect_routes():
    print("=== APPLICATION ROUTE AND ROLE INVENTORY ===")
    rules = []
    for rule in app.app.url_map.iter_rules():
        func = app.app.view_functions.get(rule.endpoint)
        methods = sorted(list(rule.methods - {'HEAD', 'OPTIONS'}))
        
        # Check source code of function for role requirements or login_required
        src = inspect.getsource(func) if func else ""
        has_login = "@login_required" in src
        
        roles_allowed = "ALL (Public)"
        if "role_required" in src:
            for line in src.splitlines():
                if "@role_required" in line:
                    roles_allowed = line.strip()
                    break
        elif has_login:
            roles_allowed = "Authenticated (Any Role)"
            
        rules.append((rule.rule, rule.endpoint, ",".join(methods), roles_allowed))
        
    for r in sorted(rules, key=lambda x: x[0]):
        print(f"{r[0]:<42} {r[1]:<25} {r[2]:<12} {r[3]}")

if __name__ == "__main__":
    inspect_routes()
