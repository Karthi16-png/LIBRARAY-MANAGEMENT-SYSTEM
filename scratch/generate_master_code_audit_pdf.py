import os
import sys
import time
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Preformatted
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_PDF = os.path.join(BASE_DIR, "VITCC_Library_Master_Source_Code_and_Verification_Dossier.pdf")


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        print(f"Total Pages Generated in PDF: {num_pages}")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page

        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header
        self.drawString(36, 814, "VIT CHENNAI CENTRAL LIBRARY SYSTEM — MASTER CODE AUDIT & LLM VERIFICATION DOSSIER")
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(595 - 36, 814, "CONFIDENTIAL / VERIFICATION REPOSITORY")

        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 808, 595 - 36, 808)

        # Running Footer
        self.line(36, 32, 595 - 36, 32)
        self.drawString(36, 22, "Multi-Agent AI Code Verification • Python/Flask + Neo4j AuraDB Architecture")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(595 - 36, 22, page_str)
        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()

    styles = {
        'CoverTitle': ParagraphStyle(
            'CoverTitle',
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=8
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle',
            fontName='Helvetica',
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor('#334155'),
            spaceAfter=14
        ),
        'SectionHeader': ParagraphStyle(
            'SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        ),
        'SubSectionHeader': ParagraphStyle(
            'SubSectionHeader',
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True
        ),
        'SubSubSectionHeader': ParagraphStyle(
            'SubSubSectionHeader',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155'),
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body',
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#334155'),
            spaceAfter=5
        ),
        'BodyBold': ParagraphStyle(
            'BodyBold',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=5
        ),
        'Bullet': ParagraphStyle(
            'Bullet',
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#334155'),
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3
        ),
        'CalloutTitle': ParagraphStyle(
            'CalloutTitle',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0F172A')
        ),
        'CalloutBody': ParagraphStyle(
            'CalloutBody',
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#334155')
        ),
        'CodeStyle': ParagraphStyle(
            'CodeStyle',
            fontName='Courier',
            fontSize=5.6,
            leading=7.0,
            textColor=colors.HexColor('#0F172A')
        ),
        'TableHead': ParagraphStyle(
            'TableHead',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#0F172A')
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#334155')
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold',
            fontName='Helvetica-Bold',
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#0F172A')
        ),
        'TableCellMono': ParagraphStyle(
            'TableCellMono',
            fontName='Courier',
            fontSize=6.5,
            leading=8.5,
            textColor=colors.HexColor('#0F172A')
        )
    }
    return styles


def wrap_code_line(line, max_len=108):
    if len(line) <= max_len:
        return [line]
    chunks = []
    first = line[:max_len]
    chunks.append(first)
    rem = line[max_len:]
    while rem:
        chunk = rem[:max_len - 6]
        chunks.append("      | " + chunk)
        rem = rem[max_len - 6:]
    return chunks


def load_file_chunks(filepath, lines_per_chunk=80):
    full_path = os.path.join(BASE_DIR, filepath)
    if not os.path.exists(full_path):
        return [], 0

    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = f.readlines()

    formatted_lines = []
    line_num = 1
    for raw in raw_lines:
        clean = raw.rstrip("\r\n")
        wrapped = wrap_code_line(clean, max_len=108)
        formatted_lines.append(f"{line_num:04d}: {wrapped[0]}")
        for cont in wrapped[1:]:
            formatted_lines.append(cont)
        line_num += 1

    chunks = []
    for i in range(0, len(formatted_lines), lines_per_chunk):
        chunk_text = "\n".join(formatted_lines[i:i + lines_per_chunk])
        chunks.append(chunk_text)

    return chunks, len(raw_lines)


def build_file_header_card(filename, category, lang, total_lines, purpose, checklist_items, styles):
    card_data = [
        [
            Paragraph(f"<b>MODULE SOURCE: {filename}</b>", styles['CalloutTitle']),
            Paragraph(f"<b>Lines:</b> {total_lines} | <b>Lang:</b> {lang} | <b>Category:</b> {category}", styles['CalloutBody'])
        ],
        [
            Paragraph(f"<b>Core Role & Purpose:</b> {purpose}", styles['CalloutBody']),
            ""
        ]
    ]

    # Checklist items
    checklist_text = "<b>REVIEWING LLM VERIFICATION CHECKLIST FOR THIS FILE:</b><br/>"
    for item in checklist_items:
        checklist_text += f"• {item}<br/>"

    card_data.append([
        Paragraph(checklist_text, styles['CalloutBody']),
        ""
    ])

    table = Table(card_data, colWidths=[360, 163])
    table.setStyle(TableStyle([
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (0, 2), (1, 2)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#E2E8F0')),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def build_pdf():
    print(f"Initializing Master Code Audit PDF generation...")
    t0 = time.time()
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=40
    )

    styles = get_styles()
    story = []

    # =========================================================================
    # COVER / TITLE BLOCK
    # =========================================================================
    cover_box = [
        [
            Paragraph("<b>VELLORE INSTITUTE OF TECHNOLOGY — CHENNAI CAMPUS</b><br/><font size=7 color='#64748B'>CENTRAL LIBRARY & LEARNING RESOURCE CENTRE • ADVANCED KNOWLEDGE GRAPH SYSTEM</font>", styles['TableCellBold']),
            Paragraph(f"<b>DATE:</b> {datetime.now().strftime('%Y-%m-%d')}<br/><b>VERSION:</b> 2.4-PROD", styles['TableCell'])
        ]
    ]
    t_cover_meta = Table(cover_box, colWidths=[380, 143])
    t_cover_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cover_meta)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Master Source Code Compilation & Autonomous Verification Dossier", styles['CoverTitle']))
    story.append(Paragraph(
        "Complete production codebase, system architectural specifications, and rigorous multi-agent verification instructions for comprehensive LLM validation of Role-Based Access Control (RBAC), Neo4j AuraDB graph consistency, book circulation workflows, live visualizers, and UI logic.",
        styles['CoverSubtitle']
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0F172A"), spaceBefore=2, spaceAfter=12))

    # Architecture Summary Table
    arch_data = [
        [Paragraph("<b>Component / Layer</b>", styles['TableHead']), Paragraph("<b>Technology / Specifications</b>", styles['TableHead']), Paragraph("<b>Primary Responsibilities & Verification Focus</b>", styles['TableHead'])],
        [Paragraph("<b>Backend Web Framework</b>", styles['TableCellBold']), Paragraph("Python 3.12, Flask, Flask-WTF (CSRF), Werkzeug Security", styles['TableCell']), Paragraph("Full application routing, authentication, session tokens, protected role gates, parameterized Cypher queries, and REST APIs.", styles['TableCell'])],
        [Paragraph("<b>Graph Database Layer</b>", styles['TableCellBold']), Paragraph("Neo4j AuraDB (Cloud Instance), Cypher Query Engine, neo4j Python Driver", styles['TableCell']), Paragraph("Property graph persistence: Users, Books, Copies, Categories, Authors, Publishers, Loans, Fines, and LoanRequests.", styles['TableCell'])],
        [Paragraph("<b>RBAC Security Model</b>", styles['TableCellBold']), Paragraph("4 Roles: Admin, Librarian, Staff, Student with Protected Admin Hierarchy", styles['TableCell']), Paragraph("Strict role boundary enforcement: Admin immunity against peer tampering; Librarian supervision; Student/Staff privacy isolation.", styles['TableCell'])],
        [Paragraph("<b>Interactive Graph Visualization</b>", styles['TableCellBold']), Paragraph("Vis.js Network Engine, Barnes-Hut Physics Solver, Vanilla JS", styles['TableCell']), Paragraph("Dynamic spring/repulsion graph simulation, state-aware Play/Pause toggling, auto-freeze layout, and empty graph handling.", styles['TableCell'])],
        [Paragraph("<b>Recommendation Engine</b>", styles['TableCellBold']), Paragraph("Collaborative Graph Filtering, Jaccard Similarity, Traversals", styles['TableCell']), Paragraph("Intelligent book discovery, peer borrowing (Book Bridge), and curated academic learning paths without raw debug strings.", styles['TableCell'])],
    ]
    t_arch = Table(arch_data, colWidths=[110, 150, 263])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 14))

    # =========================================================================
    # PART I: INSTRUCTIONS FOR THE REVIEWING LLM
    # =========================================================================
    story.append(Paragraph("PART I: VERIFICATION INSTRUCTIONS & GUIDELINES FOR THE REVIEWING LLM", styles['SectionHeader']))
    story.append(Paragraph(
        "<b>Notice to the Evaluating AI / LLM Auditor:</b> This document contains the full, unabridged source code for the VIT Chennai Central Library Management & Knowledge Graph System. Your objective is to perform an exhaustive, rigorous, and systematic code verification to guarantee that all intended architectural, functional, security, and algorithmic requirements have been implemented correctly and without logical errors. Evaluate the codebase across the following seven core dimensions:",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    eval_dimensions = [
        ("1. Role-Based Access Control (RBAC) & Protected Hierarchy Logic", [
            "<b>Four Distinct Roles:</b> Validate that the system strictly defines and enforces <code>Admin</code>, <code>Librarian</code>, <code>Staff</code>, and <code>Student</code> across decorators, template conditional renders, and route handlers.",
            "<b>Protected Administrator Immunity:</b> An Admin CANNOT be suspended, deleted, or have their password reset by another Admin via the web interface or API (protects against accidental lockout and privilege de-escalation attacks). Verify that <code>/delete_user/&lt;username&gt;</code>, <code>/suspend_user/&lt;username&gt;</code>, and <code>/reset_user_password/&lt;username&gt;</code> explicitly block targeting Admin accounts.",
            "<b>Administrative Control over Librarians:</b> An Admin CAN suspend, delete, and reset passwords for Librarians. Verify that <code>templates/manage_users.html</code> renders the Reset Password button for Librarian rows and that the backend properly handles password reset for Librarians.",
            "<b>Librarian Scope Boundaries:</b> Librarians can manage book records, issue copies, and approve loan requests, but CANNOT manage Admin or Librarian accounts, nor reset Admin passwords.",
            "<b>Staff and Student Privacy Isolation:</b> Staff and Students must be strictly isolated to their own records. They cannot access administrative routes, cannot approve loans, and only view their own borrowings, disciplinary liabilities, and recommendations."
        ]),
        ("2. Neo4j AuraDB Graph Modeling & Cypher Parameterization", [
            "<b>Graph Data Schema:</b> Verify node labels: <code>User</code>, <code>Book</code>, <code>Author</code>, <code>Category</code>, <code>Publisher</code>, <code>Copy</code>, <code>Loan</code>, <code>Fine</code>, <code>LoanRequest</code>.",
            "<b>Cypher Injection Prevention:</b> Ensure that every database query uses parameterized Cypher queries (<code>session.run(query, params)</code>). Verify that no user inputs are directly concatenated or formatted into Cypher strings.",
            "<b>Physical Copy Cardinality & Inventory Tracking:</b> Each <code>Book</code> is linked to physical copies via <code>(:Book)-[:HAS_COPY]-&gt;(:Copy)</code>. Verify that book borrowing marks <code>Copy.is_borrowed = true</code> and decrements available count, while book return marks <code>is_borrowed = false</code> and increments available count.",
            "<b>Transaction Lifecycle:</b> Check that sessions and transactions are properly opened and closed, with robust error catching and database rollback on failure."
        ]),
        ("3. Book Issuance Workflow & Substring Live Autocomplete", [
            "<b>Substring Matching:</b> Verify that on <code>/issue_loan</code>, typing into the User or Book search inputs performs a live substring filter (e.g. matching any part of a user's name, username, or book title/ISBN) rather than restricting to strict prefix matching.",
            "<b>Availability Verification:</b> Verify that a loan cannot be issued if available copies are 0, preventing negative inventory bugs.",
            "<b>Active Loan Creation:</b> Verify that issuing a book establishes the <code>(:User)-[:BORROWED {status: 'ACTIVE', issue_date: ...}]-&gt;(:Book)</code> and <code>(:Loan)-[:FOR_COPY]-&gt;(:Copy)</code> relationships."
        ]),
        ("4. Disciplinary Liabilities & Fine Management Terminology", [
            "<b>Terminology Compliance:</b> In Admin and Librarian dashboards, verify that the disciplinary liabilities section uses the exact terminology <b>'Disciplinary Liabilities'</b> and <b>'Disciplinary Fines'</b>, with the redundant qualifier 'outstanding' completely removed.",
            "<b>Overdue Calculation:</b> Verify that overdue loans calculate fines based on due date vs return date and create <code>Fine</code> nodes with status <code>'unpaid'</code>.",
            "<b>Settlement Engine:</b> Verify that members can view their fines on <code>/my_fines</code> and that librarians/admins can settle or waive liabilities."
        ]),
        ("5. AI Recommendations & Book Bridge Peer Sharing", [
            "<b>Graph Recommendation Algorithm:</b> Verify that recommendations are computed using collaborative graph traversals (co-borrowed books among users with shared reading histories).",
            "<b>Clean User-Facing Copy:</b> Confirm that technical debug labels such as <code>(Jaccard Graph Similarity)</code> are omitted from user-facing recommendation cards.",
            "<b>Book Bridge:</b> Verify that students and faculty can list books for peer sharing and submit borrow requests to peer owners."
        ]),
        ("6. Live Graph Explorer Physics Controls & Edge Cases", [
            "<b>Vis.js Barnes-Hut Physics Solver:</b> Inspect <code>templates/graph_visualizer.html</code> to verify that physics is configured with proper gravitational constant, spring length, and central gravity.",
            "<b>State-Aware Play/Pause Toggle:</b> When physics simulation is actively running, the button must display the <b>Pause icon (⏸️)</b> with title <i>'Pause Physics Simulation (Freeze Layout)'</i>. When frozen, it must display the <b>Play icon (▶️)</b> with title <i>'Resume Physics Simulation (Unfreeze Layout)'</i>.",
            "<b>Useless State Removal (0 Nodes):</b> When 0 nodes are visible (e.g. all filters deselected or empty dataset), the play/pause button provides no utility and must be hidden (<code>display: none</code>).",
            "<b>Re-stabilize Auto-Sync:</b> If physics was frozen, clicking <i>'Re-stabilize Layout'</i> must automatically re-enable physics before triggering stabilization."
        ]),
        ("7. Security, CSRF Protection & Credential Integrity", [
            "<b>Password Security:</b> Passwords must be hashed using Werkzeug salted PBKDF2/SHA-256 (<code>generate_password_hash</code>, <code>check_password_hash</code>).",
            "<b>CSRF Protection:</b> All POST forms must validate CSRF tokens via <code>flask_wtf.csrf.CSRFProtect</code>.",
            "<b>Session Integrity:</b> Check that session state stores user ID, username, and role securely, with complete invalidation upon logout."
        ])
    ]

    for title, points in eval_dimensions:
        story.append(Paragraph(title, styles['SubSectionHeader']))
        for pt in points:
            story.append(Paragraph(f"• {pt}", styles['Bullet']))
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART II: COMPLETE INTENDED FEATURES SPECIFICATION
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("PART II: COMPLETE INTENDED FEATURES SPECIFICATION & FUNCTIONAL REQUIREMENTS", styles['SectionHeader']))
    story.append(Paragraph(
        "The following matrix specifies all intended features that the application was engineered to provide. Use this functional requirements specification to cross-reference every route, query, and UI element in the code:",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    features_matrix = [
        ("F-01: Multi-Role Authentication & Session Management", [
            "<b>Feature Scope:</b> Secure authentication portal (<code>/login</code>), self-registration (<code>/register</code>), and credential modification (<code>/change_password</code>).",
            "<b>Expected Behavior:</b> Users authenticate via username/email and password. Upon successful login, the user's role (Admin, Librarian, Staff, Student) determines dashboard routing and menu visibility. Invalid credentials flash an error without revealing user existence.",
            "<b>Security Rules:</b> Passwords stored exclusively as salted hashes; session tokens invalidated on <code>/logout</code>."
        ]),
        ("F-02: User Administration & Protected Hierarchy", [
            "<b>Feature Scope:</b> Central user management dashboard (<code>/manage_users</code>) accessible strictly to Administrators.",
            "<b>Expected Behavior:</b> Displays all registered users with role badges and status (Active, Suspended). Admin can suspend or delete Librarians, Staff, and Students. Admin can trigger a password reset for Librarian accounts, generating a secure temporary credential.",
            "<b>Safety Restraint:</b> Admin accounts CANNOT be suspended, deleted, or reset by anyone via the interface (hardened against peer admin lockout)."
        ]),
        ("F-03: Multi-Copy Catalog & Category Taxonomy", [
            "<b>Feature Scope:</b> Hierarchical book catalog (<code>/catalog</code>), category-specific book browser (<code>/categories/&lt;cat_id&gt;/books</code>), book registration (<code>/add_book</code>), and metadata editing (<code>/edit_book/&lt;id&gt;</code>).",
            "<b>Expected Behavior:</b> Books are linked to Authors, Publishers, and Categories. Each Book tracks total physical copies and real-time available copies. Register new book button renders a single clean plus sign (<code>+ Register New Book</code>).",
            "<b>Role Scoping:</b> Category cards show <i>'inspect copy availability, and manage loans'</i> for Admin/Librarian, and <i>'check real-time copy availability, and request loans'</i> for Staff/Student."
        ]),
        ("F-04: Manual Book Checkout with Substring Autocomplete", [
            "<b>Feature Scope:</b> Librarian and Admin loan issuance console (<code>/issue_loan</code>).",
            "<b>Expected Behavior:</b> Typing any partial name, username, title, or ISBN dynamically filters matching members and books in an interactive dropdown. Selecting a book verifies available copy count before permitting checkout.",
            "<b>State Transition:</b> Generates a new active <code>Loan</code> relationship, decrements book available copies, and sets loan due date (default: 14 days)."
        ]),
        ("F-05: Loan Request, Approval & Return Pipeline", [
            "<b>Feature Scope:</b> Self-service loan request queue (<code>/loan_requests</code>) and loan return processing (<code>/return_book/&lt;loan_id&gt;</code>).",
            "<b>Expected Behavior:</b> Students and Staff can request books online. Librarians review the queue with audited request timestamps (header formatted as <code>REQUEST TIMESTAMP</code>). Approving issues the loan; returning marks the copy available and checks for overdue fines."
        ]),
        ("F-06: Disciplinary Liabilities & Fine Settlement", [
            "<b>Feature Scope:</b> Disciplinary liabilities tracking across dashboards and member fine inspection (<code>/my_fines</code>).",
            "<b>Expected Behavior:</b> Overdue loans automatically accrue fines ($1.00/day). Fines display status (Unpaid, Paid, Waived).",
            "<b>Terminology Standard:</b> Admin and Librarian dashboards cleanly display 'Disciplinary Liabilities' and 'Disciplinary Fines' without the word 'outstanding'."
        ]),
        ("F-07: AI Graph Recommendations & Book Bridge", [
            "<b>Feature Scope:</b> Graph-based recommendation engine (<code>/recommendations</code>) and peer-to-peer book sharing (<code>/book_bridge</code>).",
            "<b>Expected Behavior:</b> Recommends books based on co-borrowing clusters and author/category proximity. UI displays clean similarity metrics without raw debug text (<code>Jaccard Graph Similarity</code> removed). Book Bridge allows students and staff to list and request personal books."
        ]),
        ("F-08: Interactive Vis.js Knowledge Graph Visualizer", [
            "<b>Feature Scope:</b> Live Neo4j property graph visualizer (<code>/graph_visualizer</code>) with dynamic view switching (Full, Catalog, Personal/Global Circulation).",
            "<b>Expected Behavior:</b> Visualizes nodes (color-coded by group) and directed relationships with physics. Clicking a node opens a slide-out drawer showing properties and connected neighbors.",
            "<b>Physics Play/Pause Button:</b> Active simulation shows Pause (⏸️) icon; frozen simulation shows Play (▶️) icon. Automatically hidden when 0 nodes are visible. Re-stabilize automatically re-activates physics if paused."
        ]),
        ("F-09: Role-Scoped Central Dashboards", [
            "<b>Feature Scope:</b> Central dashboard (<code>/dashboard</code>) adapting its analytics, quick actions, and data tables to the authenticated role.",
            "<b>Expected Behavior:</b> Admin sees campus-wide KPIs, system user counts, and global disciplinary liabilities. Librarian sees circulation queues and catalog actions. Staff/Student sees personal borrowings, return deadlines, and personalized recommendations."
        ]),
        ("F-10: Academic Learning Paths & Analytics", [
            "<b>Feature Scope:</b> Curated prerequisite book paths (<code>/learning_paths</code>) and circulation analytics (<code>/library_analytics</code>).",
            "<b>Expected Behavior:</b> Provides structured domain reading roadmaps and visual charts illustrating borrow trends by category and role."
        ])
    ]

    for code, details in features_matrix:
        story.append(Paragraph(code, styles['SubSectionHeader']))
        for d in details:
            story.append(Paragraph(f"• {d}", styles['Bullet']))
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART III: CODE COMPILATION WITH HEADERS & CHECKLISTS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("PART III: ORGANIZED SOURCE CODE MODULES & IMPLEMENTATION", styles['SectionHeader']))
    story.append(Paragraph(
        "Below is the complete, line-numbered source code of every essential application file. Each file begins with a comprehensive module header detailing its architectural role, line count, and a targeted LLM verification checklist:",
        styles['Body']
    ))
    story.append(Spacer(1, 8))

    # Master list of source files to compile
    SOURCE_FILES = [
        {
            "file": "app.py",
            "cat": "Core Backend & API Layer",
            "lang": "Python 3.12",
            "purpose": "Primary Flask application handling all HTTP routing, Neo4j AuraDB Cypher queries, RBAC authentication decorators, user administration, loan issuance, fine settlement, recommendation algorithms, and visualizer APIs.",
            "checklist": [
                "Verify @login_required and @role_required(['Admin', ...]) decorator logic on all routes.",
                "Verify Admin immunity in /manage_users, /delete_user, /suspend_user, and /reset_user_password.",
                "Verify Admin's capability to reset password, suspend, and delete Librarian accounts.",
                "Verify parameterized Cypher execution across all database interactions (session.run with parameters).",
                "Verify /issue_loan substring user/book lookup and copy availability decrement.",
                "Verify /return_book loan completion, copy availability increment, and overdue fine calculation.",
                "Verify that Admin and Librarian dashboard fine metrics use 'Disciplinary Liabilities' copy.",
                "Verify /api/graph_data JSON formatting for Vis.js visualization."
            ]
        },
        {
            "file": "seed_all_data.py",
            "cat": "Database Seeding & Schema Engine",
            "lang": "Python 3.12 / Cypher",
            "purpose": "Neo4j AuraDB database seeding script establishing uniqueness constraints, schema indexes, sample users (Admin, Librarian, Staff, Student), book catalog, multi-copy relationships, active loans, and disciplinary fines.",
            "checklist": [
                "Verify creation of UNIQUE constraints on User(username), User(email), Book(book_id), and Copy(copy_id).",
                "Verify password hashing for seeded accounts using generate_password_hash.",
                "Verify relationship consistency: (:User)-[:BORROWED]->(:Book), (:Book)-[:HAS_COPY]->(:Copy), (:User)-[:HAS_FINE]->(:Fine).",
                "Verify that available_copies on Book matches the count of Copy nodes where is_borrowed = false."
            ]
        },
        {
            "file": "requirements.txt",
            "cat": "Dependencies & Environment",
            "lang": "Pip Requirements",
            "purpose": "Python package dependency manifest declaring Flask, neo4j, Flask-WTF, ReportLab, and supporting utilities.",
            "checklist": [
                "Verify neo4j official driver dependency.",
                "Verify Flask and Flask-WTF for CSRF protection.",
                "Verify ReportLab for programmatic PDF audit generation."
            ]
        },
        {
            "file": "templates/base.html",
            "cat": "Master UI Shell & Navigation",
            "lang": "HTML5 / Jinja2 / Vanilla CSS",
            "purpose": "Global master layout template providing the dark glassmorphic design system, responsive sidebar, topbar, role-based navigation scoping, notification toasts, and security headers.",
            "checklist": [
                "Verify that sidebar navigation items are strictly role-gated (Manage Users visible only to Admin; Issue Book visible only to Admin/Librarian).",
                "Verify CSRF token meta tags or form hook availability.",
                "Verify breadcrumb and active page highlight logic."
            ]
        },
        {
            "file": "templates/manage_users.html",
            "cat": "User Administration & RBAC",
            "lang": "HTML5 / Jinja2",
            "purpose": "Admin user management interface providing user listing, role status toggles, user suspension, user deletion, and Librarian password reset modal.",
            "checklist": [
                "Verify that Admin rows display NO delete, suspend, or password reset buttons (hardened against peer admin tampering).",
                "Verify that Librarian rows DO render the 'Reset Password' button triggering the reset modal.",
                "Verify password reset modal form POSTs to /reset_user_password with CSRF token."
            ]
        },
        {
            "file": "templates/dashboard.html",
            "cat": "Circulation & Core Dashboard",
            "lang": "HTML5 / Jinja2",
            "purpose": "Central role-scoped dashboard rendering disciplinary liabilities, borrowing statistics, quick actions, and recent activity tables.",
            "checklist": [
                "Verify that the liabilities card displays 'Disciplinary Liabilities' and 'Disciplinary Fines' without the word 'outstanding'.",
                "Verify role-conditional rendering of action buttons (e.g. Issue Book for Librarians, Request Book for Students)."
            ]
        },
        {
            "file": "templates/issue_loan.html",
            "cat": "Circulation Console",
            "lang": "HTML5 / Jinja2 / JavaScript",
            "purpose": "Manual book checkout interface featuring live substring autocomplete dropdowns for user selection and book selection.",
            "checklist": [
                "Verify that member search input uses live substring filtering (matching any part of the query against name or username).",
                "Verify that book title search filters titles containing the substring.",
                "Verify client-side validation that at least one physical copy is available before allowing form submission."
            ]
        },
        {
            "file": "templates/loan_requests.html",
            "cat": "Circulation Queue",
            "lang": "HTML5 / Jinja2",
            "purpose": "Administrative loan request review and approval queue.",
            "checklist": [
                "Verify table header typo fix: column displays 'REQUEST TIMESTAMP' with a space.",
                "Verify Approve and Reject buttons include CSRF tokens and target correct route endpoints."
            ]
        },
        {
            "file": "templates/graph_visualizer.html",
            "cat": "Knowledge Graph Visualizer",
            "lang": "HTML5 / Jinja2 / Vis.js",
            "purpose": "Interactive Vis.js knowledge graph visualizer featuring Barnes-Hut physics, dynamic state-aware Play/Pause controls, drawer details, and filter pills.",
            "checklist": [
                "Verify that #physicsToggleBtn displays Pause icon (⏸️) when simulation is actively running, and Play icon (▶️) when frozen.",
                "Verify that updatePhysicsBtnUI hides the button (display: none) when visible nodes count is 0.",
                "Verify that reStabilize() automatically restores isPhysicsActive = true and syncs the button icon.",
                "Verify that view switcher resets physics and loads correct subgraph."
            ]
        },
        {
            "file": "templates/catalog.html",
            "cat": "Catalog & Search",
            "lang": "HTML5 / Jinja2",
            "purpose": "Master book catalog interface with live search and category browsing cards.",
            "checklist": [
                "Verify category card subtitles are role-scoped: Admin/Librarian see 'inspect copy availability, and manage loans'; Staff/Student see 'check real-time copy availability, and request loans'.",
                "Verify '+ Register New Book' button renders a single clean plus sign."
            ]
        },
        {
            "file": "templates/category_books.html",
            "cat": "Category Subgraph Browser",
            "lang": "HTML5 / Jinja2",
            "purpose": "Category-filtered book list with real-time copy availability badges and role-based action buttons.",
            "checklist": [
                "Verify single plus sign on Register New Book button.",
                "Verify copy status badges (Available, Total) and loan request buttons for eligible members."
            ]
        },
        {
            "file": "templates/recommendations.html",
            "cat": "AI Recommendation Engine",
            "lang": "HTML5 / Jinja2",
            "purpose": "AI graph recommendation dashboard based on collaborative borrowing similarity and graph proximity.",
            "checklist": [
                "Verify that raw debug label '(Jaccard Graph Similarity)' has been completely removed from recommendation cards.",
                "Verify clean rendering of recommendation reasons and borrow request triggers."
            ]
        },
        {
            "file": "templates/book_bridge.html",
            "cat": "Peer Sharing Network",
            "lang": "HTML5 / Jinja2",
            "purpose": "Peer-to-peer student and faculty book sharing and community borrowing exchange.",
            "checklist": [
                "Verify listing submission form and peer borrow request workflow.",
                "Verify peer contact detail visibility and request status tracking."
            ]
        },
        {
            "file": "templates/login.html",
            "cat": "Authentication",
            "lang": "HTML5 / Jinja2",
            "purpose": "User login portal with CSRF protection and role-aware navigation redirection.",
            "checklist": [
                "Verify CSRF token input field.",
                "Verify form submission targeting /login."
            ]
        },
        {
            "file": "templates/register.html",
            "cat": "User Registration",
            "lang": "HTML5 / Jinja2",
            "purpose": "New member registration form with campus role selection and input validation.",
            "checklist": [
                "Verify role selection (Student, Staff).",
                "Verify password confirmation and CSRF protection."
            ]
        },
        {
            "file": "templates/change_password.html",
            "cat": "Credentials Management",
            "lang": "HTML5 / Jinja2",
            "purpose": "Self-service password modification interface enforcing current password verification.",
            "checklist": [
                "Verify current password validation field.",
                "Verify new password matching validation."
            ]
        },
        {
            "file": "templates/my_fines.html",
            "cat": "Fine Management",
            "lang": "HTML5 / Jinja2",
            "purpose": "Member fine inspection and settlement history interface.",
            "checklist": [
                "Verify fine status badge rendering (Unpaid, Paid, Waived).",
                "Verify settlement status reporting."
            ]
        },
        {
            "file": "templates/add_book.html",
            "cat": "Catalog Management",
            "lang": "HTML5 / Jinja2",
            "purpose": "New book registration form with automatic physical copy generation.",
            "checklist": [
                "Verify author, publisher, category inputs and copy count creation."
            ]
        },
        {
            "file": "templates/edit_book.html",
            "cat": "Catalog Editing",
            "lang": "HTML5 / Jinja2",
            "purpose": "Book metadata editing interface for Librarians and Admins.",
            "checklist": [
                "Verify title, ISBN, and publication year modification fields."
            ]
        },
        {
            "file": "templates/learning_paths.html",
            "cat": "Academic Pathways",
            "lang": "HTML5 / Jinja2",
            "purpose": "Curated academic book tracks and sequential learning paths.",
            "checklist": [
                "Verify milestone progression and prerequisite reading trail links."
            ]
        },
        {
            "file": "templates/library_analytics.html",
            "cat": "System Analytics",
            "lang": "HTML5 / Jinja2",
            "purpose": "Circulation analytics and category distribution reporting interface.",
            "checklist": [
                "Verify borrowing trend charts and category KPI statistics."
            ]
        },
        {
            "file": "templates/unauthorized.html",
            "cat": "Security & RBAC",
            "lang": "HTML5 / Jinja2",
            "purpose": "403 Forbidden security error page shown when role boundaries are violated.",
            "checklist": [
                "Verify clear denial message and redirect link to dashboard."
            ]
        }
    ]

    total_files_compiled = 0
    total_lines_compiled = 0

    for item in SOURCE_FILES:
        filepath = item["file"]
        chunks, line_count = load_file_chunks(filepath, lines_per_chunk=80)
        if not chunks:
            print(f"Warning: file {filepath} not found or empty.")
            continue

        total_files_compiled += 1
        total_lines_compiled += line_count
        print(f"Compiling [{total_files_compiled}/{len(SOURCE_FILES)}] {filepath} ({line_count} lines, {len(chunks)} pages)...")

        # Add Header Callout
        header_card = build_file_header_card(
            filename=item["file"],
            category=item["cat"],
            lang=item["lang"],
            total_lines=line_count,
            purpose=item["purpose"],
            checklist_items=item["checklist"],
            styles=styles
        )
        story.append(header_card)
        story.append(Spacer(1, 4))

        # Add Code Chunks
        for idx, chunk in enumerate(chunks):
            story.append(Preformatted(chunk, styles['CodeStyle']))
            # Add page break between chunks, except after the last chunk
            if idx < len(chunks) - 1:
                story.append(PageBreak())
        
        story.append(Spacer(1, 14))

    print(f"\nBuilding PDF document ({total_files_compiled} files, {total_lines_compiled} total lines)...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Build Completed in {time.time()-t0:.2f}s!")
    print(f"Output saved to: {OUTPUT_PDF}")
    file_size_mb = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
    print(f"Final PDF Size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    build_pdf()
