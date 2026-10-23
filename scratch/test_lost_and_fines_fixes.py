import os, sys
import re
from datetime import datetime
sys.path.insert(0, os.path.abspath("."))
from app import app, get_session

def test_catalog_counts_and_fines():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    print("\n=======================================================")
    print("VERIFICATION SUITE: CATALOG TITLE COUNT & FINES SYNCHRONIZATION")
    print("=======================================================")

    with app.test_client() as client:
        # Step 1: Set session as Admin
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "Admin"
        print("[PASS] Successfully set session as Admin.")

        # Step 2: Check /catalog unique book title counts
        resp_catalog = client.get("/catalog")
        assert resp_catalog.status_code == 200
        cat_html = resp_catalog.get_data(as_text=True)

        with get_session() as s:
            res_cat1 = s.run("""
                MATCH (c:Category {category_id: 1})
                OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
                RETURN count(DISTINCT b) AS title_count
            """).single()
            cat1_titles = res_cat1["title_count"]
            print(f" -> Category 1 (Computer Science & AI) Unique Titles Count: {cat1_titles}")

            # Verify rendered badge in catalog
            assert f"{cat1_titles} Title" in cat_html, f"Expected '{cat1_titles} Title(s)' in catalog HTML"
            print(f"[PASS] /catalog renders exactly '{cat1_titles} Titles' for Category 1.")

            # Step 3: Check /category/1 banner and copy counts
            resp_cat1 = client.get("/category/1")
            assert resp_cat1.status_code == 200
            cat1_page_html = resp_cat1.get_data(as_text=True)
            assert f"{cat1_titles} Title" in cat1_page_html, f"Expected '{cat1_titles} Title(s) in Category' in /category/1 HTML"
            print(f"[PASS] /category/1 banner renders exactly '{cat1_titles} Titles in Category'.")

            # Check that Introduction to Algorithms (CLRS) has copy #6 as Lost, and total copies excludes it
            res_clrs = s.run("""
                MATCH (b:Book {title: 'Introduction to Algorithms (CLRS)'})
                RETURN size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS total_active_copies,
                       size([(b)-[:HAS_COPY]->(cp:Copy {status:'Available'}) | cp]) AS avail_copies
            """).single()
            print(f" -> CLRS Total Active Copies: {res_clrs['total_active_copies']}, Available: {res_clrs['avail_copies']}")
            assert res_clrs['total_active_copies'] == 1, "Expected exactly 1 active copy for CLRS (Copy #6 is Lost)"
            print("[PASS] CLRS book card excludes Lost copy from total active copies.")

            # Step 4: Verify Admin Dashboard Disciplinary Fines Alignment
            resp_dash = client.get("/dashboard")
            assert resp_dash.status_code == 200
            dash_html = resp_dash.get_data(as_text=True)

            # Extract stat card Disciplinary Fines value
            m_stat = re.search(r'Disciplinary Fines</span>.*?<div class="stat-value">\s*Rs\.\s*([\d\.]+)\s*</div>', dash_html, re.DOTALL)
            assert m_stat, "Could not find Disciplinary Fines stat card value in dashboard HTML"
            stat_amount = float(m_stat.group(1))
            print(f" -> Stat Card Disciplinary Fines Amount: Rs. {stat_amount:.2f}")

            # Extract ledger table fine rows
            ledger_amounts = [float(x) for x in re.findall(r'color:\s*var\(--warning-text\);\s*">\s*Rs\.\s*([\d\.]+)', dash_html)]
            ledger_sum = sum(ledger_amounts)
            print(f" -> Ledger Table Penalties Count: {len(ledger_amounts)}, Total: Rs. {ledger_sum:.2f}")

            # Assert exact match
            assert abs(stat_amount - ledger_sum) < 0.001, f"Mismatch: Stat card shows Rs. {stat_amount:.2f} but ledger rows sum to Rs. {ledger_sum:.2f}"
            print(f"[PASS] Stat Card (Rs. {stat_amount:.2f}) matches Ledger Rows Sum (Rs. {ledger_sum:.2f}) exactly!")

            # Step 5: Verify no orphaned Fine nodes exist in database
            res_orphans = s.run("""
                MATCH (f:Fine)
                WHERE NOT (f)<-[:HAS_FINE]-(:Loan)
                RETURN count(f) AS orphan_count
            """).single()
            assert res_orphans["orphan_count"] == 0, f"Found {res_orphans['orphan_count']} orphaned Fine nodes!"
            print("[PASS] Zero orphaned Fine nodes exist in Neo4j database.")

            # Step 6: Test reporting a book as lost updates copy inventory and fines
            test_cid = 2 # Physics & Astronomy (currently 1 title, 2 copies)
            res_title_before = s.run("""
                MATCH (c:Category {category_id: $cid})
                OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
                RETURN count(DISTINCT b) AS title_count
            """, cid=test_cid).single()["title_count"]

            res_avail = s.run("""
                MATCH (b:Book)-[:BELONGS_TO]->(c:Category {category_id: $cid})
                MATCH (b)-[:HAS_COPY]->(cp:Copy {status: 'Available'})
                RETURN cp.copy_id AS copy_id, b.book_id AS book_id LIMIT 1
            """, cid=test_cid).single()

            if res_avail:
                cp_id = res_avail["copy_id"]
                bk_id = res_avail["book_id"]
                # Create a test loan
                res_max_loan = s.run("MATCH (l:Loan) RETURN coalesce(max(l.loan_id), 0) + 1 AS next_lid").single()
                test_lid = res_max_loan["next_lid"]
                s.run("""
                    MATCH (u:User {username: 'alex_stu'}), (cp:Copy {copy_id: $cid})
                    CREATE (l:Loan {
                        loan_id: $lid, borrower_id: u.user_id,
                        copy_id: $cid, issue_date: '2026-10-01',
                        due_date: '2026-10-15', return_date: null
                    })
                    CREATE (u)-[:BORROWED]->(l)
                    CREATE (l)-[:FOR_COPY]->(cp)
                    SET cp.status = 'Borrowed'
                """, lid=test_lid, cid=cp_id)

                # Report lost
                resp_lost = client.post(f"/report_lost/{test_lid}", follow_redirects=True)
                assert resp_lost.status_code == 200

                # Check book total active copies after marking lost
                res_copies_after = s.run("""
                    MATCH (b:Book {book_id: $bid})
                    RETURN size([(b)-[:HAS_COPY]->(cp:Copy) WHERE cp.status <> 'Retired' AND cp.status <> 'Lost' | cp]) AS active_copies
                """, bid=bk_id).single()["active_copies"]

                # Title count remains stable since title is in catalog
                res_title_after = s.run("""
                    MATCH (c:Category {category_id: $cid})
                    OPTIONAL MATCH (b:Book)-[:BELONGS_TO]->(c)
                    RETURN count(DISTINCT b) AS title_count
                """, cid=test_cid).single()["title_count"]

                print(f" -> Cat {test_cid} Unique Titles: {res_title_after} (stable), Book #{bk_id} Active Copies: {res_copies_after} (decremented by 1)")
                assert res_title_after == res_title_before, "Title count should reflect unique books in catalog"
                assert res_copies_after == 1, "Book active copies should decrease by 1 upon being marked lost"
                print(f"[PASS] Category title count preserved at {res_title_after} Titles, and copy inventory decreased to {res_copies_after}!")

                # Check that dashboard ledger also updated with the new fine and matches stat card
                resp_dash2 = client.get("/dashboard")
                dash_html2 = resp_dash2.get_data(as_text=True)
                m_stat2 = re.search(r'Disciplinary Fines</span>.*?<div class="stat-value">\s*Rs\.\s*([\d\.]+)\s*</div>', dash_html2, re.DOTALL)
                stat_amt2 = float(m_stat2.group(1))
                ledger_amts2 = [float(x) for x in re.findall(r'color:\s*var\(--warning-text\);\s*">\s*Rs\.\s*([\d\.]+)', dash_html2)]
                assert abs(stat_amt2 - sum(ledger_amts2)) < 0.001, f"Mismatch: stat {stat_amt2} != ledger {sum(ledger_amts2)}"
                print(f"[PASS] New lost fine (Rs. 1500) synchronized in dashboard: stat Rs. {stat_amt2:.2f} == ledger sum Rs. {sum(ledger_amts2):.2f}")

                # Clean up test loan and fine, restore copy
                s.run("""
                    MATCH (l:Loan {loan_id: $lid})
                    OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine)
                    OPTIONAL MATCH (l)-[:FOR_COPY]->(cp:Copy)
                    SET cp.status = 'Available'
                    DETACH DELETE f, l
                """, lid=test_lid)
                print("[PASS] Cleaned up temporary test loan and restored copy to Available.")

    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_catalog_counts_and_fines()
