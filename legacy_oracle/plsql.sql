-- ============================================================================
-- Enterprise Library Management System - Advanced PL/SQL Architecture
-- Target Database: Oracle Database 21c
-- Components: Packages, Explicit Cursors, Exception Handling, & Triggers
-- ============================================================================

SET SERVEROUTPUT ON;

-- ============================================================================
-- PART 1: PACKAGE SPECIFICATION
-- ============================================================================
CREATE OR REPLACE PACKAGE LIBRARY_OPS_PKG AS
    /*
     * Package: LIBRARY_OPS_PKG
     * Purpose: Encapsulates transactional business logic, domain rules, and
     *          integrity checks for book issuance, returns, and financial audits.
     */

    -- Custom Exception Declarations for Standardized Error Handling
    e_user_suspended        EXCEPTION;
    e_unpaid_fines_exist    EXCEPTION;
    e_book_unavailable      EXCEPTION;
    e_max_loans_exceeded    EXCEPTION;
    e_loan_already_returned EXCEPTION;

    PRAGMA EXCEPTION_INIT(e_user_suspended, -20001);
    PRAGMA EXCEPTION_INIT(e_unpaid_fines_exist, -20002);
    PRAGMA EXCEPTION_INIT(e_book_unavailable, -20003);
    PRAGMA EXCEPTION_INIT(e_max_loans_exceeded, -20004);
    PRAGMA EXCEPTION_INIT(e_loan_already_returned, -20006);

    -- Constant Definition: Daily fine assessment rate (in currency units)
    c_daily_fine_rate CONSTANT NUMBER(5, 2) := 10.00;

    -- Constant Definition: Maximum allowable concurrent active loans per user
    c_max_borrow_limit CONSTANT PLS_INTEGER := 3;

    /*
     * Function: fn_Get_Unpaid_Fines
     * Description: Aggregates total outstanding fines for a specified user
     *              using an explicit cursor.
     * Parameter: p_user_id - Unique identifier of the borrower.
     * Returns: Total outstanding fine balance (NUMBER). Returns 0 if none exist.
     */
    FUNCTION fn_Get_Unpaid_Fines(
        p_user_id IN Users.User_ID%TYPE
    ) RETURN NUMBER;

    /*
     * Procedure: sp_IssueBook
     * Description: Validates patron eligibility and inventory status before
     *              creating a loan record and transitioning copy inventory.
     * Parameters:
     *   - p_copy_id: Inventory copy identifier.
     *   - p_borrower_id: User ID of patron borrowing the item.
     *   - p_issued_by: User ID of staff/librarian authorizing issuance.
     */
    PROCEDURE sp_IssueBook(
        p_copy_id     IN Book_Copies.Copy_ID%TYPE,
        p_borrower_id IN Users.User_ID%TYPE,
        p_issued_by   IN Users.User_ID%TYPE,
        p_due_days    IN NUMBER DEFAULT 14
    );

    /*
     * Procedure: sp_ReturnBook
     * Description: Marks loan as returned, restores inventory copy status to
     *              'Available', and automatically assesses overdue penalties.
     * Parameter: p_loan_id - Loan record identifier.
     */
    PROCEDURE sp_ReturnBook(
        p_loan_id IN Loans.Loan_ID%TYPE
    );

    /*
     * Procedure: sp_AssessDailyFines
     * Description: Synchronizes financial ledger with real-time accrued fines
     *              for actively overdue loans using an atomic MERGE operation.
     */
    PROCEDURE sp_AssessDailyFines;

END LIBRARY_OPS_PKG;
/

