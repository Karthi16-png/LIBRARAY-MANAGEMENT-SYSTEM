import sys
sys.path.insert(0, ".")
from app import app

client = app.test_client()

print("=================================================================")
print("VERIFYING ROLE-BASED WORDING ADJUSTMENTS")
print("=================================================================")

# 1. Admin checks
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"

admin_rec_html = client.get("/recommendations").get_data(as_text=True)
admin_lp_html = client.get("/learning_paths").get_data(as_text=True)
admin_dash_html = client.get("/dashboard").get_data(as_text=True)

# Admin learning paths: no "you" in the pathways subtitle
assert "Structured reading pathways from foundational textbooks" in admin_lp_html, "Missing admin learning paths subtitle"
assert "guiding you from foundational" not in admin_lp_html, "Found 'guiding you' in admin learning paths"
print("? [ADMIN] learning_paths subtitle verified: 'you' removed.")

# Admin recommendations: patron borrowing history, not "your borrowing history"
assert "based on patron borrowing history" in admin_rec_html, "Missing patron borrowing history in admin recs"
assert "based on your borrowing history" not in admin_rec_html, "Found 'your borrowing history' in admin recs"
assert "Recommended Books (Patron Cohort)" in admin_rec_html, "Missing admin section title"
print("? [ADMIN] recommendations subtitle verified: 'your' removed.")

# Admin sidebar: AI Recommendations instead of Recommended For You
assert "AI Recommendations" in admin_dash_html, "Missing 'AI Recommendations' in admin sidebar"
print("? [ADMIN] sidebar verified: 'AI Recommendations' present.")


# 2. Librarian checks
with client.session_transaction() as sess:
    sess["user_id"] = 2
    sess["username"] = "librarian1"
    sess["role"] = "Librarian"

lib_rec_html = client.get("/recommendations").get_data(as_text=True)
lib_lp_html = client.get("/learning_paths").get_data(as_text=True)
lib_dash_html = client.get("/dashboard").get_data(as_text=True)

assert "Structured reading pathways from foundational textbooks" in lib_lp_html
assert "guiding you from foundational" not in lib_lp_html
print("? [LIBRARIAN] learning_paths subtitle verified: 'you' removed.")

assert "based on patron borrowing history" in lib_rec_html
assert "based on your borrowing history" not in lib_rec_html
print("? [LIBRARIAN] recommendations subtitle verified: 'your' removed.")

assert "AI Recommendations" in lib_dash_html
print("? [LIBRARIAN] sidebar verified: 'AI Recommendations' present.")


# 3. Student checks
with client.session_transaction() as sess:
    sess["user_id"] = 6
    sess["username"] = "student1"
    sess["role"] = "Student"

stu_rec_html = client.get("/recommendations").get_data(as_text=True)
stu_lp_html = client.get("/learning_paths").get_data(as_text=True)
stu_dash_html = client.get("/dashboard").get_data(as_text=True)

assert "Structured reading pathways guiding you from foundational textbooks" in stu_lp_html
print("? [STUDENT] learning_paths subtitle verified: contains 'guiding you'.")

assert "based on your borrowing history" in stu_rec_html
assert "Recommended Books For You" in stu_rec_html
print("? [STUDENT] recommendations subtitle verified: contains 'your borrowing history' and 'Recommended Books For You'.")

assert "Recommended For You" in stu_dash_html
print("? [STUDENT] sidebar verified: 'Recommended For You' present.")

print("\n=================================================================")
print("ALL ROLE-BASED WORDING VERIFICATIONS PASSED SUCCESSFULLY!")
print("=================================================================")
