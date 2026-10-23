"""
Enterprise Library Management System - Core Application
Migrated from Oracle 21c to Neo4j AuraDB for DA-3 Project Assessment.
Engineered with Flask, Neo4j Graph Database, and Role-Based Access Control (RBAC).

Graph Relationships:
  (User)-[:BORROWED]->(Loan)-[:FOR_COPY]->(Copy)<-[:HAS_COPY]-(Book)-[:BELONGS_TO]->(Category)
  (Book)-[:PUBLISHED_BY]->(Publisher)
  (Author)-[:WROTE]->(Book)
  (User)-[:ISSUED]->(Loan)
  (Loan)-[:HAS_FINE]->(Fine)
  (User)-[:REQUESTED]->(LoanRequest)-[:FOR_BOOK]->(Book)

DA-3 Team:
  KARTHIK VALLIAPPAN C  - 25BAI1051
  NITHIN RANGASWAMY     - 25BAI1210
  NATRAJ                - 25BAI1079
"""

import os
import re
import html
from datetime import datetime, timedelta, date
from functools import wraps

from neo4j import GraphDatabase
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

# ============================================================================
# Application Initialization & Configuration
# ============================================================================
app = Flask(__name__)

app.config["SECRET_KEY"] = "enterprise-library-secret-key-change-in-production"
app.config["WTF_CSRF_ENABLED"] = not app.config.get("TESTING", False)
csrf = CSRFProtect(app)

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_session")
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
Session(app)

# ============================================================================
# Neo4j AuraDB Connection
# ============================================================================
NEO4J_URI      = "neo4j+s://e7f1b8d0.databases.neo4j.io"
NEO4J_USERNAME = "e7f1b8d0"
NEO4J_PASSWORD = "ROzf6G2s6B2tP6C61ODmEGMbmG-pzeCq5KZgI6CmxHI"
NEO4J_DATABASE = "e7f1b8d0"

_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def get_session():
    """Returns a Neo4j driver session scoped to AuraDB database."""
    return _driver.session(database=NEO4J_DATABASE)


# ============================================================================
# Jinja2 Date Helper  (preserves .strftime() calls in existing templates)
# ============================================================================
class DateWrapper:
    """Wraps a string date (YYYY-MM-DD) so templates can call .strftime()."""
    def __init__(self, val):
        if val is None:
            self._d = None
        elif isinstance(val, (datetime, date)):
            self._d = val
        elif isinstance(val, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    self._d = datetime.strptime(val, fmt)
                    break
                except ValueError:
                    pass
            else:
                self._d = None
        else:
            self._d = None

    def strftime(self, fmt):
        if self._d is None:
            return ""
        return self._d.strftime(fmt)

    def __str__(self):
        return self.strftime("%Y-%m-%d") if self._d else ""

    def __bool__(self):
        return self._d is not None

    def __repr__(self):
        return f"DateWrapper({self._d})"


def wrap_dates(record: dict) -> dict:
    """Wrap all date-string values in a dict with DateWrapper so templates work."""
    DATE_KEYS = {"issue_date", "due_date", "return_date", "request_date", "payment_date"}
    return {k: (DateWrapper(v) if k in DATE_KEYS else v) for k, v in record.items()}


def rows(result) -> list:
    """Convert Neo4j result to a list of plain dicts with date wrapping."""
    return [wrap_dates(dict(r)) for r in result]


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ============================================================================
# Session Idle Timeout
# ============================================================================
@app.before_request
def check_session_idle_timeout():
    """Enforces a strict 10-minute idle session timeout."""
    if request.endpoint == "static":
        return
    if "user_id" in session:
        now = datetime.now().timestamp()
        last_activity = session.get("last_activity")
        if last_activity is not None and (now - last_activity) > 600:
            session.clear()
            flash("Security Timeout: Your session has expired due to 10 minutes of inactivity.", "warning")
            return redirect(url_for("login"))
        session["last_activity"] = now


# ============================================================================
# Password & Email Validators
# ============================================================================
def validate_password_strength(password):
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 8 or len(password) > 64:
        return False, "Password must be between 8 and 64 characters in length."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter (A-Z)."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least 1 lowercase letter (a-z)."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number (0-9)."
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False, "Password must contain at least 1 special character (e.g. !@#$%^&*)."
    return True, None


def validate_email_format(email):
    if not email:
        return False, "Email address cannot be empty."
    email = email.strip()
    if "@" not in email or "." not in email:
        return False, "Email address must contain both '@' and '.' characters."
    parts = email.split("@")
    if len(parts) != 2 or not parts[0] or not parts[1] or "." not in parts[1]:
        return False, "Please enter a valid email address (e.g. user@domain.com)."
    return True, None


# ============================================================================
# RBAC Decorators
# ============================================================================
def login_required(f):
    """Ensures user is authenticated; evicts zombie sessions for suspended accounts."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))

        # Check live account status in Neo4j
        try:
            with get_session() as s:
                result = s.run(
                    "MATCH (u:User {user_id: $uid}) RETURN u.account_status AS account_status, u.role AS role",
                    uid=session["user_id"]
                )
                record = result.single()
                if not record or record["account_status"] != "Active":
                    session.clear()
                    flash("Access Denied: Your account is no longer active or has been suspended.", "danger")
                    return redirect(url_for("login"))
                session["role"] = record["role"]
        except Exception:
            pass

        return f(*args, **kwargs)
    return decorated_function


def role_required(allowed_roles):
    """Restricts view access to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to proceed.", "warning")
                return redirect(url_for("login"))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash("Access Denied: You do not have permissions for this action.", "danger")
                return render_template("unauthorized.html", user_role=user_role), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# Helper: next sequential ID
# ============================================================================
def next_id(s, label: str, id_field: str) -> int:
    valid_labels = {"User", "Book", "Loan", "Copy", "LoanRequest", "Fine", "Category", "Author", "Publisher"}
    valid_id_fields = {"user_id", "book_id", "loan_id", "copy_id", "request_id", "fine_id", "category_id", "author_id", "publisher_id"}
    if label not in valid_labels or id_field not in valid_id_fields:
        raise ValueError(f"Invalid label '{label}' or id_field '{id_field}' for next_id")
    result = s.run(f"MATCH (n:{label}) RETURN coalesce(max(n.{id_field}), 0) AS mx")
    rec = result.single()
    return ((rec["mx"] if rec else 0) or 0) + 1


def sync_fulfilled_loan_requests(session_tx):
    """
    Ensures data consistency for loan requests and physical copies:
    1. If a user already has an active Loan for a book, any lingering Pending or
       Awaiting Pickup LoanRequest for that book is marked Fulfilled.
    2. Any 'Awaiting Pickup' request must be linked ([:RESERVED_COPY]) to a real
       physical Copy whose status is 'Reserved'. If no copy is available or all copies
       are already 'Borrowed' (like CLRS in #REQ-3), re-sync request to 'Pending'.
    3. Any orphaned 'Reserved' copy without an 'Awaiting Pickup' hold is restored to 'Available'.
    """
    try:
        # 1. Auto-fulfill requests where user already holds active loan for this book
        session_tx.run("""
            MATCH (u:User)-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)
            MATCH (b:Book)-[:HAS_COPY]->(cp)
            WHERE l.return_date IS NULL
            MATCH (u)-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b)
            WHERE r.status IN ['Pending', 'Awaiting Pickup']
            WITH r, cp, r.copy_id AS old_copy_id
            OPTIONAL MATCH (r)-[old_rel:RESERVED_COPY]->()
            DELETE old_rel
            SET r.status = 'Fulfilled', r.copy_id = cp.copy_id
            WITH old_copy_id, cp
            WHERE old_copy_id IS NOT NULL AND old_copy_id <> cp.copy_id
            MATCH (reserved_cp:Copy {copy_id: old_copy_id, status: 'Reserved'})
            SET reserved_cp.status = 'Available'
        """)

        # 2. Check 'Awaiting Pickup' requests one-by-one: ensure valid reserved copy exists
        broken_res = session_tx.run("""
            MATCH (r:LoanRequest {status: 'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book)
            OPTIONAL MATCH (r)-[:RESERVED_COPY]->(rcp:Copy)
            WITH r, b, rcp, r.copy_id AS cid
            OPTIONAL MATCH (c_by_id:Copy {copy_id: cid})
            WITH r, b, coalesce(rcp, c_by_id) AS linked_cp
            WHERE linked_cp IS NULL OR linked_cp.status = 'Borrowed' OR linked_cp.status = 'Retired'
            RETURN r.request_id AS rid, b.book_id AS bid
            ORDER BY r.request_date ASC, r.request_id ASC
        """)
        broken_reqs = list(broken_res)
        for req in broken_reqs:
            rid = req["rid"]
            bid = req["bid"]
            avail_rec = session_tx.run("""
                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(avail_cp:Copy {status: 'Available'})
                WITH avail_cp ORDER BY avail_cp.copy_id ASC LIMIT 1
                RETURN avail_cp.copy_id AS cid
            """, bid=bid).single()

            if avail_rec:
                next_cid = avail_rec["cid"]
                session_tx.run("""
                    MATCH (cp:Copy {copy_id: $cid}), (r:LoanRequest {request_id: $rid})
                    SET cp.status = 'Reserved', r.copy_id = $cid
                    OPTIONAL MATCH (r)-[old_rel:RESERVED_COPY]->()
                    DELETE old_rel
                    CREATE (r)-[:RESERVED_COPY]->(cp)
                """, cid=next_cid, rid=rid)
            else:
                session_tx.run("""
                    MATCH (r:LoanRequest {request_id: $rid})
                    OPTIONAL MATCH (r)-[old_rel:RESERVED_COPY]->()
                    DELETE old_rel
                    SET r.status = 'Pending', r.copy_id = null
                """, rid=rid)

        # 3. Clean up relationships and ensure [:RESERVED_COPY] matches r.copy_id
        session_tx.run("""
            MATCH (r:LoanRequest)-[rel:RESERVED_COPY]->()
            WHERE r.status <> 'Awaiting Pickup'
            DELETE rel
        """)
        session_tx.run("""
            MATCH (r:LoanRequest {status: 'Awaiting Pickup'})
            WHERE r.copy_id IS NOT NULL
            OPTIONAL MATCH (r)-[old_rel:RESERVED_COPY]->(old_cp:Copy)
            WHERE old_cp.copy_id <> r.copy_id
            DELETE old_rel
        """)
        session_tx.run("""
            MATCH (r:LoanRequest {status: 'Awaiting Pickup'})
            WHERE r.copy_id IS NOT NULL
            MATCH (cp:Copy {copy_id: r.copy_id})
            SET cp.status = 'Reserved'
            MERGE (r)-[:RESERVED_COPY]->(cp)
        """)

        # 4. Release orphaned 'Reserved' copies without an Awaiting Pickup hold
        session_tx.run("""
            MATCH (cp:Copy {status: 'Reserved'})
            WHERE NOT (cp)<-[:RESERVED_COPY]-(:LoanRequest {status: 'Awaiting Pickup'})
              AND NOT EXISTS {
                  MATCH (req:LoanRequest {status: 'Awaiting Pickup'})
                  WHERE req.copy_id = cp.copy_id
              }
            SET cp.status = 'Available'
        """)
    except Exception as e:
        app.logger.warning(f"sync_fulfilled_loan_requests warning: {e}")


def sync_active_overdue_fines(session_tx):
    """
    Auto-syncs live overdue fines for all active unreturned loans (return_date IS NULL and due_date < today).
    Guarantees Days Overdue * Rs. 10 always matches the Disciplinary Fine ledger amount.
    """
    try:
        today = today_str()
        # 0. Clean up any orphaned Fine nodes without a connected Loan
        session_tx.run("""
            MATCH (f:Fine)
            WHERE NOT (f)<-[:HAS_FINE]-(:Loan)
            DETACH DELETE f
        """)

        # 1. Update existing Unpaid fines on active overdue loans to reflect live days_late * Rs. 10
        session_tx.run("""
            MATCH (l:Loan)
            WHERE l.return_date IS NULL AND l.due_date < $today
            WITH l, duration.inDays(date(l.due_date), date($today)).days AS days_late
            WHERE days_late > 0
            MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
            SET f.fine_amount = toFloat(days_late * 10)
        """, today=today)

        # 2. For active overdue loans without any Fine node, create new Fine node
        res = session_tx.run("""
            MATCH (l:Loan)
            WHERE l.return_date IS NULL AND l.due_date < $today
              AND NOT (l)-[:HAS_FINE]->(:Fine)
            WITH l, duration.inDays(date(l.due_date), date($today)).days AS days_late
            WHERE days_late > 0
            RETURN l.loan_id AS loan_id, days_late
        """, today=today)
        unfined = list(res)
        for row in unfined:
            lid = row["loan_id"]
            days_late = row["days_late"]
            amt = float(days_late * 10)
            fid = next_id(session_tx, "Fine", "fine_id")
            session_tx.run("""
                MATCH (l:Loan {loan_id: $lid})
                CREATE (f:Fine {
                    fine_id: $fid, loan_id: $lid,
                    fine_amount: $amt, payment_status: 'Unpaid',
                    payment_date: null, collected_by: null
                })
                CREATE (l)-[:HAS_FINE]->(f)
            """, fid=fid, lid=lid, amt=amt)
    except Exception as e:
        app.logger.warning(f"sync_active_overdue_fines warning: {e}")


# ============================================================================
# Routes
# ============================================================================

# ----------------------------------------------------------------------------
# / and /login
# ----------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and Password are required.", "danger")
            return render_template("login.html")

        try:
            with get_session() as s:
                result = s.run("""
                    MATCH (u:User)
                    WHERE toLower(u.username) = toLower($username)
                    RETURN u.user_id AS user_id, u.username AS username,
                           u.password_hash AS password_hash,
                           u.role AS role, u.account_status AS account_status
                """, username=username)
                user = result.single()

            if user and check_password_hash(user["password_hash"], password):
                if user["account_status"] != "Active":
                    flash("Account is suspended. Please contact the library administrator.", "danger")
                    return render_template("login.html")

                session.permanent = True
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["last_activity"] = datetime.now().timestamp()

                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password.", "danger")

        except Exception as e:
            flash(f"Database error during authentication: {str(e)}", "danger")

    return render_template("login.html")


# ----------------------------------------------------------------------------
# /register
# ----------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role     = request.form.get("role", "").strip()

        if role not in ["Student", "Staff"]:
            flash("Self-registration only permits 'Student' or 'Staff' accounts.", "danger")
            return render_template("register.html")

        if not username or not email or not password:
            flash("All fields are mandatory.", "warning")
            return render_template("register.html")

        is_email_valid, email_err = validate_email_format(email)
        if not is_email_valid:
            flash(f"Invalid Email: {email_err}", "warning")
            return render_template("register.html")

        email_clean = email.lower().strip()
        if not (email_clean.endswith("@vit.edu") or email_clean.endswith("@vit.ac.in")):
            flash("Registration requires a valid institutional email domain (@vit.edu or @vit.ac.in).", "danger")
            return render_template("register.html")

        is_pass_valid, pass_err = validate_password_strength(password)
        if not is_pass_valid:
            flash(f"Invalid Password: {pass_err}", "warning")
            return render_template("register.html")

        try:
            with get_session() as s:
                # Check uniqueness
                result = s.run("""
                    MATCH (u:User)
                    WHERE toLower(u.username) = toLower($uname) OR toLower(u.email) = toLower($email)
                    RETURN u.user_id AS user_id
                """, uname=username, email=email)
                if result.single():
                    flash("Username or Email is already registered.", "warning")
                    return render_template("register.html")

                pw_hash = generate_password_hash(password)
                new_uid = next_id(s, "User", "user_id")
                s.run("""
                    CREATE (u:User {
                        user_id: $uid, username: $uname, password_hash: $pw,
                        email: $email, role: $role, account_status: 'Active'
                    })
                """, uid=new_uid, uname=username, pw=pw_hash, email=email, role=role)

            flash(f"Account for '{username}' ({role}) created successfully! Please sign in.", "success")
            return redirect(url_for("login"))

        except Exception:
            flash("Transaction failed: An unexpected error occurred during registration.", "danger")

    return render_template("register.html")


# ----------------------------------------------------------------------------
# /logout
# ----------------------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))


# ----------------------------------------------------------------------------
# /dashboard
# ----------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    role    = session.get("role")
    user_id = session.get("user_id")
    data    = {}

    try:
        with get_session() as s:
            sync_active_overdue_fines(s)
            if role in ["Admin", "Librarian"]:
                # Counts
                data["total_books"] = s.run("MATCH (b:Book) RETURN count(b) AS c").single()["c"]

                data["active_loans"] = s.run(
                    "MATCH (l:Loan) WHERE l.return_date IS NULL RETURN count(l) AS c"
                ).single()["c"]

                today = today_str()
                data["overdue_loans"] = s.run("""
                    MATCH (l:Loan)
                    WHERE l.return_date IS NULL AND l.due_date < $today
                    RETURN count(l) AS c
                """, today=today).single()["c"]

                data["unpaid_fines"] = 0.0

                data["pending_requests"] = s.run("""
                    MATCH (r:LoanRequest {status: 'Pending'}) RETURN count(r) AS c
                """).single()["c"]

                data["awaiting_pickup_count"] = s.run("""
                    MATCH (r:LoanRequest {status: 'Awaiting Pickup'}) RETURN count(r) AS c
                """).single()["c"]

                # Active loans list
                res = s.run("""
                    MATCH (u:User)-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                    WHERE l.return_date IS NULL
                    OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    RETURN l.loan_id AS loan_id, u.username AS borrower_name,
                           u.email AS borrower_email, u.role AS borrower_role,
                           b.title AS book_title, cp.copy_id AS copy_id,
                           l.issue_date AS issue_date, l.due_date AS due_date,
                           coalesce(sum(f.fine_amount), 0) AS fine_amount
                    ORDER BY l.due_date ASC
                """)
                data["active_loans_list"] = rows(res)

                # Overdue list
                res = s.run("""
                    MATCH (u:User)-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                    WHERE l.return_date IS NULL AND l.due_date < $today
                    RETURN l.loan_id AS loan_id, u.username AS borrower_name,
                           u.email AS borrower_email, u.role AS borrower_role,
                           b.title AS book_title, cp.copy_id AS copy_id,
                           l.issue_date AS issue_date, l.due_date AS due_date,
                           duration.inDays(date(l.due_date), date($today)).days AS days_overdue
                    ORDER BY l.due_date ASC
                """, today=today)
                data["overdue_loans_list"] = rows(res)

                # Unpaid fines list
                res = s.run("""
                    MATCH (l:Loan)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    OPTIONAL MATCH (u:User)-[:BORROWED]->(l)
                    OPTIONAL MATCH (l)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                    RETURN f.fine_id AS fine_id, f.fine_amount AS fine_amount,
                           f.payment_status AS payment_status,
                           coalesce(u.username, 'Deleted Patron') AS borrower_name,
                           coalesce(u.email, 'N/A') AS borrower_email,
                           coalesce(b.title, 'Archived/Deleted Title') AS book_title,
                           l.loan_id AS loan_id, l.due_date AS due_date
                    ORDER BY f.fine_amount DESC
                """)
                data["unpaid_fines_list"] = rows(res)
                data["unpaid_fines"] = sum(f.get("fine_amount", 0.0) for f in data["unpaid_fines_list"])

                if role == "Admin":
                    data["total_users"] = s.run("MATCH (u:User) RETURN count(u) AS c").single()["c"]
                    return render_template("dashboard.html", data=data)
                else:
                    return render_template("dashboard.html", data=data)

            elif role == "Staff":
                today = today_str()
                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                    WHERE l.return_date IS NULL
                    OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    WITH u, l, cp, b, coalesce(sum(f.fine_amount), 0) AS fine_amount
                    OPTIONAL MATCH (pre_book:Book)-[:PREREQUISITE_FOR]->(b)
                    WITH u, l, cp, b, fine_amount,
                         collect(DISTINCT CASE WHEN pre_book IS NOT NULL THEN {
                             book_id: pre_book.book_id,
                             title: pre_book.title,
                             category_id: pre_book.category_id
                         } ELSE null END) AS pre_list
                    OPTIONAL MATCH (b)-[:PREREQUISITE_FOR]->(next_book:Book)
                    RETURN l.loan_id AS loan_id, b.book_id AS book_id, b.title AS title,
                           cp.copy_id AS copy_id, l.issue_date AS issue_date,
                           l.due_date AS due_date,
                           CASE WHEN l.due_date < $today THEN 1 ELSE 0 END AS is_overdue,
                           fine_amount,
                           [x IN pre_list WHERE x IS NOT NULL] AS prerequisites,
                           [x IN collect(DISTINCT CASE WHEN next_book IS NOT NULL THEN {
                               book_id: next_book.book_id,
                               title: next_book.title,
                               category_id: next_book.category_id,
                               available_copies: size([(next_book)-[:HAS_COPY]->(nc:Copy {status:'Available'}) | nc])
                           } ELSE null END) WHERE x IS NOT NULL] AS next_books
                    ORDER BY l.due_date ASC
                """, uid=user_id, today=today)
                data["current_loans"] = rows(res)
                data["active_loans"]  = data["current_loans"]

                # Accurate Committed Books Calculation (Active Loans + Awaiting Pickup)
                data["active_loans_count"] = len(data["current_loans"])
                await_res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest {status: 'Awaiting Pickup'})
                    RETURN count(r) AS c
                """, uid=user_id)
                data["awaiting_pickup_count"] = await_res.single()["c"]
                data["total_committed"] = data["active_loans_count"] + data["awaiting_pickup_count"]

                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                    OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    RETURN coalesce(sum(f.fine_amount), 0) AS total_fines
                """, uid=user_id)
                data["total_fines"] = res.single()["total_fines"]

                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b:Book)
                    RETURN r.request_id AS request_id, b.book_id AS book_id,
                           r.copy_id AS copy_id, b.title AS book_title,
                           r.request_date AS request_date, r.status AS status
                    ORDER BY r.request_id DESC
                """, uid=user_id)
                data["loan_requests"] = rows(res)

                return render_template("dashboard.html", data=data)

            elif role == "Student":
                today = today_str()
                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                    WHERE l.return_date IS NULL
                    OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    WITH u, l, cp, b, coalesce(sum(f.fine_amount), 0) AS fine_amount
                    OPTIONAL MATCH (pre_book:Book)-[:PREREQUISITE_FOR]->(b)
                    WITH u, l, cp, b, fine_amount,
                         collect(DISTINCT CASE WHEN pre_book IS NOT NULL THEN {
                             book_id: pre_book.book_id,
                             title: pre_book.title,
                             category_id: pre_book.category_id
                         } ELSE null END) AS pre_list
                    OPTIONAL MATCH (b)-[:PREREQUISITE_FOR]->(next_book:Book)
                    RETURN l.loan_id AS loan_id, b.book_id AS book_id, b.title AS title,
                           cp.copy_id AS copy_id,
                           l.issue_date AS issue_date, l.due_date AS due_date,
                           CASE WHEN l.due_date < $today THEN 1 ELSE 0 END AS is_overdue,
                           fine_amount,
                           [x IN pre_list WHERE x IS NOT NULL] AS prerequisites,
                           [x IN collect(DISTINCT CASE WHEN next_book IS NOT NULL THEN {
                               book_id: next_book.book_id,
                               title: next_book.title,
                               category_id: next_book.category_id,
                               available_copies: size([(next_book)-[:HAS_COPY]->(nc:Copy {status:'Available'}) | nc])
                           } ELSE null END) WHERE x IS NOT NULL] AS next_books
                    ORDER BY l.due_date ASC
                """, uid=user_id, today=today)
                data["active_loans"] = rows(res)

                # Accurate Committed Books Calculation (Active Loans + Awaiting Pickup)
                data["active_loans_count"] = len(data["active_loans"])
                await_res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest {status: 'Awaiting Pickup'})
                    RETURN count(r) AS c
                """, uid=user_id)
                data["awaiting_pickup_count"] = await_res.single()["c"]
                data["total_committed"] = data["active_loans_count"] + data["awaiting_pickup_count"]

                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                    OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    RETURN coalesce(sum(f.fine_amount), 0) AS total_fines
                """, uid=user_id)
                data["total_fines"] = res.single()["total_fines"]

                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b:Book)
                    RETURN r.request_id AS request_id, b.book_id AS book_id,
                           r.copy_id AS copy_id, b.title AS book_title,
                           r.request_date AS request_date, r.status AS status
                    ORDER BY r.request_id DESC
                """, uid=user_id)
                data["loan_requests"] = rows(res)

                return render_template("dashboard.html", data=data)

            else:
                flash("Unknown user role.", "danger")
                return redirect(url_for("logout"))

    except Exception as e:
        flash(f"Error fetching dashboard metrics: {str(e)}", "danger")
        return render_template("dashboard.html", data={})


