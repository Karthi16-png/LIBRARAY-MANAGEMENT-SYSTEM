import oracledb

conn = oracledb.connect(user='system', password='root', dsn='localhost:1521/XEPDB1')
cur = conn.cursor()

try:
    cur.execute('ALTER TABLE Loan_Requests DROP CONSTRAINT chk_req_status')
    print('Dropped chk_req_status')
except Exception as e:
    print('Drop error:', e)

cur.execute("""
    ALTER TABLE Loan_Requests 
    ADD CONSTRAINT chk_req_status 
    CHECK (Status IN ('Pending', 'Approved', 'Awaiting Pickup', 'Fulfilled', 'Rejected'))
""")
print('Added updated chk_req_status successfully.')

conn.commit()
conn.close()
