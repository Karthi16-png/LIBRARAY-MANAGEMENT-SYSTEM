import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

stmts = [
    # 1. Book_Copies (referencing Books)
    "ALTER TABLE Book_Copies DROP CONSTRAINT fk_bookcopies_book",
    "ALTER TABLE Book_Copies ADD CONSTRAINT fk_bookcopies_book FOREIGN KEY (Book_ID) REFERENCES Books (Book_ID) ON DELETE CASCADE",
    
    # 2. Book_Authors (referencing Books)
    "ALTER TABLE Book_Authors DROP CONSTRAINT fk_bookauthors_book",
    "ALTER TABLE Book_Authors ADD CONSTRAINT fk_bookauthors_book FOREIGN KEY (Book_ID) REFERENCES Books (Book_ID) ON DELETE CASCADE",
    
    # 3. Loans (referencing Book_Copies)
    "ALTER TABLE Loans DROP CONSTRAINT fk_loans_copy",
    "ALTER TABLE Loans ADD CONSTRAINT fk_loans_copy FOREIGN KEY (Copy_ID) REFERENCES Book_Copies (Copy_ID) ON DELETE CASCADE"
]

for s in stmts:
    try:
        cur.execute(s)
        print("SUCCESS:", s)
    except Exception as e:
        print("ERROR on:", s, "->", e)

conn.commit()
conn.close()