# ----------------------------------------------------------------------------
# /catalog and /books
# ----------------------------------------------------------------------------
@app.route("/catalog", methods=["GET"])
@app.route("/books", methods=["GET"])
@login_required
def books():
    category_id_param = request.args.get("category_id", type=int)
    if category_id_param:
        return redirect(url_for("category_books", category_id=category_id_param))

    categories_list = []
    try:
        with get_session() as s:
            res = s.run("""
                MATCH (c:Category)
                OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
                RETURN c.category_id AS category_id, c.name AS name,
                       c.section_code AS section_code,
                       count(DISTINCT b) AS book_count
                ORDER BY c.name ASC
            """)
            categories_list = rows(res)
    except Exception as e:
        flash(f"Error retrieving category catalog: {str(e)}", "danger")

    return render_template("catalog.html", categories=categories_list)


# ----------------------------------------------------------------------------
# /category/<int:category_id>
# ----------------------------------------------------------------------------
@app.route("/category/<int:category_id>", methods=["GET"])
@login_required
def category_books(category_id):
    category    = None
    book_list   = []
    user_requests         = set()
    user_pending_requests = set()
    user_awaiting_pickup  = set()
    user_active_loans     = set()
    user_borrowing_blocked = False
    block_reason = ""
    q    = request.args.get("q", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        with get_session() as s:
            # Category metadata
            res = s.run("""
                MATCH (c:Category {category_id: $cid})
                OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
                RETURN c.category_id AS category_id, c.name AS name,
                       c.section_code AS section_code,
                       count(DISTINCT b) AS total_books
            """, cid=category_id)
            rec = res.single()
            if not rec:
                flash("The requested category was not found.", "warning")
                return redirect(url_for("books"))
            category = dict(rec)

            # Books in category with optional search
            if q:
                res = s.run("""
                    MATCH (b:Book)-[:BELONGS_TO]->(c:Category {category_id: $cid})
                    OPTIONAL MATCH (pub:Publisher)<-[:PUBLISHED_BY]-(b)
                    OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                    WITH b, c, pub,
                         collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                    WHERE toLower(b.title) CONTAINS toLower($q)
                       OR toLower(b.isbn) CONTAINS toLower($q)
                       OR replace(toLower(b.isbn), '-', '') CONTAINS replace(toLower($q), '-', '')
                       OR toLower(coalesce(pub.name, '')) CONTAINS toLower($q)
                       OR toString(b.publication_year) = $q
                       OR any(author IN author_list WHERE toLower(author) CONTAINS toLower($q))
                    RETURN b.book_id AS book_id, b.isbn AS isbn, b.title AS title,
                           b.publication_year AS publication_year,
                           b.category_id AS category_id, c.name AS category_name,
                           coalesce(pub.name, '') AS publisher_name,
                           reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                           size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_copies,
                           size([(b)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies
                    ORDER BY b.title ASC
                """, cid=category_id, q=q)
            else:
                limit  = 20
                offset = (page - 1) * limit
                res = s.run("""
                    MATCH (b:Book)-[:BELONGS_TO]->(c:Category {category_id: $cid})
                    OPTIONAL MATCH (pub:Publisher)<-[:PUBLISHED_BY]-(b)
                    OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                    WITH b, c, pub,
                         collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                    RETURN b.book_id AS book_id, b.isbn AS isbn, b.title AS title,
                           b.publication_year AS publication_year,
                           b.category_id AS category_id, c.name AS category_name,
                           coalesce(pub.name, '') AS publisher_name,
                           reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                           size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_copies,
                           size([(b)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies
                    ORDER BY b.title ASC
                    SKIP $offset LIMIT $limit
                """, cid=category_id, offset=offset, limit=limit)

            book_list = rows(res)

            # Frequently Borrowed Together: Co-borrowing Graph Analysis
            companion_res = s.run("""
                MATCH (b1:Book)-[:BELONGS_TO]->(:Category {category_id: $cid})
                OPTIONAL MATCH (b1)-[:HAS_COPY]->(:Copy)<-[:FOR_COPY]-(:Loan)<-[:BORROWED]-(u:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2:Book)
                WHERE b1.book_id <> b2.book_id
                WITH b1, b2, count(DISTINCT u) AS common_patrons
                ORDER BY common_patrons DESC, b2.title ASC
                WITH b1, collect(CASE WHEN b2 IS NOT NULL THEN {id: b2.book_id, title: b2.title, count: common_patrons} ELSE null END)[0] AS companion
                RETURN b1.book_id AS book_id, companion
            """, cid=category_id)
            companions_by_book = {r["book_id"]: r["companion"] for r in companion_res if r["companion"]}

            # Academic Progression: Prerequisites and Books to Study Next
            bids = [bk["book_id"] for bk in book_list]
            uid = session.get("user_id") or -1
            prereqs_by_book = {}
            nexts_by_book = {}
            if bids:
                prog_res = s.run("""
                    MATCH (b:Book) WHERE b.book_id IN $bids
                    OPTIONAL MATCH (pre:Book)-[:PREREQUISITE_FOR]->(b)
                    OPTIONAL MATCH (u:User {user_id: $uid})-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(pre)
                    WITH b, pre, (count(u) > 0) AS pre_completed
                    WITH b, collect(DISTINCT CASE WHEN pre IS NOT NULL THEN {
                        book_id: pre.book_id,
                        title: pre.title,
                        completed: pre_completed
                    } ELSE null END) AS prereqs
                    OPTIONAL MATCH (b)-[:PREREQUISITE_FOR]->(next_b:Book)
                    RETURN b.book_id AS book_id,
                           [x IN prereqs WHERE x IS NOT NULL] AS prerequisites,
                           [x IN collect(DISTINCT CASE WHEN next_b IS NOT NULL THEN {
                               book_id: next_b.book_id,
                               title: next_b.title
                           } ELSE null END) WHERE x IS NOT NULL] AS next_books
                """, bids=bids, uid=uid)
                for pr in rows(prog_res):
                    prereqs_by_book[pr["book_id"]] = pr.get("prerequisites", [])
                    nexts_by_book[pr["book_id"]] = pr.get("next_books", [])

            for bk in book_list:
                bk["companion"] = companions_by_book.get(bk["book_id"])
                bk["prerequisites"] = prereqs_by_book.get(bk["book_id"], [])
                bk["next_books"] = nexts_by_book.get(bk["book_id"], [])

            # User-specific flags
            user_id   = session.get("user_id")
            user_role = session.get("role")
            if user_id and user_role in ["Student", "Staff"]:
                today = today_str()

                # Active requests
                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b:Book)
                    WHERE r.status IN ['Pending', 'Awaiting Pickup']
                    RETURN b.book_id AS book_id, r.status AS status
                """, uid=user_id)
                for r in res:
                    bid = r["book_id"]
                    user_requests.add(bid)
                    if r["status"] == "Pending":
                        user_pending_requests.add(bid)
                    elif r["status"] == "Awaiting Pickup":
                        user_awaiting_pickup.add(bid)

                # Active loans
                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan {return_date: null})-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                    RETURN DISTINCT b.book_id AS book_id
                """, uid=user_id)
                for r in res:
                    user_active_loans.add(r["book_id"])

                # Unpaid fines check
                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                    RETURN count(f) AS unpaid_count, coalesce(sum(f.fine_amount), 0) AS unpaid_total
                """, uid=user_id)
                f_check = res.single()

                # Overdue check
                res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                    WHERE l.return_date IS NULL AND l.due_date < $today
                    RETURN count(l) AS overdue_count
                """, uid=user_id, today=today)
                od_check = res.single()

                if f_check and f_check["unpaid_count"] > 0:
                    user_borrowing_blocked = True
                    block_reason = f"Unpaid fines (Rs. {f_check['unpaid_total']:.2f}). Please pay before borrowing."
                elif od_check and od_check["overdue_count"] > 0:
                    user_borrowing_blocked = True
                    block_reason = f"{od_check['overdue_count']} loan(s) overdue. Please return before borrowing."

    except Exception as e:
        flash(f"Error retrieving category book collection: {str(e)}", "danger")
        return redirect(url_for("books"))

    return render_template(
        "category_books.html",
        category=category,
        books=book_list,
        user_requests=user_requests,
        user_pending_requests=user_pending_requests,
        user_awaiting_pickup=user_awaiting_pickup,
        user_active_loans=user_active_loans,
        user_borrowing_blocked=user_borrowing_blocked,
        block_reason=block_reason,
        page=page,
        q=q
    )


# ----------------------------------------------------------------------------
# /adjust_inventory/<int:book_id>
# ----------------------------------------------------------------------------
@app.route("/adjust_inventory/<int:book_id>", methods=["POST"])
@login_required
@role_required(["Admin", "Librarian"])
def adjust_inventory(book_id):
    action       = request.form.get("action")
    category_id  = request.form.get("category_id")
    quantity_str = request.form.get("quantity", "1").strip()

    if not re.match(r"^\d+$", quantity_str):
        flash("Invalid quantity: Only positive numerical digits are allowed.", "warning")
        if category_id:
            try:
                return redirect(url_for("category_books", category_id=int(category_id)))
            except (ValueError, TypeError):
                pass
        return redirect(url_for("books"))

    qty = int(quantity_str)
    if qty <= 0 or qty > 100:
        flash("Quantity must be between 1 and 100.", "warning")
        if category_id:
            try:
                return redirect(url_for("category_books", category_id=int(category_id)))
            except (ValueError, TypeError):
                pass
        return redirect(url_for("books"))

    try:
        with get_session() as s:
            res = s.run("MATCH (b:Book {book_id: $bid}) RETURN b.title AS title", bid=book_id)
            rec = res.single()
            if not rec:
                flash("Target book not found.", "warning")
                return redirect(url_for("books"))

            book_title = rec["title"]

            if action == "increase":
                cid_start = next_id(s, "Copy", "copy_id")
                for i in range(qty):
                    new_cid = cid_start + i
                    s.run("""
                        MATCH (bk:Book {book_id: $bid})
                        CREATE (cp:Copy {copy_id: $cid, book_id: $bid,
                                         status: 'Available', condition: 'Good'})
                        CREATE (bk)-[:HAS_COPY]->(cp)
                    """, bid=book_id, cid=new_cid)

                res = s.run("""
                    MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy)
                    WHERE cp.status <> 'Retired'
                    RETURN count(cp) AS total,
                           size([(b)-[:HAS_COPY]->(c:Copy {status:'Available'}) | c]) AS avail
                """, bid=book_id)
                counts = res.single()
                flash(f"Added {qty} copies for '{book_title}' (Total: {counts['total']}, Available: {counts['avail']}).", "success")

            elif action == "decrease":
                res = s.run("""
                    MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy {status: 'Available'})
                    RETURN cp.copy_id AS copy_id LIMIT $qty
                """, bid=book_id, qty=qty)
                copy_ids = [r["copy_id"] for r in res]

                if not copy_ids:
                    flash(f"No available copies in stock for '{book_title}'.", "warning")
                else:
                    for cid in copy_ids:
                        has_loans = s.run("""
                            MATCH (cp:Copy {copy_id: $cid})
                            RETURN EXISTS { MATCH (cp)<-[:FOR_COPY]-(:Loan) } AS has_loans
                        """, cid=cid).single()["has_loans"]

                        if has_loans:
                            s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Retired'", cid=cid)
                        else:
                            s.run("MATCH (cp:Copy {copy_id: $cid}) DETACH DELETE cp", cid=cid)
                    flash(f"Reduced inventory for '{book_title}' by {len(copy_ids)} copy/copies.", "success")

    except Exception as e:
        flash(f"Error updating inventory: {str(e)}", "danger")

    if category_id:
        try:
            return redirect(url_for("category_books", category_id=int(category_id)))
        except (ValueError, TypeError):
            pass
    return redirect(url_for("books"))


# ----------------------------------------------------------------------------
# Curriculum & Prerequisite Linking Helpers
# ----------------------------------------------------------------------------
def resolve_curriculum_track(s, track_choice, category_id):
    """Resolves specialization track name for academic prerequisite edges."""
    valid_tracks = [
        "Software Engineering",
        "Artificial Intelligence",
        "Data Engineering",
        "Systems & Infrastructure",
        "Theoretical CS"
    ]
    if track_choice in valid_tracks:
        return track_choice

    cat_name = ""
    if category_id:
        try:
            res_c = s.run("MATCH (c:Category {category_id: $cid}) RETURN c.name AS name", cid=int(category_id))
            rec_c = res_c.single()
            if rec_c and rec_c["name"]:
                cat_name = rec_c["name"]
        except Exception:
            pass

    c_low = cat_name.lower()
    if "data" in c_low or "database" in c_low:
        return "Data Engineering"
    elif "math" in c_low or "stat" in c_low:
        return "Theoretical CS"
    elif "physics" in c_low or "astronomy" in c_low or "hardware" in c_low or "network" in c_low or "operating" in c_low:
        return "Systems & Infrastructure"
    elif "ai" in c_low or "intelligence" in c_low:
        return "Artificial Intelligence"
    elif "computer" in c_low or "software" in c_low or "code" in c_low:
        return "Software Engineering"
    return cat_name if cat_name else "Software Engineering"


def link_book_prerequisites(s, book_id, category_id, prereq_param, next_param, track_param, book_title=None):
    """
    Creates or updates [:PREREQUISITE_FOR] edges in Neo4j AuraDB.
    Supports smart auto-detection, prevents self-loops and direct 2-node cycles.
    """
    try:
        bid = int(book_id)
        cid = None
        if category_id is not None and str(category_id).strip():
            try:
                cid = int(str(category_id).strip())
            except (ValueError, TypeError):
                cid = None

        # Resolve track
        track = resolve_curriculum_track(s, track_param, cid)

        # Resolve prereq ID
        resolved_prereq_id = None
        is_auto = False
        if prereq_param == "auto" and cid:
            # Find foundational book in the same Category with lowest incoming :PREREQUISITE_FOR degree
            foundational_res = s.run("""
                MATCH (cand:Book)-[:BELONGS_TO]->(:Category {category_id: $cid})
                WHERE cand.book_id <> $bid
                OPTIONAL MATCH (cand)<-[r_in:PREREQUISITE_FOR]-()
                WITH cand, count(r_in) AS in_degree
                ORDER BY in_degree ASC, cand.book_id ASC
                LIMIT 1
                RETURN cand.book_id AS prereq_id, cand.title AS prereq_title
            """, cid=cid, bid=bid)
            found_rec = foundational_res.single()
            if found_rec:
                resolved_prereq_id = found_rec["prereq_id"]
                is_auto = True
        elif prereq_param and prereq_param != "auto":
            try:
                resolved_prereq_id = int(prereq_param)
            except (ValueError, TypeError):
                resolved_prereq_id = None

        # Resolve next step ID
        resolved_next_id = None
        if next_param:
            try:
                resolved_next_id = int(next_param)
            except (ValueError, TypeError):
                resolved_next_id = None

        # Guard 1: Prevent self-loops
        if resolved_prereq_id and resolved_prereq_id == bid:
            resolved_prereq_id = None
        if resolved_next_id and resolved_next_id == bid:
            resolved_next_id = None

        # Guard 2: Prevent direct 2-node cycles (A -> B and B -> A)
        if resolved_prereq_id and resolved_next_id and resolved_prereq_id == resolved_next_id:
            resolved_next_id = None

        # 1. Apply Prerequisite Link (pre -> b)
        if resolved_prereq_id:
            if is_auto:
                jump = "Category Progression"
                stage = "Stage 1 -> Stage 2"
            else:
                jump = "Curriculum Progression"
                stage = "Stage 1 -> Stage 2"

            s.run("""
                MATCH (pre:Book {book_id: $pre_id}), (b:Book {book_id: $bid})
                MERGE (pre)-[r:PREREQUISITE_FOR]->(b)
                SET r.difficulty_jump = $jump,
                    r.stage = $stage,
                    r.track = $track
            """, pre_id=resolved_prereq_id, bid=bid, jump=jump, stage=stage, track=track)

        # 2. Apply Next-Step Link (b -> nxt)
        if resolved_next_id:
            nxt_jump = "Advanced Specialization"
            nxt_stage = "Stage 2 -> Stage 3"

            s.run("""
                MATCH (b:Book {book_id: $bid}), (nxt:Book {book_id: $nxt_id})
                MERGE (b)-[r:PREREQUISITE_FOR]->(nxt)
                SET r.difficulty_jump = $nxt_jump,
                    r.stage = $nxt_stage,
                    r.track = $track
            """, bid=bid, nxt_id=resolved_next_id, nxt_jump=nxt_jump, nxt_stage=nxt_stage, track=track)

    except Exception as e:
        app.logger.warning(f"link_book_prerequisites warning: {e}")


