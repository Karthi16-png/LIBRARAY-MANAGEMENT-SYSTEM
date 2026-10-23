import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

trigger_sql = """
CREATE OR REPLACE TRIGGER trg_Audit_User_Suspension
AFTER UPDATE OF Account_Status ON Users
FOR EACH ROW
WHEN (NEW.Account_Status = 'Suspended' AND (OLD.Account_Status IS NULL OR OLD.Account_Status != 'Suspended'))
BEGIN
    INSERT INTO Audit_Logs (
        Action_Type,
        Target_User,
        Performed_By,
        Log_Date,
        Details
    ) VALUES (
        'USER_SUSPENDED',
        :NEW.Username,
        COALESCE(SYS_CONTEXT('USERENV', 'CLIENT_INFO'), USER),
        SYSDATE,
        'User ' || :NEW.Username || ' (User_ID: ' || :NEW.User_ID || ') was SUSPENDED.'
    );
END;
"""

cur.execute(trigger_sql)
conn.commit()

cur.execute("SELECT status FROM user_objects WHERE object_name = 'TRG_AUDIT_USER_SUSPENSION'")
print("trg_Audit_User_Suspension status:", cur.fetchall())
conn.close()
