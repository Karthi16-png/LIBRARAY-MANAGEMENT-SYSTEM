import oracledb

with open("plsql.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()

# Split into package spec and body
parts = sql_content.split("/")
conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

for block in parts:
    block = block.strip()
    # Skip sqlplus directives
    lines = [line for line in block.splitlines() if not line.strip().upper().startswith("SET ")]
    clean_block = "\n".join(lines).strip()
    if not clean_block:
        continue
    try:
        cur.execute(clean_block)
        print("Block executed successfully.")
    except Exception as e:
        print("Error executing block:", e)

# Check errors
cur.execute("SELECT name, type, line, position, text FROM user_errors WHERE name = 'LIBRARY_OPS_PKG'")
errors = cur.fetchall()
if errors:
    print("Compilation errors:", errors)
else:
    print("LIBRARY_OPS_PKG compiled cleanly with 0 errors!")

conn.close()