# ----------------------------------------------------------------------------
# /add_book
# ----------------------------------------------------------------------------
@app.route("/add_book", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Librarian"])
def add_book():
    categories = []
    publishers = []
    authors    = []
    all_books  = []

    try:
        with get_session() as s:
            # Query all existing books with category and prerequisite hierarchy level
            book_res = s.run("""
                MATCH (b:Book)
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH in_path = (root:Book)-[:PREREQUISITE_FOR*1..5]->(b)
                WHERE NOT ()-[:PREREQUISITE_FOR]->(root)
                WITH b, c, coalesce(max(length(in_path)) + 1, 1) AS level
                RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                       c.category_id AS category_id,
                       coalesce(c.name, 'General') AS category_name,
                       level
                ORDER BY category_name ASC, level ASC, b.title ASC
            """)
            all_books = rows(book_res)

            res = s.run("MATCH (c:Category) RETURN c.category_id AS category_id, c.name AS name ORDER BY c.name")
            categories = [dict(r) for r in res]

            res = s.run("MATCH (p:Publisher) RETURN p.publisher_id AS publisher_id, p.name AS name ORDER BY p.name")
            publishers = [dict(r) for r in res]

            res = s.run("""
                MATCH (a:Author)
                RETURN a.author_id AS author_id,
                       (a.first_name + ' ' + a.last_name) AS full_name
                ORDER BY a.last_name
            """)
            authors = [dict(r) for r in res]

            if request.method == "POST":
                isbn             = request.form.get("isbn", "").strip()
                title            = request.form.get("title", "").strip()
                pub_year_str     = request.form.get("publication_year", "").strip()
                category_id      = request.form.get("category_id")
                selected_authors = request.form.getlist("author_ids")

                # Validate mandatory fields BEFORE creating any on-the-fly nodes in Neo4j
                if not isbn or not title:
                    flash("ISBN and Title are mandatory fields.", "warning")
                    return render_template("add_book.html", categories=categories, publishers=publishers, authors=authors, all_books=all_books)

                pub_year_val = None
                if pub_year_str:
                    try:
                        pub_year_val = int(pub_year_str)
                    except ValueError:
                        flash("Publication Year must be a valid numerical year.", "warning")
                        return render_template("add_book.html", categories=categories, publishers=publishers, authors=authors, all_books=all_books)

                res_isbn = s.run("MATCH (b:Book {isbn: $isbn}) RETURN b.title AS title LIMIT 1", isbn=isbn)
                if res_isbn.single():
                    flash(f"A book with ISBN '{isbn}' already exists in the catalog.", "warning")
                    return render_template("add_book.html", categories=categories, publishers=publishers, authors=authors, all_books=all_books)

                try:
                    num_copies = min(max(1, int(request.form.get("num_copies", 1))), 50)
                except (ValueError, TypeError):
                    num_copies = 1

                publisher_id = request.form.get("publisher_id")

                # On-the-fly category (created only after validations pass)
                new_cat_name = request.form.get("new_category_name", "").strip()
                new_cat_code = request.form.get("new_category_code", "").strip()
                if new_cat_name:
                    res = s.run("MATCH (c:Category) WHERE toLower(c.name)=toLower($n) RETURN c.category_id AS cid", n=new_cat_name)
                    rec = res.single()
                    if rec:
                        category_id = rec["cid"]
                    else:
                        new_cid = next_id(s, "Category", "category_id")
                        cat_code_val = new_cat_code if new_cat_code else new_cat_name[:3].upper()
                        s.run("CREATE (c:Category {category_id: $cid, name: $n, section_code: $code})",
                              cid=new_cid, n=new_cat_name, code=cat_code_val)
                        category_id = new_cid

                # On-the-fly publisher
                new_pub_name  = request.form.get("new_publisher_name", "").strip()
                new_pub_email = request.form.get("new_publisher_email", "").strip()
                if new_pub_name:
                    res = s.run("MATCH (p:Publisher) WHERE toLower(p.name)=toLower($n) RETURN p.publisher_id AS pid", n=new_pub_name)
                    rec = res.single()
                    if rec:
                        publisher_id = rec["pid"]
                    else:
                        new_pid = next_id(s, "Publisher", "publisher_id")
                        s.run("CREATE (p:Publisher {publisher_id: $pid, name: $n, contact_email: $e})",
                              pid=new_pid, n=new_pub_name, e=new_pub_email or "")
                        publisher_id = new_pid

                # On-the-fly author (supports single-field authors without silently dropping them)
                new_auth_first = request.form.get("new_author_first", "").strip()
                new_auth_last  = request.form.get("new_author_last", "").strip()
                if new_auth_first or new_auth_last:
                    fn = new_auth_first or ""
                    ln = new_auth_last or ""
                    res = s.run("""
                        MATCH (a:Author)
                        WHERE toLower(a.first_name)=toLower($fn) AND toLower(a.last_name)=toLower($ln)
                        RETURN a.author_id AS aid
                    """, fn=fn, ln=ln)
                    rec = res.single()
                    if rec:
                        selected_authors.append(str(rec["aid"]))
                    else:
                        new_aid = next_id(s, "Author", "author_id")
                        s.run("CREATE (a:Author {author_id: $aid, first_name: $fn, last_name: $ln})",
                              aid=new_aid, fn=fn, ln=ln)
                        selected_authors.append(str(new_aid))

                cat_id_int = None
                if category_id is not None and str(category_id).strip():
                    try:
                        cat_id_int = int(str(category_id).strip())
                    except (ValueError, TypeError):
                        cat_id_int = None

                pub_id_int = None
                if publisher_id is not None and str(publisher_id).strip():
                    try:
                        pub_id_int = int(str(publisher_id).strip())
                    except (ValueError, TypeError):
                        pub_id_int = None

                new_bid = next_id(s, "Book", "book_id")
                s.run("""
                    CREATE (b:Book {
                        book_id: $bid, isbn: $isbn, title: $title,
                        publication_year: $year, category_id: $cat_id,
                        publisher_id: $pub_id
                    })
                """, bid=new_bid, isbn=isbn, title=title,
                     year=pub_year_val,
                     cat_id=cat_id_int,
                     pub_id=pub_id_int)

                if cat_id_int:
                    s.run("MATCH (b:Book {book_id: $bid}), (c:Category {category_id: $cid}) CREATE (b)-[:BELONGS_TO]->(c)",
                          bid=new_bid, cid=cat_id_int)
                if pub_id_int:
                    s.run("MATCH (b:Book {book_id: $bid}), (p:Publisher {publisher_id: $pid}) CREATE (b)-[:PUBLISHED_BY]->(p)",
                          bid=new_bid, pid=pub_id_int)

                for aid_str in set(selected_authors):
                    try:
                        aid = int(aid_str)
                        s.run("MATCH (a:Author {author_id: $aid}), (b:Book {book_id: $bid}) CREATE (a)-[:WROTE]->(b)",
                              aid=aid, bid=new_bid)
                    except (ValueError, TypeError):
                        pass

                cid_start = next_id(s, "Copy", "copy_id")
                for i in range(num_copies):
                    new_cid = cid_start + i
                    s.run("""
                        MATCH (bk:Book {book_id: $bid})
                        CREATE (cp:Copy {copy_id: $cid, book_id: $bid,
                                         status: 'Available', condition: 'New'})
                        CREATE (bk)-[:HAS_COPY]->(cp)
                    """, bid=new_bid, cid=new_cid)

                # Create academic prerequisite and next-step links
                prereq_book_id   = request.form.get("prereq_book_id", "").strip()
                next_book_id     = request.form.get("next_book_id", "").strip()
                curriculum_track = request.form.get("curriculum_track", "").strip()

                link_book_prerequisites(s, new_bid, category_id, prereq_book_id, next_book_id, curriculum_track, title)

                flash(f"Book '{title}' and {num_copies} copies created with academic roadmap links successfully!", "success")
                return redirect(url_for("books"))

    except Exception as e:
        flash(f"Error in add book: {str(e)}", "danger")

    return render_template("add_book.html", categories=categories, publishers=publishers, authors=authors, all_books=all_books)


# ----------------------------------------------------------------------------
# /edit_book/<int:book_id>
# ----------------------------------------------------------------------------
@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Librarian"])
def edit_book(book_id):
    try:
        with get_session() as s:
            # Query book metadata along with existing incoming/outgoing prerequisite links, publisher, and authors
            res = s.run("""
                MATCH (b:Book {book_id: $bid})
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH (b)-[:PUBLISHED_BY]->(p:Publisher)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                OPTIONAL MATCH (pre:Book)-[r_pre:PREREQUISITE_FOR]->(b)
                OPTIONAL MATCH (b)-[r_nxt:PREREQUISITE_FOR]->(nxt:Book)
                WITH b, c, p,
                     collect(DISTINCT a.author_id) AS current_author_ids,
                     collect(DISTINCT pre.book_id) AS prereq_ids,
                     collect(DISTINCT nxt.book_id) AS next_ids,
                     collect(DISTINCT coalesce(r_pre.track, r_nxt.track)) AS tracks
                RETURN b.book_id AS book_id, b.isbn AS isbn, b.title AS title,
                       b.publication_year AS publication_year,
                       coalesce(b.category_id, c.category_id) AS category_id,
                       c.name AS category_name,
                       coalesce(b.publisher_id, p.publisher_id) AS publisher_id,
                       p.name AS publisher_name,
                       current_author_ids,
                       prereq_ids[0] AS current_prereq_id,
                       next_ids[0] AS current_next_id,
                       tracks[0] AS current_track
            """, bid=book_id)
            book = res.single()
            if not book:
                flash("Target book not found.", "warning")
                return redirect(url_for("books"))
            book = dict(book)

            # Query all categories for dropdown
            c_res = s.run("MATCH (c:Category) RETURN c.category_id AS category_id, c.name AS name ORDER BY c.name")
            categories = [dict(r) for r in c_res]

            # Query all publishers for dropdown
            p_res = s.run("MATCH (p:Publisher) RETURN p.publisher_id AS publisher_id, p.name AS name ORDER BY p.name")
            publishers = [dict(r) for r in p_res]

            # Query all authors for dropdown
            a_res = s.run("""
                MATCH (a:Author)
                RETURN a.author_id AS author_id, (a.first_name + ' ' + a.last_name) AS full_name
                ORDER BY a.last_name, a.first_name
            """)
            authors = [dict(r) for r in a_res]

            # Query all books with category and prerequisite hierarchy level
            book_res = s.run("""
                MATCH (b:Book)
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH in_path = (root:Book)-[:PREREQUISITE_FOR*1..5]->(b)
                WHERE NOT ()-[:PREREQUISITE_FOR]->(root)
                WITH b, c, coalesce(max(length(in_path)) + 1, 1) AS level
                RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                       c.category_id AS category_id,
                       coalesce(c.name, 'General') AS category_name,
                       level
                ORDER BY category_name ASC, level ASC, b.title ASC
            """)
            all_books = rows(book_res)

            if request.method == "POST":
                title            = request.form.get("title", "").strip()
                isbn             = request.form.get("isbn", "").strip()
                pub_year         = request.form.get("publication_year", "").strip()
                category_id      = request.form.get("category_id")
                publisher_id     = request.form.get("publisher_id")
                selected_authors = request.form.getlist("author_ids")

                if not title or not isbn:
                    flash("Title and ISBN are mandatory.", "warning")
                    return render_template("edit_book.html", book=book, categories=categories, publishers=publishers, authors=authors, all_books=all_books)

                try:
                    pub_year_val = int(pub_year) if pub_year else None
                except ValueError:
                    flash("Publication Year must be a valid numerical year.", "warning")
                    return render_template("edit_book.html", book=book, categories=categories, publishers=publishers, authors=authors, all_books=all_books)

                res_isbn = s.run("""
                    MATCH (b:Book {isbn: $isbn})
                    WHERE b.book_id <> $bid
                    RETURN b.title AS title LIMIT 1
                """, isbn=isbn, bid=book_id)
                if res_isbn.single():
                    flash(f"Another book with ISBN '{isbn}' already exists in the catalog.", "warning")
                    return render_template("edit_book.html", book=book, categories=categories, publishers=publishers, authors=authors, all_books=all_books)

                cat_id_val = None
                if category_id is not None and str(category_id).strip():
                    try:
                        cat_id_val = int(str(category_id).strip())
                    except (ValueError, TypeError):
                        cat_id_val = book.get("category_id")
                else:
                    cat_id_val = book.get("category_id")

                pub_id_val = None
                if publisher_id is not None and str(publisher_id).strip():
                    try:
                        pub_id_val = int(str(publisher_id).strip())
                    except (ValueError, TypeError):
                        pub_id_val = book.get("publisher_id")
                else:
                    pub_id_val = book.get("publisher_id")

                # Update primary metadata, category, and publisher properties
                s.run("""
                    MATCH (b:Book {book_id: $bid})
                    SET b.title = $title, b.isbn = $isbn, b.publication_year = $year,
                        b.category_id = $cid, b.publisher_id = $pid
                """, bid=book_id, title=title, isbn=isbn, year=pub_year_val, cid=cat_id_val, pid=pub_id_val)

                # Synchronize [:BELONGS_TO] Category edge
                if cat_id_val:
                    s.run("""
                        MATCH (b:Book {book_id: $bid})
                        OPTIONAL MATCH (b)-[r:BELONGS_TO]->()
                        DELETE r
                        WITH b
                        MATCH (c:Category {category_id: $cid})
                        MERGE (b)-[:BELONGS_TO]->(c)
                    """, bid=book_id, cid=cat_id_val)

                # Synchronize [:PUBLISHED_BY] Publisher edge
                if pub_id_val:
                    s.run("""
                        MATCH (b:Book {book_id: $bid})
                        OPTIONAL MATCH (b)-[r:PUBLISHED_BY]->()
                        DELETE r
                        WITH b
                        MATCH (p:Publisher {publisher_id: $pid})
                        MERGE (b)-[:PUBLISHED_BY]->(p)
                    """, bid=book_id, pid=pub_id_val)

                # Synchronize [:WROTE] Author edges
                if selected_authors:
                    s.run("""
                        MATCH (a:Author)-[r:WROTE]->(b:Book {book_id: $bid})
                        DELETE r
                    """, bid=book_id)
                    for aid_str in set(selected_authors):
                        try:
                            aid = int(aid_str)
                            s.run("""
                                MATCH (a:Author {author_id: $aid}), (b:Book {book_id: $bid})
                                MERGE (a)-[:WROTE]->(b)
                            """, aid=aid, bid=book_id)
                        except (ValueError, TypeError):
                            pass

                # Clear old :PREREQUISITE_FOR edges before applying updated selections
                s.run("""
                    MATCH (b:Book {book_id: $bid})
                    OPTIONAL MATCH (old_pre:Book)-[r_in:PREREQUISITE_FOR]->(b)
                    OPTIONAL MATCH (b)-[r_out:PREREQUISITE_FOR]->(old_nxt:Book)
                    DELETE r_in, r_out
                """, bid=book_id)

                prereq_book_id   = request.form.get("prereq_book_id", "").strip()
                next_book_id     = request.form.get("next_book_id", "").strip()
                curriculum_track = request.form.get("curriculum_track", "").strip()

                link_book_prerequisites(s, book_id, cat_id_val, prereq_book_id, next_book_id, curriculum_track, title)

                flash(f"Book '{title}' and academic learning roadmap links updated successfully.", "success")
                if cat_id_val:
                    return redirect(url_for("category_books", category_id=int(cat_id_val)))
                return redirect(url_for("books"))

            return render_template("edit_book.html", book=book, categories=categories, publishers=publishers, authors=authors, all_books=all_books)

    except Exception as e:
        flash(f"Error updating book: {str(e)}", "danger")
        return redirect(url_for("books"))


# ----------------------------------------------------------------------------
# /delete_book/<int:book_id>
# ----------------------------------------------------------------------------
@app.route("/delete_book/<int:book_id>", methods=["POST"])
@login_required
@role_required(["Admin"])
def delete_book(book_id):
    raw_cat = request.form.get("category_id")
    category_id_val = None
    if raw_cat is not None and str(raw_cat).strip():
        try:
            category_id_val = int(str(raw_cat).strip())
        except (ValueError, TypeError):
            category_id_val = None

    try:
        with get_session() as s:
            res = s.run("MATCH (b:Book {book_id: $bid}) RETURN b.title AS title, b.category_id AS category_id", bid=book_id)
            rec = res.single()
            if not rec:
                flash("Book record not found.", "warning")
                return redirect(url_for("books"))

            book_title = rec["title"]
            if category_id_val is None:
                category_id_val = rec.get("category_id")

            # Check active loans
            res = s.run("""
                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy)<-[:FOR_COPY]-(l:Loan)
                WHERE l.return_date IS NULL
                RETURN count(l) AS active_loans
            """, bid=book_id)
            active_loans = res.single()["active_loans"]

            if active_loans > 0:
                flash(f"Cannot delete '{book_title}': {active_loans} active loan(s) exist.", "danger")
                if category_id_val:
                    return redirect(url_for("category_books", category_id=category_id_val))
                return redirect(url_for("books"))

            # Check unpaid fines
            res = s.run("""
                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(:Copy)<-[:FOR_COPY]-(:Loan)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
                RETURN count(f) AS unpaid_fines
            """, bid=book_id)
            unpaid_fines = res.single()["unpaid_fines"]
            if unpaid_fines > 0:
                flash(f"Cannot delete '{book_title}': {unpaid_fines} unpaid fine(s) exist on loans for this book.", "danger")
                if category_id_val:
                    return redirect(url_for("category_books", category_id=category_id_val))
                return redirect(url_for("books"))

            # Check active awaiting pickup reservations
            res = s.run("""
                MATCH (r:LoanRequest {status: 'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book {book_id: $bid})
                RETURN count(r) AS awaiting_count
            """, bid=book_id)
            awaiting_count = res.single()["awaiting_count"]
            if awaiting_count > 0:
                flash("Cannot delete book: Active pickup reservation(s) exist.", "danger")
                if category_id_val:
                    return redirect(url_for("category_books", category_id=category_id_val))
                return redirect(url_for("books"))

            # Delete loan requests
            s.run("MATCH (r:LoanRequest)-[:FOR_BOOK]->(b:Book {book_id: $bid}) DETACH DELETE r", bid=book_id)
            # Delete fines & loans via copies
            s.run("""
                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy)<-[:FOR_COPY]-(l:Loan)
                OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine)
                DETACH DELETE f, l
            """, bid=book_id)
            # Delete copies and book
            s.run("MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy) DETACH DELETE cp", bid=book_id)
            s.run("MATCH (b:Book {book_id: $bid}) DETACH DELETE b", bid=book_id)

            flash(f"Book '{book_title}' and all associated records were permanently deleted.", "success")

    except Exception as e:
        flash(f"Error archiving book: {str(e)}", "danger")

    if category_id_val:
        return redirect(url_for("category_books", category_id=category_id_val))
    return redirect(url_for("books"))


# ----------------------------------------------------------------------------
# /issue_loan
# ----------------------------------------------------------------------------
@app.route("/issue_loan", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Librarian"])
def issue_loan():
    patrons          = []
    available_copies = []
    all_books        = []

    try:
        with get_session() as s:
            sync_active_overdue_fines(s)
            if request.method == "POST":
                copy_id_raw       = request.form.get("copy_id")
                book_id_raw       = request.form.get("book_id")
                borrower_username = (request.form.get("borrower_username") or request.form.get("patron_quick_search") or "").strip()
                borrower_id_raw   = request.form.get("borrower_id")
                due_in_days_raw   = request.form.get("due_in_days", 14)
                issued_by         = session["user_id"]
                today             = today_str()

                try:
                    due_in_days = int(due_in_days_raw)
                except (ValueError, TypeError):
                    flash("Invalid loan duration: Must be a valid integer between 1 and 60 days.", "danger")
                    return redirect(url_for("issue_loan"))

                if due_in_days < 1 or due_in_days > 60:
                    flash("Invalid loan duration: Must be between 1 and 60 days.", "danger")
                    return redirect(url_for("issue_loan"))

                copy_id = None
                if copy_id_raw:
                    try:
                        copy_id = int(copy_id_raw)
                    except (ValueError, TypeError):
                        flash("Invalid copy ID specified.", "danger")
                        return redirect(url_for("issue_loan"))

                book_id = None
                if book_id_raw:
                    try:
                        book_id = int(book_id_raw)
                    except (ValueError, TypeError):
                        pass

                # Fallback: pick first available copy for a book
                if not copy_id and book_id:
                    try:
                        res = s.run("""
                            MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy)
                            WHERE cp.status = 'Available'
                            RETURN cp.copy_id AS copy_id LIMIT 1
                        """, bid=book_id)
                        rec = res.single()
                        if rec:
                            copy_id = rec["copy_id"]
                    except (ValueError, TypeError):
                        pass

                # Resolve borrower
                borrower_status = None
                borrower_role   = None
                if borrower_username:
                    res = s.run("""
                        MATCH (u:User)
                        WHERE toLower(u.username) = toLower($uname)
                        RETURN u.user_id AS user_id, u.account_status AS account_status, u.role AS role
                    """, uname=borrower_username)
                    rec = res.single()
                    if not rec:
                        flash(f"Borrower '{borrower_username}' not found.", "danger")
                        borrower_id = None
                    else:
                        borrower_id     = rec["user_id"]
                        borrower_status = rec["account_status"]
                        borrower_role   = rec["role"]
                elif borrower_id:
                    try:
                        borrower_id = int(borrower_id)
                        res = s.run("""
                            MATCH (u:User {user_id: $uid})
                            RETURN u.account_status AS account_status, u.role AS role
                        """, uid=borrower_id)
                        rec = res.single()
                        if rec:
                            borrower_status = rec["account_status"]
                            borrower_role   = rec["role"]
                        else:
                            borrower_id = None
                            flash("Borrower not found.", "danger")
                    except (ValueError, TypeError):
                        borrower_id = None

                if not copy_id or not borrower_id:
                    flash("Please provide both a valid copy and a patron username.", "warning")
                elif borrower_status != "Active":
                    flash(f"Borrowing Prohibited: Borrower account is {borrower_status or 'Inactive'}.", "danger")
                elif borrower_role not in ["Student", "Staff"]:
                    flash(f"Borrowing Prohibited: User role '{borrower_role}' is not eligible to borrow books (only Student or Staff accounts).", "danger")
                else:
                    # Check copy status & reservation ownership
                    res_cp = s.run("""
                        MATCH (cp:Copy {copy_id: $cid})
                        OPTIONAL MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)
                        WHERE r.status = 'Awaiting Pickup' AND (r.copy_id = cp.copy_id OR (r)-[:RESERVED_COPY]->(cp))
                        RETURN cp.status AS status, count(r) AS reserved_for_user
                    """, cid=int(copy_id), uid=borrower_id)
                    cp_rec = res_cp.single()

                    # Unpaid fines check
                    res = s.run("""
                        MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'})
                        RETURN coalesce(sum(f.fine_amount),0) AS unpaid_total
                    """, uid=borrower_id)
                    unpaid_total = res.single()["unpaid_total"]

                    # Overdue check
                    res = s.run("""
                        MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                        WHERE l.return_date IS NULL AND l.due_date < $today
                        RETURN count(l) AS overdue_count
                    """, uid=borrower_id, today=today)
                    overdue_count = res.single()["overdue_count"]

                    # Quota check (active loans + awaiting pickup, excluding this book)
                    res = s.run("""
                        MATCH (cp:Copy {copy_id: $cid})<-[:HAS_COPY]-(b:Book)
                        WITH b.book_id AS this_book_id
                        MATCH (u:User {user_id: $uid})
                        OPTIONAL MATCH (u)-[:BORROWED]->(al:Loan) WHERE al.return_date IS NULL
                        OPTIONAL MATCH (u)-[:REQUESTED]->(ar:LoanRequest)-[:FOR_BOOK]->(ab:Book)
                        WHERE ar.status = 'Awaiting Pickup' AND ab.book_id <> this_book_id
                        RETURN count(DISTINCT al) + count(DISTINCT ar) AS other_commitments
                    """, cid=int(copy_id), uid=borrower_id)
                    other_commitments = res.single()["other_commitments"]

                    # Same-book duplicate check
                    res = s.run("""
                        MATCH (cp:Copy {copy_id: $cid})<-[:HAS_COPY]-(b:Book)
                        MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan {return_date:null})-[:FOR_COPY]->(c2:Copy)<-[:HAS_COPY]-(b)
                        RETURN count(l) AS same_book_count
                    """, cid=int(copy_id), uid=borrower_id)
                    same_book_count = res.single()["same_book_count"]

                    if not cp_rec:
                        flash(f"Copy #{copy_id} not found in inventory.", "danger")
                    elif cp_rec["status"] != "Available" and not (cp_rec["status"] == "Reserved" and cp_rec["reserved_for_user"] > 0):
                        flash(f"Checkout Prohibited: Copy #{copy_id} is currently {cp_rec['status']}.", "warning")
                    elif unpaid_total > 0:
                        flash(f"Borrowing Prohibited: Patron has unpaid fines of Rs. {unpaid_total:.2f}.", "warning")
                    elif overdue_count > 0:
                        flash(f"Borrowing Prohibited: Patron has {overdue_count} overdue loan(s).", "warning")
                    elif (other_commitments + 1) > 3:
                        flash(f"Borrowing Prohibited: Patron would exceed 3-book threshold ({other_commitments} existing).", "warning")
                    elif same_book_count > 0:
                        flash("Duplicate Loan Prohibited: Patron already has this book on loan.", "warning")
                    else:
                        # Issue the loan
                        issue_dt = datetime.now()
                        due_dt   = issue_dt + timedelta(days=due_in_days)
                        new_lid  = next_id(s, "Loan", "loan_id")

                        s.run("""
                            CREATE (l:Loan {
                                loan_id: $lid, copy_id: $cid, borrower_id: $bid,
                                issued_by: $issby,
                                issue_date: $issue_date, due_date: $due_date,
                                return_date: null
                            })
                        """, lid=new_lid, cid=int(copy_id), bid=borrower_id,
                             issby=issued_by,
                             issue_date=issue_dt.strftime("%Y-%m-%d"),
                             due_date=due_dt.strftime("%Y-%m-%d"))

                        s.run("""
                            MATCH (u:User {user_id: $uid}), (l:Loan {loan_id: $lid})
                            CREATE (u)-[:BORROWED]->(l)
                        """, uid=borrower_id, lid=new_lid)

                        s.run("""
                            MATCH (l:Loan {loan_id: $lid}), (cp:Copy {copy_id: $cid})
                            CREATE (l)-[:FOR_COPY]->(cp)
                        """, lid=new_lid, cid=int(copy_id))

                        s.run("""
                            MATCH (lib:User {user_id: $uid}), (l:Loan {loan_id: $lid})
                            CREATE (lib)-[:ISSUED]->(l)
                        """, uid=issued_by, lid=new_lid)

                        s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Borrowed'", cid=int(copy_id))

                        # Fulfil Awaiting Pickup or Pending request if exists
                        s.run("""
                            MATCH (cp:Copy {copy_id: $cid})<-[:HAS_COPY]-(b:Book)
                            MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b)
                            WHERE r.status IN ['Awaiting Pickup', 'Pending']
                            WITH r, cp, r.copy_id AS old_cid
                            OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                            DELETE rel
                            SET r.status = 'Fulfilled', r.copy_id = cp.copy_id
                            WITH old_cid, cp
                            WHERE old_cid IS NOT NULL AND old_cid <> cp.copy_id
                            MATCH (rcp:Copy {copy_id: old_cid, status: 'Reserved'})
                            SET rcp.status = 'Available'
                        """, cid=int(copy_id), uid=borrower_id)

                        flash(f"Loan successfully issued for Copy #{copy_id}.", "success")
                        return redirect(url_for("dashboard"))

            # GET: fetch dropdown data
            res = s.run("""
                MATCH (b:Book)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                WITH b, c, collect(DISTINCT a.first_name + ' ' + a.last_name) AS alist
                RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                       c.name AS category_name,
                       reduce(s='', a IN alist | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                       size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status = 'Available' | cp]) AS available_copies_count,
                       size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_copies_count
                ORDER BY b.title ASC
            """)
            all_books = [dict(r) for r in res]

            today_cur = today_str()
            res = s.run("""
                MATCH (u:User)
                WHERE u.role IN ['Student','Staff'] AND u.account_status = 'Active'
                WITH u,
                     size([(u)-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'}) | f]) AS unpaid_fines_count,
                     size([(u)-[:BORROWED]->(ol:Loan) WHERE ol.return_date IS NULL AND ol.due_date < $today | ol]) AS overdue_count
                RETURN u.user_id AS user_id, u.username AS username,
                       u.role AS role, u.email AS email,
                       (unpaid_fines_count > 0 OR overdue_count > 0) AS has_blocking_issue,
                       unpaid_fines_count, overdue_count
                ORDER BY u.role ASC, u.username ASC
            """, today=today_cur)
            patrons = [dict(r) for r in res]

            res = s.run("""
                MATCH (b:Book)-[:HAS_COPY]->(cp:Copy)
                WHERE cp.status = 'Available'
                RETURN cp.copy_id AS copy_id, cp.book_id AS book_id,
                       b.title AS book_title, b.isbn AS isbn,
                       cp.status AS status, cp.condition AS condition
                ORDER BY b.title ASC, cp.copy_id ASC
            """)
            available_copies = [dict(r) for r in res]

    except Exception as e:
        flash(f"Failed to issue loan: {str(e)}", "danger")

    return render_template("issue_loan.html", patrons=patrons,
                           available_copies=available_copies, all_books=all_books)


# ----------------------------------------------------------------------------
# /my_fines
# ----------------------------------------------------------------------------
@app.route("/my_fines", methods=["GET"])
@login_required
def my_fines():
    user_id    = session.get("user_id")
    fines_list = []

    try:
        with get_session() as s:
            sync_active_overdue_fines(s)
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine)
                OPTIONAL MATCH (l)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                RETURN f.fine_id AS fine_id, f.fine_amount AS fine_amount,
                       f.payment_status AS payment_status,
                       l.loan_id AS loan_id, l.issue_date AS issue_date,
                       l.due_date AS due_date, l.return_date AS return_date,
                       coalesce(b.title, 'Archived/Deleted Title') AS book_title,
                       coalesce(b.title, 'Archived/Deleted Title') AS title,
                       cp.copy_id AS copy_id
                ORDER BY f.fine_id DESC
            """, uid=user_id)
            fines_list = rows(res)

    except Exception as e:
        flash(f"Error fetching fine statements: {str(e)}", "danger")

    return render_template("my_fines.html", fines=fines_list)


# ----------------------------------------------------------------------------
# /manage_users (Admin only)
# ----------------------------------------------------------------------------
@app.route("/manage_users", methods=["GET", "POST"])
@login_required
@role_required(["Admin"])
def manage_users():
    users_list = []
    try:
        with get_session() as s:
            if request.method == "POST":
                action = request.form.get("action")

                if action == "add_user":
                    new_uname = request.form.get("username", "").strip()
                    new_email = request.form.get("email", "").lower().strip()
                    new_pass  = request.form.get("password", "")
                    new_role  = request.form.get("role", "Student")

                    if not new_uname or not new_email or not new_pass:
                        flash("All fields are required.", "warning")
                    elif new_role not in ["Admin", "Librarian", "Staff", "Student"]:
                        flash(f"Invalid role: '{new_role}'. Permitted roles are Admin, Librarian, Staff, or Student.", "danger")
                    else:
                        is_email_valid, email_err = validate_email_format(new_email)
                        if not is_email_valid:
                            flash(f"Invalid Email: {email_err}", "warning")
                        elif not (new_email.endswith("@vit.edu") or new_email.endswith("@vit.ac.in")):
                            flash("Registration requires a valid institutional email domain (@vit.edu or @vit.ac.in).", "danger")
                        else:
                            is_pass_valid, pass_err = validate_password_strength(new_pass)
                            if not is_pass_valid:
                                flash(f"Invalid Password: {pass_err}", "warning")
                            else:
                                res_chk = s.run("""
                                    MATCH (u:User)
                                    WHERE toLower(u.username) = toLower($uname) OR toLower(u.email) = toLower($email)
                                    RETURN u.username AS username, u.email AS email LIMIT 1
                                """, uname=new_uname, email=new_email)
                                if res_chk.single():
                                    flash(f"User with username '{new_uname}' or email '{new_email}' already exists.", "warning")
                                else:
                                    pw_hash = generate_password_hash(new_pass)
                                    new_uid = next_id(s, "User", "user_id")
                                    s.run("""
                                        CREATE (u:User {
                                            user_id: $uid, username: $uname,
                                            password_hash: $pw, email: $email,
                                            role: $role, account_status: 'Active'
                                        })
                                    """, uid=new_uid, uname=new_uname, pw=pw_hash,
                                         email=new_email, role=new_role)
                                    flash(f"User '{new_uname}' ({new_role}) created successfully!", "success")

                elif action == "toggle_status":
                    target_uid_raw = request.form.get("user_id")
                    current_status = request.form.get("current_status")

                    try:
                        target_uid = int(target_uid_raw)
                    except (ValueError, TypeError):
                        flash("Invalid user ID specified.", "danger")
                        return redirect(url_for("manage_users"))

                    if target_uid == session.get("user_id"):
                        flash("Action Prohibited: Cannot suspend your own session.", "danger")
                        return redirect(url_for("manage_users"))

                    # Protect Admin from suspension
                    res = s.run("MATCH (u:User {user_id: $uid}) RETURN u.role AS role, u.username AS username", uid=target_uid)
                    u_rec = res.single()
                    if u_rec and u_rec["role"] == "Admin":
                        flash(f"Action Prohibited: Admin account '{u_rec['username']}' cannot be suspended by system policy.", "danger")
                        return redirect(url_for("manage_users"))

                    new_status = "Suspended" if current_status == "Active" else "Active"
                    s.run("""
                        MATCH (u:User {user_id: $uid}) SET u.account_status = $status
                    """, uid=target_uid, status=new_status)
                    flash(f"User #{target_uid} status updated to '{new_status}'.", "info")

                elif action == "reset_password":
                    target_uid_raw = request.form.get("user_id")
                    try:
                        target_uid = int(target_uid_raw)
                    except (ValueError, TypeError):
                        flash("Invalid user ID specified.", "danger")
                        return redirect(url_for("manage_users"))

                    try:
                        res = s.run("MATCH (u:User {user_id: $uid}) RETURN u.role AS role, u.username AS username", uid=target_uid)
                        u_rec = res.single()
                        if not u_rec:
                            flash("User not found.", "warning")
                        elif u_rec["role"] not in ["Student", "Staff", "Librarian"]:
                            flash("Action Prohibited: Password reset via this panel is not permitted for Admin accounts.", "danger")
                        else:
                            uname = u_rec["username"]
                            temp_pass = f"{uname.capitalize()}#Lib2026"
                            new_hash = generate_password_hash(temp_pass)
                            s.run("MATCH (u:User {user_id: $uid}) SET u.password_hash = $ph", uid=int(target_uid), ph=new_hash)
                            flash(f"Password for {u_rec['role']} '{uname}' has been reset to temporary password: {temp_pass}", "success")
                    except Exception as e:
                        flash(f"Error resetting password: {str(e)}", "danger")

            res = s.run("""
                MATCH (u:User)
                RETURN u.user_id AS user_id, u.username AS username,
                       u.email AS email, u.role AS role, u.account_status AS account_status
                ORDER BY u.user_id ASC
            """)
            users_list = [dict(r) for r in res]

    except Exception as e:
        flash(f"Error managing users: {str(e)}", "danger")

    return render_template("manage_users.html", users=users_list)


# ----------------------------------------------------------------------------
# /delete_user/<int:user_id>
# ----------------------------------------------------------------------------
@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
@role_required(["Admin"])
def delete_user(user_id):
    if user_id == session.get("user_id"):
        flash("Action Prohibited: Cannot delete your own Admin account.", "danger")
        return redirect(url_for("manage_users"))

    try:
        with get_session() as s:
            res = s.run("""
                MATCH (u:User {user_id: $uid})
                RETURN u.role AS role, u.username AS username
            """, uid=user_id)
            rec = res.single()
            if not rec:
                flash("User not found.", "warning")
                return redirect(url_for("manage_users"))

            if rec["role"] == "Admin":
                flash(f"Action Prohibited: Admin account '{rec['username']}' cannot be deleted by policy.", "danger")
                return redirect(url_for("manage_users"))

            # Check active loans
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                WHERE l.return_date IS NULL
                RETURN count(l) AS active_loans
            """, uid=user_id)
            if res.single()["active_loans"] > 0:
                flash("Cannot delete user: Active loans exist.", "danger")
                return redirect(url_for("manage_users"))

            # Check unpaid fines
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'})
                RETURN count(f) AS unpaid_fines
            """, uid=user_id)
            if res.single()["unpaid_fines"] > 0:
                flash("Cannot delete user: Unpaid fines exist.", "danger")
                return redirect(url_for("manage_users"))

            # Release reserved copies before deleting loan requests
            s.run("""
                MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)
                OPTIONAL MATCH (r)-[:RESERVED_COPY]->(cp:Copy)
                OPTIONAL MATCH (cp2:Copy {copy_id: r.copy_id})
                FOREACH (c IN CASE WHEN cp IS NOT NULL THEN [cp] ELSE [] END | SET c.status = 'Available')
                FOREACH (c IN CASE WHEN cp2 IS NOT NULL THEN [cp2] ELSE [] END | SET c.status = 'Available')
                DETACH DELETE r
            """, uid=user_id)

            # Detach returned loans (anonymize to user_id=0)
            s.run("""
                MATCH (u:User {user_id: $uid})-[rel:BORROWED]->(l:Loan)
                WHERE l.return_date IS NOT NULL
                DELETE rel
                SET l.borrower_id = 0
            """, uid=user_id)

            # Delete user node
            s.run("MATCH (u:User {user_id: $uid}) DETACH DELETE u", uid=user_id)
            flash(f"User '{rec['username']}' (ID #{user_id}) deleted successfully.", "success")

    except Exception as e:
        flash(f"Error during account deletion: {str(e)}", "danger")

    return redirect(url_for("manage_users"))


# ----------------------------------------------------------------------------
# /change_password
# ----------------------------------------------------------------------------
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    user_id = session.get("user_id")

    if request.method == "POST":
        current_pass = request.form.get("current_password", "")
        new_pass     = request.form.get("new_password", "")
        confirm_pass = request.form.get("confirm_password", "")

        if not current_pass or not new_pass or not confirm_pass:
            flash("All password fields are required.", "warning")
            return render_template("change_password.html")

        if new_pass != confirm_pass:
            flash("New password and confirmation do not match.", "warning")
            return render_template("change_password.html")

        is_valid, err_msg = validate_password_strength(new_pass)
        if not is_valid:
            flash(f"Invalid New Password: {err_msg}", "warning")
            return render_template("change_password.html")

        try:
            with get_session() as s:
                res = s.run("""
                    MATCH (u:User {user_id: $uid})
                    RETURN u.password_hash AS password_hash
                """, uid=user_id)
                rec = res.single()

                if not rec or not check_password_hash(rec["password_hash"], current_pass):
                    flash("Current password verification failed.", "danger")
                    return render_template("change_password.html")

                if check_password_hash(rec["password_hash"], new_pass):
                    flash("New password cannot be identical to your current password.", "warning")
                    return render_template("change_password.html")

                new_hash = generate_password_hash(new_pass)
                s.run("MATCH (u:User {user_id: $uid}) SET u.password_hash = $ph", uid=user_id, ph=new_hash)

            flash("Password changed successfully! Please log in again.", "success")
            session.clear()
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error updating password: {str(e)}", "danger")

    return render_template("change_password.html")


# ----------------------------------------------------------------------------
# /request_loan/<int:book_id>
# ----------------------------------------------------------------------------
@app.route("/request_loan/<int:book_id>", methods=["POST"])
@login_required
def request_loan(book_id):
    user_id = session.get("user_id")
    role    = session.get("role")
    today   = today_str()

    if role not in ["Student", "Staff"]:
        flash("Only Students and Staff may request book loans.", "warning")
        return redirect(url_for("books"))

    try:
        with get_session() as s:
            sync_active_overdue_fines(s)
            # 1. Unpaid fines check
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'})
                RETURN coalesce(sum(f.fine_amount), 0) AS unpaid_total
            """, uid=user_id)
            unpaid_total = res.single()["unpaid_total"]
            if unpaid_total > 0:
                flash(f"You have unpaid fines of Rs. {unpaid_total:.2f}. Settle them before requesting.", "danger")
                return redirect(url_for("my_fines"))

            # 2. Overdue check
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                WHERE l.return_date IS NULL AND l.due_date < $today
                RETURN count(l) AS overdue_count
            """, uid=user_id, today=today)
            overdue_count = res.single()["overdue_count"]
            if overdue_count > 0:
                flash(f"You have {overdue_count} overdue book(s). Return them before requesting.", "danger")
                return redirect(url_for("dashboard"))

            # 3. Duplicate active loan check
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan {return_date:null})-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book {book_id: $bid})
                RETURN count(l) AS same_book_count
            """, uid=user_id, bid=book_id)
            if res.single()["same_book_count"] > 0:
                flash("Duplicate Loan: You already have this book on active loan.", "warning")
                return redirect(url_for("books"))

            # 4. Existing pending/awaiting check
            res = s.run("""
                MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b:Book {book_id: $bid})
                WHERE r.status IN ['Pending', 'Awaiting Pickup']
                RETURN count(r) AS pending_count
            """, uid=user_id, bid=book_id)
            if res.single()["pending_count"] > 0:
                flash("You already have an active request for this title.", "info")
                return redirect(url_for("books"))

            # 5. Quota check (active + awaiting + pending >= 3)
            res = s.run("""
                MATCH (u:User {user_id: $uid})
                OPTIONAL MATCH (u)-[:BORROWED]->(al:Loan) WHERE al.return_date IS NULL
                OPTIONAL MATCH (u)-[:REQUESTED]->(ap:LoanRequest) WHERE ap.status = 'Awaiting Pickup'
                OPTIONAL MATCH (u)-[:REQUESTED]->(pnd:LoanRequest) WHERE pnd.status = 'Pending'
                RETURN count(DISTINCT al) AS act_cnt,
                       count(DISTINCT ap)  AS ap_cnt,
                       count(DISTINCT pnd) AS pend_cnt
            """, uid=user_id)
            q = res.single()
            act_cnt  = q["act_cnt"]  or 0
            ap_cnt   = q["ap_cnt"]   or 0
            pend_cnt = q["pend_cnt"] or 0
            combined = act_cnt + ap_cnt + pend_cnt

            if combined >= 3:
                flash(f"Quota Reached: {combined}/3 books ({act_cnt} active, {ap_cnt} awaiting, {pend_cnt} pending).", "warning")
                cat_id = request.form.get("category_id")
                if cat_id:
                    try:
                        return redirect(url_for("category_books", category_id=int(cat_id)))
                    except (ValueError, TypeError):
                        pass
                return redirect(url_for("books"))

            # 6. Get book title
            res = s.run("MATCH (b:Book {book_id: $bid}) RETURN b.title AS title", bid=book_id)
            rec = res.single()
            book_title = rec["title"] if rec else f"Book #{book_id}"

            # 7. Create LoanRequest node and relationships
            new_rid  = next_id(s, "LoanRequest", "request_id")
            req_date = datetime.now().strftime("%Y-%m-%d")

            s.run("""
                CREATE (r:LoanRequest {
                    request_id: $rid, book_id: $bid, borrower_id: $uid,
                    copy_id: null, request_date: $rdate, status: 'Pending'
                })
            """, rid=new_rid, bid=book_id, uid=user_id, rdate=req_date)

            s.run("""
                MATCH (u:User {user_id: $uid}), (r:LoanRequest {request_id: $rid})
                CREATE (u)-[:REQUESTED]->(r)
            """, uid=user_id, rid=new_rid)

            s.run("""
                MATCH (r:LoanRequest {request_id: $rid}), (b:Book {book_id: $bid})
                CREATE (r)-[:FOR_BOOK]->(b)
            """, rid=new_rid, bid=book_id)

            flash(f"Loan request for '{book_title}' submitted! Awaiting Librarian approval.", "success")

    except Exception as e:
        flash(f"Failed to submit loan request: {str(e)}", "danger")

    if request.form.get("from_dashboard"):
        return redirect(url_for("dashboard"))
    cat_id = request.form.get("category_id")
    if cat_id:
        try:
            return redirect(url_for("category_books", category_id=int(cat_id)))
        except (ValueError, TypeError):
            pass
    return redirect(url_for("books"))


