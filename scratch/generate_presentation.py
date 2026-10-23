import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ==============================================================================
# COLOR PALETTE DEFINITION (Modern Academic Dark Glassmorphism)
# ==============================================================================
BG_DARK      = RGBColor(11, 15, 25)       # #0B0F19 - Base Canvas
CARD_BG      = RGBColor(22, 30, 49)       # #161E31 - Elevated Card
CARD_BORDER  = RGBColor(45, 60, 90)       # #2D3C5A - Card Stroke
CODE_BG      = RGBColor(15, 23, 42)       # #0F172A - Code Panel Fill
ACCENT_BLUE  = RGBColor(59, 130, 246)     # #3B82F6 - Primary Brand Blue
ACCENT_CYAN  = RGBColor(6, 182, 212)      # #06B6D4 - Secondary Cyan
ACCENT_GREEN = RGBColor(16, 185, 129)     # #10B981 - Success Green
ACCENT_AMBER = RGBColor(245, 158, 11)     # #F59E0B - Warning Amber
ACCENT_ROSE  = RGBColor(244, 63, 94)      # #F43F5E - Rose/Red Accent
TEXT_WHITE   = RGBColor(248, 250, 252)    # #F8FAFC - Primary Text
TEXT_MUTED   = RGBColor(148, 163, 184)    # #94A3B8 - Secondary Muted
TEXT_DIM     = RGBColor(100, 116, 139)    # #64748B - Subtle Caption Text

FONT_HEADING = "Segoe UI"
FONT_BODY    = "Segoe UI"
FONT_CODE    = "Consolas"

