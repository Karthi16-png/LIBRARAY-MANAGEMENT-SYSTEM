import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ==============================================================================
# PROFESSIONAL ACADEMIC LIGHT PALETTE (Human/Student Presentation Standard)
# ==============================================================================
BG_PAGE       = RGBColor(248, 250, 252)   # #F8FAFC - Crisp, soft off-white
CARD_BG       = RGBColor(255, 255, 255)   # #FFFFFF - Pure white card fill
CARD_BORDER   = RGBColor(203, 213, 225)   # #CBD5E1 - Elegant slate gray border
NAVY_PRIMARY  = RGBColor(15, 37, 71)      # #0F2547 - Deep Academic Navy
BLUE_ACCENT   = RGBColor(30, 64, 175)     # #1E40AF - Classical Royal Blue
BLUE_HEADER   = RGBColor(238, 242, 255)   # #EEF2FF - Soft Blue Pill/Banner
TEXT_MAIN     = RGBColor(30, 41, 59)      # #1E293B - Deep Charcoal (High Legibility)
TEXT_MUTED    = RGBColor(71, 85, 105)     # #475569 - Secondary Muted Slate
CODE_BG       = RGBColor(241, 245, 249)   # #F1F5F9 - Light Code Box Fill
CODE_BORDER   = RGBColor(203, 213, 225)   # #CBD5E1 - Code Box Border
CODE_TEXT     = RGBColor(15, 23, 42)      # #0F172A - Sharp Code Text
BORDER_ACCENT = RGBColor(37, 99, 235)     # #2563EB - Accent Border Line

FONT_HEADING  = "Segoe UI"
FONT_BODY     = "Segoe UI"
FONT_CODE     = "Consolas"

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ER_IMAGE_PATH = r"C:\Users\ckart\.gemini\antigravity-ide\brain\e12709c6-609a-40b2-b6c6-3265ad4d545b\.user_uploaded\media_1791301975093.jpg"
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "scratch", "screenshots")

