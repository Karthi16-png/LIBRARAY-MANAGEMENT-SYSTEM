import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

trigger_sql = """
CREATE OR REPLACE TRIGGER trg_Secure_Fines_Deletion
BEFORE DELETE OR UPDATE ON Fines
FOR EACH ROW
BEGIN
    IF DELETING THEN
        IF SYS_CONTEXT('USERENV', 'CLIENT_INFO') = 'ALLOW_DELETE' THEN
            RETURN;
        END IF;

        RAISE_APPLICATION_ERROR(
            -20005, 
            'Security Violation: Fines cannot be deleted. They must be updated to ''Paid'' or ''Waived''.'
        );
    ELSIF UPDATING THEN
        IF :NEW.Fine_Amount < :OLD.Fine_Amount AND :NEW.Payment_Status != 'Waived' THEN
            RAISE_APPLICATION_ERROR(
                -20015,
                'Security Violation: Unauthorized fine tampering detected. Fine amount cannot be reduced unless Payment_Status is explicitly set to ''Waived''.'
            );
        END IF;
    END IF;
END;
"""

cur.execute(trigger_sql)
print("Trigger recompiled successfully.")

cur.execute("SELECT status FROM user_objects WHERE object_name = 'TRG_SECURE_FINES_DELETION'")
print("Trigger status:", cur.fetchall())

conn.close()
