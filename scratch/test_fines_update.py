import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

# 1. Verify Collected_By column in Fines
cur.execute("SELECT column_name, data_type FROM user_tab_cols WHERE table_name = 'FINES' AND column_name = 'COLLECTED_BY'")
print("Fines.Collected_By:", cur.fetchall())

# 2. Verify fk_fines_collected_by constraint
cur.execute("SELECT constraint_name, constraint_type FROM user_constraints WHERE constraint_name = 'FK_FINES_COLLECTED_BY'")
print("Constraint FK_FINES_COLLECTED_BY:", cur.fetchall())

# 3. Test pay_fine SQL query update with Collected_By
cur.execute("""
    UPDATE Fines
    SET Payment_Status = 'Paid',
        Payment_Date = SYSDATE,
        Collected_By = :admin_id
    WHERE Fine_ID = (SELECT Fine_ID FROM Fines WHERE ROWNUM = 1)
""", {"admin_id": 1})
conn.commit()
print("SUCCESS: Fines updated with Collected_By = 1")

conn.close()
