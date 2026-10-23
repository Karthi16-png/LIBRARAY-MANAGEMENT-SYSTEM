import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
cur.execute("SELECT object_name, object_type, status FROM user_objects WHERE status != 'VALID'")
invalid_objs = cur.fetchall()
if invalid_objs:
    print("Invalid objects found:", invalid_objs)
else:
    print("ALL database objects are VALID!")
conn.close()