-- ============================================================================
-- PART 1: PACKAGE BODY
-- ============================================================================
CREATE OR REPLACE PACKAGE BODY LIBRARY_OPS_PKG AS

    -- ------------------------------------------------------------------------
    -- FUNCTION: fn_Get_Unpaid_Fines
    -- ------------------------------------------------------------------------
    FUNCTION fn_Get_Unpaid_Fines(
        p_user_id IN Users.User_ID%TYPE
    ) RETURN NUMBER IS
        -- Variable to accumulate the fine total
        v_total_unpaid NUMBER(10, 2) := 0;
        v_fine_amount  Fines.Fine_Amount%TYPE;

        /*
         * Explicit Cursor: Traverses individual unpaid fine line items
         * linked to the specified borrower through the Loans join table.
         */
        CURSOR cur_unpaid_fines IS
            SELECT f.Fine_Amount
            FROM Fines f
            JOIN Loans l ON f.Loan_ID = l.Loan_ID
            WHERE l.Borrower_ID = p_user_id
              AND f.Payment_Status = 'Unpaid';
    BEGIN
        -- Open explicit cursor
        OPEN cur_unpaid_fines;
        LOOP
            FETCH cur_unpaid_fines INTO v_fine_amount;
            EXIT WHEN cur_unpaid_fines%NOTFOUND;

            -- Accumulate balance
            v_total_unpaid := v_total_unpaid + NVL(v_fine_amount, 0);
        END LOOP;
        CLOSE cur_unpaid_fines;

        RETURN v_total_unpaid;

    EXCEPTION
        WHEN OTHERS THEN
            -- Defensive programming: Ensure cursor is closed before propagating
            IF cur_unpaid_fines%ISOPEN THEN
                CLOSE cur_unpaid_fines;
            END IF;
            RAISE_APPLICATION_ERROR(
                -20099, 
                'Error calculating unpaid fines for User ID ' || p_user_id || ': ' || SQLERRM
            );
    END fn_Get_Unpaid_Fines;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: sp_IssueBook
    -- ------------------------------------------------------------------------
    PROCEDURE sp_IssueBook(
        p_copy_id     IN Book_Copies.Copy_ID%TYPE,
        p_borrower_id IN Users.User_ID%TYPE,
        p_issued_by   IN Users.User_ID%TYPE,
        p_due_days    IN NUMBER DEFAULT 14
    ) IS
        v_account_status    Users.Account_Status%TYPE;
        v_unpaid_fines      NUMBER(10, 2);
        v_copy_status       Book_Copies.Status%TYPE;
        v_active_loans      PLS_INTEGER := 0;
        v_duplicate_books   PLS_INTEGER := 0;
        v_issuer_role       Users.Role%TYPE;
        v_dummy             NUMBER;
    BEGIN
        -- 1. Verify borrower exists and validate account active status
        BEGIN
            SELECT Account_Status 
            INTO v_account_status
            FROM Users
            WHERE User_ID = p_borrower_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20010, 'Borrower User ID ' || p_borrower_id || ' does not exist.');
        END;

        IF v_account_status != 'Active' THEN
            RAISE_APPLICATION_ERROR(
                -20001, 
                'Transaction Blocked: Borrower account status is ' || v_account_status || '. Must be Active.'
            );
        END IF;

        -- 2. Verify staff issuer credentials
        BEGIN
            SELECT Role 
            INTO v_issuer_role
            FROM Users
            WHERE User_ID = p_issued_by AND Account_Status = 'Active';

            IF v_issuer_role NOT IN ('Admin', 'Librarian', 'Staff') THEN
                RAISE_APPLICATION_ERROR(-20011, 'Unauthorized: Issuing user lacks administrative privileges.');
            END IF;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20012, 'Issuing user ID ' || p_issued_by || ' not found or inactive.');
        END;

        -- 3. Check for any delinquent fines via explicit cursor function
        v_unpaid_fines := fn_Get_Unpaid_Fines(p_borrower_id);
        IF v_unpaid_fines > 0 THEN
            RAISE_APPLICATION_ERROR(
                -20002, 
                'Transaction Blocked: Patron has outstanding unpaid fines of Rs. ' || 
                TO_CHAR(v_unpaid_fines, 'FM999,990.00') || '. Clearance required.'
            );
        END IF;

        -- 4. Check book inventory copy status with row-level lock (pessimistic concurrency)
        BEGIN
            SELECT Status 
            INTO v_copy_status
            FROM Book_Copies
            WHERE Copy_ID = p_copy_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20013, 'Physical Copy ID ' || p_copy_id || ' does not exist in inventory.');
        END;

        IF v_copy_status NOT IN ('Available', 'Reserved') THEN
            RAISE_APPLICATION_ERROR(
                -20003, 
                'Transaction Blocked: Physical Copy ID ' || p_copy_id || 
                ' is currently unavailable (Status: ' || v_copy_status || ').'
            );
        END IF;

        -- 5. Lock patron row to serialize concurrent issuance attempts for the same patron
        SELECT User_ID INTO v_dummy FROM Users WHERE User_ID = p_borrower_id FOR UPDATE;

        -- Validate patron borrowing quota limit (active loans + approved holds awaiting pickup + pending requests combined)
        SELECT 
            (SELECT COUNT(*) FROM Loans WHERE Borrower_ID = p_borrower_id AND Return_Date IS NULL) +
            (SELECT COUNT(*) FROM Loan_Requests WHERE Borrower_ID = p_borrower_id AND Status IN ('Pending', 'Awaiting Pickup') AND Book_ID != (SELECT Book_ID FROM Book_Copies WHERE Copy_ID = p_copy_id))
        INTO v_active_loans
        FROM DUAL;

        IF (v_active_loans + 1) > c_max_borrow_limit THEN
            RAISE_APPLICATION_ERROR(
                -20004, 
                'Transaction Blocked: Patron would exceed the maximum quota of ' || 
                c_max_borrow_limit || ' books (active loans, approved holds awaiting pickup, and pending requests combined).'
            );
        END IF;

        -- 6. Duplicate Book Check: Verify patron does not already hold an active loan for this book title
        SELECT COUNT(*)
        INTO v_duplicate_books
        FROM Loans l
        JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID
        WHERE l.Borrower_ID = p_borrower_id
          AND l.Return_Date IS NULL
          AND bc.Book_ID = (SELECT Book_ID FROM Book_Copies WHERE Copy_ID = p_copy_id);

        IF v_duplicate_books > 0 THEN
            RAISE_APPLICATION_ERROR(
                -20014,
                'Transaction Blocked: Patron already holds an active loan for this book title. Duplicate borrowing is prohibited.'
            );
        END IF;

        -- 6. Insert new loan transaction with dynamic p_due_days
        INSERT INTO Loans (
            Copy_ID,
            Borrower_ID,
            Issued_By,
            Issue_Date,
            Due_Date,
            Return_Date
        ) VALUES (
            p_copy_id,
            p_borrower_id,
            p_issued_by,
            SYSDATE,
            SYSDATE + NVL(p_due_days, 14),
            NULL
        );

        -- 7. Update copy inventory state to 'Borrowed'
        UPDATE Book_Copies
        SET Status = 'Borrowed'
        WHERE Copy_ID = p_copy_id;

        -- Commit atomic transaction
        COMMIT;

        DBMS_OUTPUT.PUT_LINE(
            'SUCCESS: Book Copy #' || p_copy_id || ' successfully issued to Patron #' || 
            p_borrower_id || '. Due Date: ' || TO_CHAR(SYSDATE + 14, 'YYYY-MM-DD')
        );

    EXCEPTION
        WHEN OTHERS THEN
            -- Rollback in-flight locks and mutations on unexpected failure
            ROLLBACK;
            RAISE;
    END sp_IssueBook;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: sp_ReturnBook
    -- ------------------------------------------------------------------------
    PROCEDURE sp_ReturnBook(
        p_loan_id IN Loans.Loan_ID%TYPE
    ) IS
        v_copy_id       Book_Copies.Copy_ID%TYPE;
        v_due_date      Loans.Due_Date%TYPE;
        v_return_date   Loans.Return_Date%TYPE;
        v_days_overdue  PLS_INTEGER := 0;
        v_fine_amount   NUMBER(10, 2) := 0;
    BEGIN
        -- 1. Retrieve and lock active loan record for deterministic update
        BEGIN
            SELECT Copy_ID, Due_Date, Return_Date
            INTO v_copy_id, v_due_date, v_return_date
            FROM Loans
            WHERE Loan_ID = p_loan_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20014, 'Loan transaction ID ' || p_loan_id || ' does not exist.');
        END;

        -- Prevent duplicate return processing
        IF v_return_date IS NOT NULL THEN
            RAISE_APPLICATION_ERROR(
                -20006, 
                'Transaction Blocked: Loan ID ' || p_loan_id || 
                ' was already completed on ' || TO_CHAR(v_return_date, 'YYYY-MM-DD HH24:MI:SS') || '.'
            );
        END IF;

        -- 2. Mark loan as returned
        UPDATE Loans
        SET Return_Date = SYSDATE
        WHERE Loan_ID = p_loan_id;

        -- 3. Return physical inventory copy status back to 'Available'
        UPDATE Book_Copies
        SET Status = 'Available'
        WHERE Copy_ID = v_copy_id;

        -- 4. Audit overdue status and assess automated penalty if applicable
        IF TRUNC(SYSDATE) > TRUNC(v_due_date) THEN
            -- Calculate calendar days overdue with a maximum fine threshold of Rs. 500.00
            v_days_overdue := TRUNC(SYSDATE) - TRUNC(v_due_date);
            v_fine_amount  := LEAST(v_days_overdue * c_daily_fine_rate, 500);

            -- Update existing unpaid fine balance or insert new fine if none exists
            UPDATE Fines
            SET Fine_Amount = Fine_Amount + v_fine_amount
            WHERE Loan_ID = p_loan_id AND Payment_Status = 'Unpaid';

            IF SQL%ROWCOUNT = 0 THEN
                INSERT INTO Fines (
                    Loan_ID,
                    Fine_Amount,
                    Payment_Status
                ) VALUES (
                    p_loan_id,
                    v_fine_amount,
                    'Unpaid'
                );
            END IF;

            DBMS_OUTPUT.PUT_LINE(
                'PENALTY ASSESSED: Loan #' || p_loan_id || ' is ' || v_days_overdue || 
                ' day(s) overdue. Fine of Rs. ' || TO_CHAR(v_fine_amount, 'FM999,990.00') || ' recorded.'
            );
        ELSE
            DBMS_OUTPUT.PUT_LINE('SUCCESS: Book returned on time. No overdue penalties applied.');
        END IF;

        -- Commit atomic transaction
        COMMIT;

    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END sp_ReturnBook;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: sp_AssessDailyFines
    -- ------------------------------------------------------------------------
    PROCEDURE sp_AssessDailyFines IS
    BEGIN
        MERGE INTO Fines f
        USING (
            SELECT 
                Loan_ID,
                LEAST((TRUNC(SYSDATE) - TRUNC(Due_Date)) * c_daily_fine_rate, 500) AS calculated_fine
            FROM Loans
            WHERE Return_Date IS NULL 
              AND Due_Date < SYSDATE
        ) d
        ON (f.Loan_ID = d.Loan_ID)
        WHEN MATCHED THEN
            UPDATE SET f.Fine_Amount = d.calculated_fine
            WHERE f.Payment_Status = 'Unpaid'
        WHEN NOT MATCHED THEN
            INSERT (Loan_ID, Fine_Amount, Payment_Status)
            VALUES (d.Loan_ID, d.calculated_fine, 'Unpaid');

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END sp_AssessDailyFines;

