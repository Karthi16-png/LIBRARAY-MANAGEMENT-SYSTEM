import subprocess
import sys
import time

PHASES = [
    ("Phase 1: Auth & Access Control Matrix", "scratch/phase1_test_auth_matrix.py"),
    ("Phase 2: Dashboard Experience by Role", "scratch/phase2_test_dashboards.py"),
    ("Phase 3: Catalog, Categories & Books", "scratch/phase3_test_catalog_and_books.py"),
    ("Phase 4: Circulation, Loans & Fines", "scratch/phase4_test_circulation.py"),
    ("Phase 5: Graph, Roadmaps & AI Recs", "scratch/phase5_test_graph_and_intelligence.py"),
    ("Phase 6: Admin, Analytics & Fine Ledgers", "scratch/phase6_test_admin_and_analytics.py"),
    ("Phase 7: Template AST, URLs & Spelling", "scratch/check_templates.py")
]

def main():
    print("=" * 70)
    print("MASTER SYSTEM AUDIT: EXECUTING ALL 7 VERIFICATION PHASES")
    print("=" * 70)
    results = []
    start_total = time.time()

    for name, script in PHASES:
        print(f"\n>>> Running {name} ({script})...")
        t0 = time.time()
        res = subprocess.run([sys.executable, script], capture_output=True, text=True)
        dur = time.time() - t0
        passed = (res.returncode == 0)
        results.append((name, script, passed, dur, res.stdout, res.stderr))
        status_str = "[PASS]" if passed else "[FAIL]"
        print(f"{status_str} in {dur:.2f}s")
        if not passed:
            print("--- STDERR ---")
            print(res.stderr)
            print("--- STDOUT ---")
            print(res.stdout[-500:])

    total_dur = time.time() - start_total
    print("\n" + "=" * 70)
    print("AUDIT EXECUTIVE SUMMARY MATRIX")
    print("=" * 70)
    all_passed = True
    for name, script, passed, dur, _, _ in results:
        status_text = "PASS (100%)" if passed else "FAILED"
        print(f"  {name:<42} | {status_text:<12} | {dur:5.2f}s")
        if not passed:
            all_passed = False

    print("-" * 70)
    print(f"Total Execution Time: {total_dur:.2f} seconds")
    if all_passed:
        print("ALL PHASES PASSED WITH ZERO REGRESSIONS AND ZERO DEFECTS.")
    else:
        print("CRITICAL: One or more audit phases failed.")
    print("=" * 70)

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
