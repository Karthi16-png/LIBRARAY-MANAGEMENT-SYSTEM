import oracledb

conn = oracledb.connect(user='system', password='root', dsn='localhost:1521/XEPDB1')
cur = conn.cursor()

with open('plsql.sql', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize newlines
content = content.replace('\r\n', '\n')
blocks = [b.strip() for b in content.split('\n/\n') if b.strip()]

for i, block in enumerate(blocks):
    clean_lines = [line for line in block.splitlines() if not line.strip().upper().startswith('SET SERVEROUTPUT')]
    sql_text = '\n'.join(clean_lines).strip()
    # Strip leading comments
    lines = sql_text.split('\n')
    idx = 0
    while idx < len(lines) and lines[idx].strip().startswith('--'):
        idx += 1
    sql_text = '\n'.join(lines[idx:]).strip()
    if sql_text.endswith('/'):
        sql_text = sql_text[:-1].strip()
    if sql_text:
        try:
            cur.execute(sql_text)
            print(f'Executed block {i+1} successfully.')
        except Exception as e:
            print(f'Error in block {i+1}: {e}')

cur.execute("SELECT object_name, object_type, status FROM user_objects WHERE object_name = 'LIBRARY_OPS_PKG'")
for row in cur.fetchall():
    print('Object status:', row)

cur.execute("SELECT type, line, position, text FROM user_errors WHERE name = 'LIBRARY_OPS_PKG'")
for err in cur.fetchall():
    print('Compile error:', err)

conn.close()
