import re

def check_get_none_bugs(filepath="app.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    issues = []
    for idx, line in enumerate(lines, 1):
        # Look for .get(key, default) followed later by string operations
        # or dict access where value could be None
        if " in " in line and ("e.get(" in line or "p.get(" in line or "b.get(" in line or "rec.get(" in line or "auth.get(" in line):
            issues.append((idx, line.strip()))

    print(f"Total potential .get() string operation issues: {len(issues)}")
    for idx, l in issues:
        print(f"Line {idx}: {l}")

if __name__ == "__main__":
    check_get_none_bugs()