def create_professional_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color=BG_PAGE):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, section_tag, title_text, slide_num=None):
        # Subtle top header band
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.08))
        band.fill.solid()
        band.fill.fore_color.rgb = BLUE_ACCENT
        band.line.fill.background()

        # Section Tag / Breadcrumb
        tx_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(8.5), Inches(0.28))
        tf_tag = tx_tag.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = section_tag.upper()
        p_tag.font.name = FONT_HEADING
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = BLUE_ACCENT

        # Slide Title
        tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(10.5), Inches(0.6))
        tf_title = tx_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(21)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY_PRIMARY

        # Slide Number Badge
        if slide_num:
            tx_num = slide.shapes.add_textbox(Inches(11.5), Inches(0.45), Inches(1.0), Inches(0.4))
            tf_num = tx_num.text_frame
            p_num = tf_num.paragraphs[0]
            p_num.alignment = PP_ALIGN.RIGHT
            p_num.text = f"{slide_num:02d} / 22"
            p_num.font.name = FONT_BODY
            p_num.font.size = Pt(11)
            p_num.font.bold = True
            p_num.font.color.rgb = TEXT_MUTED

    def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg
        card.line.color.rgb = border
        card.line.width = Pt(1)
        return card

    # ==========================================================================
    # SLIDE 1: TITLE SLIDE (Clean Academic VIT Standard)
    # ==========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, RGBColor(255, 255, 255))

    # Top University Bar
    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.6))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_PRIMARY
    top_bar.line.fill.background()

    tx_top = s1.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.733), Inches(0.4))
    tf_top = tx_top.text_frame
    p_top = tf_top.paragraphs[0]
    p_top.alignment = PP_ALIGN.CENTER
    p_top.text = "VELLORE INSTITUTE OF TECHNOLOGY (VIT), CHENNAI  •  SCHOOL OF COMPUTER SCIENCE AND ENGINEERING (SCOPE)"
    p_top.font.name = FONT_HEADING
    p_top.font.size = Pt(10.5)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(255, 255, 255)

    # Main Project Title Box
    add_card(s1, Inches(0.8), Inches(0.9), Inches(11.733), Inches(2.5), bg=RGBColor(248, 250, 252), border=CARD_BORDER)

    tx_title = s1.shapes.add_textbox(Inches(1.1), Inches(1.1), Inches(11.133), Inches(2.1))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True

    p_t1 = tf_title.paragraphs[0]
    p_t1.text = "VITCC ENTERPRISE LIBRARY MANAGEMENT SYSTEM"
    p_t1.font.name = FONT_HEADING
    p_t1.font.size = Pt(26)
    p_t1.font.bold = True
    p_t1.font.color.rgb = NAVY_PRIMARY

    p_t2 = tf_title.add_paragraph()
    p_t2.text = "Dual-Paradigm Relational (Oracle 21c) and Graph (Neo4j AuraDB) Database Application Project"
    p_t2.font.name = FONT_HEADING
    p_t2.font.size = Pt(13)
    p_t2.font.bold = True
    p_t2.font.color.rgb = BLUE_ACCENT
    p_t2.space_before = Pt(6)

    p_t3 = tf_title.add_paragraph()
    p_t3.text = "Course Project Assessment (DA-3) covering Schema Normalization, PL/SQL Automation, Graph Traversal & Role-Based Access Control"
    p_t3.font.name = FONT_BODY
    p_t3.font.size = Pt(11)
    p_t3.font.color.rgb = TEXT_MUTED
    p_t3.space_before = Pt(4)

    # Two Structured Cards Below (Course Info on Left, Team Info on Right)
    # Left Card: Academic Details
    add_card(s1, Inches(0.8), Inches(3.6), Inches(5.7), Inches(3.4), bg=CARD_BG, border=CARD_BORDER)
    tx_c_info = s1.shapes.add_textbox(Inches(1.1), Inches(3.8), Inches(5.1), Inches(3.0))
    tf_c_info = tx_c_info.text_frame
    tf_c_info.word_wrap = True

    p = tf_c_info.paragraphs[0]
    p.text = "COURSE & FACULTY DETAILS"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    course_rows = [
        ("Course Code", "BACSE202"),
        ("Course Name", "Database Systems"),
        ("Class Slot", "F1+TF1"),
        ("Faculty Guide", "Dr. R. Priyadarshini"),
        ("Department", "Department of Computer Science & Engineering"),
        ("Institution", "VIT Chennai Campus")
    ]
    for label, val in course_rows:
        pi = tf_c_info.add_paragraph()
        pi.space_before = Pt(4)
        r1 = pi.add_run()
        r1.text = f"{label}: "
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = TEXT_MAIN
        r2 = pi.add_run()
        r2.text = val
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = BLUE_ACCENT if label == "Class Slot" else TEXT_MUTED

    # Right Card: Project Team
    add_card(s1, Inches(6.8), Inches(3.6), Inches(5.733), Inches(3.4), bg=CARD_BG, border=CARD_BORDER)
    tx_team = s1.shapes.add_textbox(Inches(7.1), Inches(3.8), Inches(5.133), Inches(3.0))
    tf_team = tx_team.text_frame
    tf_team.word_wrap = True

    p = tf_team.paragraphs[0]
    p.text = "SUBMITTED BY (PROJECT TEAM)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    team_members = [
        ("KARTHIK VALLIAPPAN C", "25BAI1051", "System Architecture, Neo4j Graph Model & Web Controllers"),
        ("NITHIN RANGASWAMY", "25BAI1210", "Relational Schema, Oracle DDL/DML, Constraints & Auditing"),
        ("NATRAJ", "25BAI1079", "PL/SQL Programming, Stored Procedures, Functions & Triggers")
    ]
    for name, regno, contrib in team_members:
        pi = tf_team.add_paragraph()
        pi.space_before = Pt(8)
        r1 = pi.add_run()
        r1.text = name + "  "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = TEXT_MAIN
        r2 = pi.add_run()
        r2.text = f"({regno})"
        r2.font.bold = True
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = BLUE_ACCENT

        p_sub = tf_team.add_paragraph()
        p_sub.text = contrib
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 2: AGENDA
    # ==========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Section 1: Project Introduction & Design", "Presentation Roadmap & Topics Covered", 2)

    agenda_boxes = [
        ("SECTION 1", "Introduction & Architecture", [
            "Problem Statement & Objectives",
            "Proposed Dual-Database Solution",
            "4-Tier Architecture & Tech Stack",
            "Core Modules & Data Interaction"
        ]),
        ("SECTION 2", "Database Design & Schema", [
            "Entity-Relationship (ER) Diagram",
            "Relational Mapping & Normalization (BCNF)",
            "Table DDL & Integrity Constraints",
            "Sample Records & Referential Integrity"
        ]),
        ("SECTION 3", "SQL & Database Programming", [
            "Feature-to-Query Mapping",
            "DDL, DML & Role-Based DCL Security",
            "Analytical Subqueries & Complex Joins",
            "PL/SQL Triggers, Cursors & Procedures"
        ]),
        ("SECTION 4", "Implementation & Results", [
            "Application Workflow & Code Structure",
            "Working Application Screenshots (8 views)",
            "Role-Based Access Control & Innovations",
            "Build Steps, GitHub Repository & Conclusion"
        ])
    ]

    for idx, (sec_num, sec_title, bullets) in enumerate(agenda_boxes):
        left = Inches(0.8 + idx * 2.98)
        top = Inches(1.5)
        w = Inches(2.82)
        h = Inches(5.4)

        add_card(s2, left, top, w, h)
        # Top banner
        hdr = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, w, Inches(0.7))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = NAVY_PRIMARY
        hdr.line.fill.background()

        tx_h = s2.shapes.add_textbox(left, top + Inches(0.08), w, Inches(0.6))
        tf_h = tx_h.text_frame
        p_h1 = tf_h.paragraphs[0]
        p_h1.alignment = PP_ALIGN.CENTER
        p_h1.text = sec_num
        p_h1.font.bold = True
        p_h1.font.size = Pt(9)
        p_h1.font.color.rgb = RGBColor(191, 219, 254)

        p_h2 = tf_h.add_paragraph()
        p_h2.alignment = PP_ALIGN.CENTER
        p_h2.text = sec_title
        p_h2.font.bold = True
        p_h2.font.size = Pt(11)
        p_h2.font.color.rgb = RGBColor(255, 255, 255)

        tx_b = s2.shapes.add_textbox(left + Inches(0.15), top + Inches(0.85), w - Inches(0.3), h - Inches(0.95))
        tf_b = tx_b.text_frame
        tf_b.word_wrap = True
        for b_idx, b in enumerate(bullets):
            pb = tf_b.paragraphs[0] if b_idx == 0 else tf_b.add_paragraph()
            pb.text = "• " + b
            pb.font.size = Pt(10)
            pb.font.color.rgb = TEXT_MAIN
            pb.space_before = Pt(10)

    # ==========================================================================
    # SLIDE 3: INTRODUCTION & PROJECT OVERVIEW
    # ==========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Section 1: Project Introduction & Design", "Problem Statement, Objectives & Solution Scope", 3)

    add_card(s3, Inches(0.8), Inches(1.5), Inches(3.7), Inches(5.4))
    tx1 = s3.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(3.3), Inches(5.0))
    tf1 = tx1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "PROBLEM STATEMENT"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    p1_items = [
        "Traditional relational library management systems struggle with recursive multi-table joins when discovering multi-degree book connections.",
        "Students lack structured academic reading roadmaps showing prerequisite foundational books before advanced texts.",
        "Manual circulation desk verification often fails to enforce patron loan limits (3 books) and calculate overdue penalties reliably.",
        "Borrowing histories are exposed across patrons without proper role-based privacy masking."
    ]
    for it in p1_items:
        pi = tf1.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(10)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(8)

    add_card(s3, Inches(4.8), Inches(1.5), Inches(3.7), Inches(5.4))
    tx2 = s3.shapes.add_textbox(Inches(5.0), Inches(1.7), Inches(3.3), Inches(5.0))
    tf2 = tx2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "PROPOSED SOLUTION & SCOPE"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    p2_items = [
        "Dual-Database Engineering: Combines an enterprise Oracle 21c relational schema with a Neo4j AuraDB property graph.",
        "Role-Based Access Control (RBAC): Provides four distinct experiences for Admin, Librarian, Staff (Faculty), and Students.",
        "Automated Circulation Rules: Real-time 3-book borrowing quota enforcement and daily Rs. 5/day overdue fine calculation.",
        "Interactive Graph Capabilities: Real-time knowledge graph visualizer, shortest-path degrees of separation, and DAG prerequisite learning tracks."
    ]
    for it in p2_items:
        pi = tf2.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(10)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(8)

    add_card(s3, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.4))
    tx3 = s3.shapes.add_textbox(Inches(9.0), Inches(1.7), Inches(3.3), Inches(5.0))
    tf3 = tx3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "TECHNOLOGY STACK SUMMARY"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    p3_stack = [
        ("Web Framework", "Python 3.12, Flask 3.1, Flask-Session, Flask-WTF CSRF"),
        ("Relational Engine", "Oracle Database 21c (Tables, Constraints, PL/SQL)"),
        ("Graph Engine", "Neo4j AuraDB v5+ (Cypher, Graph Traversal Algorithms)"),
        ("Frontend UI", "HTML5, Vanilla CSS, Plus Jakarta Sans, JetBrains Mono"),
        ("Graph Canvas", "Vis.js Network v9.1.2 (Interactive Physics Rendering)"),
        ("Verification", "7 End-to-End Automated Verification Suites (100% Pass)")
    ]
    for label, val in p3_stack:
        pi = tf3.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = label + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_MAIN
        r2 = pi.add_run()
        r2.text = val
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 4: SYSTEM DESIGN & MULTI-TIER ARCHITECTURE
    # ==========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Section 1: Project Introduction & Design", "Overall System Architecture & Multi-Tier Data Interaction", 4)

    tier_cards = [
        ("Tier 1: Client & Presentation Layer", "Web Browser UI & Interactive Graph Canvas", [
            "Responsive Web Portal implemented in HTML5 and clean Vanilla CSS (Modern Slate Theme).",
            "Vis.js physics-driven canvas rendering interactive knowledge graphs and prerequisite roadmaps.",
            "Role-specific UI views tailored for Admin, Librarian, Faculty/Staff, and Students."
        ]),
        ("Tier 2: Application Controller & Security Layer", "Flask WSGI Middleware & RBAC Controllers", [
            "Central request router managing authentication, catalog browsing, loan processing, and graph APIs.",
            "Flask-WTF CSRF token validation on all mutable operations (loan issue, returns, password updates).",
            "10-minute idle session timeout with automatic server-side cleanup and institutional email checks."
        ]),
        ("Tier 3: Data Access & Business Logic Layer", "Parameterized Database Drivers & Controllers", [
            "Neo4j Bolt Protocol (neo4j+s://) executing optimized Cypher shortestPath() and prerequisite queries.",
            "Oracle Client / cx_Oracle connector executing transaction-managed PL/SQL stored procedures.",
            "Dynamic patron privacy masking to anonymize fellow student loan requests on shared canvases."
        ]),
        ("Tier 4: Enterprise Storage Tier", "Relational Database (Oracle) & Property Graph (Neo4j)", [
            "Oracle 21c Database: 10 normalized tables in BCNF, foreign key cascades, triggers, and views.",
            "Neo4j AuraDB: 9 node entity types, 7 relationship edges, and 12 schema uniqueness constraints.",
            "Automated quota enforcement, copy status synchronization, and audit logging."
        ])
    ]

    for idx, (head, sub, pts) in enumerate(tier_cards):
        top = Inches(1.5 + idx * 1.35)
        add_card(s4, Inches(0.8), top, Inches(11.733), Inches(1.22))

        # Navy side bar
        sb = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top, Inches(0.12), Inches(1.22))
        sb.fill.solid()
        sb.fill.fore_color.rgb = BLUE_ACCENT
        sb.line.fill.background()

        tx = s4.shapes.add_textbox(Inches(1.1), top + Inches(0.08), Inches(3.6), Inches(1.06))
        tf = tx.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = head
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_MUTED

        tx_pts = s4.shapes.add_textbox(Inches(4.8), top + Inches(0.08), Inches(7.5), Inches(1.06))
        tf_pts = tx_pts.text_frame
        tf_pts.word_wrap = True
        for p_idx, pt_text in enumerate(pts):
            p_pt = tf_pts.paragraphs[0] if p_idx == 0 else tf_pts.add_paragraph()
            p_pt.text = "• " + pt_text
            p_pt.font.size = Pt(9.5)
            p_pt.font.color.rgb = TEXT_MAIN
            if p_idx > 0:
                p_pt.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 5: ER DIAGRAM AND TABLE MAPPING
    # ==========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Section 2: Database Design & Implementation", "Conceptual Data Model — Entity-Relationship (ER) Diagram", 5)

    # Left: Embed ER diagram image
    add_card(s5, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    if os.path.exists(ER_IMAGE_PATH):
        s5.shapes.add_picture(ER_IMAGE_PATH, Inches(0.95), Inches(1.65), width=Inches(6.5))

    tx_c = s5.shapes.add_textbox(Inches(0.8), Inches(6.45), Inches(6.8), Inches(0.35))
    p = tx_c.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Figure: Conceptual Entity-Relationship (ER) Diagram of the Library Management System"
    p.font.size = Pt(9)
    p.font.italic = True
    p.font.color.rgb = TEXT_MUTED

    # Right: Cardinality & Entity Mapping Table
    add_card(s5, Inches(7.8), Inches(1.5), Inches(4.733), Inches(5.4))
    tx_m = s5.shapes.add_textbox(Inches(8.0), Inches(1.7), Inches(4.333), Inches(5.0))
    tf_m = tx_m.text_frame
    tf_m.word_wrap = True

    p = tf_m.paragraphs[0]
    p.text = "ENTITY & CARDINALITY MAPPING"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    er_points = [
        ("1:N Publisher to Books", "Each publisher publishes multiple titles; every book is linked to a single registered publisher."),
        ("M:N Books to Authors", "A book may have co-authors, and authors write multiple books. Mapped into the BOOK_AUTHORS relationship table."),
        ("1:N Book to Copies", "Separates abstract bibliographic titles from physical inventory tracking copies (status: Available, Borrowed, Reserved)."),
        ("1:N User to Loans", "Patrons record historical loans over time, strictly capped at 3 active concurrent borrowed books."),
        ("1:1 Loan to Fines", "Overdue book returns automatically generate a financial disciplinary record (Rs. 5 per overdue day)."),
        ("Relational Normalization", "Conceptual Member, Employee, and Admin roles are unified into the USERS entity with Role-Based Access Control.")
    ]
    for rel_title, rel_desc in er_points:
        pi = tf_m.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = rel_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = BLUE_ACCENT
        r2 = pi.add_run()
        r2.text = rel_desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 6: RELATIONAL SCHEMA & NORMALIZATION
    # ==========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Section 2: Database Design & Implementation", "Relational Schema & Functional Dependency Normalization (BCNF)", 6)

    add_card(s6, Inches(0.8), Inches(1.5), Inches(7.0), Inches(5.4))
    tx_s = s6.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(6.6), Inches(5.1))
    tf_s = tx_s.text_frame
    tf_s.word_wrap = True

    p = tf_s.paragraphs[0]
    p.text = "RELATIONAL SCHEMA SPECIFICATIONS"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    r_tables = [
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
    for tbl, cols in r_tables:
        pi = tf_s.add_paragraph()
        pi.space_before = Pt(4)
        r1 = pi.add_run()
        r1.text = tbl + " "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = BLUE_ACCENT
        r2 = pi.add_run()
        r2.text = f"({cols})"
        r2.font.name = FONT_CODE
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    add_card(s6, Inches(8.0), Inches(1.5), Inches(4.533), Inches(5.4))
    tx_n = s6.shapes.add_textbox(Inches(8.2), Inches(1.65), Inches(4.133), Inches(5.1))
    tf_n = tx_n.text_frame
    tf_n.word_wrap = True

    p = tf_n.paragraphs[0]
    p.text = "NORMALIZATION DECOMPOSITION"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    norm_steps = [
        ("1NF (First Normal Form)", "All table attributes contain atomic values. Repeated author and copy collections are separated into distinct tables."),
        ("2NF (Second Normal Form)", "Eliminated all partial key dependencies. In BOOK_AUTHORS, the composite key {book_id, author_id} determines full relationship status."),
        ("3NF (Third Normal Form)", "Eliminated all transitive functional dependencies (e.g., category_name is determined exclusively by category_id, not transitively by book_id)."),
        ("BCNF (Boyce-Codd Normal Form)", "Every determinant is a candidate key. Protects against update, insertion, and deletion anomalies across the loan lifecycle.")
    ]
    for st_title, st_desc in norm_steps:
        pi = tf_n.add_paragraph()
        pi.space_before = Pt(8)
        r1 = pi.add_run()
        r1.text = st_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_MAIN
        r2 = pi.add_run()
        r2.text = st_desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 7: TABLE CREATION AND CONSTRAINTS
    # ==========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Section 2: Database Design & Implementation", "Table Creation & Comprehensive Integrity Constraints (DDL)", 7)

    # Left: Code Card
    add_card(s7, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4), bg=CODE_BG, border=CODE_BORDER)
    tx_code = s7.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(6.4), Inches(5.1))
    tf_code = tx_code.text_frame
    tf_code.word_wrap = True

    sql_ddl = """-- Table Creation with Integrity Constraints (Oracle SQL)
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
    p.font.color.rgb = CODE_TEXT

    # Right: Constraint Explanation Card
    add_card(s7, Inches(7.8), Inches(1.5), Inches(4.733), Inches(5.4))
    tx_exp = s7.shapes.add_textbox(Inches(8.0), Inches(1.65), Inches(4.333), Inches(5.1))
    tf_exp = tx_exp.text_frame
    tf_exp.word_wrap = True

    p = tf_exp.paragraphs[0]
    p.text = "INTEGRITY CONSTRAINTS IMPLEMENTED"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    c_types = [
        ("PRIMARY KEY Constraints", "Enforces entity integrity (user_id, book_id, loan_id). Prohibits duplicate or NULL primary records."),
        ("FOREIGN KEY & CASCADES", "Maintains referential integrity. Removing a book cascades to dependent copies (ON DELETE CASCADE), preventing dangling references."),
        ("CHECK Constraints", "chk_user_role restricts accounts to authorized roles; chk_copy_status ensures valid inventory states; chk_loan_dates guarantees due_date >= issue_date."),
        ("UNIQUE Constraints", "Prevents duplicate ISBN registrations, identical usernames, and duplicate institutional email addresses."),
        ("NOT NULL & DEFAULT", "Mandates critical metadata (password_hash, email) while initializing default statuses ('Available', 'Active', 'Unpaid').")
    ]
    for c_h, c_d in c_types:
        pi = tf_exp.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = c_h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = BLUE_ACCENT
        r2 = pi.add_run()
        r2.text = c_d
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 8: SAMPLE DATA & INTEGRITY VERIFICATION
    # ==========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Section 2: Database Design & Implementation", "Sample Data Records & Referential Integrity Verification", 8)

    # Top: Sample Table
    add_card(s8, Inches(0.8), Inches(1.5), Inches(11.733), Inches(2.6))
    tx_t = s8.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.333), Inches(0.4))
    p = tx_t.text_frame.paragraphs[0]
    p.text = "SAMPLE ENTITY RECORDS POPULATED IN DATABASE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

    tbl_shape = s8.shapes.add_table(4, 6, Inches(1.0), Inches(1.95), Inches(11.333), Inches(2.0))
    table = tbl_shape.table
    table.columns[0].width = Inches(1.3)
    table.columns[1].width = Inches(2.3)
    table.columns[2].width = Inches(2.2)
    table.columns[3].width = Inches(1.8)
    table.columns[4].width = Inches(2.0)
    table.columns[5].width = Inches(1.733)

    t_headers = ["Table", "Identifier (PK)", "Attribute 1", "Attribute 2", "Status / Role", "Foreign Key Ref"]
    for c_idx, h in enumerate(t_headers):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(9.5)
            p.font.color.rgb = RGBColor(255, 255, 255)

    sample_rows = [
        ["USERS", "user_id = 1", "admin", "admin@vit.edu", "Role: Admin", "Account: Active"],
        ["BOOKS", "book_id = 2", "Clean Code: Agile Craft", "ISBN: 978-0132350884", "Pub Year: 2008", "Category: CS (ID: 1)"],
        ["LOANS", "loan_id = 14", "copy_id = 2", "user_id = 6 (student)", "Issue: 2026-03-01", "Due: 2026-03-15 (Overdue)"]
    ]
    for r_idx, r_data in enumerate(sample_rows, start=1):
        for c_idx, val in enumerate(r_data):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(255, 255, 255) if r_idx % 2 == 1 else RGBColor(241, 245, 249)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(9)
                p.font.color.rgb = TEXT_MAIN

    # Bottom Cards: Referential Integrity & Constraint Rejection
    add_card(s8, Inches(0.8), Inches(4.35), Inches(5.7), Inches(2.55))
    tx_b1 = s8.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(5.3), Inches(2.25))
    tf_b1 = tx_b1.text_frame
    tf_b1.word_wrap = True
    p = tf_b1.paragraphs[0]
    p.text = "REFERENTIAL INTEGRITY ENFORCEMENT"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

    b1_pts = [
        "Foreign Key Cascading: Deleting a category safely cascades to dependent book records or blocks deletion if active loans exist.",
        "Copy Status Synchronization: Physical copies transition automatically to 'Borrowed' upon loan issue and 'Available' upon check-in.",
        "Borrower Anonymization on Account Deletion: Historical loans retain record integrity (borrower_id = 0) to maintain statistical ledgers."
    ]
    for it in b1_pts:
        pi = tf_b1.add_paragraph()
        pi.text = "• " + it
        pi.font.size = Pt(9)
        pi.font.color.rgb = TEXT_MUTED
        pi.space_before = Pt(4)

    add_card(s8, Inches(6.8), Inches(4.35), Inches(5.733), Inches(2.55))
    tx_b2 = s8.shapes.add_textbox(Inches(7.0), Inches(4.5), Inches(5.3), Inches(2.25))
    tf_b2 = tx_b2.text_frame
    tf_b2.word_wrap = True
    p = tf_b2.paragraphs[0]
    p.text = "CONSTRAINT REJECTION TESTING (ERROR-PROOFING)"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

    b2_pts = [
        "Duplicate ISBN Rejection: ORA-00001 unique constraint violation raised when attempting to re-register an existing ISBN.",
        "Borrowing Quota Rejection: PL/SQL trigger and Flask controllers immediately reject a 4th concurrent loan request.",
        "Disciplinary Fine Locking: Loan issuance is blocked when outstanding disciplinary fines exist on a patron's record."
    ]
    for it in b2_pts:
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

    sqls = [
        ("Catalog & Category Search (/catalog, /category/<id>)",
         "SELECT b.book_id, b.title, b.isbn, b.publication_year, c.category_name,\n       COUNT(cp.copy_id) AS total_copies,\n       SUM(CASE WHEN cp.status = 'Available' THEN 1 ELSE 0 END) AS available_copies\nFROM BOOKS b\nJOIN CATEGORIES c ON b.category_id = c.category_id\nLEFT JOIN BOOK_COPIES cp ON b.book_id = cp.book_id\nWHERE LOWER(b.title) LIKE :query OR REPLACE(b.isbn, '-', '') LIKE :isbn_query\nGROUP BY b.book_id, b.title, b.isbn, b.publication_year, c.category_name;",
         "Enables fast searching across titles, authors, and hyphenated/unhyphenated ISBNs with real-time copy availability counts."),

        ("Issue Loan Transaction (/issue_loan)",
         "-- Atomic Loan Creation and Copy Status Lock\nINSERT INTO LOANS (loan_id, copy_id, user_id, issue_date, due_date, issued_by)\nVALUES (seq_loan_id.NEXTVAL, :copy_id, :user_id, SYSDATE, SYSDATE + 14, :admin_id);\n\nUPDATE BOOK_COPIES\nSET status = 'Borrowed'\nWHERE copy_id = :copy_id;",
         "Guarantees that a physical copy cannot be concurrently double-issued to another patron at the circulation desk.")
    ]

    for idx, (head, query, desc) in enumerate(sqls):
        top = Inches(1.5 + idx * 2.7)
        add_card(s9, Inches(0.8), top, Inches(11.733), Inches(2.55))

        tx = s9.shapes.add_textbox(Inches(1.0), top + Inches(0.12), Inches(11.333), Inches(2.3))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = head
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY

        pq = tf.add_paragraph()
        pq.text = query
        pq.font.name = FONT_CODE
        pq.font.size = Pt(8.5)
        pq.font.color.rgb = CODE_TEXT
        pq.space_before = Pt(3)

        pd = tf.add_paragraph()
        pd.text = "Operational Purpose: " + desc
        pd.font.size = Pt(9)
        pd.font.color.rgb = TEXT_MUTED
        pd.space_before = Pt(3)

    # ==========================================================================
    # SLIDE 10: DDL, DML, AND DCL COMMANDS
    # ==========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Section 3: SQL Queries & Database Programming", "DDL, DML, and Role-Based DCL Security Commands", 10)

    cmd_cards = [
        ("DDL (DATA DEFINITION)", [
            ("CREATE TABLE / INDEX", "CREATE TABLE LOAN_REQUESTS (\n  request_id NUMBER PRIMARY KEY,\n  user_id NUMBER REFERENCES USERS,\n  book_id NUMBER REFERENCES BOOKS,\n  status VARCHAR2(20) DEFAULT 'Pending'\n);"),
            ("ALTER TABLE CONSTRAINT", "ALTER TABLE FINES ADD CONSTRAINT chk_fine_amt\nCHECK (fine_amount >= 0);"),
            ("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX idx_isbn ON BOOKS(isbn);")
        ]),
        ("DML (DATA MANIPULATION)", [
            ("INSERT DATA", "INSERT INTO BOOK_COPIES (copy_id, book_id, status)\nVALUES (seq_copy.NEXTVAL, 2, 'Available');"),
            ("UPDATE TRANSACTION", "UPDATE FINES SET payment_status = 'Paid',\npayment_date = SYSDATE WHERE fine_id = :fid;"),
            ("DELETE CONDITIONAL", "DELETE FROM LOAN_REQUESTS\nWHERE status = 'Rejected' AND request_date < SYSDATE-30;")
        ]),
        ("DCL (DATA CONTROL)", [
            ("ROLE PROVISIONING", "CREATE ROLE LIBRARIAN_ROLE;\nCREATE ROLE STUDENT_ROLE;"),
            ("GRANT PRIVILEGES", "GRANT SELECT, INSERT, UPDATE ON LOANS\nTO LIBRARIAN_ROLE;\nGRANT SELECT ON BOOKS TO STUDENT_ROLE;"),
            ("REVOKE RESTRICTIONS", "REVOKE DELETE ON BOOKS FROM STUDENT_ROLE;\nREVOKE UPDATE ON USERS FROM LIBRARIAN_ROLE;")
        ])
    ]

    for idx, (head, snippets) in enumerate(cmd_cards):
        left = Inches(0.8 + idx * 3.98)
        top = Inches(1.5)
        w = Inches(3.78)
        h = Inches(5.4)

        add_card(s10, left, top, w, h)
        # Top banner
        hdr = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, w, Inches(0.45))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = NAVY_PRIMARY
        hdr.line.fill.background()

        tx_h = s10.shapes.add_textbox(left, top + Inches(0.06), w, Inches(0.35))
        p_h = tx_h.text_frame.paragraphs[0]
        p_h.alignment = PP_ALIGN.CENTER
        p_h.text = head
        p_h.font.bold = True
        p_h.font.size = Pt(9.5)
        p_h.font.color.rgb = RGBColor(255, 255, 255)

        tx_b = s10.shapes.add_textbox(left + Inches(0.15), top + Inches(0.55), w - Inches(0.3), h - Inches(0.65))
        tf_b = tx_b.text_frame
        tf_b.word_wrap = True

        for snip_title, snip_code in snippets:
            pt = tf_b.add_paragraph()
            pt.text = snip_title
            pt.font.bold = True
            pt.font.size = Pt(9.5)
            pt.font.color.rgb = BLUE_ACCENT
            pt.space_before = Pt(8)

            pc = tf_b.add_paragraph()
            pc.text = snip_code
            pc.font.name = FONT_CODE
            pc.font.size = Pt(8)
            pc.font.color.rgb = CODE_TEXT
            pc.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 11: SUBQUERIES AND ANALYTICAL FILTERING
    # ==========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Section 3: SQL Queries & Database Programming", "Single-Row, Multiple-Row & Correlated Subqueries", 11)

    subqs = [
        ("1. Single-Row Subquery (Scalar Comparison)",
         "SELECT b.book_id, b.title, b.publication_year\nFROM BOOKS b\nWHERE b.publication_year > (\n    SELECT AVG(publication_year)\n    FROM BOOKS\n    WHERE category_id = b.category_id\n);",
         "Identifies books published more recently than the average publication vintage of their respective subject category."),

        ("2. Multiple-Row Subquery with IN Operator",
         "SELECT u.user_id, u.username, u.email\nFROM USERS u\nWHERE u.user_id IN (\n    SELECT DISTINCT l.user_id\n    FROM LOANS l\n    JOIN FINES f ON l.loan_id = f.loan_id\n    WHERE f.payment_status = 'Unpaid'\n);",
         "Flags all patrons with outstanding overdue financial penalties to restrict borrowing permissions at checkout."),

        ("3. Correlated Subquery with EXISTS Operator",
         "SELECT b.book_id, b.title\nFROM BOOKS b\nWHERE EXISTS (\n    SELECT 1\n    FROM BOOK_COPIES cp\n    JOIN LOANS l ON cp.copy_id = l.copy_id\n    WHERE cp.book_id = b.book_id\n    GROUP BY cp.copy_id\n    HAVING COUNT(l.loan_id) >= 3\n);",
         "Discovers 'High Circulation Velocity' titles where copies have been actively checked out 3 or more times.")
    ]

    for idx, (title, sql_code, explain) in enumerate(subqs):
        top = Inches(1.5 + idx * 1.78)
        add_card(s11, Inches(0.8), top, Inches(11.733), Inches(1.68))

        tx = s11.shapes.add_textbox(Inches(1.0), top + Inches(0.08), Inches(11.333), Inches(1.55))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY

        ps = tf.add_paragraph()
        ps.text = sql_code
        ps.font.name = FONT_CODE
        ps.font.size = Pt(8.5)
        ps.font.color.rgb = CODE_TEXT
        ps.space_before = Pt(2)

        pe = tf.add_paragraph()
        pe.text = "Operational Analytics: " + explain
        pe.font.size = Pt(9)
        pe.font.color.rgb = TEXT_MUTED
        pe.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 12: SQL FUNCTIONS (AGGREGATE & SCALAR)
    # ==========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Section 3: SQL Queries & Database Programming", "SQL Functions — Aggregate, String, Date & Analytical Math", 12)

    add_card(s12, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
    tx_a = s12.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(5.1))
    tf_a = tx_a.text_frame
    tf_a.word_wrap = True

    p = tf_a.paragraphs[0]
    p.text = "AGGREGATE FUNCTIONS & GROUP BY"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    a_points = [
        ("COUNT(*), COUNT(DISTINCT l.user_id)", "Measures total circulation transactions and distinct active patron engagement across semesters."),
        ("SUM(f.fine_amount)", "Computes cumulative institutional penalty revenue and outstanding unpaid receivables."),
        ("AVG(MONTHS_BETWEEN(SYSDATE, b.acquisition_date))", "Computes the mean retention age of catalog acquisitions for inventory deprecation."),
        ("MIN(due_date), MAX(due_date)", "Identifies the earliest pending return and latest active return deadlines across campus."),
        ("GROUP BY ... HAVING COUNT(*) > 5", "Filters prolific authors and high-density categories exceeding borrowing thresholds.")
    ]
    for fn, desc in a_points:
        pi = tf_a.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = fn + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = BLUE_ACCENT
        r2 = pi.add_run()
        r2.text = desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MUTED

    add_card(s12, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.4))
    tx_s2 = s12.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(5.1))
    tf_s2 = tx_s2.text_frame
    tf_s2.word_wrap = True

    p = tf_s2.paragraphs[0]
    p.text = "SCALAR, STRING & DATE FUNCTIONS"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    s_points = [
        ("TO_CHAR(issue_date, 'YYYY-MM-DD HH24:MI')", "Standardizes temporal audit timestamps across disparate client locales."),
        ("TRUNC(SYSDATE) - TRUNC(due_date)", "Evaluates precise elapsed calendar days for overdue fine calculations."),
        ("UPPER(u.username), LOWER(u.email)", "Normalizes patron authentication credentials to ensure case-insensitive identity matching."),
        ("REPLACE(b.isbn, '-', '')", "Strips punctuation from ISBN strings for seamless barcode and query pattern matching."),
        ("NVL(return_date, 'Active Loan')", "Handles NULL return dates gracefully in patron financial ledgers and dashboard reports.")
    ]
    for fn, desc in s_points:
        pi = tf_s2.add_paragraph()
        pi.space_before = Pt(6)
        r1 = pi.add_run()
        r1.text = fn + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = BLUE_ACCENT
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

    add_card(s13, Inches(0.8), Inches(1.5), Inches(11.733), Inches(2.6))
    tx_j = s13.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.333), Inches(2.3))
    tf_j = tx_j.text_frame
    tf_j.word_wrap = True

    p = tf_j.paragraphs[0]
    p.text = "MULTI-TABLE RELATIONAL JOINS (INNER & LEFT OUTER)"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

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
    pj.font.color.rgb = CODE_TEXT
    pj.space_before = Pt(3)

    add_card(s13, Inches(0.8), Inches(4.35), Inches(11.733), Inches(2.55))
    tx_v = s13.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11.333), Inches(2.25))
    tf_v = tx_v.text_frame
    tf_v.word_wrap = True

    p = tf_v.paragraphs[0]
    p.text = "DATABASE VIEWS FOR APPLICATION REPORTING & SECURITY MASKING"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

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
    pv.font.color.rgb = CODE_TEXT
    pv.space_before = Pt(3)

    # ==========================================================================
    # SLIDE 14: TRIGGERS, CURSORS, AND AUTONOMOUS AUDITING
    # ==========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_header(s14, "Section 3: SQL Queries & Database Programming", "Database Triggers, Explicit Cursors & Automated Auditing", 14)

    add_card(s14, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4), bg=CODE_BG, border=CODE_BORDER)
    tx_trg = s14.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(5.1))
    tf_trg = tx_trg.text_frame
    tf_trg.word_wrap = True

    p = tf_trg.paragraphs[0]
    p.text = "PL/SQL TRIGGER: QUOTA ENFORCEMENT"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

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
    pt.font.color.rgb = CODE_TEXT
    pt.space_before = Pt(4)

    add_card(s14, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.4), bg=CODE_BG, border=CODE_BORDER)
    tx_cur = s14.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(5.1))
    tf_cur = tx_cur.text_frame
    tf_cur.word_wrap = True

    p = tf_cur.paragraphs[0]
    p.text = "EXPLICIT CURSOR: OVERDUE FINE BATCH"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

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
    pc.font.color.rgb = CODE_TEXT
    pc.space_before = Pt(4)

    # ==========================================================================
    # SLIDE 15: STORED PROCEDURES & EXCEPTION HANDLING
    # ==========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15)
    add_header(s15, "Section 3: SQL Queries & Database Programming", "Stored Procedures, Functions & Robust Exception Handling", 15)

    add_card(s15, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4), bg=CODE_BG, border=CODE_BORDER)
    tx_sp = s15.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.333), Inches(5.1))
    tf_sp = tx_sp.text_frame
    tf_sp.word_wrap = True

    p = tf_sp.paragraphs[0]
    p.text = "ENTERPRISE PL/SQL STORED PROCEDURE WITH PARAMETERS & TRANSACTION CONTROL"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

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
    psp.font.color.rgb = CODE_TEXT
    psp.space_before = Pt(4)

    # ==========================================================================
    # SLIDE 16: APPLICATION WORKFLOW AND CODE STRUCTURE
    # ==========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16)
    add_header(s16, "Section 4: Application Implementation & Demonstration", "Application Workflow & Modular Code Architecture", 16)

    add_card(s16, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4), bg=CODE_BG, border=CODE_BORDER)
    tx_dir = s16.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(5.1))
    tf_dir = tx_dir.text_frame
    tf_dir.word_wrap = True

    p = tf_dir.paragraphs[0]
    p.text = "PROJECT DIRECTORY TREE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

    dir_tree = """DBS DA/
