import os
import sys
import json
from datetime import datetime
from PIL import Image as PILImage

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
MANIFEST_PATH = os.path.join(SCREENSHOT_DIR, "manifest.json")
OUTPUT_PDF = os.path.join(BASE_DIR, "VITCC_Library_Multi_Role_UI_Audit.pdf")

# Custom NumberedCanvas for professional running headers and footers
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        # Don't draw headers/footers on the cover page (page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header rule and text
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        # Footer
        self.line(24, 22, 842 - 24, 22)
        self.drawString(24, 12, "VITCC Central Library System — Comprehensive Multi-Role UI & Security Verification Report")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(842 - 24, 12, page_str)
        self.restoreState()


def build_pdf():
    print(f"Loading manifest from {MANIFEST_PATH}...")
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Document setup: Landscape A4 (841.89 x 595.28 pt)
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        alignment=1  # Centered
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563EB"),
        alignment=1
    )

    desc_style = ParagraphStyle(
        'CoverDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1
    )

    role_divider_title = ParagraphStyle(
        'RoleDividerTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        alignment=0
    )

    role_divider_desc = ParagraphStyle(
        'RoleDividerDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )

    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0F172A")
    )

    card_meta_style = ParagraphStyle(
        'CardMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    card_badge_style = ParagraphStyle(
        'CardBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=2
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # =========================================================================
    # 1. COVER PAGE & EXECUTIVE SUMMARY MATRIX
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("VITCC CENTRAL LIBRARY MANAGEMENT SYSTEM", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("MULTI-ROLE INTERFACE AUDIT & ROLE-BASED ACCESS CONTROL (RBAC) VERIFICATION REPORT", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Automated high-fidelity capture of all system sections across Administrator, Librarian, Faculty/Staff, Student, and Public portals for autonomous LLM audit and compliance review.", desc_style))
    story.append(Spacer(1, 10))

    # Audit Metadata Table
    audit_meta_data = [
        [
            Paragraph("<b>Audit Date:</b> October 18, 2026", card_meta_style),
            Paragraph("<b>Target Environment:</b> Live Dev Server (http://127.0.0.1:5000)", card_meta_style),
            Paragraph("<b>Display Viewport:</b> 1440 x 960 (Desktop HD)", card_meta_style)
        ],
        [
            Paragraph("<b>Database Engines:</b> Oracle Database 23ai + Neo4j Graph DB", card_meta_style),
            Paragraph("<b>Total Views Audited:</b> 44 Unique Verified Screens", card_meta_style),
            Paragraph("<b>Security Model:</b> Session RBAC + CSRF Protection", card_meta_style)
        ]
    ]
    meta_table = Table(audit_meta_data, colWidths=[264, 264, 264])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Comprehensive RBAC Matrix Table
    matrix_headers = ["Application Section / Feature", "Route URL", "Public", "Admin", "Librarian", "Staff", "Student", "Access Scope / Security Rule"]
    matrix_rows = [
        [
            Paragraph(matrix_headers[0], table_header_style),
            Paragraph(matrix_headers[1], table_header_style),
            Paragraph(matrix_headers[2], table_header_style),
            Paragraph(matrix_headers[3], table_header_style),
            Paragraph(matrix_headers[4], table_header_style),
            Paragraph(matrix_headers[5], table_header_style),
            Paragraph(matrix_headers[6], table_header_style),
            Paragraph(matrix_headers[7], table_header_style)
        ],
        [Paragraph("Login & Authentication", table_cell_style), Paragraph("/login", table_cell_style), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("Public credential verification & session issuing", table_cell_style)],
        [Paragraph("Patron Registration", table_cell_style), Paragraph("/register", table_cell_style), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("Self-service patron sign up (Student/Staff)", table_cell_style)],
        [Paragraph("Dashboard & Overview", table_cell_style), Paragraph("/dashboard", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Full", table_cell_center), Paragraph("✓ Desk", table_cell_center), Paragraph("✓ Faculty", table_cell_center), Paragraph("✓ Personal", table_cell_center), Paragraph("Role-tailored KPI cards, borrowing queues & charts", table_cell_style)],
        [Paragraph("Catalog & Book Search", table_cell_style), Paragraph("/books", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("Global catalog search with category & author filtering", table_cell_style)],
        [Paragraph("Category & Curriculum Graph", table_cell_style), Paragraph("/category/&lt;id&gt;", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("Prerequisite & unlocks badges, co-borrowing pills", table_cell_style)],
        [Paragraph("Issue Book Loan", table_cell_style), Paragraph("/issue_loan", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Staffed", table_cell_center), Paragraph("✓ Staffed", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Direct copy allocation desk (Admin & Librarian only)", table_cell_style)],
        [Paragraph("Loan Requests & Collection", table_cell_style), Paragraph("/loan_requests", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Staffed", table_cell_center), Paragraph("✓ Staffed", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Patron pickup approvals & collection desk handover", table_cell_style)],
        [Paragraph("Manage Users & Governance", table_cell_style), Paragraph("/manage_users", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Admin", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("RBAC privileges, suspension & password resets (Admin)", table_cell_style)],
        [Paragraph("Learning Roadmaps", table_cell_style), Paragraph("/learning_paths", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("Curriculum tracks & multi-level study hierarchies", table_cell_style)],
        [Paragraph("AI Recommendations", table_cell_style), Paragraph("/recommendations", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Trends", table_cell_center), Paragraph("✓ Trends", table_cell_center), Paragraph("✓ Faculty", table_cell_center), Paragraph("✓ Peer", table_cell_center), Paragraph("Collaborative filtering, peer study partners & trends", table_cell_style)],
        [Paragraph("My Fines & Settlements", table_cell_style), Paragraph("/my_fines", table_cell_style), Paragraph("—", table_cell_center), Paragraph("—", table_cell_center), Paragraph("—", table_cell_center), Paragraph("✓ Faculty", table_cell_center), Paragraph("✓ Student", table_cell_center), Paragraph("Personal overdue fines & instant payment gateway", table_cell_style)],
        [Paragraph("Knowledge Graph Explorer", table_cell_style), Paragraph("/graph_visualizer", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Global", table_cell_center), Paragraph("✓ System", table_cell_center), Paragraph("✓ Academic", table_cell_center), Paragraph("✓ Learning", table_cell_center), Paragraph("Interactive Cytoscape / Vis.js network visualizer", table_cell_style)],
        [Paragraph("Book Bridge (Shortest Path)", table_cell_style), Paragraph("/book_bridge", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Path", table_cell_center), Paragraph("✓ Path", table_cell_center), Paragraph("✓ Path", table_cell_center), Paragraph("✓ Path", table_cell_center), Paragraph("Neo4j shortest path traversal between book nodes", table_cell_style)],
        [Paragraph("Centrality Analytics Lab", table_cell_style), Paragraph("/library_analytics", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓ Lab", table_cell_center), Paragraph("✓ Lab", table_cell_center), Paragraph("✓ Lab", table_cell_center), Paragraph("Blocked", table_cell_center), Paragraph("Author Degree, Betweenness & Closeness centrality", table_cell_style)],
        [Paragraph("Change Password", table_cell_style), Paragraph("/change_password", table_cell_style), Paragraph("—", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("✓", table_cell_center), Paragraph("Self-service credential updates (8–64 character policy)", table_cell_style)],
    ]

    col_widths = [125, 80, 42, 50, 52, 48, 48, 347]
    rbac_table = Table(matrix_rows, colWidths=col_widths)
    rbac_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(rbac_table)

    # Group manifest items by Role
    roles_order = ["Public", "Admin", "Librarian", "Staff", "Student"]
    role_info = {
        "Public": {
            "title": "SECTION 1: PUBLIC GATEWAY & PATRON ONBOARDING",
            "desc": "Unauthenticated access portals for library patrons and visitors. Includes secure authentication login with CSRF token generation and new patron account registration.",
            "color": "#64748B",
            "badge": "Public Access"
        },
        "Admin": {
            "title": "SECTION 2: SYSTEM ADMINISTRATOR PORTAL",
            "desc": "Highest privilege level with comprehensive system governance, user administration, copy allocation, loan approval desk, Neo4j graph algorithms, and centralized analytics.",
            "color": "#DC2626",
            "badge": "Role: Admin"
        },
        "Librarian": {
            "title": "SECTION 3: CIRCULATION DESK LIBRARIAN PORTAL",
            "desc": "Staffed operations for daily book loans, return processing, loan request fulfillment, physical copy reservations, and graph analytics.",
            "color": "#D97706",
            "badge": "Role: Librarian"
        },
        "Staff": {
            "title": "SECTION 4: FACULTY & ACADEMIC STAFF PORTAL",
            "desc": "Academic privileges for faculty members, including departmental borrowing, AI curriculum recommendations, graph exploration, and fine settlement.",
            "color": "#2563EB",
            "badge": "Role: Staff"
        },
        "Student": {
            "title": "SECTION 5: STUDENT PATRON PORTAL",
            "desc": "Student learning dashboard, course catalog search, curriculum prerequisite trees, peer study partner recommendations, overdue fine payments, and personal graph visualizer.",
            "color": "#16A34A",
            "badge": "Role: Student"
        }
    }

    current_role = None

    for item in manifest:
        story.append(PageBreak())

        item_role = item["role"]
        is_first_of_role = (item_role != current_role)
        current_role = item_role
        info = role_info.get(item_role, role_info["Public"])

        # Top Header Bar for Screenshot Slide
        badge_color = info["color"]
        badge_html = f'<font color="{badge_color}"><b>● {item_role.upper()} ACCESS</b></font>'
        route_html = f'<b>Route:</b> <font color="#2563EB">http://127.0.0.1:5000{item["urlPath"]}</font>'

        header_data = [
            [
                Paragraph(f"<b>{item['name']}</b>", card_title_style),
                Paragraph(badge_html, card_badge_style)
            ],
            [
                Paragraph(f"{route_html} &nbsp;|&nbsp; <b>ID:</b> {item['id']}", card_meta_style),
                Paragraph(f"<font color='#64748B'>VITCC Library UI Audit</font>", card_badge_style)
            ]
        ]
        slide_header = Table(header_data, colWidths=[590, 202])
        slide_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(slide_header)
        story.append(Spacer(1, 4))

        # Screenshot Image
        img_path = item["filePath"]
        if os.path.exists(img_path):
            # Target width = 792 pt, aspect ratio = 1440 / 960 = 1.5 -> height = 528 pt
            # We want to fit comfortably on page: width = 760 pt, height = 475 pt
            img_w = 760
            img_h = 475
            img_flowable = Image(img_path, width=img_w, height=img_h)
            
            # Wrap image in a table for border and background
            img_table = Table([[img_flowable]], colWidths=[792])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0B0F19"))
            ]))
            story.append(img_table)
        else:
            story.append(Paragraph(f"<font color='red'>Missing screenshot: {img_path}</font>", card_title_style))

    print(f"Building PDF document: {OUTPUT_PDF} ...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF build complete successfully!")

if __name__ == "__main__":
    build_pdf()
