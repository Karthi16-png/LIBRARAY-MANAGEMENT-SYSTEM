# VITCC Enterprise Library Management System

> **Next-Generation Graph-Powered Academic Library Portal**  
> Migrated from Oracle 21c Relational Database to **Neo4j AuraDB Graph Database** for High-Performance Knowledge Traversal, Academic Roadmaps, and AI Recommendations.

---

## 🏛️ Project Overview

The **VITCC Enterprise Library Management System** is a full-featured, secure, and graph-native library management application engineered for academic institutions. By transitioning from a traditional relational schema to a **Neo4j Property Graph Database**, this platform enables instantaneous shortest-path discovery, prerequisite hierarchy mapping, real-time citation analysis, and collaborative filtering recommendations that would otherwise require complex multi-table SQL joins.

### 👥 Development Team (DA-3 Project Assessment)
- **Karthik Valliappan C** — `25BAI1051`
- **Nithin Rangaswamy** — `25BAI1210`
- **Natraj** — `25BAI1079`

---

## 🚀 Key Architectural Features & Modules

### 1. 🛡️ Role-Based Access Control (RBAC) & Authentication
- **4 Distinct Roles**:
  - **Admin**: Full system authority, user account lifecycle management (provision, suspend, reactivate, password reset), book registration, book deletion, and system auditing.
  - **Librarian**: Circulation desk operations, loan issuance, loan request approval, copy reservations, physical book returns, and fine settlement.
  - **Staff (Faculty)**: Dedicated catalog browsing, 3-book academic borrowing quota, learning roadmap navigation, author centrality analytics, and personal fine statements.
  - **Student (Academic Patron)**: Book search, digital loan requests, prerequisite roadmaps, personalized AI recommendations, and patron fine ledgers.
- **Security Features**:
  - Flask-WTF CSRF token validation across all mutable POST endpoints.
  - PBKDF2:SHA256 password hashing with complexity enforcement.
  - 10-minute idle session timeout with automatic server-side invalidation.
  - Institutional email verification (`@vit.edu` or `@vit.ac.in`).

### 2. 🕸️ Interactive Live Graph Explorer (`/graph_visualizer`)
- Real-time Vis.js physics-driven canvas mapping the complete library ecosystem:
  - `(User)-[:BORROWED]->(Loan)-[:FOR_COPY]->(Copy)<-[:HAS_COPY]-(Book)-[:BELONGS_TO]->(Category)`
  - `(Book)-[:PREREQUISITE_FOR]->(Book)`
  - `(Author)-[:WROTE]->(Book)`
  - `(Publisher)-[:PUBLISHED]->(Book)`
- **Patron Privacy Masking**: When viewed by Students or Staff, borrowing records and requests of other patrons are anonymized to protect institutional privacy.

### 3. 🌉 Book-to-Book Bridge (`/book_bridge`)
- Discovers the **shortest path degrees of separation** between any two titles in the catalog.
- Traverses prerequisite connections, co-authorship, shared categories, and circulation linkages with step-by-step breadcrumb explanations.

### 4. 🗺️ Academic Learning Roadmaps (`/learning_paths`)
- Directed Acyclic Graph (DAG) visualizing prerequisite reading pathways across four academic tracks:
  - Software Engineering & Agile Architecture
  - Artificial Intelligence & Machine Learning
  - Distributed Systems & Database Architecture
  - Computer Networks & Cybersecurity
- Enforces foundational mastery before advancing to specialized texts.

### 5. 🤖 AI Recommendations & Graph Collaborative Filtering (`/recommendations`)
- Multi-vector recommendation engine combining:
  - **Collaborative Filtering**: "Patrons who borrowed this book also borrowed..."
  - **Category Affinity**: Clustering based on subject taxonomy.
  - **Downstream Prerequisite Badges**: Automatic discovery of complementary advanced texts.

### 6. 📊 Centrality & Influencer Analytics (`/library_analytics`)
- Graph analytics computing:
  - **Author Degree Centrality**: Identifies highest-impact scholars by borrowing volume.
  - **Category Closeness & Circulation Velocity**: Maps reading engagement across departments.

---

## 🛠️ Technology Stack

- **Backend Framework**: Python 3.12+, Flask 3.1, Werkzeug
- **Graph Database**: Neo4j AuraDB (Cloud Managed Instance)
- **Database Driver**: Official `neo4j` Python Driver (v5+) with Cypher Query Language
- **Security & Forms**: Flask-WTF, WTForms, Flask-Session (Server-side filesystem sessions)
- **Frontend Architecture**:
  - HTML5 & Modern Vanilla CSS (Custom Glassmorphism Dark Mode)
  - Typography: Google Fonts (*Plus Jakarta Sans* & *JetBrains Mono*)
  - Graph Visualization: Vis.js Network v9.1.2