├── app.py                # Core Flask app (24 routes, RBAC, Cypher/SQL)
├── seed_all_data.py      # Neo4j schema constraints & sample data seed
├── requirements.txt      # Python dependencies (Flask, Neo4j, WTForms)
├── .env.example          # Database connection template
├── .gitignore            # Clean Git exclusions
├── README.md             # Comprehensive architecture documentation
├── templates/            # 24 Jinja2 HTML5 Professional Views
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
    p_d.font.color.rgb = CODE_TEXT
    p_d.space_before = Pt(4)

    add_card(s16, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.4))
    tx_flow = s16.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(5.1))
    tf_flow = tx_flow.text_frame
    tf_flow.word_wrap = True

    p = tf_flow.paragraphs[0]
    p.text = "HTTP REQUEST EXECUTION LIFECYCLE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_PRIMARY

    flow_steps = [
        ("Step 1: Inbound HTTP Request", "Client browser triggers route (e.g. POST /issue_loan) with form payload and CSRF token."),
        ("Step 2: Security & Session Middleware", "Verifies active session in filesystem, validates 10-minute idle activity timestamp, and decrypts CSRF token."),
        ("Step 3: Role-Based Authorization", "@role_required(['Admin', 'Librarian']) decorator checks user role; redirects unauthorized roles to 403 Access Denied."),
        ("Step 4: Query Execution & Business Logic", "Cypher query or PL/SQL procedure invoked via database driver session with parameterized injection protection."),
        ("Step 5: Dynamic View Rendering", "Jinja2 compiles response template with DateWrapper objects and privacy-masked attributes."),
        ("Step 6: Client DOM Update", "Rendered HTML/CSS returned with clean professional visuals and interactive Vis.js graph physics.")
    ]
    for step_h, step_b in flow_steps:
        pi = tf_flow.add_paragraph()
        pi.space_before = Pt(5)
        r1 = pi.add_run()
        r1.text = step_h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = BLUE_ACCENT
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
        ("01_public_login.png", "1. Secure Multi-Role Login Portal", Inches(0.8), Inches(1.5)),
        ("03_admin_dashboard.png", "2. Admin Dashboard & Active Circulation Ledgers", Inches(6.8), Inches(1.5)),
        ("06_admin_issue_loan.png", "3. Physical Book Loan Issuance Desk", Inches(0.8), Inches(4.35)),
        ("07_admin_loan_requests.png", "4. Digital Loan Requests & Copy Reservation Desk", Inches(6.8), Inches(4.35))
    ]

    for fname, caption, left, top in shots_s17:
        add_card(s17, left, top, Inches(5.7), Inches(2.65))
        fpath = os.path.join(SCREENSHOTS_DIR, fname)
        if os.path.exists(fpath):
            s17.shapes.add_picture(fpath, left + Inches(0.1), top + Inches(0.1), width=Inches(5.5), height=Inches(2.15))

        tx_c = s17.shapes.add_textbox(left, top + Inches(2.3), Inches(5.7), Inches(0.3))
        p = tx_c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = caption
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY

    # ==========================================================================
    # SLIDE 18: WORKING APPLICATION SCREENSHOTS (GRAPH & AI INNOVATIONS)
    # ==========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18)
    add_header(s18, "Section 4: Application Implementation & Demonstration", "Working Application Screenshots — Graph & AI Innovations", 18)

    shots_s18 = [
        ("11_admin_graph_visualizer.png", "1. Live Knowledge Graph Explorer (/graph_visualizer)", Inches(0.8), Inches(1.5)),
        ("12_admin_book_bridge.png", "2. Book Bridge Shortest Path Traversal (/book_bridge)", Inches(6.8), Inches(1.5)),
        ("09_admin_learning_paths.png", "3. Academic Learning Roadmaps DAG (/learning_paths)", Inches(0.8), Inches(4.35)),
        ("10_admin_ai_recommendations.png", "4. AI Collaborative Filtering Recommendations", Inches(6.8), Inches(4.35))
    ]

    for fname, caption, left, top in shots_s18:
        add_card(s18, left, top, Inches(5.7), Inches(2.65))
        fpath = os.path.join(SCREENSHOTS_DIR, fname)
        if os.path.exists(fpath):
            s18.shapes.add_picture(fpath, left + Inches(0.1), top + Inches(0.1), width=Inches(5.5), height=Inches(2.15))

        tx_c = s18.shapes.add_textbox(left, top + Inches(2.3), Inches(5.7), Inches(0.3))
        p = tx_c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = caption
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY

    # ==========================================================================
    # SLIDE 19: ACCESS CONTROL AND CUSTOM INNOVATIONS
    # ==========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19)
    add_header(s19, "Section 4: Application Implementation & Demonstration", "Role-Based Access Control & Advanced Graph Innovations", 19)

    add_card(s19, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
    tx_rbac = s19.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(5.1))
    tf_rbac = tx_rbac.text_frame
    tf_rbac.word_wrap = True

    p = tf_rbac.paragraphs[0]
    p.text = "ROLE-BASED ACCESS CONTROL (RBAC) MATRIX"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

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
        r1.font.color.rgb = BLUE_ACCENT
        r2 = pi.add_run()
        r2.text = r_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    add_card(s19, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.4))
    tx_inn = s19.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(5.1))
    tf_inn = tx_inn.text_frame
    tf_inn.word_wrap = True

    p = tf_inn.paragraphs[0]
    p.text = "CUSTOM ARCHITECTURAL INNOVATIONS"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

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
        r1.font.color.rgb = BLUE_ACCENT
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

    steps = [
        ("STEP 1: CLONE REPOSITORY & CREATE VIRTUAL ENVIRONMENT", [
            "git clone https://github.com/Karthi16-png/LIBRARAY-MANAGEMENT-SYSTEM.git",
            "cd \"DBS DA\"",
            "python -m venv .venv",
            ".venv\\Scripts\\activate  (Windows)  OR  source .venv/bin/activate  (macOS/Linux)"
        ]),
        ("STEP 2: INSTALL DEPENDENCIES & CONFIGURE ENVIRONMENT", [
            "pip install -r requirements.txt",
            "Configure Neo4j AuraDB credentials in .env or environment variables:",
            "  NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io",
            "  NEO4J_USERNAME=neo4j  |  NEO4J_PASSWORD=<password>"
        ]),
        ("STEP 3: SEED GRAPH DATABASE (INITIAL SETUP)", [
            "python seed_all_data.py",
            "-> Establishes 12 schema uniqueness constraints",
            "-> Seeds 11 users across all 4 roles, 10 categories, 15+ books, copies, and prerequisite edges"
        ]),
        ("STEP 4: LAUNCH PORTAL & RUN TEST SUITES", [
            "python app.py",
            "-> Access interactive portal at http://127.0.0.1:5000/",
            "Execute complete 7-phase automated verification runner:",
            "  python scratch/run_all_phases.py  (100% Passing)"
        ])
    ]

    for idx, (st_title, st_lines) in enumerate(steps):
        top = Inches(1.5 + idx * 1.35)
        add_card(s20, Inches(0.8), top, Inches(11.733), Inches(1.22))

        b = s20.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top, Inches(0.12), Inches(1.22))
        b.fill.solid()
        b.fill.fore_color.rgb = BLUE_ACCENT
        b.line.fill.background()

        tx = s20.shapes.add_textbox(Inches(1.1), top + Inches(0.08), Inches(11.2), Inches(1.06))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = st_title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY

        for l in st_lines:
            pl = tf.add_paragraph()
            pl.text = l
            pl.font.name = FONT_CODE if "python" in l or "git" in l or "pip" in l else FONT_BODY
            pl.font.size = Pt(8.5)
            pl.font.color.rgb = TEXT_MAIN if "python" in l or "git" in l else TEXT_MUTED
            pl.space_before = Pt(1)

    # ==========================================================================
    # SLIDE 21: GITHUB REPOSITORY AND CONCLUSION
    # ==========================================================================
    s21 = prs.slides.add_slide(blank_layout)
    set_slide_background(s21)
    add_header(s21, "Section 4: Application Implementation & Demonstration", "GitHub Repository & Project Key Learning Outcomes", 21)

    add_card(s21, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
    tx_gh = s21.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(5.3), Inches(5.1))
    tf_gh = tx_gh.text_frame
    tf_gh.word_wrap = True

    p = tf_gh.paragraphs[0]
    p.text = "OPEN-SOURCE GITHUB REPOSITORY"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

    p_url = tf_gh.add_paragraph()
    p_url.text = "Repository URL:\nhttps://github.com/Karthi16-png/LIBRARAY-MANAGEMENT-SYSTEM"
    p_url.font.name = FONT_CODE
    p_url.font.size = Pt(9.5)
    p_url.font.color.rgb = BLUE_ACCENT
    p_url.space_before = Pt(8)

    gh_pts = [
        ("Production Codebase", "Contains app.py (4,230 lines), seed scripts, 24 template views, and full verification test suites."),
        ("Branching & Hygiene", "Clean Git commit history on branch main with .gitignore preventing credential exposure and cache staging."),
        ("Documentation & Dossier", "Includes detailed README.md setup instructions and the 211-page master forensic audit report PDF.")
    ]
    for h, d in gh_pts:
        pi = tf_gh.add_paragraph()
        pi.space_before = Pt(8)
        r1 = pi.add_run()
        r1.text = h + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_MAIN
        r2 = pi.add_run()
        r2.text = d
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    add_card(s21, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.4))
    tx_out = s21.shapes.add_textbox(Inches(7.0), Inches(1.65), Inches(5.333), Inches(5.1))
    tf_out = tx_out.text_frame
    tf_out.word_wrap = True

    p = tf_out.paragraphs[0]
    p.text = "PROJECT OUTCOMES & FUTURE ROADMAP"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_PRIMARY

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
        r1.font.color.rgb = BLUE_ACCENT
        r2 = pi.add_run()
        r2.text = o_d
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MUTED

    # ==========================================================================
    # SLIDE 22: CONCLUSION & Q&A
    # ==========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_background(s22)

    add_card(s22, Inches(1.5), Inches(1.2), Inches(10.333), Inches(5.1), bg=RGBColor(255, 255, 255), border=NAVY_PRIMARY)

    tx_q = s22.shapes.add_textbox(Inches(2.0), Inches(1.6), Inches(9.333), Inches(4.3))
    tf_q = tx_q.text_frame
    tf_q.word_wrap = True

    p = tf_q.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "THANK YOU!"
    p.font.name = FONT_HEADING
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    p2 = tf_q.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "Questions & Faculty Evaluation Discussion"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(17)
    p2.font.bold = True
    p2.font.color.rgb = BLUE_ACCENT
    p2.space_before = Pt(8)

    p3 = tf_q.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.text = "VITCC Enterprise Library Management System\nDual Relational & Graph Database Implementation"
    p3.font.size = Pt(12)
    p3.font.color.rgb = TEXT_MUTED
    p3.space_before = Pt(14)

    p4 = tf_q.add_paragraph()
    p4.alignment = PP_ALIGN.CENTER
    p4.text = "Course: BACSE202 — Database Systems | Slot: F1+TF1\nFaculty Guide: Dr. R. Priyadarshini"
    p4.font.size = Pt(12)
    p4.font.bold = True
    p4.font.color.rgb = NAVY_PRIMARY
    p4.space_before = Pt(12)

    p5 = tf_q.add_paragraph()
    p5.alignment = PP_ALIGN.CENTER
    p5.text = "Team Members: KARTHIK VALLIAPPAN C (25BAI1051) | NITHIN RANGASWAMY (25BAI1210) | NATRAJ (25BAI1079)\nSchool of Computer Science & Engineering (SCOPE), VIT Chennai"
    p5.font.size = Pt(11)
    p5.font.color.rgb = TEXT_MAIN
    p5.space_before = Pt(14)

    # Save presentation
    output_path = os.path.join(BASE_DIR, "VITCC_Library_Management_System_Presentation.pptx")
    prs.save(output_path)
    print(f"[SUCCESS] Professional academic presentation generated: {output_path}")
    print(f"Total Slides: {len(prs.slides)}")

if __name__ == "__main__":
    create_professional_presentation()
