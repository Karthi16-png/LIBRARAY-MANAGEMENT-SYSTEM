import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
cur.execute("SELECT index_name FROM user_indexes WHERE index_name = 'UQ_ACTIVE_REQUESTS'")
print(cur.fetchall())
conn.close()
