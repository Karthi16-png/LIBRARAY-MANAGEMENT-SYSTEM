import ast

def inspect_routes(filepath="app.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    routes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check decorators
            for dec in node.decorator_list:
                is_route = False
                rule = None
                methods = ["GET"]
                if isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Attribute) and dec.func.attr == "route":
                        is_route = True
                        if dec.args:
                            if isinstance(dec.args[0], ast.Constant):
                                rule = dec.args[0].value
                        for kw in dec.keywords:
                            if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                                methods = [elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)]
                if is_route:
                    # check if it has login_required or role_required
                    dec_names = []
                    for d in node.decorator_list:
                        if isinstance(d, ast.Name):
                            dec_names.append(d.id)
                        elif isinstance(d, ast.Call):
                            if isinstance(d.func, ast.Name):
                                dec_names.append(d.func.id)
                            elif isinstance(d.func, ast.Attribute):
                                dec_names.append(d.func.attr)

                    routes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "rule": rule,
                        "methods": methods,
                        "decorators": dec_names
                    })

    print(f"Total routes found: {len(routes)}")
    for r in routes:
        print(f"Line {r['line']:4d}: {r['name']:<30} {r['rule']:<35} {str(r['methods']):<20} {r['decorators']}")

if __name__ == "__main__":
    inspect_routes()