# ----------------------------------------------------------------------------
# /loan_requests (Admin/Librarian approval workflow)
# ----------------------------------------------------------------------------
@app.route("/loan_requests", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Librarian"])
def loan_requests():
    requests_list       = []
    awaiting_pickup_list = []

    try:
        with get_session() as s:
            sync_fulfilled_loan_requests(s)
            sync_active_overdue_fines(s)
            today    = today_str()
            issuer_id = session.get("user_id")

            if request.method == "POST":
                req_id_raw = request.form.get("request_id")
                action     = request.form.get("action")

                try:
                    req_id = int(req_id_raw)
                except (ValueError, TypeError):
                    flash("Invalid or missing request ID.", "warning")
                    return redirect(url_for("loan_requests"))

                if action == "approve":
                    res = s.run("""
                        MATCH (r:LoanRequest {request_id: $rid})
                        RETURN r.book_id AS book_id, r.borrower_id AS borrower_id, r.status AS status
                    """, rid=req_id)
                    req_data = res.single()

                    if not req_data or req_data["status"] != "Pending":
                        flash("Invalid or already processed request.", "warning")
                    else:
                        borrower_id = req_data["borrower_id"]
                        b_id        = req_data["book_id"]

                        res = s.run("MATCH (u:User {user_id: $uid}) RETURN u.username AS username, u.account_status AS account_status", uid=borrower_id)
                        u_info = res.single()
                        b_name = (u_info or {}).get("username", f"User #{borrower_id}")
                        b_status = (u_info or {}).get("account_status", "Active")

                        # Fines check
                        res = s.run("""
                            MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'})
                            RETURN coalesce(sum(f.fine_amount),0) AS unpaid_total
                        """, uid=borrower_id)
                        unpaid_total = res.single()["unpaid_total"]

                        # Overdue check
                        res = s.run("""
                            MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                            WHERE l.return_date IS NULL AND l.due_date < $today
                            RETURN count(l) AS overdue_count
                        """, uid=borrower_id, today=today)
                        overdue_count = res.single()["overdue_count"]

                        # Quota (active + awaiting)
                        res = s.run("""
                            MATCH (u:User {user_id: $uid})
                            OPTIONAL MATCH (u)-[:BORROWED]->(al:Loan) WHERE al.return_date IS NULL
                            OPTIONAL MATCH (u)-[:REQUESTED]->(ap:LoanRequest {status:'Awaiting Pickup'})
                            RETURN count(DISTINCT al) AS active_loans_cnt,
                                   count(DISTINCT ap)  AS awaiting_pickup_cnt
                        """, uid=borrower_id)
                        q = res.single()
                        active_cnt  = q["active_loans_cnt"]  or 0
                        await_cnt   = q["awaiting_pickup_cnt"] or 0
                        committed   = active_cnt + await_cnt

                        # Same-book check
                        res = s.run("""
                            MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan {return_date:null})-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book {book_id: $bid})
                            RETURN count(l) AS same_book_count
                        """, uid=borrower_id, bid=b_id)
                        same_book_count = res.single()["same_book_count"]

                        if b_status == "Suspended":
                            flash(f"Approval Prohibited: Patron '{b_name}' account is currently suspended.", "danger")
                        elif unpaid_total > 0:
                            flash(f"Approval Prohibited: '{b_name}' has unpaid fines of Rs. {unpaid_total:.2f}.", "danger")
                        elif overdue_count > 0:
                            flash(f"Approval Prohibited: '{b_name}' has {overdue_count} overdue loan(s).", "danger")
                        elif same_book_count > 0:
                            # Auto-fulfill lingering request since user already holds active loan for this book
                            s.run("""
                                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)
                                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp)
                                WHERE l.return_date IS NULL
                                MATCH (u)-[:REQUESTED]->(r:LoanRequest {request_id: $rid})-[:FOR_BOOK]->(b)
                                WHERE r.status IN ['Pending', 'Awaiting Pickup']
                                WITH r, cp, r.copy_id AS old_cid
                                OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                                DELETE rel
                                SET r.status = 'Fulfilled', r.copy_id = cp.copy_id
                                WITH old_cid, cp
                                WHERE old_cid IS NOT NULL AND old_cid <> cp.copy_id
                                MATCH (rcp:Copy {copy_id: old_cid, status: 'Reserved'})
                                SET rcp.status = 'Available'
                            """, uid=borrower_id, bid=b_id, rid=req_id)
                            flash(f"Approval Prohibited: '{b_name}' already has this book on active loan. Request #{req_id} marked Fulfilled.", "warning")
                        elif committed >= 3:
                            flash(f"Approval Prohibited: '{b_name}' has reached the 3-book threshold ({committed}).", "danger")
                        else:
                            # Find available copy
                            res = s.run("""
                                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy {status:'Available'})
                                RETURN cp.copy_id AS copy_id LIMIT 1
                            """, bid=b_id)
                            avail = res.single()

                            if not avail:
                                flash("Cannot approve: No physical copies available in inventory (0 stock).", "danger")
                            else:
                                copy_id = avail["copy_id"]
                                s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Reserved'", cid=copy_id)
                                s.run("""
                                    MATCH (r:LoanRequest {request_id: $rid}), (cp:Copy {copy_id: $cid})
                                    SET r.status = 'Awaiting Pickup', r.copy_id = $cid
                                    MERGE (r)-[:RESERVED_COPY]->(cp)
                                """, rid=req_id, cid=copy_id)

                                flash(f"Request #{req_id} approved! Copy #{copy_id} reserved for '{b_name}'.", "success")

                elif action == "confirm_pickup":
                    res = s.run("""
                        MATCH (r:LoanRequest {request_id: $rid, status: 'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book)
                        MATCH (u:User {user_id: r.borrower_id})
                        RETURN r.borrower_id AS borrower_id, r.copy_id AS copy_id,
                               r.book_id AS book_id, b.title AS book_title,
                               u.username AS borrower_name, u.account_status AS borrower_status
                    """, rid=req_id)
                    pickup_req = res.single()

                    if not pickup_req:
                        flash("Request not found or not in 'Awaiting Pickup' status.", "warning")
                    else:
                        c_id  = pickup_req["copy_id"]
                        b_id2 = pickup_req["borrower_id"]
                        b_name = pickup_req["borrower_name"]
                        b_title = pickup_req["book_title"]

                        if not c_id:
                            res = s.run("""
                                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy {status:'Reserved'})
                                WHERE NOT (cp)<-[:RESERVED_COPY]-(:LoanRequest)
                                RETURN min(cp.copy_id) AS copy_id
                            """, bid=pickup_req["book_id"])
                            c_id = (res.single() or {}).get("copy_id")

                        if not c_id:
                            flash(f"No reserved copy found for '{b_title}'.", "danger")
                        else:
                            today_cur = today_str()
                            # Re-verify borrower eligibility before physical handover
                            res_fine = s.run("""
                                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:HAS_FINE]->(f:Fine {payment_status:'Unpaid'})
                                RETURN coalesce(sum(f.fine_amount), 0) AS unpaid_total
                            """, uid=b_id2)
                            unpaid_total = res_fine.single()["unpaid_total"]

                            res_ovd = s.run("""
                                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                                WHERE l.return_date IS NULL AND l.due_date < $today
                                RETURN count(l) AS overdue_count
                            """, uid=b_id2, today=today_cur)
                            overdue_count = res_ovd.single()["overdue_count"]

                            res_act = s.run("""
                                MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)
                                WHERE l.return_date IS NULL
                                RETURN count(l) AS active_loans_count
                            """, uid=b_id2)
                            active_loans_count = res_act.single()["active_loans_count"]

                            if pickup_req.get("borrower_status") == "Suspended":
                                flash(f"Handover Prohibited: Patron '{b_name}' account is currently suspended.", "danger")
                            elif unpaid_total > 0:
                                flash(f"Handover Prohibited: '{b_name}' has unpaid disciplinary fines of Rs. {unpaid_total:.2f}.", "danger")
                            elif overdue_count > 0:
                                flash(f"Handover Prohibited: '{b_name}' has {overdue_count} overdue loan(s).", "danger")
                            elif active_loans_count >= 3:
                                flash(f"Handover Prohibited: '{b_name}' has reached the 3 active loans limit ({active_loans_count} active).", "danger")
                            else:
                                due_days = 14
                                issue_dt = datetime.now()
                                due_dt   = issue_dt + timedelta(days=due_days)
                                new_lid  = next_id(s, "Loan", "loan_id")

                                s.run("""
                                    CREATE (l:Loan {
                                        loan_id: $lid, copy_id: $cid, borrower_id: $bid,
                                        issued_by: $issby,
                                        issue_date: $issue_date, due_date: $due_date,
                                        return_date: null
                                    })
                                """, lid=new_lid, cid=c_id, bid=b_id2, issby=issuer_id,
                                     issue_date=issue_dt.strftime("%Y-%m-%d"),
                                     due_date=due_dt.strftime("%Y-%m-%d"))

                                s.run("""
                                    MATCH (u:User {user_id: $uid}), (l:Loan {loan_id: $lid})
                                    CREATE (u)-[:BORROWED]->(l)
                                """, uid=b_id2, lid=new_lid)

                                s.run("""
                                    MATCH (l:Loan {loan_id: $lid}), (cp:Copy {copy_id: $cid})
                                    CREATE (l)-[:FOR_COPY]->(cp)
                                """, lid=new_lid, cid=c_id)

                                s.run("""
                                    MATCH (lib:User {user_id: $uid}), (l:Loan {loan_id: $lid})
                                    CREATE (lib)-[:ISSUED]->(l)
                                """, uid=issuer_id, lid=new_lid)

                                s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Borrowed'", cid=c_id)
                                s.run("""
                                    MATCH (r:LoanRequest {request_id: $rid})
                                    OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                                    DELETE rel
                                    SET r.status = 'Fulfilled', r.copy_id = $cid
                                """, rid=req_id, cid=c_id)

                                # Clean up any other duplicate/lingering requests for the same book and borrower
                                s.run("""
                                    MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest)-[:FOR_BOOK]->(b:Book {book_id: $bid})
                                    WHERE r.status IN ['Pending', 'Awaiting Pickup']
                                    WITH r, r.copy_id AS old_cid
                                    OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                                    DELETE rel
                                    SET r.status = 'Fulfilled', r.copy_id = $cid
                                    WITH old_cid
                                    WHERE old_cid IS NOT NULL AND old_cid <> $cid
                                    MATCH (rcp:Copy {copy_id: old_cid, status: 'Reserved'})
                                    SET rcp.status = 'Available'
                                """, uid=b_id2, bid=pickup_req["book_id"], cid=c_id)

                                flash(f"Collection Confirmed! '{b_title}' issued to {b_name}.", "success")

                elif action == "cancel_pickup":
                    res = s.run("""
                        MATCH (r:LoanRequest {request_id: $rid, status: 'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book)
                        MATCH (u:User {user_id: r.borrower_id})
                        RETURN r.copy_id AS copy_id, r.book_id AS book_id,
                               u.username AS borrower_name
                    """, rid=req_id)
                    c_req = res.single()
                    if c_req:
                        s.run("""
                            MATCH (r:LoanRequest {request_id: $rid})
                            OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                            DELETE rel
                            SET r.status = 'Rejected'
                        """, rid=req_id)
                        if c_req["copy_id"]:
                            s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Available'", cid=c_req["copy_id"])
                        else:
                            res2 = s.run("""
                                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy {status:'Reserved'})
                                WHERE NOT (cp)<-[:RESERVED_COPY]-(:LoanRequest)
                                RETURN min(cp.copy_id) AS copy_id
                            """, bid=c_req["book_id"])
                            reserved_cid = (res2.single() or {}).get("copy_id")
                            if reserved_cid:
                                s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Available'", cid=reserved_cid)

                        flash(f"Pickup #{req_id} for '{c_req['borrower_name']}' cancelled.", "info")

                elif action == "reject":
                    res = s.run("""
                        MATCH (r:LoanRequest {request_id: $rid})
                        RETURN r.book_id AS book_id
                    """, rid=req_id)
                    rej_data = res.single()
                    s.run("""
                        MATCH (r:LoanRequest {request_id: $rid})
                        OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                        DELETE rel
                        SET r.status = 'Rejected'
                    """, rid=req_id)

                    if rej_data:
                        r_bid = rej_data["book_id"]
                        # Release one reserved copy if more reserved than awaiting
                        res = s.run("""
                            MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy {status:'Reserved'})
                            RETURN count(cp) AS res_cnt
                        """, bid=r_bid)
                        res_cnt = res.single()["res_cnt"]

                        res = s.run("""
                            MATCH (r2:LoanRequest {status:'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book {book_id: $bid})
                            RETURN count(r2) AS await_cnt
                        """, bid=r_bid)
                        await_cnt = res.single()["await_cnt"]

                        if res_cnt > await_cnt:
                            res3 = s.run("""
                                MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy {status:'Reserved'})
                                WHERE NOT (cp)<-[:RESERVED_COPY]-(:LoanRequest)
                                RETURN cp.copy_id AS copy_id LIMIT 1
                            """, bid=r_bid)
                            rec3 = res3.single()
                            if rec3:
                                s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Available'", cid=rec3["copy_id"])

                    flash(f"Loan Request #{req_id} rejected.", "info")

            # Fetch pending requests
            res = s.run("""
                MATCH (r:LoanRequest {status:'Pending'})-[:FOR_BOOK]->(b:Book)
                MATCH (u:User {user_id: r.borrower_id})
                RETURN r.request_id AS request_id, b.book_id AS book_id,
                       b.title AS book_title, b.isbn AS isbn,
                       r.borrower_id AS borrower_id,
                       u.username AS borrower_name, u.email AS borrower_email,
                       u.role AS borrower_role, r.request_date AS request_date,
                       size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status = 'Available' | cp]) AS available_copies_count,
                       size([(u)-[:BORROWED]->(al:Loan) WHERE al.return_date IS NULL | al]) AS borrower_active_loans,
                       size([(u)-[:REQUESTED]->(ap:LoanRequest {status:'Awaiting Pickup'}) | ap]) AS borrower_awaiting_pickup,
                       size([(u)-[:BORROWED]->(al2:Loan) WHERE al2.return_date IS NULL | al2])
                       + size([(u)-[:REQUESTED]->(ap2:LoanRequest {status:'Awaiting Pickup'}) | ap2]) AS borrower_committed_total,
                       size([(u)-[:BORROWED]->(ol:Loan) WHERE ol.return_date IS NULL AND ol.due_date < $today | ol]) AS borrower_overdue_loans,
                       coalesce(reduce(total=0.0, f IN [(u)-[:BORROWED]->(ol2:Loan)-[:HAS_FINE]->(fin:Fine {payment_status:'Unpaid'}) | fin.fine_amount] | total + f), 0.0) AS borrower_unpaid_fines
                ORDER BY r.request_date ASC
            """, today=today)
            requests_list = rows(res)

            # Fetch awaiting pickup
            res = s.run("""
                MATCH (r:LoanRequest {status:'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book)-[:BELONGS_TO]->(c:Category)
                MATCH (u:User {user_id: r.borrower_id})
                OPTIONAL MATCH (r)-[:RESERVED_COPY]->(rcp:Copy)
                OPTIONAL MATCH (cp_fallback:Copy {copy_id: r.copy_id})
                WITH r, b, c, u, coalesce(rcp, cp_fallback) AS cp
                RETURN r.request_id AS request_id, b.book_id AS book_id,
                       coalesce(cp.copy_id, r.copy_id) AS copy_id, b.title AS book_title,
                       b.isbn AS isbn, c.name AS category_name,
                       cp.condition AS copy_condition,
                       r.borrower_id AS borrower_id,
                       u.username AS borrower_name, u.email AS borrower_email,
                       u.role AS borrower_role, r.request_date AS request_date
                ORDER BY r.request_date ASC
            """)
            awaiting_pickup_list = rows(res)

    except Exception as e:
        flash(f"Error handling loan requests: {str(e)}", "danger")
        requests_list        = []
        awaiting_pickup_list = []

    return render_template("loan_requests.html", requests=requests_list,
                           awaiting_pickup=awaiting_pickup_list)


# ----------------------------------------------------------------------------
# /return_book/<int:loan_id>
# ----------------------------------------------------------------------------
@app.route("/return_book/<int:loan_id>", methods=["POST"])
@login_required
@role_required(["Admin", "Librarian"])
def return_book(loan_id):
    try:
        with get_session() as s:
            res = s.run("""
                MATCH (l:Loan {loan_id: $lid})-[:FOR_COPY]->(cp:Copy)
                RETURN l.copy_id AS copy_id, l.due_date AS due_date,
                       l.return_date AS return_date
            """, lid=loan_id)
            rec = res.single()

            if not rec:
                flash(f"Loan #{loan_id} not found.", "warning")
                return redirect(url_for("dashboard"))

            if rec["return_date"] is not None:
                flash(f"Loan #{loan_id} is already returned.", "info")
                return redirect(url_for("dashboard"))

            return_dt = datetime.now()
            return_str = return_dt.strftime("%Y-%m-%d")
            due_str    = rec["due_date"]

            s.run("""
                MATCH (l:Loan {loan_id: $lid}) SET l.return_date = $rdt
            """, lid=loan_id, rdt=return_str)

            s.run("""
                MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Available'
            """, cid=rec["copy_id"])

            # Calculate overdue fine (Rs. 10/day)
            try:
                due_d    = datetime.strptime(due_str, "%Y-%m-%d")
                ret_d    = return_dt
                days_late = max(0, (ret_d.date() - due_d.date()).days)
                if days_late > 0:
                    fine_amount = days_late * 10.0
                    res_fine = s.run("""
                        MATCH (l:Loan {loan_id: $lid})
                        OPTIONAL MATCH (l)-[:HAS_FINE]->(existing_f:Fine)
                        RETURN existing_f.fine_id AS fine_id, existing_f.payment_status AS payment_status
                    """, lid=loan_id).single()

                    if res_fine and res_fine["fine_id"] is not None:
                        if res_fine["payment_status"] == "Unpaid":
                            s.run("""
                                MATCH (f:Fine {fine_id: $fid})
                                SET f.fine_amount = $amt
                            """, fid=res_fine["fine_id"], amt=fine_amount)
                            flash(f"Loan #{loan_id} returned. Overdue fine updated to Rs. {fine_amount:.2f} ({days_late} day(s) late).", "warning")
                        else:
                            flash(f"Loan #{loan_id} returned. Pre-existing fine is already {res_fine['payment_status']}.", "info")
                    else:
                        new_fid = next_id(s, "Fine", "fine_id")
                        s.run("""
                            MATCH (l:Loan {loan_id: $lid})
                            CREATE (f:Fine {
                                fine_id: $fid, loan_id: $lid,
                                fine_amount: $amt, payment_status: 'Unpaid',
                                payment_date: null, collected_by: null
                            })
                            CREATE (l)-[:HAS_FINE]->(f)
                        """, fid=new_fid, lid=loan_id, amt=fine_amount)
                        flash(f"Loan #{loan_id} returned. Overdue fine of Rs. {fine_amount:.2f} assessed ({days_late} day(s) late).", "warning")
                else:
                    flash(f"Loan #{loan_id} returned successfully. No overdue fine.", "success")
            except Exception:
                flash(f"Loan #{loan_id} returned. Could not calculate fine.", "info")

    except Exception as e:
        flash(f"Error processing book return: {str(e)}", "danger")

    return redirect(url_for("dashboard"))


# ----------------------------------------------------------------------------
# /pay_fine/<int:fine_id>
# ----------------------------------------------------------------------------
@app.route("/pay_fine/<int:fine_id>", methods=["POST"])
@login_required
@role_required(["Admin", "Librarian"])
def pay_fine(fine_id):
    payment_action = request.form.get("payment_action", "Paid").strip()
    if payment_action not in ["Paid", "Waived"]:
        payment_action = "Paid"

    try:
        with get_session() as s:
            res = s.run("""
                MATCH (l:Loan)-[:HAS_FINE]->(f:Fine {fine_id: $fid})
                OPTIONAL MATCH (u:User)-[:BORROWED]->(l)
                RETURN f.fine_id AS fine_id, f.fine_amount AS fine_amount,
                       f.payment_status AS payment_status, coalesce(u.username, 'Deleted Patron') AS username
            """, fid=fine_id)
            fine = res.single()

            if not fine:
                flash(f"Fine #{fine_id} not found.", "warning")
                return redirect(url_for("dashboard"))

            if fine["payment_status"] in ["Paid", "Waived"]:
                flash(f"Fine #{fine_id} was already {fine['payment_status']}.", "info")
                return redirect(url_for("dashboard"))

            pay_date = datetime.now().strftime("%Y-%m-%d")
            s.run("""
                MATCH (f:Fine {fine_id: $fid})
                SET f.payment_status = $action, f.payment_date = $pdate,
                    f.collected_by = $admin_id
            """, fid=fine_id, action=payment_action, pdate=pay_date,
                 admin_id=session.get("user_id"))

            action_desc = "waived" if payment_action == "Waived" else "marked as Paid"
            flash(f"Fine #{fine_id} (Rs. {fine['fine_amount']:.2f}) for '{fine['username']}' {action_desc}!", "success")

    except Exception as e:
        flash(f"Error updating fine: {str(e)}", "danger")

    return redirect(url_for("dashboard"))


# ----------------------------------------------------------------------------
# /delete_loan/<int:loan_id>
# ----------------------------------------------------------------------------
@app.route("/delete_loan/<int:loan_id>", methods=["POST"])
@login_required
@role_required(["Admin", "Librarian"])
def delete_loan(loan_id):
    try:
        with get_session() as s:
            res = s.run("""
                MATCH (l:Loan {loan_id: $lid})-[:FOR_COPY]->(cp:Copy)
                OPTIONAL MATCH (u:User)-[:BORROWED]->(l)
                OPTIONAL MATCH (cp)<-[:HAS_COPY]-(b:Book)
                RETURN l.return_date AS return_date, cp.copy_id AS copy_id,
                       coalesce(u.username, 'Deleted Patron') AS borrower_name, u.user_id AS borrower_id,
                       coalesce(b.title, 'Unknown') AS book_title
            """, lid=loan_id)
            loan = res.single()

            if not loan:
                flash(f"Loan #{loan_id} not found.", "warning")
                return redirect(url_for("dashboard"))

            was_active    = loan["return_date"] is None
            copy_id       = loan["copy_id"]
            borrower_name = loan["borrower_name"]
            book_title    = loan["book_title"]

            # Delete fines then loan
            s.run("""
                MATCH (l:Loan {loan_id: $lid})
                OPTIONAL MATCH (l)-[:HAS_FINE]->(f1:Fine)
                OPTIONAL MATCH (f2:Fine {loan_id: $lid})
                DETACH DELETE f1, f2
            """, lid=loan_id)

            if was_active:
                s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Available'", cid=copy_id)

            s.run("MATCH (l:Loan {loan_id: $lid}) DETACH DELETE l", lid=loan_id)

            if was_active:
                flash(f"Loan #{loan_id} for '{borrower_name}' ('{book_title}') deleted. Copy #{copy_id} restored.", "success")
            else:
                flash(f"Historical loan #{loan_id} for '{borrower_name}' ('{book_title}') deleted.", "success")

    except Exception as e:
        flash(f"Error deleting loan: {str(e)}", "danger")

    return redirect(url_for("dashboard"))


# ----------------------------------------------------------------------------
# /report_lost/<int:loan_id>
# ----------------------------------------------------------------------------
@app.route("/report_lost/<int:loan_id>", methods=["POST"])
@login_required
@role_required(["Admin", "Librarian"])
def report_lost(loan_id):
    try:
        with get_session() as s:
            res = s.run("""
                MATCH (l:Loan {loan_id: $lid})-[:FOR_COPY]->(cp:Copy)
                OPTIONAL MATCH (u:User)-[:BORROWED]->(l)
                OPTIONAL MATCH (cp)<-[:HAS_COPY]-(b:Book)
                RETURN l.return_date AS return_date, cp.copy_id AS copy_id,
                       coalesce(u.username, 'Deleted Patron') AS borrower_name,
                       coalesce(b.title, 'Unknown') AS book_title
            """, lid=loan_id)
            loan = res.single()

            if not loan:
                flash(f"Loan #{loan_id} not found.", "warning")
                return redirect(url_for("dashboard"))

            if loan["return_date"] is not None:
                flash(f"Loan #{loan_id} is already returned/closed. Cannot report lost.", "info")
                return redirect(url_for("dashboard"))

            copy_id       = loan["copy_id"]
            borrower_name = loan["borrower_name"]
            book_title    = loan["book_title"]

            s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Lost'", cid=copy_id)
            s.run("""
                MATCH (l:Loan {loan_id: $lid})
                SET l.return_date = $rdt
            """, lid=loan_id, rdt=datetime.now().strftime("%Y-%m-%d"))

            # Check if loan has pre-existing Unpaid overdue fine node
            res_fine = s.run("""
                MATCH (l:Loan {loan_id: $lid})
                OPTIONAL MATCH (l)-[:HAS_FINE]->(existing_f:Fine)
                RETURN existing_f.fine_id AS fine_id, existing_f.payment_status AS payment_status
            """, lid=loan_id).single()

            if res_fine and res_fine["fine_id"] is not None and res_fine["payment_status"] == "Unpaid":
                s.run("""
                    MATCH (f:Fine {fine_id: $fid})
                    SET f.fine_amount = 1500.0
                """, fid=res_fine["fine_id"])
            else:
                new_fid = next_id(s, "Fine", "fine_id")
                s.run("""
                    MATCH (l:Loan {loan_id: $lid})
                    CREATE (f:Fine {
                        fine_id: $fid, loan_id: $lid,
                        fine_amount: 1500.0, payment_status: 'Unpaid',
                        payment_date: null, collected_by: null
                    })
                    CREATE (l)-[:HAS_FINE]->(f)
                """, fid=new_fid, lid=loan_id)

            flash(f"'{book_title}' (Copy #{copy_id}) marked Lost for '{borrower_name}'. Replacement fine of Rs. 1500.00 assessed.", "warning")

    except Exception as e:
        flash(f"Error recording lost book: {str(e)}", "danger")

    return redirect(url_for("dashboard"))


# ============================================================================
# Task 4 — Graph Collaborative Filtering: Book Recommendations
# ============================================================================
@app.route("/recommendations")
@login_required
def recommendations():
    """
    Graph-based book recommendation using multi-hop Cypher traversal.
    For Student/Staff: Personal collaborative filtering based on personal borrowing history.
    For Admin/Librarian: Global Patron Collaborative Filtering Network showcasing peer borrowing clusters.
    """
    role = session.get("role")
    user_id = session.get("user_id")
    is_admin_view = role in ["Admin", "Librarian"]
    recs = []

    try:
        with get_session() as s:
            if is_admin_view:
                # Global Peer Borrowing Clusters across all students and patrons
                res = s.run("""
                    MATCH (u1:User)-[:BORROWED]->(l1:Loan)-[:FOR_COPY]->(cp1:Copy)<-[:HAS_COPY]-(b1:Book)-[:BELONGS_TO]->(cat:Category)
                    MATCH (u2:User)-[:BORROWED]->(l2:Loan)-[:FOR_COPY]->(cp2:Copy)<-[:HAS_COPY]-(b2:Book)-[:BELONGS_TO]->(cat)
                    WHERE u1.user_id <> u2.user_id AND b1.book_id <> b2.book_id AND u1.role IN ['Student', 'Staff'] AND u2.role IN ['Student', 'Staff']
                    WITH b2, count(DISTINCT u2) AS mutual_borrowers, collect(DISTINCT cat.name)[0] AS category_name
                    OPTIONAL MATCH (a:Author)-[:WROTE]->(b2)
                    WITH b2, mutual_borrowers, category_name, collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                    RETURN b2.book_id AS book_id, b2.title AS title,
                           b2.isbn AS isbn, category_name,
                           reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                           mutual_borrowers,
                           size([(b2)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies
                    ORDER BY mutual_borrowers DESC, b2.title ASC
                    LIMIT 6
                """)
                recs = [dict(r) for r in res]

                # Fallback: top circulated books
                if not recs:
                    res = s.run("""
                        MATCH (u:User)-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                        WITH b, count(DISTINCT u) AS borrow_count
                        OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                        OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                        WITH b, borrow_count, cat,
                             collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                        RETURN b.book_id AS book_id, b.title AS title,
                               b.isbn AS isbn, cat.name AS category_name,
                               reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                               borrow_count AS mutual_borrowers,
                               size([(b)-[:HAS_COPY]->(cp2:Copy {status:'Available'}) | cp2]) AS available_copies
                        ORDER BY borrow_count DESC, b.title ASC
                        LIMIT 6
                    """)
                    recs = [dict(r) for r in res]
            else:
                # Personal collaborative filtering for Student/Staff (strictly matches users within the same role)
                res = s.run("""
                    MATCH (me:User {user_id: $uid})-[:BORROWED]->(l1:Loan)-[:FOR_COPY]->(cp1:Copy)<-[:HAS_COPY]-(b1:Book)-[:BELONGS_TO]->(cat:Category)
                    MATCH (other:User)-[:BORROWED]->(l2:Loan)-[:FOR_COPY]->(cp2:Copy)<-[:HAS_COPY]-(b2:Book)-[:BELONGS_TO]->(cat)
                    WHERE other.user_id <> $uid AND other.role = me.role
                      AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2)
                      AND NOT (me)-[:REQUESTED]->(:LoanRequest)-[:FOR_BOOK]->(b2)
                    WITH b2, count(DISTINCT other) AS mutual_borrowers,
                         collect(DISTINCT cat.name)[0] AS category_name
                    OPTIONAL MATCH (a:Author)-[:WROTE]->(b2)
                    WITH b2, mutual_borrowers, category_name,
                         collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                    RETURN b2.book_id AS book_id, b2.title AS title,
                           b2.isbn AS isbn, category_name,
                           reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                           mutual_borrowers,
                           size([(b2)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies
                    ORDER BY mutual_borrowers DESC, b2.title ASC
                    LIMIT 6
                """, uid=user_id)
                recs = [dict(r) for r in res]

                # Graph-content traversal fallback for Staff when peer count is 0:
                # Traverse shared Categories, Authors, and Prerequisite chains without mixing in student peers
                if not recs and role == "Staff":
                    res = s.run("""
                        MATCH (u:User {user_id: $uid})-[:BORROWED|REQUESTED]->()-[:FOR_COPY|FOR_BOOK]->()-[:HAS_COPY*0..1]-(b:Book)
                        MATCH (b)-[:BELONGS_TO|WROTE|PREREQUISITE_FOR*1..2]-(rec:Book)
                        WHERE rec.book_id <> b.book_id
                          AND NOT (u)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(rec)
                          AND NOT (u)-[:REQUESTED]->(:LoanRequest)-[:FOR_BOOK]->(rec)
                        WITH rec, count(DISTINCT b) AS shared_connections
                        OPTIONAL MATCH (cat:Category)<-[:BELONGS_TO]-(rec)
                        OPTIONAL MATCH (a:Author)-[:WROTE]->(rec)
                        WITH rec, shared_connections, collect(DISTINCT cat.name)[0] AS category_name,
                             collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list,
                             size([(rec)<-[:HAS_COPY]-(:Copy)<-[:FOR_COPY]-(:Loan)<-[:BORROWED]-(st:User {role: 'Staff'}) WHERE st.user_id <> $uid | st]) AS staff_readers
                        RETURN rec.book_id AS book_id, rec.title AS title,
                               rec.isbn AS isbn, category_name,
                               reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                               staff_readers AS mutual_borrowers,
                               CASE WHEN staff_readers > 0 THEN NULL ELSE 'Curriculum Match' END AS badge_label,
                               size([(rec)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies
                        ORDER BY shared_connections DESC, rec.title ASC
                        LIMIT 6
                    """, uid=user_id)
                    recs = [dict(r) for r in res]

                # Fallback: most circulated books the user hasn't read (isolated for Staff)
                if not recs:
                    if role == "Staff":
                        res = s.run("""
                            MATCH (b:Book)<-[:HAS_COPY]-(cp:Copy)<-[:FOR_COPY]-(l:Loan)
                            WHERE NOT (b)<-[:FOR_BOOK]-(:LoanRequest)<-[:REQUESTED]-(:User {user_id: $uid})
                              AND NOT (b)<-[:HAS_COPY]-(:Copy)<-[:FOR_COPY]-(:Loan)<-[:BORROWED]-(:User {user_id: $uid})
                            WITH b, size([(b)<-[:HAS_COPY]-(:Copy)<-[:FOR_COPY]-(:Loan)<-[:BORROWED]-(st:User {role: 'Staff'}) WHERE st.user_id <> $uid | st]) AS staff_readers
                            OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                            OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                            WITH b, staff_readers, cat,
                                 collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                            RETURN b.book_id AS book_id, b.title AS title,
                                   b.isbn AS isbn, cat.name AS category_name,
                                   reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                                   staff_readers AS mutual_borrowers,
                                   CASE WHEN staff_readers > 0 THEN NULL ELSE 'Curriculum Match' END AS badge_label,
                                   size([(b)-[:HAS_COPY]->(cp2:Copy {status:'Available'}) | cp2]) AS available_copies
                            ORDER BY staff_readers DESC, b.title ASC
                            LIMIT 6
                        """, uid=user_id)
                    else:
                        res = s.run("""
                            MATCH (u:User)-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy)<-[:HAS_COPY]-(b:Book)
                            WHERE NOT (b)<-[:FOR_BOOK]-(:LoanRequest)<-[:REQUESTED]-(:User {user_id: $uid})
                              AND NOT (b)<-[:HAS_COPY]-(:Copy)<-[:FOR_COPY]-(:Loan)<-[:BORROWED]-(:User {user_id: $uid})
                            WITH b, count(DISTINCT u) AS borrow_count
                            OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                            OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                            WITH b, borrow_count, cat,
                                 collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                            RETURN b.book_id AS book_id, b.title AS title,
                                   b.isbn AS isbn, cat.name AS category_name,
                                   reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                                   borrow_count AS mutual_borrowers,
                                   size([(b)-[:HAS_COPY]->(cp2:Copy {status:'Available'}) | cp2]) AS available_copies
                            ORDER BY borrow_count DESC, b.title ASC
                            LIMIT 6
                        """, uid=user_id)
                    recs = [dict(r) for r in res]

            # -------------------------------------------------------------
            # Role-Scoped Jaccard Similarity "Study Partner" Matchmaker
            # -------------------------------------------------------------
            study_partners = []
            if role == "Student" and user_id:
                # Student view: Personalized peer study partners based STRICTLY on actual borrowed books
                j_res = s.run("""
                    MATCH (u1:User {user_id: $uid})-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b:Book)
                    WITH u1, collect(DISTINCT b) AS u1_books
                    MATCH (u2:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2:Book)
                    WHERE u2.user_id <> u1.user_id AND u2.role = 'Student'
                    WITH u1_books, u2, collect(DISTINCT b2) AS u2_books
                    WITH u2, [x IN u1_books WHERE x IN u2_books] AS shared, u1_books + [x IN u2_books WHERE NOT x IN u1_books] AS union_books
                    WHERE size(shared) > 0
                    RETURN u2.username AS peer_name, size(shared) AS shared_count, round(toFloat(size(shared)) / size(union_books) * 100, 1) AS jaccard_pct, [b IN shared | b.title] AS shared_titles
                    ORDER BY jaccard_pct DESC LIMIT 5
                """, uid=user_id)
                study_partners = rows(j_res)
            elif role in ["Admin", "Librarian"]:
                # Admin / Librarian view: Global Student Cohort Study Pairs based STRICTLY on actual borrowed books
                gj_res = s.run("""
                    MATCH (u1:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b:Book)
                    WHERE u1.role = 'Student'
                    WITH u1, collect(DISTINCT b) AS u1_books
                    MATCH (u2:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2:Book)
                    WHERE u1.user_id < u2.user_id AND u2.role = 'Student'
                    WITH u1, u1_books, u2, collect(DISTINCT b2) AS u2_books
                    WITH u1, u2, [x IN u1_books WHERE x IN u2_books] AS shared, u1_books + [x IN u2_books WHERE NOT x IN u1_books] AS union_books
                    WHERE size(shared) > 0
                    RETURN u1.username + ' & ' + u2.username AS peer_name, size(shared) AS shared_count, round(toFloat(size(shared)) / size(union_books) * 100, 1) AS jaccard_pct, [b IN shared | b.title] AS shared_titles
                    ORDER BY jaccard_pct DESC, shared_count DESC LIMIT 5
                """)
                study_partners = rows(gj_res)
            # For Staff (Faculty): study_partners remains empty [] as faculty members only need book recommendations

    except Exception as e:
        flash(f"Error loading recommendations: {str(e)}", "danger")

    return render_template(
        "recommendations.html",
        recommendations=recs,
        study_partners=study_partners,
        is_admin_view=is_admin_view,
        admin_banner=f"{role} View: Global Patron Collaborative Filtering Network" if is_admin_view else None
    )


# ============================================================================
# Task 5 — Interactive Graph Visualizer & Graph API (Vis.js Network)
# ============================================================================
def serialize_graph_val(v):
    """Safely converts Neo4j data types into JSON-serializable primitives."""
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if hasattr(v, "iso_format"):
        return v.iso_format()
    if hasattr(v, "to_native"):
        native = v.to_native()
        if hasattr(native, "isoformat"):
            return native.isoformat()
        return str(native)
    if isinstance(v, (int, float, bool, str)):
        return v
    return str(v)


def format_graph_node(n, custom_group=None, custom_label=None):
    """Formats a Neo4j node into a Vis.js Network node structure."""
    labels = list(n.labels) if hasattr(n, "labels") else []
    primary_label = custom_group or (labels[0] if labels else "Node")
    raw_props = dict(n) if hasattr(n, "items") else {}
    props = {k: serialize_graph_val(v) for k, v in raw_props.items() if k != "password_hash"}

    if custom_label:
        display_label = custom_label
    elif primary_label == "Book":
        title = props.get("title", f"Book #{props.get('book_id')}")
        display_label = title if len(title) <= 24 else title[:22] + "..."
    elif primary_label == "User":
        display_label = f"{props.get('username')} ({props.get('role', 'User')})"
    elif primary_label == "Author":
        display_label = f"{props.get('first_name', '')} {props.get('last_name', '')}".strip()
    elif primary_label == "Category":
        display_label = f"{props.get('name', 'Category')}"
    elif primary_label == "Publisher":
        display_label = f"{props.get('name', 'Publisher')}"
    elif primary_label == "Copy":
        display_label = f"Copy #{props.get('copy_id')} [{props.get('status', 'Available')}]"
    elif primary_label == "Loan":
        ret_date = props.get("return_date")
        loan_status = "Returned" if (ret_date is not None and str(ret_date).strip() not in ["", "None", "null"]) else props.get("status", "Active")
        display_label = f"Loan #{props.get('loan_id')} [{loan_status}]"
    elif primary_label == "Fine":
        display_label = f"Fine #{props.get('fine_id')}: Rs.{props.get('fine_amount', 0)}"
    elif primary_label == "LoanRequest":
        display_label = f"Req #{props.get('request_id')} [{props.get('status', 'Pending')}]"
    else:
        display_label = f"{primary_label}"

    tooltip_rows = [f"<b>{html.escape(str(k))}:</b> {html.escape(str(v))}" for k, v in list(props.items())[:6]]
    tooltip = f"<div style='font-family:sans-serif;'><b>{html.escape(str(primary_label))}</b><br/>" + "<br/>".join(tooltip_rows) + "</div>"

    return {
        "id": n.element_id,
        "label": display_label,
        "group": primary_label,
        "title": tooltip,
        "properties": props
    }


def format_graph_edge(r, from_id, to_id, custom_label=None, is_dashed=False):
    """Formats a Neo4j relationship into a Vis.js Network edge structure."""
    edge_id = r.element_id if hasattr(r, "element_id") else f"e_{from_id}_{to_id}_{custom_label or 'REL'}"
    rel_type = custom_label or (r.type if hasattr(r, "type") else "RELATED_TO")
    raw_props = dict(r) if hasattr(r, "items") else {}
    props = {k: serialize_graph_val(v) for k, v in raw_props.items()}

    edge_dict = {
        "id": edge_id,
        "from": from_id,
        "to": to_id,
        "label": rel_type,
        "title": f":{rel_type}" + (f" ({props})" if props else ""),
        "arrows": "to"
    }
    if is_dashed:
        edge_dict["dashes"] = True
        edge_dict["width"] = 2
    return edge_dict


@app.route("/graph_visualizer")
@login_required
def graph_visualizer():
    """
    Renders the interactive Graph Visualizer canvas powered by Vis-Network.
    Allows dynamic exploration of knowledge graph entities and borrowing subgraphs.
    """
    return render_template(
        "graph_visualizer.html",
        user_role=session.get("role", "Student"),
        username=session.get("username", "User"),
        user_id=session.get("user_id")
    )


@app.route("/api/graph_data")
@login_required
def api_graph_data():
    """
    REST API returning graph nodes and edges for Vis-Network visualization.
    Supports filtering by view ('personal', 'catalog', 'full', 'recommendations').
    """
    user_id = session.get("user_id")
    user_role = session.get("role", "Student")

    default_view = "full" if user_role in ["Admin", "Librarian"] else "personal"
    view = request.args.get("view", default_view).strip().lower()

    # Enforce role-based view boundary: regular students/staff can view personal or catalog graphs
    if user_role in ["Student", "Staff"] and view == "full":
        view = "catalog"

    nodes = {}
    edges = []

    try:
        with get_session() as s:
            sync_fulfilled_loan_requests(s)

            if view in ["personal", "circulation", "borrowing"]:
                if user_role in ["Admin", "Librarian"] or view == "circulation":
                    # Global Circulation & Fines Subgraph across the entire library
                    # Strictly return only circulation and financial nodes:
                    # User (only users who have loans/requests/fines), Loan, Fine, LoanRequest (status IN ['Pending', 'Awaiting Pickup']),
                    # Copy (only copies linked to loans), and Book (only books linked to those copies/requests).
                    # Completely exclude Author, Category, and Publisher nodes.
                    circ_res = s.run("""
                        MATCH (u:User)-[r1:BORROWED]->(l:Loan)-[r2:FOR_COPY]->(cp:Copy)<-[r3:HAS_COPY]-(b:Book)
                        OPTIONAL MATCH (l)-[r4:HAS_FINE]->(f:Fine)
                        RETURN u, l, cp, b, f, r1, r2, r3, r4
                        LIMIT 300
                    """)
                    for rec in circ_res:
                        for node_key in ["u", "l", "cp", "b", "f"]:
                            item = rec[node_key]
                            if item is not None and item.element_id not in nodes:
                                nodes[item.element_id] = format_graph_node(item)
                        for r_key in ["r1", "r2", "r3", "r4"]:
                            r = rec[r_key]
                            if r is not None and r.element_id not in [e["id"] for e in edges]:
                                edges.append(format_graph_edge(r, r.start_node.element_id, r.end_node.element_id))

                    req_res = s.run("""
                        MATCH (u:User)-[r1:REQUESTED]->(lr:LoanRequest)-[r2:FOR_BOOK]->(b:Book)
                        WHERE lr.status IN ['Pending', 'Awaiting Pickup']
                        RETURN u, lr, b, r1, r2
                        LIMIT 150
                    """)
                    for rec in req_res:
                        for node_key in ["u", "lr", "b"]:
                            item = rec[node_key]
                            if item is not None and item.element_id not in nodes:
                                nodes[item.element_id] = format_graph_node(item)
                        for r_key in ["r1", "r2"]:
                            r = rec[r_key]
                            if r is not None and r.element_id not in [e["id"] for e in edges]:
                                edges.append(format_graph_edge(r, r.start_node.element_id, r.end_node.element_id))
                else:
                    # Student & Staff personal borrowing graph: You, Active Loans, Fines, Active Requests, Copies, and Books.
                    # Filter out historical returned loans (WHERE l.return_date IS NULL) so personal view reflects active loans without conflict.
                    res = s.run("""
                        MATCH (u:User {user_id: $uid})
                        OPTIONAL MATCH (u)-[r1:BORROWED]->(l:Loan)
                        WHERE l.return_date IS NULL
                        OPTIONAL MATCH (l)-[r2:FOR_COPY]->(cp:Copy)
                        OPTIONAL MATCH (b1:Book)-[r3:HAS_COPY]->(cp)
                        OPTIONAL MATCH (u)-[r_all:BORROWED]->(all_l:Loan)-[r4:HAS_FINE]->(f:Fine)
                        WHERE f.payment_status = 'Unpaid' OR l.loan_id = all_l.loan_id
                        OPTIONAL MATCH (all_l)-[r_cp:FOR_COPY]->(f_cp:Copy)<-[r_bk:HAS_COPY]-(f_b:Book)
                        OPTIONAL MATCH (u)-[r5:REQUESTED]->(lr:LoanRequest)
                        WHERE lr.status IN ['Pending', 'Awaiting Pickup']
                        OPTIONAL MATCH (lr)-[r6:FOR_BOOK]->(b2:Book)
                        RETURN u, l, cp, b1, all_l, f_cp, f_b, f, lr, b2,
                               r1, r2, r3, r_all, r_cp, r_bk, r4, r5, r6
                    """, uid=user_id)
                    for rec in res:
                        u = rec["u"]
                        if u is not None and u.element_id not in nodes:
                            nodes[u.element_id] = format_graph_node(u, custom_label=f"⭐ You ({u.get('username')})", custom_group="User")
                        for node_key in ["l", "cp", "b1", "all_l", "f_cp", "f_b", "f", "lr", "b2"]:
                            item = rec[node_key]
                            if item is not None and item.element_id not in nodes:
                                nodes[item.element_id] = format_graph_node(item)
                        for r_key in ["r1", "r2", "r3", "r_all", "r_cp", "r_bk", "r4", "r5", "r6"]:
                            r = rec[r_key]
                            if r is not None and r.element_id not in [e["id"] for e in edges]:
                                edges.append(format_graph_edge(r, r.start_node.element_id, r.end_node.element_id))

            elif view == "catalog":
                # Catalog Knowledge Graph (Books, Categories, Authors, Publishers, Copies)
                res = s.run("""
                    MATCH (b:Book)
                    OPTIONAL MATCH (b)-[r1:BELONGS_TO]->(cat:Category)
                    OPTIONAL MATCH (a:Author)-[r2:WROTE]->(b)
                    OPTIONAL MATCH (b)-[r3:PUBLISHED_BY]->(p:Publisher)
                    OPTIONAL MATCH (b)-[r4:HAS_COPY]->(cp:Copy)
                    RETURN b, cat, a, p, cp, r1, r2, r3, r4
                    LIMIT 200
                """)
                for rec in res:
                    for node_key in ["b", "cat", "a", "p", "cp"]:
                        item = rec[node_key]
                        if item is not None and item.element_id not in nodes:
                            nodes[item.element_id] = format_graph_node(item)
                    for r_key in ["r1", "r2", "r3", "r4"]:
                        r = rec[r_key]
                        if r is not None and r.element_id not in [e["id"] for e in edges]:
                            edges.append(format_graph_edge(r, r.start_node.element_id, r.end_node.element_id))

            elif view == "recommendations":
                target_uid = user_id
                is_admin_librarian = user_role in ["Admin", "Librarian"]
                target_label = f"You ({session.get('username', 'User')})"

                if is_admin_librarian:
                    # Preview top active student borrower's collaborative path for Admin/Librarian
                    top_user = s.run("""
                        MATCH (u:User {role: 'Student'})-[:BORROWED]->(l:Loan)
                        RETURN u.user_id AS uid, u.username AS username, count(l) AS c
                        ORDER BY c DESC LIMIT 1
                    """).single()
                    if top_user:
                        target_uid = top_user["uid"]
                        target_label = f"Active Patron ({top_user['username']})"
                    else:
                        target_label = "Active Patron"

                # Multi-hop Collaborative Filtering Path (strictly matches same role)
                res = s.run("""
                    MATCH (me:User {user_id: $uid})-[:BORROWED]->(l1:Loan)-[:FOR_COPY]->(cp1:Copy)<-[:HAS_COPY]-(b1:Book)-[:BELONGS_TO]->(cat:Category)
                    MATCH (other:User)-[:BORROWED]->(l2:Loan)-[:FOR_COPY]->(cp2:Copy)<-[:HAS_COPY]-(b2:Book)-[:BELONGS_TO]->(cat)
                    WHERE other.user_id <> $uid AND other.role = me.role
                      AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2)
                    RETURN me, b1, other, b2, cat
                    LIMIT 15
                """, uid=target_uid)
                recs_found = False

                def add_synth_edge(from_id, to_id, label):
                    eid = f"rec_{from_id}_{to_id}_{label}"
                    if eid not in [e["id"] for e in edges]:
                        edges.append({
                            "id": eid, "from": from_id, "to": to_id, "label": label,
                            "title": label, "arrows": "to",
                            "font": {"size": 10, "align": "middle", "background": "#0f172a", "color": "#94A3B8"}
                        })

                for rec in res:
                    recs_found = True
                    me = rec["me"]
                    b1 = rec["b1"]
                    other = rec["other"]
                    b2 = rec["b2"]
                    cat = rec["cat"]

                    # Level 0 (Column 1 - Left): You / Active Patron
                    if me.element_id not in nodes:
                        n = format_graph_node(me, custom_label=f"⭐ {target_label}", custom_group="CurrentUser")
                        n["level"] = 0
                        nodes[me.element_id] = n

                    # Level 1 (Column 2 - Center-Left): Your Read Books / Shared Categories
                    if b1.element_id not in nodes:
                        n = format_graph_node(b1, custom_label=f"📖 Read:\n{b1.get('title')}", custom_group="SharedBook")
                        n["level"] = 1
                        nodes[b1.element_id] = n
                    if cat and cat.element_id not in nodes:
                        n = format_graph_node(cat, custom_label=f"📁 Category:\n{cat.get('name')}", custom_group="Category")
                        n["level"] = 1
                        nodes[cat.element_id] = n

                    # Level 2 (Column 3 - Center-Right): Peer Readers
                    if other.element_id not in nodes:
                        n = format_graph_node(other, custom_label=f"👥 Peer:\n{other.get('username')}", custom_group="PeerUser")
                        n["level"] = 2
                        nodes[other.element_id] = n

                    # Level 3 (Column 4 - Right): Recommended Books
                    if b2.element_id not in nodes:
                        n = format_graph_node(b2, custom_label=f"✨ Recommended:\n{b2.get('title')}", custom_group="RecommendedBook")
                        n["level"] = 3
                        nodes[b2.element_id] = n

                    # Sequential multi-hop flow: Level 0 -> Level 1 -> Level 2 -> Level 3
                    add_synth_edge(me.element_id, b1.element_id, "borrowed")
                    add_synth_edge(b1.element_id, other.element_id, "shared")
                    if cat:
                        add_synth_edge(me.element_id, cat.element_id, "shared")
                        add_synth_edge(cat.element_id, other.element_id, "shared")
                    add_synth_edge(other.element_id, b2.element_id, "recommends")

                if not recs_found:
                    if user_role == "Staff":
                        # Graph-content traversal fallback for Staff without peer matches:
                        # (You) -> [:borrowed] -> (Borrowed Book) -> [:shared] -> (Shared Category/Author/Prerequisite) -> [:recommends] -> (Recommended Book)
                        staff_fallback_res = s.run("""
                            MATCH (me:User {user_id: $uid})-[:BORROWED|REQUESTED]->()-[:FOR_COPY|FOR_BOOK]->()-[:HAS_COPY*0..1]-(b1:Book)
                            MATCH path = (b1)-[r:BELONGS_TO|WROTE|PREREQUISITE_FOR*1..2]-(rec:Book)
                            WHERE rec.book_id <> b1.book_id
                              AND NOT (me)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(rec)
                              AND NOT (me)-[:REQUESTED]->(:LoanRequest)-[:FOR_BOOK]->(rec)
                            RETURN me, b1, nodes(path) AS p_nodes, relationships(path) AS p_rels, rec
                            LIMIT 15
                        """, uid=target_uid)
                        for row in staff_fallback_res:
                            me = row["me"]
                            b1 = row["b1"]
                            rec = row["rec"]
                            p_nodes = row["p_nodes"]
                            p_rels = row["p_rels"]

                            # Level 0 (Column 1 - Left): You
                            if me.element_id not in nodes:
                                n = format_graph_node(me, custom_label=f"⭐ {target_label}", custom_group="CurrentUser")
                                n["level"] = 0
                                nodes[me.element_id] = n

                            # Level 1 (Column 2 - Center-Left): Borrowed Book
                            if b1.element_id not in nodes:
                                n = format_graph_node(b1, custom_label=f"📖 Borrowed:\n{b1.get('title')}", custom_group="SharedBook")
                                n["level"] = 1
                                nodes[b1.element_id] = n

                            add_synth_edge(me.element_id, b1.element_id, "borrowed")

                            # Level 2 (Column 3 - Center-Right): Shared Category / Author / Prerequisite
                            inter_id = None
                            if len(p_nodes) == 3:
                                inter = p_nodes[1]
                                inter_id = inter.element_id
                                if inter_id not in nodes:
                                    labels = list(inter.labels)
                                    if "Category" in labels:
                                        n = format_graph_node(inter, custom_label=f"📁 Category:\n{inter.get('name')}", custom_group="Category")
                                    elif "Author" in labels:
                                        n = format_graph_node(inter, custom_label=f"✍️ Author:\n{inter.get('first_name', '')} {inter.get('last_name', '')}", custom_group="Author")
                                    else:
                                        n = format_graph_node(inter, custom_label=f"🔗 Prerequisite:\n{inter.get('title')}", custom_group="Prerequisite")
                                    n["level"] = 2
                                    nodes[inter_id] = n
                                add_synth_edge(b1.element_id, inter_id, "shared")
                            else:
                                rel_type = p_rels[0].type if p_rels else "PREREQUISITE_FOR"
                                synth_node_id = f"synth_prereq_{b1.element_id}_{rec.element_id}"
                                if synth_node_id not in nodes:
                                    nodes[synth_node_id] = {
                                        "id": synth_node_id,
                                        "label": "🔗 Prerequisite\nPathway",
                                        "group": "Prerequisite",
                                        "level": 2,
                                        "title": "Prerequisite Academic Pathway"
                                    }
                                inter_id = synth_node_id
                                add_synth_edge(b1.element_id, inter_id, "requires" if rel_type == "PREREQUISITE_FOR" else "shared")

                            # Level 3 (Column 4 - Right): Recommended Book
                            if rec.element_id not in nodes:
                                n = format_graph_node(rec, custom_label=f"✨ Recommended:\n{rec.get('title')}", custom_group="RecommendedBook")
                                n["level"] = 3
                                nodes[rec.element_id] = n

                            if inter_id:
                                add_synth_edge(inter_id, rec.element_id, "recommends")
                    else:
                        # Fallback graph for users with no loan history yet
                        fallback_res = s.run("""
                            MATCH (me:User {user_id: $uid})
                            MATCH (b:Book)<-[:HAS_COPY]-(cp:Copy)<-[:FOR_COPY]-(l:Loan)<-[:BORROWED]-(other:User {role: 'Student'})
                            OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                            RETURN me, b, other, cat, count(l) as borrow_count
                            ORDER BY borrow_count DESC
                            LIMIT 6
                        """, uid=target_uid)
                        for rec in fallback_res:
                            me = rec["me"]
                            b = rec["b"]
                            other = rec["other"]
                            cat = rec["cat"]
                            if me.element_id not in nodes:
                                n = format_graph_node(me, custom_label=f"⭐ {target_label}", custom_group="CurrentUser")
                                n["level"] = 0
                                nodes[me.element_id] = n
                            if cat and cat.element_id not in nodes:
                                n = format_graph_node(cat, custom_label=f"📁 Category:\n{cat.get('name')}", custom_group="Category")
                                n["level"] = 1
                                nodes[cat.element_id] = n
                            if other and other.element_id not in nodes:
                                n = format_graph_node(other, custom_label=f"👥 Peer:\n{other.get('username')}", custom_group="PeerUser")
                                n["level"] = 2
                                nodes[other.element_id] = n
                            if b.element_id not in nodes:
                                n = format_graph_node(b, custom_label=f"✨ Recommended:\n{b.get('title')}", custom_group="RecommendedBook")
                                n["level"] = 3
                                nodes[b.element_id] = n

                            if cat:
                                add_synth_edge(me.element_id, cat.element_id, "shared")
                                if other:
                                    add_synth_edge(cat.element_id, other.element_id, "shared")
                            if other:
                                add_synth_edge(other.element_id, b.element_id, "recommends")

            else:
                # Full system graph (Admin / Librarian)
                res = s.run("""
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN n, r, m
                """)
                for rec in res:
                    n = rec["n"]
                    m = rec["m"]
                    r = rec["r"]
                    if n is not None and n.element_id not in nodes:
                        nodes[n.element_id] = format_graph_node(n)
                    if m is not None and m.element_id not in nodes:
                        nodes[m.element_id] = format_graph_node(m)
                    if r is not None and r.element_id not in [e["id"] for e in edges]:
                        edges.append(format_graph_edge(r, n.element_id, m.element_id))

    except Exception as e:
        return jsonify({"error": str(e), "nodes": [], "edges": [], "stats": {}}), 500

    # Build group statistics
    counts = {}
    for node in nodes.values():
        grp = node.get("group", "Other")
        counts[grp] = counts.get(grp, 0) + 1

    return jsonify({
        "nodes": list(nodes.values()),
        "edges": edges,
        "view": view,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "counts": counts
        }
    })