END LIBRARY_OPS_PKG;
/

-- ============================================================================
-- PART 2: STANDALONE TRIGGERS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TRIGGER A: trg_Secure_Fines_Deletion
-- Timing: BEFORE DELETE ON Fines (Row-Level)
-- Objective: Enforce immutable ledger integrity by blocking deletion of fine
--            records to prevent concealment or tampering.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER trg_Secure_Fines_Deletion
BEFORE DELETE OR UPDATE ON Fines
FOR EACH ROW
BEGIN
    /*
     * Compliance Rule: Library audit governance forbids unauthorized deletion of
     * penalty records. Programmatic administrative purges set CLIENT_INFO = 'ALLOW_DELETE'.
     */
    IF DELETING THEN
        IF SYS_CONTEXT('USERENV', 'CLIENT_INFO') = 'ALLOW_DELETE' THEN
            RETURN;
        END IF;

        RAISE_APPLICATION_ERROR(
            -20005, 
            'Security Violation: Fines cannot be deleted. They must be updated to ''Paid'' or ''Waived''.'
        );
    ELSIF UPDATING THEN
        -- Prevent unauthorized fine tampering: fine amount cannot be reduced without marking status as Waived
        IF :NEW.Fine_Amount < :OLD.Fine_Amount AND :NEW.Payment_Status != 'Waived' THEN
            RAISE_APPLICATION_ERROR(
                -20015,
                'Security Violation: Unauthorized fine tampering detected. Fine amount cannot be reduced unless Payment_Status is explicitly set to ''Waived''.'
            );
        END IF;
    END IF;
