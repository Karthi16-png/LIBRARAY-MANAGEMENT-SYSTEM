import oracledb

conn = oracledb.connect(user='system', password='root', dsn='localhost:1521/XEPDB1')
cur = conn.cursor()

cur.execute("""
    SELECT constraint_name, search_condition 
    FROM user_constraints 
    WHERE table_name = 'LOAN_REQUESTS' AND constraint_type = 'C'
""")
for row in cur.fetchall():
    print(row)

conn.close()