# ============================================================================
# Task 6 — The "Book-to-Book Bridge" Shortest Path Route (/book_bridge)
# ============================================================================
def format_bridge_node(n, idx, total_nodes, user_role):
    """
    Formats a graph node for the Book-to-Book Bridge with role-based privacy masking.
    If the path traverses :User or :Loan nodes and the user is a Student or Staff,
    masks identities as 'Anonymous Reader' and 'Circulation Link' to protect patron privacy.
    Admins and Librarians view full patron usernames and loan details.
    """
    labels = list(n.labels) if hasattr(n, "labels") else []
    primary_label = labels[0] if labels else "Node"
    is_privacy_masked = user_role in ["Student", "Staff"]

    custom_grp = None
    custom_lbl = None
    if idx == 0:
        custom_grp = "StartBook"
        custom_lbl = f"⭐ Origin: {n.get('title', '')[:22]}"
    elif idx == total_nodes - 1:
        custom_grp = "TargetBook"
        custom_lbl = f"🎯 Destination: {n.get('title', '')[:22]}"
    elif "Book" in labels:
        custom_grp = "IntermediateBook"
        book_title = n.get("title", "")
        short_title = book_title if len(book_title) <= 22 else book_title[:20] + "..."
        custom_lbl = f"📖 {short_title}"

    if is_privacy_masked and "User" in labels:
        node_dict = {
            "id": n.element_id,
            "label": "Anonymous Reader",
            "group": "User",
            "title": "<div style='font-family:sans-serif;'><b>Anonymous Reader</b><br/>Privacy Masked: Patron Identity Hidden</div>",
            "properties": {"role": "Reader", "status": "Anonymous Reader"}
        }
        step_item = {"step": idx + 1, "type": "User", "name": "Anonymous Reader"}
        return node_dict, step_item
    elif is_privacy_masked and "Loan" in labels:
        node_dict = {
            "id": n.element_id,
            "label": "Circulation Link",
            "group": "Loan",
            "title": "<div style='font-family:sans-serif;'><b>Circulation Link</b><br/>Confidential Circulation Record</div>",
            "properties": {"status": "Circulation Link"}
        }
        step_item = {"step": idx + 1, "type": "Loan", "name": "Circulation Link"}
        return node_dict, step_item
    elif is_privacy_masked and "LoanRequest" in labels:
        node_dict = {
            "id": n.element_id,
            "label": "Circulation Request",
            "group": "LoanRequest",
            "title": "<div style='font-family:sans-serif;'><b>Circulation Request</b><br/>Confidential Request Record</div>",
            "properties": {"status": "Circulation Request"}
        }
        step_item = {"step": idx + 1, "type": "LoanRequest", "name": "Circulation Request"}
        return node_dict, step_item
    else:
        node_dict = format_graph_node(n, custom_group=custom_grp, custom_label=custom_lbl)
        item_name = n.get("title") or n.get("name") or n.get("username") or f"{primary_label} #{n.get('book_id', n.get('copy_id', n.get('loan_id', '')))}"
        step_type = "Intermediate Book" if custom_grp == "IntermediateBook" else primary_label
        step_item = {"step": idx + 1, "type": step_type, "name": item_name}
        return node_dict, step_item


