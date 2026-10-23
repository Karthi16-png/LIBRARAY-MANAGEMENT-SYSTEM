import ast
import re

def analyze_app_py(filepath="app.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    print(f"Total lines in {filepath}: {len(lines)}")

    # 1. Check for unparameterized Cypher queries (string formatting in run())
    cypher_concat_issues = []
    for idx, line in enumerate(lines, 1):
        if re.search(r's\.run\s*\(\s*f["\']', line) or re.search(r'session\.run\s*\(\s*f["\']', line):
            # Check if it interpolates anything other than safe static fragments or if variables are inserted directly
            cypher_concat_issues.append((idx, line.strip()))

    print(f"\n--- Cypher String Interpolation in run() ---: {len(cypher_concat_issues)}")
    for idx, l in cypher_concat_issues:
        print(f"Line {idx}: {l[:100]}")

    # 2. Check for unsafe int() or float() casts from request.form or request.args
    unsafe_casts = []
    for idx, line in enumerate(lines, 1):
        # e.g., int(request.form.get(...)) or int(request.args.get(...))
        if re.search(r'int\(\s*request\.(form|args)\.get', line) or re.search(r'float\(\s*request\.(form|args)\.get', line):
            # check if line is inside a try block by checking surrounding lines
            start = max(0, idx - 8)
            context = "\n".join(lines[start:idx])
            if "try:" not in context:
                unsafe_casts.append((idx, line.strip()))

    print(f"\n--- Unsafe int()/float() casts from request without try: ---: {len(unsafe_casts)}")
    for idx, l in unsafe_casts:
        print(f"Line {idx}: {l[:100]}")

    # 3. Check for potential ZeroDivisionError (e.g. / or //)
    div_issues = []
    for idx, line in enumerate(lines, 1):
        # Look for division operators in python code (excluding comments)
        clean = line.split('#')[0].strip()
        if re.search(r'[\w\)]\s*/\s*[\w\(]', clean) and not clean.startswith('//') and not clean.startswith('http'):
            # check what is dividing
            div_issues.append((idx, clean))

    print(f"\n--- Division Operations in Python ---: {len(div_issues)}")
    for idx, l in div_issues:
        print(f"Line {idx}: {l[:100]}")

    # 4. Check for unhandled [0] indexing on query results (e.g. .single()[0] or list()[0] or records[0])
    index_issues = []
    for idx, line in enumerate(lines, 1):
        clean = line.split('#')[0].strip()
        if re.search(r'\.data\(\)\[0\]', clean) or re.search(r'\.values\(\)\[0\]', clean) or re.search(r'list\([^\)]+\)\[0\]', clean):
            start = max(0, idx - 5)
            context = "\n".join(lines[start:idx])
            if "if " not in context and "try:" not in context:
                index_issues.append((idx, clean))

    print(f"\n--- Unchecked [0] Indexing on DB results ---: {len(index_issues)}")
    for idx, l in index_issues:
        print(f"Line {idx}: {l[:100]}")

if __name__ == "__main__":
    analyze_app_py()