- **Testing & Verification**: 7 Automated End-to-End Test Suites (100% Passing)

---

## 📋 Prerequisites & System Requirements

Before running the application, ensure the following components are available on your system:

### 1. Software & Runtimes
- **Python**: `3.10` or higher (`3.12` recommended). Verify with `python --version`.
- **Git**: Installed for repository cloning and version control.
- **pip** & **venv**: Standard Python package manager and virtual environment tools.

### 2. Neo4j Graph Database
This application is powered by **Neo4j 5+**. You can connect via either:
- **Option A (Cloud Neo4j AuraDB - Recommended)**:
  - Create a free instance at [console.neo4j.io](https://console.neo4j.io).
  - Note your connection URI (`neo4j+s://<instance-id>.databases.neo4j.io`), username, and generated password.
  - *Note*: AuraDB Free Tier databases automatically pause after 3 days of inactivity. If connection fails, log into [console.neo4j.io](https://console.neo4j.io) and click **"Resume"**.
- **Option B (Local Neo4j via Docker or Desktop)**:
  - Run a local Neo4j 5 container:
    ```bash
    docker run -d --name neo4j-vitcc -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:5-community
    ```
  - Connection URI: `bolt://localhost:7687`

### 3. Institutional Policies & Credentials
- **Email Validation**: Account registration (`/register`) and user provisioning (`/manage_users`) strictly require valid institutional domains: `@vit.edu` or `@vit.ac.in`.
- **Password Complexity**: 8 to 64 characters, with at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special symbol.

---

## 🔑 Default Test Accounts (RBAC)

When the database is seeded using `python seed_all_data.py`, 11 pre-configured users are initialized across all four roles:

| Role | Username | Password | Institutional Email | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | `admin@vit.edu` | Full system control, user provisioning/suspension, book deletion |
| **Librarian** | `librarian` | `Lib@12345` | `librarian@vit.edu` | Circulation desk, book loans, request approvals, returns, fine payments |
| **Staff** | `staff` | `Staff@123` | `staff@vit.edu` | Faculty catalog search, 3-book quota, learning paths, centrality stats |
| **Staff** | `prof_turing` | `Staff@123` | `turing@vit.edu` | Faculty catalog search, borrowing, academic roadmaps |
| **Student** | `student` | `Student@1` | `student@vit.edu` | Patron book search, loan requests, learning roadmaps, fine statements |
| **Student** | `alex_stu` | `Student@1` | `alex@vit.edu` | Academic student patron account |

---

## 📦 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "DBS DA"
```

### 2. Set Up Virtual Environment
```bash
# Windows (PowerShell / Command Prompt)
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` or set environment variables:
```bash
# Windows PowerShell
$env:NEO4J_URI="neo4j+s://<your-instance-id>.databases.neo4j.io"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="<your-password>"
$env:NEO4J_DATABASE="neo4j"

# Linux / macOS
export NEO4J_URI="neo4j+s://<your-instance-id>.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="<your-password>"
export NEO4J_DATABASE="neo4j"
```
*(If no environment variables are set, `app.py` falls back to the default team cloud instance configuration).*

### 5. Seed Database (Required on Fresh Databases)
> ⚠️ **Notice**: `seed_all_data.py` executes `MATCH (n) DETACH DELETE n` to reset schema constraints and populate standard categories, books, copies, prerequisite edges, and users.
```bash
python seed_all_data.py
```

### 6. Launch Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000/`**

---

## 🧪 Comprehensive Verification Suite

To run all 7 automated test suites verifying every role, route, quota, and edge case:
```bash
python scratch/run_all_phases.py
```

### Test Suite Matrix:
- `scratch/phase1_test_auth_matrix.py`: Authentication, idle timeout & RBAC 403 matrix
- `scratch/phase2_test_dashboards.py`: Role-specific dashboards & quota metrics
- `scratch/phase3_test_catalog_and_books.py`: Catalog browsing, search & book management
- `scratch/phase4_test_circulation.py`: Loan requests, copy reservations, issues, returns & fines
- `scratch/phase5_test_graph_and_intelligence.py`: Graph privacy, Book Bridge & AI recommendations
- `scratch/phase6_test_admin_and_analytics.py`: User lifecycle, analytics & fine statements
- `scratch/check_templates.py`: Jinja2 AST parsing, endpoint validation & typography audit

---

## 📄 License & Attribution

Developed for academic evaluation as part of the **VITCC Database Systems Assessment (DA-3)**. All rights reserved.