@app.route("/book_bridge", methods=["GET", "POST"])
@login_required
def book_bridge():
    """
    Renders and executes the 'Book-to-Book Bridge' shortest path traversal.
    Calculates degrees of separation connecting two library volumes using Neo4j shortestPath().
    """
    book_a_id = request.values.get("book_a", type=int)
    book_b_id = request.values.get("book_b", type=int)

    all_books = []
    path_nodes = []
    path_edges = []
    path_steps = []
    degrees_of_separation = 0
    path_found = False
    error_msg = None

    try:
        with get_session() as s:
            # Fetch all books for dropdown selection
            books_res = s.run("""
                MATCH (b:Book)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                       cat.name AS category_name,
                       collect(DISTINCT a.first_name + ' ' + a.last_name) AS authors
                ORDER BY b.title ASC
            """)
            raw_books = rows(books_res)
            all_books = []
            for rb in raw_books:
                auth_list = [a for a in rb.get("authors", []) if a and a.strip()]
                rb["author_name"] = ", ".join(auth_list) if auth_list else "Author"
                all_books.append(rb)

            # Default to first and fifth book if none specified
            if not book_a_id and not book_b_id and len(all_books) >= 2:
                book_a_id = all_books[0]["book_id"]
                book_b_id = all_books[4]["book_id"] if len(all_books) > 4 else all_books[1]["book_id"]

            if book_a_id and book_b_id:
                if book_a_id == book_b_id:
                    error_msg = "Please select two different books to calculate the shortest path bridge."
                else:
                    # 1. Primary shortest path across metadata and prerequisite learning hierarchy
                    res = s.run("""
                        MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PUBLISHED_BY|PREREQUISITE_FOR*1..5]-(b2:Book {book_id: $id2}))
                        RETURN p
                    """, id1=book_a_id, id2=book_b_id)
                    rec = res.single()

                    # 2. Resilient multi-hop fallback across readers/copies if cross-domain
                    if not (rec and rec["p"]):
                        res = s.run("""
                            MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|PUBLISHED_BY|HAS_COPY|FOR_COPY|BORROWED|FOR_BOOK*1..10]-(b2:Book {book_id: $id2}))
                            RETURN p
                        """, id1=book_a_id, id2=book_b_id)
                        rec = res.single()

                    if rec and rec["p"]:
                        path = rec["p"]
                        path_found = True
                        degrees_of_separation = len(path.relationships)

                        # Format nodes with role-based privacy masking
                        user_role = session.get("role") or session.get("Role")
                        total_nodes = len(path.nodes)
                        for idx, n in enumerate(path.nodes):
                            f_node, step_item = format_bridge_node(n, idx, total_nodes, user_role)
                            path_nodes.append(f_node)
                            path_steps.append(step_item)

                        # Format relationships preserving true Neo4j schema edge direction
                        for idx, r in enumerate(path.relationships):
                            from_id = r.start_node.element_id
                            to_id = r.end_node.element_id
                            edge_dict = format_graph_edge(r, from_id, to_id)
                            edge_dict["label"] = f"Step {idx+1}: {r.type}"
                            path_edges.append(edge_dict)
                    else:
                        error_msg = f"No connecting graph bridge discovered between Book #{book_a_id} and Book #{book_b_id} within maximum traversal depth."

    except Exception as e:
        error_msg = f"Database error evaluating graph shortest path: {str(e)}"

    return render_template(
        "book_bridge.html",
        all_books=all_books,
        book_a_id=book_a_id,
        book_b_id=book_b_id,
        path_nodes=path_nodes,
        path_edges=path_edges,
        path_steps=path_steps,
        degrees=degrees_of_separation,
        path_found=path_found,
        error_msg=error_msg
    )


