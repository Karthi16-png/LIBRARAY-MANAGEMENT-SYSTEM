import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import get_session

def sync_awaiting_pickup_and_reserved():
    with get_session() as s:
        # 1. Inspect all LoanRequests with status 'Awaiting Pickup'
        reqs = s.run("""
            MATCH (r:LoanRequest {status: 'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book)
            RETURN r.request_id AS rid, r.copy_id AS cid, b.book_id AS bid, b.title AS title
        """).data()
        print("Awaiting Pickup requests:", reqs)

        for req in reqs:
            rid = req["rid"]
            cid = req["cid"]
            bid = req["bid"]

            # Check if assigned copy exists and is reserved for this request
            valid_copy = None
            if cid:
                cp_check = s.run("""
                    MATCH (cp:Copy {copy_id: $cid, book_id: $bid})
                    RETURN cp.copy_id AS copy_id, cp.status AS status
                """, cid=int(cid), bid=bid).single()
                if cp_check and cp_check["status"] in ["Available", "Reserved"]:
                    valid_copy = cp_check["copy_id"]

            if not valid_copy:
                # Find any available or reserved copy of this book
                avail = s.run("""
                    MATCH (b:Book {book_id: $bid})-[:HAS_COPY]->(cp:Copy)
                    WHERE cp.status IN ['Available', 'Reserved']
                    RETURN cp.copy_id AS copy_id LIMIT 1
                """, bid=bid).single()
                if avail:
                    valid_copy = avail["copy_id"]

            if valid_copy:
                print(f"Assigning and linking Copy #{valid_copy} to Request #{rid}")
                s.run("""
                    MATCH (r:LoanRequest {request_id: $rid})
                    MATCH (cp:Copy {copy_id: $cid})
                    SET r.status = 'Awaiting Pickup', r.copy_id = $cid, cp.status = 'Reserved'
                    MERGE (r)-[:RESERVED_COPY]->(cp)
                """, rid=rid, cid=valid_copy)
            else:
                print(f"No copy available for Book '{req['title']}'. Re-syncing Request #{rid} to 'Pending'!")
                s.run("""
                    MATCH (r:LoanRequest {request_id: $rid})
                    OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()
                    DELETE rel
                    SET r.status = 'Pending'
                    REMOVE r.copy_id
                """, rid=rid)

        # 2. Release orphaned reserved copies (copies marked 'Reserved' that have no 'Awaiting Pickup' request)
        orphans = s.run("""
            MATCH (cp:Copy {status: 'Reserved'})
            WHERE NOT (cp)<-[:RESERVED_COPY]-(:LoanRequest {status: 'Awaiting Pickup'})
              AND NOT (cp)<-[:FOR_COPY]-(:LoanRequest {status: 'Awaiting Pickup'})
            RETURN cp.copy_id AS copy_id
        """).data()
        print("Orphaned reserved copies to release:", orphans)
        for o in orphans:
            s.run("MATCH (cp:Copy {copy_id: $cid}) SET cp.status = 'Available'", cid=o["copy_id"])

        print("Sync complete!")

if __name__ == "__main__":
    sync_awaiting_pickup_and_reserved()