# Asset Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ER_IMAGE_PATH = r"C:\Users\ckart\.gemini\antigravity-ide\brain\e12709c6-609a-40b2-b6c6-3265ad4d545b\.user_uploaded\media_1791301975093.jpg"
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "scratch", "screenshots")

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color=BG_DARK):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, section_tag, title_text, slide_num=None):
        # Top accent line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.04))
        line.fill.solid()
        line.fill.fore_color.rgb = ACCENT_BLUE
        line.line.fill.background()

        # Section Pill / Tag
        tx_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(8.0), Inches(0.3))
        tf_tag = tx_tag.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = section_tag.upper()
        p_tag.font.name = FONT_HEADING
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = ACCENT_CYAN

        # Slide Title
        tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(10.5), Inches(0.6))
        tf_title = tx_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

        # Slide Number Badge
        if slide_num:
            tx_num = slide.shapes.add_textbox(Inches(11.5), Inches(0.7), Inches(1.0), Inches(0.4))
            tf_num = tx_num.text_frame
            p_num = tf_num.paragraphs[0]
            p_num.alignment = PP_ALIGN.RIGHT
            p_num.text = f"{slide_num:02d} / 22"
            p_num.font.name = FONT_CODE
            p_num.font.size = Pt(11)
            p_num.font.bold = True
            p_num.font.color.rgb = TEXT_DIM

    def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg
        card.line.color.rgb = border
        card.line.width = Pt(1)
        return card

    # ==========================================================================
    # SLIDE 1: TITLE SLIDE
    # ==========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Decorative background glows
    g1 = s1.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.5), Inches(0.5), Inches(4.5), Inches(4.5))
    g1.fill.solid()
    g1.fill.fore_color.rgb = RGBColor(25, 45, 80)
    g1.line.fill.background()

    # Main Center Title Card
    c_title = add_card(s1, Inches(1.0), Inches(0.9), Inches(11.333), Inches(5.7), bg=RGBColor(16, 24, 40), border=RGBColor(59, 130, 246))

    tx = s1.shapes.add_textbox(Inches(1.4), Inches(1.15), Inches(10.5), Inches(2.3))
    tf = tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "VITCC ENTERPRISE LIBRARY MANAGEMENT SYSTEM"
    p.font.name = FONT_HEADING
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    p2 = tf.add_paragraph()
    p2.text = "Dual-Paradigm Relational & Graph Database Architecture for Next-Generation Academic Libraries"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(14)
    p2.font.color.rgb = ACCENT_CYAN
    p2.space_before = Pt(6)

    p3 = tf.add_paragraph()
    p3.text = "Comprehensive Database Design, PL/SQL Automation, Neo4j AuraDB Integration & RBAC Security"
    p3.font.name = FONT_BODY
    p3.font.size = Pt(11)
    p3.font.color.rgb = TEXT_MUTED
    p3.space_before = Pt(4)

    # Academic & Faculty Metadata Card (Left side)
    add_card(s1, Inches(1.4), Inches(3.6), Inches(4.8), Inches(2.6), bg=RGBColor(24, 34, 56), border=CARD_BORDER)
    tx_meta = s1.shapes.add_textbox(Inches(1.6), Inches(3.75), Inches(4.4), Inches(2.3))
    tf_meta = tx_meta.text_frame
    tf_meta.word_wrap = True

    p_m1 = tf_meta.paragraphs[0]
    p_m1.text = "ACADEMIC COURSE DETAILS"
    p_m1.font.name = FONT_HEADING
    p_m1.font.size = Pt(11)
    p_m1.font.bold = True
    p_m1.font.color.rgb = ACCENT_BLUE

    meta_items = [
        ("Course Code", "BACSE202"),
        ("Course Name", "Database Systems"),
        ("Slot", "F1+TF1"),
        ("Faculty Guide", "Dr. R. Priyadarshini"),
        ("Department", "School of Computer Science & Eng. (SCOPE)"),
        ("Institution", "Vellore Institute of Technology, Chennai")
    ]
    for label, val in meta_items:
        p_item = tf_meta.add_paragraph()
        p_item.space_before = Pt(3)
        run_lbl = p_item.add_run()
        run_lbl.text = f"{label}: "
        run_lbl.font.bold = True
        run_lbl.font.size = Pt(10)
        run_lbl.font.color.rgb = TEXT_WHITE
        run_val = p_item.add_run()
        run_val.text = val
        run_val.font.size = Pt(10)
        run_val.font.color.rgb = ACCENT_CYAN if label == "Slot" else TEXT_MUTED

    # Team Members Card (Right side)
    add_card(s1, Inches(6.5), Inches(3.6), Inches(5.4), Inches(2.6), bg=RGBColor(24, 34, 56), border=CARD_BORDER)
    tx_team = s1.shapes.add_textbox(Inches(6.7), Inches(3.75), Inches(5.0), Inches(2.3))
    tf_team = tx_team.text_frame
    tf_team.word_wrap = True

    p_t1 = tf_team.paragraphs[0]
    p_t1.text = "PROJECT DEVELOPMENT TEAM"
    p_t1.font.name = FONT_HEADING
    p_t1.font.size = Pt(11)
    p_t1.font.bold = True
    p_t1.font.color.rgb = ACCENT_GREEN

    members = [
        ("KARTHIK VALLIAPPAN C", "25BAI1051", "Lead Architecture, Graph Modeling, Backend & RBAC"),
        ("NITHIN RANGASWAMY", "25BAI1210", "Database Schema, SQL DDL/DML, Constraints & Auditing"),
        ("NATRAJ", "25BAI1079", "PL/SQL Programming, Stored Procedures & Triggers")
    ]
    for name, reg, role in members:
        p_mem = tf_team.add_paragraph()
        p_mem.space_before = Pt(6)
        r_name = p_mem.add_run()
        r_name.text = name + "  "
        r_name.font.bold = True
        r_name.font.size = Pt(11)
        r_name.font.color.rgb = TEXT_WHITE

        r_reg = p_mem.add_run()
        r_reg.text = f"[{reg}]"
        r_reg.font.name = FONT_CODE
        r_reg.font.size = Pt(10)
        r_reg.font.color.rgb = ACCENT_AMBER

        p_role = tf_team.add_paragraph()
        p_role.text = role
        p_role.font.size = Pt(9)
        p_role.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 2: AGENDA
    # ==========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Section 1: Project Introduction & Design", "Executive Presentation Agenda", 2)

    agenda_cards = [
        ("01", "Project Introduction & Design", [
            "Problem Statement & Academic Objectives",
            "Proposed Solution & System Scope",
            "Multi-Tier Architecture & Tech Stack",
            "Module Responsibilities & Data Flow"
        ], ACCENT_BLUE),
        ("02", "Database Design & Implementation", [
            "Conceptual Entity-Relationship (ER) Diagram",
            "Relational Schema Mapping & Normalization (BCNF)",
            "Table DDL & Comprehensive Integrity Constraints",
            "Sample Records & Referential Integrity Proof"
        ], ACCENT_CYAN),
        ("03", "SQL Queries & Database Programming", [
            "Application Feature-to-Query Mapping",
            "DDL, DML & Role-Based DCL Security",
            "Analytical Subqueries & Complex Joins / Views",
            "PL/SQL Triggers, Cursors, Procedures & Exceptions"
        ], ACCENT_GREEN),
        ("04", "Application Demonstration & Verification", [
            "Application Workflow & Code Architecture",
            "Live UI Screenshots: Circulation, Ledgers & Admin",
            "Graph Innovations: Explorer, Book Bridge & Recs",
            "Build Instructions, GitHub Repo & Outcomes"
        ], ACCENT_AMBER)
    ]

    for idx, (num, title, bullets, color) in enumerate(agenda_cards):
        left = Inches(0.8 + idx * 2.98)
        top = Inches(1.8)
        w = Inches(2.82)
        h = Inches(5.1)

        card = add_card(s2, left, top, w, h)
        # Top color tag
        tag = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, w, Inches(0.08))
        tag.fill.solid()
        tag.fill.fore_color.rgb = color
        tag.line.fill.background()

        tx = s2.shapes.add_textbox(left + Inches(0.15), top + Inches(0.2), w - Inches(0.3), h - Inches(0.4))
        tf = tx.text_frame
        tf.word_wrap = True

        p_num = tf.paragraphs[0]
        p_num.text = num
        p_num.font.name = FONT_CODE
        p_num.font.size = Pt(28)
        p_num.font.bold = True
        p_num.font.color.rgb = color

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(4)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = "• " + b
            pb.font.name = FONT_BODY
            pb.font.size = Pt(10)
            pb.font.color.rgb = TEXT_MUTED
            pb.space_before = Pt(10)

    # ==========================================================================
    # SLIDE 3: INTRODUCTION & PROJECT OVERVIEW
    # ==========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Section 1: Project Introduction & Design", "Introduction & Project Overview", 3)

    # 3 Cards Layout: Problem Statement, Proposed Solution, Tech Stack
    # Card 1: Problem Statement
    add_card(s3, Inches(0.8), Inches(1.7), Inches(3.7), Inches(5.2))
    tx1 = s3.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(3.3), Inches(4.8))
    tf1 = tx1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "PROBLEM STATEMENT"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = ACCENT_ROSE

    items1 = [
        "Traditional library systems rely solely on relational tables with high-latency recursive joins for prerequisite tracking.",
        "Students lack visibility into multi-degree academic reading roadmaps across disciplines.",
        "Disciplinary fines and loan quotas are frequently bypassed due to lack of real-time database constraints.",
        "Patron privacy is vulnerable when borrowing histories are exposed without RBAC masking."
    ]
    for it in items1:
        pi = tf1.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(10.5)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(8)

    # Card 2: Proposed Solution & Scope
    add_card(s3, Inches(4.8), Inches(1.7), Inches(3.7), Inches(5.2))
    tx2 = s3.shapes.add_textbox(Inches(5.0), Inches(1.85), Inches(3.3), Inches(4.8))
    tf2 = tx2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "PROPOSED SOLUTION & SCOPE"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = ACCENT_GREEN

    items2 = [
        "Engineered a Dual-Paradigm Architecture: Enterprise Relational Schema in Oracle 21c + Property Graph in Neo4j AuraDB.",
        "Strict 4-Role RBAC: Admin, Librarian, Faculty/Staff, and Academic Student.",
        "Automated Circulation Controls: 3-book patron quota enforcement, daily overdue fine auto-calculation (Rs. 5/day).",
        "Graph-Native Innovations: Live Interactive Graph Explorer, Book-to-Book Shortest Path Bridge, and Acyclic Prerequisite Roadmaps."
    ]
    for it in items2:
        pi = tf2.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(10.5)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(8)

    # Card 3: Technologies Used
    add_card(s3, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.2))
    tx3 = s3.shapes.add_textbox(Inches(9.0), Inches(1.85), Inches(3.3), Inches(4.8))
    tf3 = tx3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "TECHNOLOGY STACK"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = ACCENT_CYAN

    stack = [
        ("Frontend Presentation", "HTML5, Vanilla CSS Glassmorphism Dark Theme, Plus Jakarta Sans, JetBrains Mono"),
        ("Interactive Graphics", "Vis.js Network v9.1.2 (Physics-driven hierarchical graph canvas)"),
        ("Application Backend", "Python 3.12+, Flask 3.1, Flask-Session (Server-side files), Flask-WTF (CSRF)"),
        ("Relational Database", "Oracle Database 21c Enterprise (PL/SQL Triggers, Procedures, Constraints)"),
        ("Graph Database", "Neo4j AuraDB Cloud v5+ (Cypher traversal, shortestPath algorithms)"),
        ("Quality Assurance", "7 Automated Test Suites with 100% Phase-by-Phase Verification")
    ]
    for title, desc in stack:
        pi = tf3.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = desc
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 4: SYSTEM DESIGN & MULTI-TIER ARCHITECTURE
    # ==========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Section 1: Project Introduction & Design", "System Design & Multi-Tier Architecture", 4)

    # 4 Architecture Tier Boxes
    tiers = [
        ("TIER 1: PRESENTATION LAYER", "Client-Side User Interface", [
            "Glassmorphism Dark-Mode Web Portal (Vanilla CSS & HTML5)",
            "Vis.js Interactive Physics Network for Knowledge Graphs",
            "Role-Adapted Views: Admin, Librarian, Faculty/Staff, Student",
            "Real-Time Barcode & Hyphen-Agnostic ISBN Search"
        ], ACCENT_BLUE),
        ("TIER 2: APPLICATION & SECURITY LAYER", "Flask WSGI Middleware & RBAC", [
            "Central Controller (app.py) managing 24 template endpoints",
            "Flask-WTF CSRF Protection on all mutable POST requests",
            "Role-Based Access Control (@role_required, @login_required)",
            "10-minute Server-Side Idle Session Expiration & Sanitization"
        ], ACCENT_CYAN),
        ("TIER 3: DATA ACCESS & ORCHESTRATION", "Dual Database Drivers", [
            "Neo4j Bolt Protocol (neo4j+s://) with Cypher Query Language",
            "cx_Oracle / Oracle Client Driver for Relational Transactions",
            "Transaction Controller: Atomic Copy Status & Loan Handover",
            "Dynamic Date Wrapping & Patron Privacy Masking Middleware"
        ], ACCENT_GREEN),
        ("TIER 4: PERSISTENCE & STORAGE TIER", "Dual-Paradigm Database", [
            "Oracle 21c Relational Tables: 10 tables in BCNF, constraints, PL/SQL",
            "Neo4j AuraDB Graph: 9 node entity types, 7 relationship edges",
            "Autonomous Triggers: Quota enforcement, copy synchronization",
            "Continuous Integrity Checks: Foreign Key Cascades & Locks"
        ], ACCENT_AMBER)
    ]

    for idx, (heading, sub, points, col) in enumerate(tiers):
        left = Inches(0.8)
        top = Inches(1.7 + idx * 1.35)
        w = Inches(11.733)
        h = Inches(1.2)

        add_card(s4, left, top, w, h)
        # Left color bar
        bar = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(0.12), h)
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tx = s4.shapes.add_textbox(left + Inches(0.3), top + Inches(0.08), Inches(3.2), h - Inches(0.16))
        tf = tx.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = heading
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_MUTED

        tx_pts = s4.shapes.add_textbox(left + Inches(3.6), top + Inches(0.08), Inches(8.0), h - Inches(0.16))
        tf_pts = tx_pts.text_frame
        tf_pts.word_wrap = True
        for p_idx, pt_text in enumerate(points):
            p_pt = tf_pts.paragraphs[0] if p_idx == 0 else tf_pts.add_paragraph()
            p_pt.text = "• " + pt_text
            p_pt.font.size = Pt(9.5)
            p_pt.font.color.rgb = TEXT_WHITE
            if p_idx > 0:
                p_pt.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 5: ER DIAGRAM AND TABLE MAPPING
    # ==========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Section 2: Database Design & Implementation", "Conceptual Data Modeling — ER Diagram & Entity Mapping", 5)

    # Left: Embed actual user's ER diagram image
    add_card(s5, Inches(0.8), Inches(1.7), Inches(6.8), Inches(5.3))
    if os.path.exists(ER_IMAGE_PATH):
        s5.shapes.add_picture(ER_IMAGE_PATH, Inches(0.95), Inches(1.85), width=Inches(6.5))

    tx_cap = s5.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(6.8), Inches(0.4))
    p_cap = tx_cap.text_frame.paragraphs[0]
    p_cap.alignment = PP_ALIGN.CENTER
    p_cap.text = "Figure: Conceptual Entity-Relationship (ER) Diagram of the Library System"
    p_cap.font.size = Pt(9)
    p_cap.font.italic = True
    p_cap.font.color.rgb = TEXT_MUTED

    # Right: Cardinality & Entity Mapping Analysis
    add_card(s5, Inches(7.8), Inches(1.7), Inches(4.733), Inches(5.3))
    tx_map = s5.shapes.add_textbox(Inches(8.0), Inches(1.85), Inches(4.333), Inches(4.9))
    tf_map = tx_map.text_frame
    tf_map.word_wrap = True

    p = tf_map.paragraphs[0]
    p.text = "ENTITY & CARDINALITY MAPPING"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = ACCENT_CYAN

    mappings = [
        ("1:N PUBLISHER -> BOOKS", "One publisher produces many book titles; each title belongs to exactly one publisher."),
        ("M:N BOOKS <-> AUTHORS", "A book can have multiple co-authors; an author writes multiple books. Resolved via BOOK_AUTHORS associative table."),
        ("1:N BOOK -> BOOK_COPIES", "Decouples abstract bibliographic metadata from physical trackable inventory copies."),
        ("1:N USER -> LOANS", "A patron can have multiple historical borrowing events, strictly capped at 3 active concurrent loans."),
        ("1:1 LOAN -> FINES", "An overdue loan generates a financial penalty record with automated Rs. 5/day calculation."),
        ("RELATIONAL NORMALIZATION", "Member, Employee, and Admin conceptual entities unified into USERS table with Role-Based Access Control.")
    ]
    for rel, exp in mappings:
        pi = tf_map.add_paragraph()
        pi.space_before = Pt(6)
        r_r = pi.add_run()
        r_r.text = rel + "\n"
        r_r.font.bold = True
        r_r.font.size = Pt(10)
        r_r.font.color.rgb = ACCENT_AMBER
        r_e = pi.add_run()
        r_e.text = exp
        r_e.font.size = Pt(9)
        r_e.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 6: RELATIONAL SCHEMA & NORMALIZATION
    # ==========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Section 2: Database Design & Implementation", "Relational Schema & Normalization Proof (BCNF)", 6)

    # 10 Relational Tables Display (2 Columns)
    add_card(s6, Inches(0.8), Inches(1.7), Inches(7.0), Inches(5.3))
    tx_sch = s6.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(6.6), Inches(4.9))
    tf_sch = tx_sch.text_frame
    tf_sch.word_wrap = True

    p = tf_sch.paragraphs[0]
    p.text = "RELATIONAL SCHEMA (PRIMARY & FOREIGN KEYS)"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_BLUE

    schema_tables = [
        ("CATEGORIES", "category_id [PK], category_name, description"),
        ("PUBLISHERS", "publisher_id [PK], name, address, phone, email"),
        ("AUTHORS", "author_id [PK], first_name, last_name, bio"),
        ("BOOKS", "book_id [PK], title, isbn, publication_year, category_id [FK], publisher_id [FK]"),
        ("BOOK_AUTHORS", "book_id [PK, FK], author_id [PK, FK]"),
        ("BOOK_COPIES", "copy_id [PK], book_id [FK], status, acquisition_date"),
        ("USERS", "user_id [PK], username, password_hash, email, role, account_status"),
        ("LOANS", "loan_id [PK], copy_id [FK], user_id [FK], issue_date, due_date, return_date, issued_by [FK]"),
        ("LOAN_REQUESTS", "request_id [PK], user_id [FK], book_id [FK], request_date, status, copy_id [FK]"),
        ("FINES", "fine_id [PK], loan_id [FK], fine_amount, payment_status, payment_date, collected_by [FK]")
    ]

    for tbl, cols in schema_tables:
        p_t = tf_sch.add_paragraph()
        p_t.space_before = Pt(4)
        r1 = p_t.add_run()
        r1.text = f"{tbl} ("
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = ACCENT_CYAN

        # Highlight PK and FK
        r2 = p_t.add_run()
        r2.text = cols
        r2.font.size = Pt(9)
        r2.font.name = FONT_CODE
        r2.font.color.rgb = TEXT_WHITE

        r3 = p_t.add_run()
        r3.text = ")"
        r3.font.bold = True
        r3.font.size = Pt(9.5)
        r3.font.color.rgb = ACCENT_CYAN

    # Right: Normalization Analysis Card
    add_card(s6, Inches(8.0), Inches(1.7), Inches(4.533), Inches(5.3))
    tx_norm = s6.shapes.add_textbox(Inches(8.2), Inches(1.85), Inches(4.133), Inches(4.9))
    tf_norm = tx_norm.text_frame
    tf_norm.word_wrap = True

    p = tf_norm.paragraphs[0]
    p.text = "NORMALIZATION JUSTIFICATION"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_GREEN

    norms = [
        ("First Normal Form (1NF)", "All attributes contain atomic, indivisible values. Multivalued authors and inventory copies are split into distinct relational tables."),
        ("Second Normal Form (2NF)", "No partial functional dependencies exist. In BOOK_AUTHORS, composite key {book_id, author_id} determines full relationship membership."),
        ("Third Normal Form (3NF)", "Eliminated all transitive dependencies (e.g. category_name determined solely by category_id, not by book_id)."),
        ("Boyce-Codd Normal Form (BCNF)", "Every functional dependency X -> Y has X as a candidate key. Prevents update, insertion, and deletion anomalies across loan lifecycles.")
    ]
    for lvl, exp in norms:
        pi = tf_norm.add_paragraph()
        pi.space_before = Pt(8)
        r1 = pi.add_run()
        r1.text = lvl + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = exp
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 7: TABLE CREATION AND CONSTRAINTS
    # ==========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Section 2: Database Design & Implementation", "Table Creation & Comprehensive Integrity Constraints", 7)

    # Left: SQL DDL Code Panel
    add_card(s7, Inches(0.8), Inches(1.7), Inches(6.8), Inches(5.3), bg=CODE_BG)
    tx_code = s7.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(6.4), Inches(4.9))
    tf_code = tx_code.text_frame
    tf_code.word_wrap = True

    sql_ddl = """-- Comprehensive Constraints in Oracle DDL
CREATE TABLE USERS (
    user_id        NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    username       VARCHAR2(50) NOT NULL UNIQUE,
    email          VARCHAR2(100) NOT NULL UNIQUE,
    password_hash  VARCHAR2(255) NOT NULL,
    role           VARCHAR2(20) DEFAULT 'Student' NOT NULL,
    account_status VARCHAR2(20) DEFAULT 'Active' NOT NULL,
    CONSTRAINT chk_user_role CHECK (role IN ('Admin', 'Librarian', 'Staff', 'Student')),
    CONSTRAINT chk_user_status CHECK (account_status IN ('Active', 'Suspended'))
);

CREATE TABLE BOOK_COPIES (
    copy_id NUMBER PRIMARY KEY,
    book_id NUMBER NOT NULL REFERENCES BOOKS(book_id) ON DELETE CASCADE,
    status  VARCHAR2(20) DEFAULT 'Available' NOT NULL,
    CONSTRAINT chk_copy_status CHECK (status IN ('Available', 'Borrowed', 'Reserved', 'Maintenance'))
);

CREATE TABLE LOANS (
    loan_id     NUMBER PRIMARY KEY,
    copy_id     NUMBER NOT NULL REFERENCES BOOK_COPIES(copy_id),
    user_id     NUMBER NOT NULL REFERENCES USERS(user_id) ON DELETE CASCADE,
    issue_date  DATE DEFAULT SYSDATE NOT NULL,
    due_date    DATE NOT NULL,
    return_date DATE,
    CONSTRAINT chk_loan_dates CHECK (due_date >= issue_date)
);"""

    p = tf_code.paragraphs[0]
    p.text = sql_ddl
    p.font.name = FONT_CODE
    p.font.size = Pt(8.5)
    p.font.color.rgb = RGBColor(165, 243, 252)

    # Right: Constraint Taxonomy & Explanation
    add_card(s7, Inches(7.8), Inches(1.7), Inches(4.733), Inches(5.3))
    tx_c = s7.shapes.add_textbox(Inches(8.0), Inches(1.85), Inches(4.333), Inches(4.9))
    tf_c = tx_c.text_frame
    tf_c.word_wrap = True

    p = tf_c.paragraphs[0]
    p.text = "INTEGRITY CONSTRAINTS IMPLEMENTED"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_AMBER

    constraints_info = [
        ("PRIMARY KEY", "Enforces entity integrity (user_id, book_id, loan_id). Prohibits duplicate or NULL primary values."),
        ("FOREIGN KEY & CASCADES", "Maintains referential integrity. Deleting a book automatically removes dependent copies (ON DELETE CASCADE), preventing dangling references."),
        ("CHECK CONSTRAINTS", "chk_user_role validates authorized roles; chk_copy_status prevents illegal inventory transitions; chk_loan_dates guarantees due_date >= issue_date."),
        ("UNIQUE CONSTRAINTS", "Guarantees uniqueness across ISBN, username, and institutional email addresses."),
        ("DEFAULT & NOT NULL", "Enforces required metadata and sets default values ('Active' account, 'Available' status, 'Unpaid' fine).")
    ]
    for c_type, desc in constraints_info:
        pi = tf_c.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = c_type + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 8: SAMPLE DATA & INTEGRITY VERIFICATION
    # ==========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Section 2: Database Design & Implementation", "Sample Data Records & Referential Integrity Verification", 8)

    # Data Records Table Layout (Top)
    add_card(s8, Inches(0.8), Inches(1.7), Inches(11.733), Inches(2.6))
    tx_t = s8.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(2.3))
    tf_t = tx_t.text_frame
    tf_t.word_wrap = True

    p = tf_t.paragraphs[0]
    p.text = "SAMPLE ENTITY RECORDS POPULATED IN DATABASE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_GREEN

    table_shape = s8.shapes.add_table(4, 6, Inches(1.0), Inches(2.1), Inches(11.333), Inches(2.0))
    table = table_shape.table
    table.columns[0].width = Inches(1.2)
    table.columns[1].width = Inches(2.4)
    table.columns[2].width = Inches(2.0)
    table.columns[3].width = Inches(1.8)
    table.columns[4].width = Inches(2.0)
    table.columns[5].width = Inches(1.933)

    headers = ["Table", "Identifier (PK)", "Attribute 1", "Attribute 2", "Status / Role", "Foreign Key Ref"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(9.5)
            p.font.color.rgb = ACCENT_CYAN

    rows_data = [
        ["USERS", "user_id = 1", "admin", "admin@vit.edu", "Role: Admin", "Account: Active"],
        ["BOOKS", "book_id = 2", "Clean Code: Agile Craft", "ISBN: 978-0132350884", "Pub Year: 2008", "Category: CS (ID: 1)"],
        ["LOANS", "loan_id = 14", "copy_id = 2", "user_id = 6 (student)", "Issue: 2026-03-01", "Due: 2026-03-15 (Overdue)"]
    ]
    for r_idx, r_data in enumerate(rows_data, start=1):
        for c_idx, val in enumerate(r_data):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(18, 26, 43) if r_idx % 2 == 1 else RGBColor(14, 20, 34)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(9)
                p.font.color.rgb = TEXT_WHITE

    # Bottom 2 Cards: Referential Integrity & Constraint Rejection Test
    add_card(s8, Inches(0.8), Inches(4.5), Inches(5.7), Inches(2.5))
    tx_b1 = s8.shapes.add_textbox(Inches(1.0), Inches(4.6), Inches(5.3), Inches(2.2))
    tf_b1 = tx_b1.text_frame
    tf_b1.word_wrap = True
    p = tf_b1.paragraphs[0]
    p.text = "REFERENTIAL INTEGRITY ENFORCEMENT"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_BLUE

    items_b1 = [
        "Foreign Key Cascade: Deleting a category safely cascades to book catalog references or rejects if active loans exist.",
        "Copy Status Synchronization: Physical copy status is automatically flipped to 'Borrowed' upon loan issue and 'Available' upon check-in.",
        "Loan Anonymization on User Removal: Returning loans anonymize borrower references (user_id = 0) to preserve institutional statistical ledgers."
    ]
    for it in items_b1:
        pi = tf_b1.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(9)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(4)

    add_card(s8, Inches(6.8), Inches(4.5), Inches(5.733), Inches(2.5))
    tx_b2 = s8.shapes.add_textbox(Inches(7.0), Inches(4.6), Inches(5.3), Inches(2.2))
    tf_b2 = tx_b2.text_frame
    tf_b2.word_wrap = True
    p = tf_b2.paragraphs[0]
    p.text = "CONSTRAINT REJECTION TESTING (ERROR-PROOFING)"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_ROSE

    items_b2 = [
        "Duplicate ISBN Rejection: ORA-00001 unique constraint violated if an existing ISBN is registered again.",
        "Borrowing Quota Rejection: PL/SQL Trigger and Flask middleware reject 4th borrowing attempt with 'Quota Limit Reached'.",
        "Disciplinary Fine Locking: Borrowing is blocked when unpaid disciplinary fines exist on a patron's ledger."
    ]
    for it in items_b2:
        pi = tf_b2.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(9)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(4)

    # ==========================================================================
    # SLIDE 9: SQL QUERIES FOR APPLICATION FEATURES
    # ==========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Section 3: SQL Queries & Database Programming", "SQL Queries Mapped to Application Features", 9)

    feature_queries = [
        ("Catalog & Category Search (/catalog, /category/<id>)",
         "SELECT b.book_id, b.title, b.isbn, b.publication_year, c.category_name,\n       COUNT(cp.copy_id) AS total_copies,\n       SUM(CASE WHEN cp.status = 'Available' THEN 1 ELSE 0 END) AS available_copies\nFROM BOOKS b\nJOIN CATEGORIES c ON b.category_id = c.category_id\nLEFT JOIN BOOK_COPIES cp ON b.book_id = cp.book_id\nWHERE LOWER(b.title) LIKE :query OR REPLACE(b.isbn, '-', '') LIKE :isbn_query\nGROUP BY b.book_id, b.title, b.isbn, b.publication_year, c.category_name;",
         "Supports instant filtering across titles, hyphenated/unhyphenated ISBNs, and authors with copy availability metrics."),

        ("Issue Loan Transaction (/issue_loan)",
         "-- Atomic Loan Creation and Copy Status Lock\nINSERT INTO LOANS (loan_id, copy_id, user_id, issue_date, due_date, issued_by)\nVALUES (seq_loan_id.NEXTVAL, :copy_id, :user_id, SYSDATE, SYSDATE + 14, :admin_id);\n\nUPDATE BOOK_COPIES\nSET status = 'Borrowed'\nWHERE copy_id = :copy_id;",
         "Guarantees that a physical book copy cannot be double-issued to another patron concurrently.")
    ]

    for idx, (title, sql_text, desc) in enumerate(feature_queries):
        top = Inches(1.7 + idx * 2.65)
        add_card(s9, Inches(0.8), top, Inches(11.733), Inches(2.45))

        tx = s9.shapes.add_textbox(Inches(1.0), top + Inches(0.1), Inches(11.333), Inches(2.2))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

        p_sql = tf.add_paragraph()
        p_sql.text = sql_text
        p_sql.font.name = FONT_CODE
        p_sql.font.size = Pt(8.5)
        p_sql.font.color.rgb = RGBColor(186, 230, 253)
        p_sql.space_before = Pt(3)

        p_d = tf.add_paragraph()
        p_d.text = "Operational Purpose: " + desc
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = TEXT_MUTED
        p_d.space_before = Pt(3)

    # ==========================================================================
    # SLIDE 10: DDL, DML, AND DCL COMMANDS
    # ==========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Section 3: SQL Queries & Database Programming", "DDL, DML, and Role-Based DCL Security Commands", 10)

    cmd_sections = [
        ("DDL (DATA DEFINITION LANGUAGE)", [
            ("CREATE TABLE / INDEX", "CREATE TABLE LOAN_REQUESTS (\n  request_id NUMBER PRIMARY KEY,\n  user_id NUMBER REFERENCES USERS(user_id),\n  book_id NUMBER REFERENCES BOOKS(book_id),\n  status VARCHAR2(20) DEFAULT 'Pending'\n);"),
            ("ALTER TABLE CONSTRAINT", "ALTER TABLE FINES ADD CONSTRAINT chk_fine_amt\nCHECK (fine_amount >= 0);"),
            ("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX idx_isbn ON BOOKS(isbn);")
        ], ACCENT_BLUE),

        ("DML (DATA MANIPULATION LANGUAGE)", [
            ("INSERT DATA", "INSERT INTO BOOK_COPIES (copy_id, book_id, status)\nVALUES (seq_copy.NEXTVAL, 2, 'Available');"),
            ("UPDATE TRANSACTION", "UPDATE FINES SET payment_status = 'Paid',\npayment_date = SYSDATE WHERE fine_id = :fid;"),
            ("DELETE CONDITIONAL", "DELETE FROM LOAN_REQUESTS\nWHERE status = 'Rejected' AND request_date < SYSDATE-30;")
        ], ACCENT_GREEN),

        ("DCL (DATA CONTROL LANGUAGE)", [
            ("ROLE PROVISIONING", "CREATE ROLE LIBRARIAN_ROLE;\nCREATE ROLE STUDENT_ROLE;"),
            ("GRANT PRIVILEGES", "GRANT SELECT, INSERT, UPDATE ON LOANS\nTO LIBRARIAN_ROLE;\nGRANT SELECT ON BOOKS TO STUDENT_ROLE;"),
            ("REVOKE RESTRICTIONS", "REVOKE DELETE ON BOOKS FROM STUDENT_ROLE;\nREVOKE UPDATE ON USERS FROM LIBRARIAN_ROLE;")
        ], ACCENT_AMBER)
    ]

    for idx, (head, snippets, color) in enumerate(cmd_sections):
        left = Inches(0.8 + idx * 3.98)
        top = Inches(1.7)
        w = Inches(3.78)
        h = Inches(5.3)

        add_card(s10, left, top, w, h, bg=CODE_BG)
        # Top color tag
        tag = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, w, Inches(0.08))
        tag.fill.solid()
        tag.fill.fore_color.rgb = color
        tag.line.fill.background()

        tx = s10.shapes.add_textbox(left + Inches(0.15), top + Inches(0.15), w - Inches(0.3), h - Inches(0.3))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = head
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color

        for snip_title, snip_code in snippets:
            pt = tf.add_paragraph()
            pt.text = snip_title
            pt.font.bold = True
            pt.font.size = Pt(9.5)
            pt.font.color.rgb = TEXT_WHITE
            pt.space_before = Pt(8)

            pc = tf.add_paragraph()
            pc.text = snip_code
            pc.font.name = FONT_CODE
            pc.font.size = Pt(8)
            pc.font.color.rgb = RGBColor(186, 230, 253)
            pc.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 11: SUBQUERIES AND ANALYTICAL FILTERING
    # ==========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Section 3: SQL Queries & Database Programming", "Single-Row, Multiple-Row & Correlated Subqueries", 11)

    subqueries = [
        ("1. Single-Row Subquery (Scalar Comparison)",
         "SELECT b.book_id, b.title, b.publication_year\nFROM BOOKS b\nWHERE b.publication_year > (\n    SELECT AVG(publication_year)\n    FROM BOOKS\n    WHERE category_id = b.category_id\n);",
         "Identifies books published more recently than the average publication vintage of their respective subject category."),

        ("2. Multiple-Row Subquery with IN / NOT IN Operators",
         "SELECT u.user_id, u.username, u.email\nFROM USERS u\nWHERE u.user_id IN (\n    SELECT DISTINCT l.user_id\n    FROM LOANS l\n    JOIN FINES f ON l.loan_id = f.loan_id\n    WHERE f.payment_status = 'Unpaid'\n);",
         "Flags all patrons with outstanding overdue financial penalties to restrict borrowing permissions at checkout."),

        ("3. Correlated Subquery with EXISTS Operator",
         "SELECT b.book_id, b.title\nFROM BOOKS b\nWHERE EXISTS (\n    SELECT 1\n    FROM BOOK_COPIES cp\n    JOIN LOANS l ON cp.copy_id = l.copy_id\n    WHERE cp.book_id = b.book_id\n    GROUP BY cp.copy_id\n    HAVING COUNT(l.loan_id) >= 3\n);",
         "Discovers 'High Circulation Velocity' titles where copies have been actively checked out 3 or more times.")
    ]

    for idx, (title, sql_code, explain) in enumerate(subqueries):
        top = Inches(1.7 + idx * 1.75)
        add_card(s11, Inches(0.8), top, Inches(11.733), Inches(1.65))

        tx = s11.shapes.add_textbox(Inches(1.0), top + Inches(0.08), Inches(11.333), Inches(1.5))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

        p_sql = tf.add_paragraph()
        p_sql.text = sql_code
        p_sql.font.name = FONT_CODE
        p_sql.font.size = Pt(8.5)
        p_sql.font.color.rgb = RGBColor(165, 243, 252)
        p_sql.space_before = Pt(2)

        p_e = tf.add_paragraph()
        p_e.text = "Operational Analytics: " + explain
        p_e.font.size = Pt(9)
        p_e.font.color.rgb = TEXT_MUTED
        p_e.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 12: SQL FUNCTIONS (AGGREGATE & SCALAR)
    # ==========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Section 3: SQL Queries & Database Programming", "SQL Functions — Aggregate, String, Date & Analytical Math", 12)

    # 2 Column Comparison: Aggregate Functions & Scalar Functions
    # Left: Aggregate
    add_card(s12, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3))
    tx_agg = s12.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.9))
    tf_agg = tx_agg.text_frame
    tf_agg.word_wrap = True

    p = tf_agg.paragraphs[0]
    p.text = "AGGREGATE FUNCTIONS & GROUP BY"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_BLUE

    agg_points = [
        ("COUNT(*), COUNT(DISTINCT l.user_id)", "Measures total circulation transactions and distinct active patron engagement across semesters."),
        ("SUM(f.fine_amount)", "Computes cumulative institutional penalty revenue and outstanding unpaid receivables."),
        ("AVG(MONTHS_BETWEEN(SYSDATE, b.acquisition_date))", "Computes the mean retention age of catalog acquisitions for inventory deprecation."),
        ("MIN(due_date), MAX(due_date)", "Identifies the earliest pending return and latest active return deadlines across campus."),
        ("GROUP BY ... HAVING COUNT(*) > 5", "Filters prolific authors and high-density categories exceeding borrowing thresholds.")
    ]
    for fn, desc in agg_points:
        pi = tf_agg.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = fn + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # Right: Scalar Functions
    add_card(s12, Inches(6.8), Inches(1.7), Inches(5.733), Inches(5.3))
    tx_sc = s12.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.333), Inches(4.9))
    tf_sc = tx_sc.text_frame
    tf_sc.word_wrap = True

    p = tf_sc.paragraphs[0]
    p.text = "SCALAR, STRING & DATE FUNCTIONS"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_GREEN

    scalar_points = [
        ("TO_CHAR(issue_date, 'YYYY-MM-DD HH24:MI')", "Standardizes temporal audit timestamps across disparate client locales."),
        ("TRUNC(SYSDATE) - TRUNC(due_date)", "Evaluates precise elapsed calendar days for overdue fine calculations."),
        ("UPPER(u.username), LOWER(u.email)", "Normalizes patron authentication credentials to ensure case-insensitive identity matching."),
        ("REPLACE(b.isbn, '-', '')", "Strips punctuation from ISBN strings for seamless barcode and query pattern matching."),
        ("NVL(return_date, 'Active Loan')", "Handles NULL return dates gracefully in patron financial ledgers and dashboard reports.")
    ]
    for fn, desc in scalar_points:
        pi = tf_sc.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = fn + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 13: JOINS AND DATABASE VIEWS
    # ==========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)
    add_header(s13, "Section 3: SQL Queries & Database Programming", "Multi-Table Relational Joins & Abstract Database Views", 13)

    # Top: Multi-Table Joins
    add_card(s13, Inches(0.8), Inches(1.7), Inches(11.733), Inches(2.6))
    tx_j = s13.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(2.3))
    tf_j = tx_j.text_frame
    tf_j.word_wrap = True

    p = tf_j.paragraphs[0]
    p.text = "MULTI-TABLE RELATIONAL JOINS (INNER & LEFT OUTER)"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_CYAN

    join_code = """-- 5-Table Master Circulation Ledger Join
SELECT l.loan_id, u.username, u.role, b.title, c.category_name, cp.copy_id, l.issue_date, l.due_date, l.return_date
FROM LOANS l
INNER JOIN USERS u        ON l.user_id = u.user_id
INNER JOIN BOOK_COPIES cp ON l.copy_id = cp.copy_id
INNER JOIN BOOKS b        ON cp.book_id = b.book_id
INNER JOIN CATEGORIES c   ON b.category_id = c.category_id
LEFT OUTER JOIN FINES f   ON l.loan_id = f.loan_id;"""

    pj = tf_j.add_paragraph()
    pj.text = join_code
    pj.font.name = FONT_CODE
    pj.font.size = Pt(8.5)
    pj.font.color.rgb = RGBColor(165, 243, 252)
    pj.space_before = Pt(3)

    # Bottom: Views
    add_card(s13, Inches(0.8), Inches(4.5), Inches(11.733), Inches(2.5))
    tx_v = s13.shapes.add_textbox(Inches(1.0), Inches(4.6), Inches(11.333), Inches(2.2))
    tf_v = tx_v.text_frame
    tf_v.word_wrap = True

    p = tf_v.paragraphs[0]
    p.text = "DATABASE VIEWS FOR APPLICATION REPORTING & SECURITY MASKING"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_AMBER

    view_code = """-- Abstract View: Masks sensitive password hashes and pre-aggregates patron financial exposure
CREATE OR REPLACE VIEW VIEW_PATRON_FINANCIAL_SUMMARY AS
SELECT u.user_id, u.username, u.email, u.role, u.account_status,
       COUNT(DISTINCT l.loan_id) AS total_borrowings,
       NVL(SUM(CASE WHEN f.payment_status = 'Unpaid' THEN f.fine_amount ELSE 0 END), 0) AS total_unpaid_fines
FROM USERS u
LEFT JOIN LOANS l ON u.user_id = l.user_id
LEFT JOIN FINES f ON l.loan_id = f.loan_id
GROUP BY u.user_id, u.username, u.email, u.role, u.account_status;"""

    pv = tf_v.add_paragraph()
    pv.text = view_code
    pv.font.name = FONT_CODE
    pv.font.size = Pt(8.5)
    pv.font.color.rgb = RGBColor(254, 240, 138)
    pv.space_before = Pt(3)

    # ==========================================================================
    # SLIDE 14: TRIGGERS, CURSORS, AND AUTONOMOUS AUDITING
    # ==========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_header(s14, "Section 3: SQL Queries & Database Programming", "Database Triggers, Explicit Cursors & Automated Auditing", 14)

    # Left: PL/SQL Trigger
    add_card(s14, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3), bg=CODE_BG)
    tx_trg = s14.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.9))
    tf_trg = tx_trg.text_frame
    tf_trg.word_wrap = True

    p = tf_trg.paragraphs[0]
    p.text = "PL/SQL TRIGGER: QUOTA ENFORCEMENT"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_ROSE

    trg_code = """CREATE OR REPLACE TRIGGER trg_check_borrow_quota
BEFORE INSERT ON LOANS
FOR EACH ROW
DECLARE
    v_active_loans NUMBER;
BEGIN
    -- Count currently active unreturned books
    SELECT COUNT(*)
    INTO v_active_loans
    FROM LOANS
    WHERE user_id = :NEW.user_id
      AND return_date IS NULL;

    IF v_active_loans >= 3 THEN
        RAISE_APPLICATION_ERROR(-20001,
          'Policy Violation: Patron has reached max 3-book quota.');
    END IF;
END;"""
    pt = tf_trg.add_paragraph()
    pt.text = trg_code
    pt.font.name = FONT_CODE
    pt.font.size = Pt(8.5)
    pt.font.color.rgb = RGBColor(253, 164, 175)
    pt.space_before = Pt(4)

    # Right: Explicit Cursor Implementation
    add_card(s14, Inches(6.8), Inches(1.7), Inches(5.733), Inches(5.3), bg=CODE_BG)
    tx_cur = s14.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.333), Inches(4.9))
    tf_cur = tx_cur.text_frame
    tf_cur.word_wrap = True

    p = tf_cur.paragraphs[0]
    p.text = "EXPLICIT CURSOR: OVERDUE FINE BATCH"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_GREEN

    cur_code = """DECLARE
    CURSOR c_overdue IS
        SELECT loan_id, due_date, TRUNC(SYSDATE) - TRUNC(due_date) AS days_late
        FROM LOANS
        WHERE return_date IS NULL
          AND due_date < SYSDATE;
    r_ov c_overdue%ROWTYPE;
BEGIN
    OPEN c_overdue;
    LOOP
        FETCH c_overdue INTO r_ov;
        EXIT WHEN c_overdue%NOTFOUND;

        -- Auto-calculate Rs. 5/day fine
        UPDATE FINES
        SET fine_amount = r_ov.days_late * 5.0
        WHERE loan_id = r_ov.loan_id
          AND payment_status = 'Unpaid';
    END LOOP;
    CLOSE c_overdue;
    COMMIT;
END;"""
    pc = tf_cur.add_paragraph()
    pc.text = cur_code
    pc.font.name = FONT_CODE
    pc.font.size = Pt(8.5)
    pc.font.color.rgb = RGBColor(167, 243, 208)
    pc.space_before = Pt(4)

    # ==========================================================================
    # SLIDE 15: STORED PROCEDURES & EXCEPTION HANDLING
    # ==========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15)
    add_header(s15, "Section 3: SQL Queries & Database Programming", "Stored Procedures, Functions & Robust Exception Handling", 15)

    add_card(s15, Inches(0.8), Inches(1.7), Inches(11.733), Inches(5.3), bg=CODE_BG)
    tx_sp = s15.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(11.333), Inches(4.9))
    tf_sp = tx_sp.text_frame
    tf_sp.word_wrap = True

    p = tf_sp.paragraphs[0]
    p.text = "ENTERPRISE PL/SQL STORED PROCEDURE WITH PARAMETERS & TRANSACTION CONTROL"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_CYAN

    sp_code = """CREATE OR REPLACE PROCEDURE sp_issue_book_loan (
    p_user_id   IN  NUMBER,
    p_copy_id   IN  NUMBER,
    p_admin_id  IN  NUMBER,
    p_loan_id   OUT NUMBER,
    p_status    OUT VARCHAR2
) AS
    v_copy_status   VARCHAR2(20);
    v_unpaid_fines  NUMBER;
    ex_copy_busy    EXCEPTION;
    ex_unpaid_fines EXCEPTION;
BEGIN
    -- Step 1: Verify physical inventory availability
    SELECT status INTO v_copy_status FROM BOOK_COPIES WHERE copy_id = p_copy_id FOR UPDATE;
    IF v_copy_status != 'Available' THEN RAISE ex_copy_busy; END IF;

    -- Step 2: Verify zero outstanding financial penalties
    SELECT NVL(SUM(fine_amount), 0) INTO v_unpaid_fines
    FROM FINES f JOIN LOANS l ON f.loan_id = l.loan_id
    WHERE l.user_id = p_user_id AND f.payment_status = 'Unpaid';
    IF v_unpaid_fines > 0 THEN RAISE ex_unpaid_fines; END IF;

    -- Step 3: Insert loan and flip copy status atomically
    INSERT INTO LOANS (copy_id, user_id, issue_date, due_date, issued_by)
    VALUES (p_copy_id, p_user_id, SYSDATE, SYSDATE + 14, p_admin_id)
    RETURNING loan_id INTO p_loan_id;

    UPDATE BOOK_COPIES SET status = 'Borrowed' WHERE copy_id = p_copy_id;

    COMMIT;
    p_status := 'SUCCESS';
EXCEPTION
    WHEN ex_copy_busy THEN
        ROLLBACK;
        p_status := 'ERROR: Physical book copy is currently reserved or checked out.';
    WHEN ex_unpaid_fines THEN
        ROLLBACK;
        p_status := 'ERROR: Patron has outstanding unpaid disciplinary fines.';
    WHEN OTHERS THEN
        ROLLBACK;
        p_status := 'ERROR: ' || SQLERRM;
END sp_issue_book_loan;"""

    psp = tf_sp.add_paragraph()
    psp.text = sp_code
    psp.font.name = FONT_CODE
    psp.font.size = Pt(8.5)
    psp.font.color.rgb = RGBColor(199, 210, 254)
    psp.space_before = Pt(4)

    # ==========================================================================
    # SLIDE 16: APPLICATION WORKFLOW AND CODE STRUCTURE
    # ==========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16)
    add_header(s16, "Section 4: Application Implementation & Demonstration", "Application Workflow & Code Architecture", 16)

    # Left: Project Directory Architecture
    add_card(s16, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3), bg=CODE_BG)
    tx_dir = s16.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.9))
    tf_dir = tx_dir.text_frame
    tf_dir.word_wrap = True

    p = tf_dir.paragraphs[0]
    p.text = "PROJECT DIRECTORY TREE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_AMBER

    dir_tree = """DBS DA/
├── app.py                # Core Flask app (24 routes, RBAC, Cypher/SQL)
├── seed_all_data.py      # Neo4j schema constraints & sample data seed
├── requirements.txt      # Python dependencies (Flask, Neo4j, WTForms)
├── .env.example          # Database connection template
├── .gitignore            # Clean Git exclusions
├── README.md             # Comprehensive architecture documentation
├── templates/            # 24 Jinja2 HTML5 Glassmorphism Views
│   ├── base.html         # Sidebar, topbar, navigation & CSRF token
│   ├── dashboard.html    # Role-based dashboard (Admin/Staff/Student)
│   ├── catalog.html      # Category directory with copy aggregations
│   ├── issue_loan.html   # Physical loan creation desk
│   ├── graph_visualizer  # Interactive Vis.js live knowledge graph
│   ├── book_bridge.html  # Shortest path traversal explorer
│   └── learning_paths    # Acyclic prerequisite roadmaps
└── scratch/              # Verification suites (phase1..phase6, test runners)"""

    p_d = tf_dir.add_paragraph()
    p_d.text = dir_tree
    p_d.font.name = FONT_CODE
    p_d.font.size = Pt(8.5)
    p_d.font.color.rgb = RGBColor(254, 240, 138)
    p_d.space_before = Pt(4)

    # Right: End-to-End Request Flowchart
    add_card(s16, Inches(6.8), Inches(1.7), Inches(5.733), Inches(5.3))
    tx_flow = s16.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.333), Inches(4.9))
    tf_flow = tx_flow.text_frame
    tf_flow.word_wrap = True

    p = tf_flow.paragraphs[0]
    p.text = "HTTP REQUEST EXECUTION LIFECYCLE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = ACCENT_CYAN

    flow_steps = [
        ("Step 1: Inbound HTTP Request", "Client browser triggers route (e.g. POST /issue_loan) with form payload and CSRF token."),
        ("Step 2: Security & Session Middleware", "Verifies active session in filesystem, validates 10-minute idle activity timestamp, and decrypts CSRF token."),
        ("Step 3: Role-Based Authorization", "@role_required(['Admin', 'Librarian']) decorator checks user role; redirects unauthorized roles to 403 Access Denied."),
        ("Step 4: Query Execution & Business Logic", "Cypher query or PL/SQL procedure invoked via database driver session with parameterized injection protection."),
        ("Step 5: Dynamic View Rendering", "Jinja2 compiles response template with DateWrapper objects and privacy-masked attributes."),
        ("Step 6: Client DOM Update", "Rendered HTML/CSS returned with glassmorphic visuals and interactive Vis.js graph physics.")
    ]
    for step_h, step_b in flow_steps:
        pi = tf_flow.add_paragraph()
        pi.space_before = Pt(5)
        r1 = pi.add_run()
        r1.text = step_h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = step_b
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 17: WORKING APPLICATION SCREENSHOTS (CIRCULATION & ADMIN)
    # ==========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17)
    add_header(s17, "Section 4: Application Implementation & Demonstration", "Working Application Screenshots — Circulation & Administration", 17)

    shots_s17 = [
        ("01_public_login.png", "1. Secure Multi-Role Login Portal", Inches(0.8), Inches(1.7)),
        ("03_admin_dashboard.png", "2. Admin Dashboard & Active Circulation Ledgers", Inches(6.8), Inches(1.7)),
        ("06_admin_issue_loan.png", "3. Physical Book Loan Issuance Desk", Inches(0.8), Inches(4.5)),
        ("07_admin_loan_requests.png", "4. Digital Loan Requests & Copy Reservation Desk", Inches(6.8), Inches(4.5))
    ]

    for fname, caption, left, top in shots_s17:
        add_card(s17, left, top, Inches(5.7), Inches(2.6))
        fpath = os.path.join(SCREENSHOTS_DIR, fname)
        if os.path.exists(fpath):
            s17.shapes.add_picture(fpath, left + Inches(0.1), top + Inches(0.1), width=Inches(5.5), height=Inches(2.1))

        tx_c = s17.shapes.add_textbox(left, top + Inches(2.25), Inches(5.7), Inches(0.3))
        p = tx_c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = caption
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    # ==========================================================================
    # SLIDE 18: WORKING APPLICATION SCREENSHOTS (GRAPH & AI INNOVATIONS)
    # ==========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18)
    add_header(s18, "Section 4: Application Implementation & Demonstration", "Working Application Screenshots — Graph & AI Innovations", 18)

    shots_s18 = [
        ("11_admin_graph_visualizer.png", "1. Live Knowledge Graph Explorer (/graph_visualizer)", Inches(0.8), Inches(1.7)),
        ("12_admin_book_bridge.png", "2. Book Bridge Shortest Path Traversal (/book_bridge)", Inches(6.8), Inches(1.7)),
        ("09_admin_learning_paths.png", "3. Academic Learning Roadmaps DAG (/learning_paths)", Inches(0.8), Inches(4.5)),
        ("10_admin_ai_recommendations.png", "4. AI Collaborative Filtering Recommendations", Inches(6.8), Inches(4.5))
    ]

    for fname, caption, left, top in shots_s18:
        add_card(s18, left, top, Inches(5.7), Inches(2.6))
        fpath = os.path.join(SCREENSHOTS_DIR, fname)
        if os.path.exists(fpath):
            s18.shapes.add_picture(fpath, left + Inches(0.1), top + Inches(0.1), width=Inches(5.5), height=Inches(2.1))

        tx_c = s18.shapes.add_textbox(left, top + Inches(2.25), Inches(5.7), Inches(0.3))
        p = tx_c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = caption
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    # ==========================================================================
    # SLIDE 19: ACCESS CONTROL AND CUSTOM INNOVATIONS
    # ==========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19)
    add_header(s19, "Section 4: Application Implementation & Demonstration", "Role-Based Access Control & Advanced Graph Innovations", 19)

    # Left: RBAC Matrix Card
    add_card(s19, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3))
    tx_rbac = s19.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.9))
    tf_rbac = tx_rbac.text_frame
    tf_rbac.word_wrap = True

    p = tf_rbac.paragraphs[0]
    p.text = "ROLE-BASED ACCESS CONTROL (RBAC) MATRIX"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_BLUE

    rbac_rows = [
        ("ADMINISTRATOR", "Full authority: User provisioning, role assignment, account suspension, password reset, book catalog registration and book deletion. Complete audit visibility."),
        ("LIBRARIAN", "Circulation desk manager: Book loan creation, digital request approvals, copy reservations, check-in returns, and fine settlement. Cannot manage user accounts."),
        ("STAFF (FACULTY)", "Academic borrower: Search catalog, borrow up to 3 books, view academic prerequisite roadmaps, explore author degree centrality, and review fine ledgers."),
        ("STUDENT (PATRON)", "Academic patron: Search catalog, submit loan requests, view personalized AI recommendations, track prerequisite roadmaps, and monitor individual fines.")
    ]
    for r_name, r_desc in rbac_rows:
        pi = tf_rbac.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = r_name + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = ACCENT_CYAN
        r2 = pi.add_run()
        r2.text = r_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    # Right: Custom Graph Innovations Card
    add_card(s19, Inches(6.8), Inches(1.7), Inches(5.733), Inches(5.3))
    tx_inn = s19.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.333), Inches(4.9))
    tf_inn = tx_inn.text_frame
    tf_inn.word_wrap = True

    p = tf_inn.paragraphs[0]
    p.text = "CUSTOM ARCHITECTURAL INNOVATIONS"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_GREEN

    innovations = [
        ("1. Book-to-Book Bridge (Degrees of Separation)", "Uses Cypher shortestPath() algorithm to uncover multi-hop links between disparate titles via prerequisites, co-authors, and categories."),
        ("2. Academic Learning Roadmaps (Directed Acyclic Graphs)", "Hierarchical Vis.js network visualizer mapping foundational courses to advanced texts across CS, AI, and Distributed Systems."),
        ("3. Privacy-Preserving Patron Masking", "When Students or Staff browse the Live Knowledge Graph, other patrons' identities and borrow requests are anonymized in real time."),
        ("4. Author Degree Centrality & Borrowing Density", "Computes influential scholars by loan volume and category closeness centrality to inform faculty acquisition budgets.")
    ]
    for in_h, in_d in innovations:
        pi = tf_inn.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = in_h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = in_d
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 20: BUILD AND EXECUTION INSTRUCTIONS
    # ==========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20)
    add_header(s20, "Section 4: Application Implementation & Demonstration", "Build, Setup & Execution Instructions", 20)

    # 4 Steps Layout
    steps = [
        ("STEP 1: CLONE & VIRTUAL ENVIRONMENT", [
            "git clone https://github.com/Karthi16-png/LIBRARAY-MANAGEMENT-SYSTEM.git",
            "cd \"DBS DA\"",
            "python -m venv .venv",
            ".venv\\Scripts\\activate  (Windows)  OR  source .venv/bin/activate  (macOS/Linux)"
        ], ACCENT_BLUE),

        ("STEP 2: INSTALL DEPENDENCIES & CONFIGURE", [
            "pip install -r requirements.txt",
            "Configure Neo4j AuraDB credentials in .env or environment variables:",
            "  NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io",
            "  NEO4J_USERNAME=neo4j  |  NEO4J_PASSWORD=<password>"
        ], ACCENT_CYAN),

        ("STEP 3: SEED GRAPH DATABASE (OPTIONAL / INITIAL)", [
            "python seed_all_data.py",
            "-> Establishes 12 schema uniqueness constraints",
            "-> Seeds 11 users across all 4 roles, 10 categories, 15+ books, copies, and prerequisite edges"
        ], ACCENT_GREEN),

        ("STEP 4: LAUNCH PORTAL & RUN TEST SUITES", [
            "python app.py",
            "-> Access interactive portal at http://127.0.0.1:5000/",
            "Execute complete 7-phase automated verification runner:",
            "  python scratch/run_all_phases.py  (100% Passing)"
        ], ACCENT_AMBER)
    ]

    for idx, (st_title, st_lines, col) in enumerate(steps):
        top = Inches(1.7 + idx * 1.35)
        add_card(s20, Inches(0.8), top, Inches(11.733), Inches(1.2))

        # Left bar
        b = s20.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top, Inches(0.12), Inches(1.2))
        b.fill.solid()
        b.fill.fore_color.rgb = col
        b.line.fill.background()

        tx = s20.shapes.add_textbox(Inches(1.1), top + Inches(0.08), Inches(11.2), Inches(1.04))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = st_title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col

        for l in st_lines:
            pl = tf.add_paragraph()
            pl.text = l
            pl.font.name = FONT_CODE if "python" in l or "git" in l or "pip" in l else FONT_BODY
            pl.font.size = Pt(8.5)
            pl.font.color.rgb = TEXT_WHITE if "python" in l or "git" in l else TEXT_MUTED
            pl.space_before = Pt(1)

    # ==========================================================================
    # SLIDE 21: GITHUB REPOSITORY AND CONCLUSION
    # ==========================================================================
    s21 = prs.slides.add_slide(blank_layout)
    set_slide_background(s21)
    add_header(s21, "Section 4: Application Implementation & Demonstration", "GitHub Repository & Project Key Learning Outcomes", 21)

    # Left Card: GitHub Repository Info
    add_card(s21, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3))
    tx_gh = s21.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.9))
    tf_gh = tx_gh.text_frame
    tf_gh.word_wrap = True

    p = tf_gh.paragraphs[0]
    p.text = "OPEN-SOURCE GITHUB REPOSITORY"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_BLUE

    p_url = tf_gh.add_paragraph()
    p_url.text = "Repository URL:\nhttps://github.com/Karthi16-png/LIBRARAY-MANAGEMENT-SYSTEM"
    p_url.font.name = FONT_CODE
    p_url.font.size = Pt(9.5)
    p_url.font.color.rgb = ACCENT_CYAN
    p_url.space_before = Pt(8)

    gh_points = [
        ("Production Codebase", "Contains app.py (4,230 lines), seed scripts, 24 template views, and full verification test suites."),
        ("Branching & Hygiene", "Clean Git commit history on branch main with .gitignore preventing credential exposure and cache staging."),
        ("Documentation & Dossier", "Includes detailed README.md setup instructions and the 211-page master forensic audit report PDF.")
    ]
    for h, d in gh_points:
        pi = tf_gh.add_paragraph()
        pi.space_before = Pt(8)
        r1 = pi.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = d
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    # Right Card: Learning Outcomes & Future Enhancements
    add_card(s21, Inches(6.8), Inches(1.7), Inches(5.733), Inches(5.3))
    tx_out = s21.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.333), Inches(4.9))
    tf_out = tx_out.text_frame
    tf_out.word_wrap = True

    p = tf_out.paragraphs[0]
    p.text = "PROJECT OUTCOMES & FUTURE ROADMAP"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = ACCENT_GREEN

    outcomes = [
        ("Dual-Database Mastery", "Gained deep architectural expertise in bridging transactional relational schemas (Oracle 21c) with connected graph stores (Neo4j AuraDB)."),
        ("PL/SQL & Constraint Automation", "Successfully replaced error-prone application validation with autonomous database triggers, procedures, and check constraints."),
        ("Enterprise RBAC Implementation", "Engineered strict multi-role permission separation with patron privacy masking and audit trail logging."),
        ("Future Roadmap 1: RFID Hardware Integration", "Deploy physical RFID return drop-boxes for automated instantaneous check-in without librarian intervention."),
        ("Future Roadmap 2: SMS & Webhook Alerts", "Automated email and WhatsApp notifications for books nearing return deadlines to minimize disciplinary fines.")
    ]
    for o_h, o_d in outcomes:
        pi = tf_out.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = o_h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_WHITE
        r2 = pi.add_run()
        r2.text = o_d
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 22: CONCLUSION & Q&A
    # ==========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_background(s22)

    # Big Central Thank You Card
    add_card(s22, Inches(1.5), Inches(1.2), Inches(10.333), Inches(5.1), bg=RGBColor(18, 26, 45), border=ACCENT_BLUE)

    tx_q = s22.shapes.add_textbox(Inches(2.0), Inches(1.6), Inches(9.333), Inches(4.3))
    tf_q = tx_q.text_frame
    tf_q.word_wrap = True

    p = tf_q.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "THANK YOU!"
    p.font.name = FONT_HEADING
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    p2 = tf_q.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "Questions & Faculty Evaluation Discussion"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_CYAN
    p2.space_before = Pt(8)

    p3 = tf_q.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.text = "VITCC Enterprise Library Management System\nDual Relational & Graph Database Implementation"
    p3.font.size = Pt(13)
    p3.font.color.rgb = TEXT_MUTED
    p3.space_before = Pt(14)

    p4 = tf_q.add_paragraph()
    p4.alignment = PP_ALIGN.CENTER
    p4.text = "Course: BACSE202 — Database Systems | Slot: F1+TF1\nFaculty Guide: Dr. R. Priyadarshini"
    p4.font.size = Pt(12)
    p4.font.bold = True
    p4.font.color.rgb = ACCENT_AMBER
    p4.space_before = Pt(12)

    p5 = tf_q.add_paragraph()
    p5.alignment = PP_ALIGN.CENTER
    p5.text = "Team Members: KARTHIK VALLIAPPAN C (25BAI1051) | NITHIN RANGASWAMY (25BAI1210) | NATRAJ (25BAI1079)\nSchool of Computer Science & Engineering (SCOPE), VIT Chennai"
    p5.font.size = Pt(11)
    p5.font.color.rgb = TEXT_WHITE
    p5.space_before = Pt(14)

    # Save presentation
    output_path = os.path.join(BASE_DIR, "VITCC_Library_Management_System_Presentation.pptx")
    prs.save(output_path)
    print(f"[SUCCESS] PowerPoint presentation generated: {output_path}")
    print(f"Total Slides: {len(prs.slides)}")

if __name__ == "__main__":
    create_presentation()