@app.route("/api/book_bridge")
@login_required
def api_book_bridge():
    """JSON API endpoint returning shortest path data for dynamic UI rendering."""
    book_a_id = request.args.get("book_a", type=int)
    book_b_id = request.args.get("book_b", type=int)

    if not book_a_id or not book_b_id:
        return jsonify({"error": "Parameters book_a and book_b are required.", "nodes": [], "edges": []}), 400

    if book_a_id == book_b_id:
        return jsonify({"error": "Book A and Book B must be different.", "nodes": [], "edges": []}), 400

    try:
        with get_session() as s:
            res = s.run("""
                MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PUBLISHED_BY|PREREQUISITE_FOR*1..5]-(b2:Book {book_id: $id2}))
                RETURN p
            """, id1=book_a_id, id2=book_b_id)
            rec = res.single()

            if not (rec and rec["p"]):
                res = s.run("""
                    MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PREREQUISITE_FOR|PUBLISHED_BY|HAS_COPY|FOR_COPY|BORROWED|FOR_BOOK*1..10]-(b2:Book {book_id: $id2}))
                    RETURN p
                """, id1=book_a_id, id2=book_b_id)
                rec = res.single()

            if not (rec and rec["p"]):
                return jsonify({"found": False, "degrees": 0, "nodes": [], "edges": [], "steps": [], "message": "No path discovered."})

            path = rec["p"]
            nodes = []
            edges = []
            steps = []

            user_role = session.get("role") or session.get("Role")
            total_nodes = len(path.nodes)
            for idx, n in enumerate(path.nodes):
                f_node, step_item = format_bridge_node(n, idx, total_nodes, user_role)
                nodes.append(f_node)
                steps.append(step_item)

            for idx, r in enumerate(path.relationships):
                from_id = r.start_node.element_id
                to_id = r.end_node.element_id
                e = format_graph_edge(r, from_id, to_id)
                e["label"] = f"Step {idx+1}: {r.type}"
                edges.append(e)

            return jsonify({
                "found": True,
                "degrees": len(path.relationships),
                "nodes": nodes,
                "edges": edges,
                "steps": steps
            })

    except Exception as e:
        return jsonify({"error": str(e), "nodes": [], "edges": []}), 500


