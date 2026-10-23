import os
import shutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DOCS_DIR = os.path.join(BASE_DIR, "docs")
LEGACY_DIR = os.path.join(BASE_DIR, "legacy_oracle")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(LEGACY_DIR, exist_ok=True)

# 1. Delete unnecessary swap file
swap_file = os.path.join(BASE_DIR, "LibraryDB~1.sql")
if os.path.exists(swap_file):
    os.remove(swap_file)
    print(f"Deleted unnecessary swap file: {swap_file}")

# 2. Move legacy Oracle files to legacy_oracle/
legacy_files = [
    "LibraryDB.sql",
    "ddl.sql",
    "plsql.sql",
    "changes.sql",
    "populate_all_sample_records.py",
    "seed_all_tables_and_users.py",
    "test_user_requirements.py"
]

for fname in legacy_files:
    src = os.path.join(BASE_DIR, fname)
    dst = os.path.join(LEGACY_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved {fname} -> legacy_oracle/")

# 3. Move documentation and reports to docs/
doc_files = [
    "Library_Management_System_DA2_Report.docx",
    "Library_Management_System_DA2_Report.pdf",
    "VITCC_Library_Codebase.pdf",
    "Neo4j-e7f1b8d0-Created-2026-10-17.txt",
    "generate_final_report.py"
]

for fname in doc_files:
    src = os.path.join(BASE_DIR, fname)
    dst = os.path.join(DOCS_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved {fname} -> docs/")

print("\nWorkspace organization complete.")
