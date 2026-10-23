import oracledb
from werkzeug.security import check_password_hash

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cursor = conn.cursor()

credentials = [
    ("admin", "Admin123!", "Admin"),
    ("librarian", "Librarian123!", "Librarian"),
    ("staff", "Staff123!", "Staff"),
    ("prof_turing", "Staff123!", "Staff"),
    ("prof_shannon", "Staff123!", "Staff"),
    ("student", "Student123!", "Student"),
    ("alex_stu", "Student123!", "Student"),
    ("priya_stu", "Student123!", "Student"),
    ("rahul_stu", "Student123!", "Student"),
    ("emily_stu", "Student123!", "Student"),
    ("marcus_stu", "Student123!", "Student"),
    ("nithin", "Student123!", "Student"),
    ("joe", "Student123!", "Student"),
    ("karthik", "Student123!", "Student"),
]

print("=" * 60)
print("TESTING DATABASE HASH AUTHENTICATION FOR ALL USERS")
print("=" * 60)

all_passed = True
for uname, pwd, expected_role in credentials:
    cursor.execute(
        "SELECT User_ID, Username, Password_Hash, Role, Account_Status FROM Users WHERE LOWER(Username) = LOWER(:u)",
        {"u": uname}
    )
    user = cursor.fetchone()
    if not user:
        print(f"FAILED: User '{uname}' does not exist in database!")
        all_passed = False
        continue

    uid, db_uname, p_hash, role, status = user
    is_valid = check_password_hash(p_hash, pwd)
    status_str = "SUCCESS" if is_valid else "FAILED"
    print(f"User '{db_uname}' ({role}, {status}) [ID {uid}]: {status_str}")
    if not is_valid:
        all_passed = False

print("=" * 60)
if all_passed:
    print("[ALL PASS] Every single user has verified credentials!")
else:
    print("[FAIL] Mismatches detected!")
print("=" * 60)
