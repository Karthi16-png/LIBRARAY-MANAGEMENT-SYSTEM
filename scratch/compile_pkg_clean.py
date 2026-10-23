import re
import oracledb

with open("plsql.sql", "r", encoding="utf-8") as f:
    content = f.read()

# Match Package Spec
spec_match = re.search(r"(CREATE OR REPLACE PACKAGE LIBRARY_OPS_PKG AS.*?END LIBRARY_OPS_PKG;)", content, re.DOTALL)
body_match = re.search(r"(CREATE OR REPLACE PACKAGE BODY LIBRARY_OPS_PKG AS.*?END LIBRARY_OPS_PKG;)", content, re.DOTALL)

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

if spec_match:
    spec_sql = spec_match.group(1).strip()
    cur.execute(spec_sql)
    print("Spec compiled successfully.")

if body_match:
    body_sql = body_match.group(1).strip()
    cur.execute(body_sql)
    print("Body compiled successfully.")

cur.execute("SELECT name, type, line, position, text FROM user_errors WHERE name = 'LIBRARY_OPS_PKG'")
errors = cur.fetchall()
if errors:
    print("Errors:", errors)
else:
    print("ALL CLEAN! Package & Package Body valid.")

conn.close()
