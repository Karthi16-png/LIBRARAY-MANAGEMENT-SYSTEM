
-- 2. Enforce the "One Admin, One Librarian" Rule
CREATE OR REPLACE TRIGGER trg_Enforce_Single_Admin_Librarian
BEFORE INSERT OR UPDATE OF Role ON Users
FOR EACH ROW
DECLARE
    v_admin_count NUMBER;
    v_lib_count   NUMBER;
BEGIN
    IF :NEW.Role = 'Admin' THEN
        SELECT COUNT(*) INTO v_admin_count FROM Users WHERE Role = 'Admin' AND User_ID != NVL(:NEW.User_ID, -1);
        IF v_admin_count >= 1 THEN
            RAISE_APPLICATION_ERROR(-20020, 'System Policy Violation: Only one Admin account is permitted.');
        END IF;
    ELSIF :NEW.Role = 'Librarian' THEN
        SELECT COUNT(*) INTO v_lib_count FROM Users WHERE Role = 'Librarian' AND User_ID != NVL(:NEW.User_ID, -1);
        IF v_lib_count >= 1 THEN
            RAISE_APPLICATION_ERROR(-20021, 'System Policy Violation: Only one Librarian account is permitted.');
        END IF;
    END IF;
END;
/