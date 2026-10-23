import sys
sys.path.insert(0, '.')
from app import app
import re

client = app.test_client()

print("==================================================")
print("TEST 1: ISSUE BOOK SECTION - PATRON DROPDOWN & ROLES")
print("==================================================")
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'Admin'

resp_issue = client.get('/issue_loan')
html_issue = resp_issue.data.decode('utf-8')

# Verify borrower_username dropdown select
has_select = '<select id="borrower_username" name="borrower_username"' in html_issue
has_staff_group = '<optgroup label="Staff Members"' in html_issue
has_student_group = '<optgroup label="Students"' in html_issue
has_copy_select = '<select id="copy_select"' in html_issue

print(f"Patron Select Dropdown: {'FOUND' if has_select else 'MISSING'}")
print(f"Staff Members Optgroup: {'FOUND' if has_staff_group else 'MISSING'}")
print(f"Students Optgroup: {'FOUND' if has_student_group else 'MISSING'}")
print(f"Physical Copy Select Dropdown: {'FOUND' if has_copy_select else 'MISSING'}")

# Print sample options in staff and student groups
staff_opts = re.findall(r'<option value="([^"]+)"[^>]*data-role="staff"[^>]*>\s*([^<]+)\s*</option>', html_issue)
student_opts = re.findall(r'<option value="([^"]+)"[^>]*data-role="student"[^>]*>\s*([^<]+)\s*</option>', html_issue)

print(f"\nSample Staff Options ({len(staff_opts)} total):")
for val, text in staff_opts[:3]:
    print(f"  value='{val}' | text='{text.strip()}'")

print(f"\nSample Student Options ({len(student_opts)} total):")
for val, text in student_opts[:3]:
    print(f"  value='{val}' | text='{text.strip()}'")

print("\n==================================================")
print("TEST 2: CATEGORY SEARCH FUNCTIONALITY")
print("==================================================")
# Test queries on Category 1 (Computer Science & Software)
queries = [
    ("Title word", "Clean", "Clean Code"),
    ("Author last name", "Martin", "Clean Code"),
    ("Author full name", "Robert Martin", "Clean Code"),
    ("Multi-term cross fields", "Martin Clean", "Clean Code"),
    ("ISBN with dashes", "978-013", "Clean Code"),
    ("ISBN without dashes", "9780132350884", "Clean Code"),
    ("Publisher name", "Pearson", "Clean Code"),
    ("Publication year", "2008", "Clean Code"),
]

with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

for label, q, expected in queries:
    r = client.get(f'/category/1?q={q}')
    h = r.data.decode('utf-8')
    found = expected in h
    status = "PASS" if found else "FAIL"
    print(f"[{status}] Search by {label} ('{q}') -> {'Found' if found else 'NOT Found'} '{expected}'")

print("\n==================================================")
print("ALL TESTS COMPLETE")
print("==================================================")