END;
/

-- ----------------------------------------------------------------------------
-- TRIGGER B: trg_Audit_User_Suspension
-- Timing: AFTER UPDATE OF Account_Status ON Users (Row-Level)
-- Objective: Emits an audit alert whenever an administrative action changes
--            a user's account status into 'Suspended'.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER trg_Audit_User_Suspension
AFTER UPDATE OF Account_Status ON Users
FOR EACH ROW
WHEN (NEW.Account_Status = 'Suspended' AND (OLD.Account_Status IS NULL OR OLD.Account_Status != 'Suspended'))
BEGIN
    /*
     * Security Audit Logger:
     * Records suspension events directly into the persistent Audit_Logs table.
     */
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
/

-- ----------------------------------------------------------------------------
-- TRIGGER C: trg_Enforce_Single_Admin_Librarian
-- Timing: BEFORE INSERT OR UPDATE ON Users (Row-Level)
-- Objective: Strictly enforce systemic governance policy of maximum 1 Admin
--            and maximum 1 Librarian account in the database.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER trg_Enforce_Single_Admin_Librarian
BEFORE INSERT OR UPDATE ON Users
FOR EACH ROW
DECLARE
    PRAGMA AUTONOMOUS_TRANSACTION;
    v_admin_count NUMBER;
    v_lib_count   NUMBER;
BEGIN
    IF :NEW.Role = 'Admin' THEN
        SELECT COUNT(*) INTO v_admin_count 
        FROM Users 
        WHERE Role = 'Admin' AND User_ID != NVL(:NEW.User_ID, -1);
        IF v_admin_count >= 1 THEN
            RAISE_APPLICATION_ERROR(-20020, 'System Policy Violation: Only one Admin account is permitted.');
        END IF;
    ELSIF :NEW.Role = 'Librarian' THEN
        SELECT COUNT(*) INTO v_lib_count 
        FROM Users 
        WHERE Role = 'Librarian' AND User_ID != NVL(:NEW.User_ID, -1);
        IF v_lib_count >= 1 THEN
            RAISE_APPLICATION_ERROR(-20021, 'System Policy Violation: Only one Librarian account is permitted.');
        END IF;
    END IF;
END;
/