# ============================================================================
# Task 7 — Author Centrality & Influencer Analytics Dashboard (/library_analytics)
# ============================================================================
@app.route("/library_analytics")
@login_required
def library_analytics():
    """
    Renders the Author Centrality & Graph Influencer Analytics Dashboard.
    Available to Staff, Librarian, and Admin roles to analyze connection density,
    borrowing centrality, and knowledge graph structure.
    """
    role = session.get("role")
    if role not in ["Admin", "Librarian", "Staff"]:
        flash("Library Analytics & Centrality Dashboard is accessible to Staff, Librarians, and Administrators.", "warning")
        return redirect(url_for("dashboard"))

    try:
        with get_session() as s:
            # 1. Total System Loans for Share Calculation
            total_system_loans = s.run("MATCH (l:Loan) RETURN count(l) AS c").single()["c"] or 0

            # 2. Author Centrality & Borrowing Density (Degree Centrality)
            # Separate OPTIONAL MATCH clauses so copies without loans are still counted accurately
            author_res = s.run("""
                MATCH (a:Author)-[:WROTE]->(b:Book)
                OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
                OPTIONAL MATCH (cp)<-[:FOR_COPY]-(l:Loan)
                RETURN a.author_id AS author_id,
                       a.first_name + ' ' + a.last_name AS author_name,
                       count(DISTINCT l) AS total_borrowings,
                       count(DISTINCT b) AS authored_books,
                       count(DISTINCT cp) AS active_copies
                ORDER BY total_borrowings DESC, authored_books DESC, active_copies DESC
                LIMIT 5
            """)
            top_authors = rows(author_res)

            # Calculate Borrowing Density Share % against total system loans and progress bar width relative to top author
            max_author_loans = top_authors[0]["total_borrowings"] if top_authors and top_authors[0]["total_borrowings"] > 0 else 1
            for auth in top_authors:
                borrowings = auth.get("total_borrowings", 0)
                auth["share_pct"] = round(borrowings / total_system_loans * 100, 1) if total_system_loans else 0.0
                auth["bar_width"] = round((borrowings / max_author_loans) * 100, 1) if max_author_loans else 0.0

            # 3. Book Degree Centrality & Circulation Influence
            # Fetch co-authors and join with ", " in Python so all authors are displayed
            book_res = s.run("""
                MATCH (b:Book)
                OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
                OPTIONAL MATCH (cp)<-[:FOR_COPY]-(l:Loan)
                OPTIONAL MATCH (b)<-[:FOR_BOOK]-(lr:LoanRequest)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                RETURN b.book_id AS book_id, b.title AS title,
                       cat.name AS category_name,
                       collect(DISTINCT a.first_name + ' ' + a.last_name) AS authors_list,
                       count(DISTINCT cp) AS copies_count,
                       count(DISTINCT l) AS loans_count,
                       count(DISTINCT lr) AS requests_count,
                       (count(DISTINCT cp) * 2 + count(DISTINCT l) * 3 + count(DISTINCT lr)) AS degree_score
                ORDER BY degree_score DESC, loans_count DESC
                LIMIT 5
            """)
            top_books = rows(book_res)
            for bk in top_books:
                authors = bk.get("authors_list", [])
                bk["author_name"] = ", ".join(authors) if authors else "Unknown"

            # 4. Category Topic Closeness & Circulation Density
            cat_res = s.run("""
                MATCH (cat:Category)<-[:BELONGS_TO]-(b:Book)
                OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)<-[:FOR_COPY]-(l:Loan)
                RETURN cat.name AS category_name,
                       cat.section_code AS section_code,
                       count(DISTINCT b) AS books_count,
                       count(l) AS total_loans
                ORDER BY total_loans DESC, books_count DESC
            """)
            categories = rows(cat_res)

            # 5. Overall Knowledge Graph Topology Metrics
            nodes_count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels_count = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]

            # Query both distinct active borrowers (unreturned loans) and active loans
            active_res = s.run("""
                MATCH (u:User)-[:BORROWED]->(l:Loan)
                WHERE l.return_date IS NULL
                RETURN count(DISTINCT u) AS active_borrowers, count(DISTINCT l) AS active_loans
            """).single()
            active_borrowers = active_res["active_borrowers"] if active_res else 0
            active_loans = active_res["active_loans"] if active_res else 0

            avg_degree = round((float(rels_count) * 2.0 / nodes_count), 2) if nodes_count else 0.0

            graph_metrics = {
                "nodes_count": nodes_count,
                "rels_count": rels_count,
                "active_borrowers": active_borrowers,
                "active_loans": active_loans,
                "avg_degree": avg_degree,
                "density_rating": "High (Multi-clustered)" if avg_degree >= 2.0 else "Sparse"
            }

            return render_template(
                "library_analytics.html",
                top_authors=top_authors,
                top_books=top_books,
                categories=categories,
                metrics=graph_metrics
            )

    except Exception as e:
        flash(f"Error loading graph centrality analytics: {str(e)}", "danger")
        return redirect(url_for("dashboard"))


# ============================================================================
# Advanced Graph Feature — Academic Learning Roadmap ([:PREREQUISITE_FOR])
# ============================================================================
def ensure_prerequisite_hierarchy(s=None):
    """
    Idempotently seeds logical (:Book)-[:PREREQUISITE_FOR]->(:Book) relationships
    in Neo4j AuraDB if not already present. Reuses existing active session s if provided.
    """
    def _run_seeding(session_tx):
        prereq_specs = [
            (2, 3, 'Code Quality to Algorithms', 'Stage 1 -> Stage 2', 'Software Engineering'),
            (3, 4, 'Algorithms to Intelligent Systems', 'Stage 2 -> Stage 3', 'Artificial Intelligence'),
            (3, 9, 'Algorithms to Theoretical Mastery', 'Stage 2 -> Stage 4', 'Theoretical CS'),
            (2, 8, 'Clean Code to Domain Architecture', 'Stage 1 -> Stage 3', 'Software Engineering'),
            (6, 7, 'OS Internals to Network Protocols', 'Stage 1 -> Stage 2', 'Systems & Infrastructure'),
            (7, 1, 'Networking to Distributed Storage', 'Stage 2 -> Stage 3', 'Data Engineering'),
            (5, 1, 'Relational Theory to Distributed Scale', 'Stage 1 -> Stage 3', 'Data Engineering')
        ]
        for src_id, dst_id, jump, stage, track in prereq_specs:
            session_tx.run("""
                MATCH (src:Book {book_id: $src_id}), (dst:Book {book_id: $dst_id})
                MERGE (src)-[r:PREREQUISITE_FOR]->(dst)
                ON CREATE SET r.difficulty_jump = $jump,
                              r.stage = $stage,
                              r.track = $track
            """, src_id=src_id, dst_id=dst_id, jump=jump, stage=stage, track=track)

    try:
        if s is not None:
            _run_seeding(s)
        else:
            with get_session() as sess:
                _run_seeding(sess)
    except Exception as e:
        app.logger.warning(f"Error checking/seeding prerequisite hierarchy: {e}")


@app.route("/learning_paths", methods=["GET"])
@login_required
def learning_paths():
    """
    Renders the Academic Learning Roadmap based on variable-length
    (:Book)-[:PREREQUISITE_FOR*1..4]->(:Book) hierarchical trees with real-time stock availability.
    """
    try:
        with get_session() as s:
            ensure_prerequisite_hierarchy(s)
            # 1. Variable-length paths query: full end-to-end Root-to-Mastery sequences
            path_res = s.run("""
                MATCH path = (root:Book)-[:PREREQUISITE_FOR*1..4]->(target:Book)
                WHERE NOT ()-[:PREREQUISITE_FOR]->(root) AND NOT (target)-[:PREREQUISITE_FOR]->()
                RETURN [n IN nodes(path) | {id: n.book_id, title: n.title}] AS nodes_in_path,
                       length(path) AS depth,
                       [r IN relationships(path) | {jump: r.difficulty_jump, track: r.track, stage: r.stage}] AS edges_in_path
            """)
            raw_paths = rows(path_res)

            # Assign clear specialization badges for distinct branching tracks
            for p in raw_paths:
                nodes_in_p = p.get("nodes_in_path") or []
                root_title = (nodes_in_p[0].get("title") or "") if nodes_in_p and isinstance(nodes_in_p[0], dict) else ""
                target_title = (nodes_in_p[-1].get("title") or "") if nodes_in_p and isinstance(nodes_in_p[-1], dict) else ""
                edge_tracks = [(e.get("track") or "") for e in (p.get("edges_in_path") or []) if isinstance(e, dict)]

                if "Artificial Intelligence" in target_title or any("Artificial Intelligence" in t for t in edge_tracks):
                    p["track_badge"] = "AI Specialization Track"
                    p["track_color"] = "#8B5CF6"
                elif "Art of Computer Programming" in target_title or any("Theoretical" in t for t in edge_tracks):
                    p["track_badge"] = "Algorithms Mastery Track"
                    p["track_color"] = "#F59E0B"
                elif "Domain-Driven Design" in target_title:
                    p["track_badge"] = "Software Architecture Track"
                    p["track_color"] = "#3B82F6"
                elif "Modern Operating Systems" in root_title:
                    p["track_badge"] = "Systems & Infrastructure Track"
                    p["track_color"] = "#06B6D4"
                elif "Database System Concepts" in root_title or any("Data Engineering" in t for t in edge_tracks):
                    p["track_badge"] = "Data Engineering Track"
                    p["track_color"] = "#10B981"
                else:
                    last_track = edge_tracks[-1] if edge_tracks else "Curriculum"
                    p["track_badge"] = f"{last_track} Track"
                    p["track_color"] = "#818CF8"

            # Fetch patron learning progress (completed reads and active loans)
            uid = session.get("user_id") or -1
            user_completed_bids = set()
            user_active_bids = set()
            if uid and uid > 0:
                prog_res = s.run("""
                    MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b:Book)
                    RETURN b.book_id AS book_id, l.return_date AS return_date
                """, uid=uid)
                for row in rows(prog_res):
                    if row.get("return_date"):
                        user_completed_bids.add(row["book_id"])
                    else:
                        user_active_bids.add(row["book_id"])

            # 2. Roadmap books with real-time stock availability, category metadata, and level attribution
            nodes_res = s.run("""
                MATCH (b:Book)
                WHERE (b)-[:PREREQUISITE_FOR]-()
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                OPTIONAL MATCH (b)-[:PREREQUISITE_FOR]->(nxt:Book)
                OPTIONAL MATCH (prv:Book)-[:PREREQUISITE_FOR]->(b)
                WITH b, cat,
                     collect(DISTINCT a.first_name + ' ' + a.last_name) AS authors,
                     collect(DISTINCT prv.book_id) AS prereqs,
                     collect(DISTINCT nxt.book_id) AS unlocks
                RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                       coalesce(cat.category_id, b.category_id, 1) AS category_id,
                       coalesce(cat.name, 'General') AS category_name,
                       reduce(s='', x IN authors | CASE WHEN s='' THEN x ELSE s+', '+x END) AS authors,
                       size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_copies,
                       size([(b)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies,
                       prereqs,
                       unlocks
                ORDER BY book_id
            """)
            book_nodes = rows(nodes_res)

            # 3. Directed edges
            edge_res = s.run("""
                MATCH (src:Book)-[r:PREREQUISITE_FOR]->(dst:Book)
                RETURN src.book_id AS source, dst.book_id AS target,
                       r.difficulty_jump AS difficulty_jump,
                       r.stage AS stage,
                       coalesce(r.track, 'General') AS track
            """)
            edge_rows = rows(edge_res)

            # Build level mapping (root nodes in-degree 0 -> level 1, etc.)
            in_degrees = {b["book_id"]: len(b["prereqs"]) for b in book_nodes}
            levels = {}
            for b in book_nodes:
                if in_degrees.get(b["book_id"], 0) == 0:
                    levels[b["book_id"]] = 1

            # Honour explicit target stages (e.g. Donald Knuth reaching Stage 4)
            for e in edge_rows:
                stage_str = e.get("stage") or ""
                if "->" in stage_str and "Stage" in stage_str:
                    try:
                        dest_stage = int(stage_str.split("->")[-1].replace("Stage", "").strip())
                        levels[e["target"]] = max(levels.get(e["target"], 1), dest_stage)
                    except Exception:
                        pass

            # Relax levels down the edges
            changed = True
            iterations = 0
            while changed and iterations < 10:
                changed = False
                iterations += 1
                for e in edge_rows:
                    src_lvl = levels.get(e["source"])
                    if src_lvl is not None:
                        target_lvl = src_lvl + 1
                        if levels.get(e["target"]) is None or levels[e["target"]] < target_lvl:
                            levels[e["target"]] = target_lvl
                            changed = True

            # Format Vis.js network data
            vis_nodes = []
            for b in book_nodes:
                bid = b["book_id"]
                lvl = levels.get(bid, 1)
                avail = b["available_copies"]
                total = b["total_copies"]
                is_avail = avail > 0

                user_status = "unattempted"
                if bid in user_completed_bids:
                    user_status = "completed"
                elif bid in user_active_bids:
                    user_status = "reading"

                stage_label = f"Level {lvl}"
                if lvl == 1:
                    stage_title = "Level 1: Foundational"
                    color_bg = "#1E293B"
                    color_border = "#3B82F6"
                elif lvl == 2:
                    stage_title = "Level 2: Core Engineering"
                    color_bg = "#1E293B"
                    color_border = "#8B5CF6"
                elif lvl == 3:
                    stage_title = "Level 3: Systems Specialization"
                    color_bg = "#1E293B"
                    color_border = "#EC4899"
                else:
                    stage_title = "Level 4: Advanced Mastery"
                    color_bg = "#1E293B"
                    color_border = "#F59E0B"

                if user_status == "completed":
                    node_border = "#10B981"
                    status_text = f"✓ Mastered ({avail}/{total} In Library)"
                    node_label = f"[{stage_label} • ✓ Mastered]\n{b['title']}\n{status_text}"
                elif user_status == "reading":
                    node_border = "#38BDF8"
                    status_text = f"📖 Active Loan ({avail}/{total} In Library)"
                    node_label = f"[{stage_label} • 📖 Reading]\n{b['title']}\n{status_text}"
                else:
                    node_border = color_border if is_avail else "#EF4444"
                    status_text = f"● {avail}/{total} Avail" if is_avail else f"● Out of Stock (0/{total})"
                    node_label = f"[{stage_label}]\n{b['title']}\n{status_text}"

                vis_nodes.append({
                    "id": bid,
                    "label": node_label,
                    "level": lvl,
                    "title": f"<b>{b['title']}</b><br>Authors: {b['authors']}<br>Category: {b['category_name']}<br>Stage: {stage_title}<br>Stock: {avail}/{total} available",
                    "shape": "box",
                    "margin": 14,
                    "color": {
                        "background": color_bg,
                        "border": node_border,
                        "highlight": { "background": "#334155", "border": "#60A5FA" }
                    },
                    "borderWidth": 3 if user_status != "unattempted" else 2,
                    "font": { "color": "#F8FAFC", "size": 15, "multi": True, "face": "Inter, sans-serif" },
                    "properties": {
                        "book_id": bid,
                        "title": b["title"],
                        "isbn": b["isbn"],
                        "authors": b["authors"],
                        "category_id": b.get("category_id") or 1,
                        "category_name": b["category_name"],
                        "level": lvl,
                        "stage_title": stage_title,
                        "available_copies": avail,
                        "total_copies": total,
                        "is_available": is_avail,
                        "user_status": user_status,
                        "prereqs": b["prereqs"],
                        "unlocks": b["unlocks"]
                    }
                })

            vis_edges = []
            for idx, e in enumerate(edge_rows):
                track = e.get("track") or "General"
                diff_jump = e.get("difficulty_jump") or "Prerequisite"
                edge_color = "#3B82F6"
                if "Intelligence" in track or "Software" in track:
                    edge_color = "#8B5CF6"
                elif "Data" in track or "Systems" in track:
                    edge_color = "#06B6D4"
                elif "Theoretical" in track:
                    edge_color = "#F59E0B"

                vis_edges.append({
                    "id": f"e_{e['source']}_{e['target']}",
                    "from": e["source"],
                    "to": e["target"],
                    "label": diff_jump,
                    "arrows": "to",
                    "color": { "color": edge_color, "highlight": "#60A5FA" },
                    "font": { "color": "#94A3B8", "size": 10, "align": "horizontal", "background": "rgba(15, 23, 42, 0.85)" },
                    "width": 2,
                    "smooth": { "type": "cubicBezier", "forceDirection": "vertical", "roundness": 0.4 },
                    "properties": {
                        "difficulty_jump": diff_jump,
                        "stage": e.get("stage") or "General",
                        "track": track
                    }
                })

            # Calculate curriculum statistics
            total_volumes = len(book_nodes)
            available_volumes = sum(1 for b in book_nodes if b["available_copies"] > 0)
            max_depth = max(levels.values()) if levels else 1
            total_edges = len(vis_edges)

            stats = {
                "total_volumes": total_volumes,
                "available_volumes": available_volumes,
                "max_depth": max_depth,
                "total_edges": total_edges,
                "total_paths": len(raw_paths)
            }

            return render_template(
                "learning_paths.html",
                vis_nodes=vis_nodes,
                vis_edges=vis_edges,
                book_nodes=book_nodes,
                edge_rows=edge_rows,
                stats=stats,
                paths=raw_paths
            )

    except Exception as e:
        flash(f"Error loading Academic Learning Roadmaps: {str(e)}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/api/learning_paths", methods=["GET"])
@login_required
def api_learning_paths():
    """Returns JSON graph data for the academic prerequisite hierarchy."""
    try:
        with get_session() as s:
            ensure_prerequisite_hierarchy(s)
            edge_res = s.run("""
                MATCH (src:Book)-[r:PREREQUISITE_FOR]->(dst:Book)
                RETURN src.book_id AS source, dst.book_id AS target,
                       r.difficulty_jump AS difficulty_jump, r.stage AS stage, r.track AS track
            """)
            edges = rows(edge_res)

            node_res = s.run("""
                MATCH (b:Book) WHERE (b)-[:PREREQUISITE_FOR]-()
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(cat:Category)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
                WITH b, cat, collect(DISTINCT a.first_name + ' ' + a.last_name) AS author_list
                RETURN b.book_id AS book_id, b.title AS title, b.isbn AS isbn,
                       coalesce(cat.category_id, b.category_id, 1) AS category_id,
                       coalesce(cat.name, 'General') AS category_name,
                       reduce(s='', a IN author_list | CASE WHEN s='' THEN a ELSE s+', '+a END) AS authors,
                       size([(b)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS available_copies,
                       size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_copies
                ORDER BY b.book_id
            """)
            nodes = rows(node_res)
            return jsonify({"status": "success", "nodes": nodes, "edges": edges})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# Entry Point
# ============================================================================
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

