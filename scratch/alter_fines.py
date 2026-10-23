import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE Fines ADD Collected_By NUMBER")
    print("SUCCESS: Added Collected_By column.")
except Exception as e:
    print("Column add:", e)

try:
    cur.execute("ALTER TABLE Fines ADD CONSTRAINT fk_fines_collected_by FOREIGN KEY (Collected_By) REFERENCES Users (User_ID)")
    print("SUCCESS: Added fk_fines_collected_by constraint.")
except Exception as e:
    print("Constraint add:", e)

conn.commit()
conn.close()
