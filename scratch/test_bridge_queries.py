from app import get_session

with get_session() as s:
    books = s.run('MATCH (b:Book) RETURN b.book_id as id, b.title as title ORDER BY id LIMIT 5').data()
    print("Testing Shortest Path across first 5 books:")
    for i in range(len(books)):
        for j in range(i+1, len(books)):
            b1 = books[i]['id']
            b2 = books[j]['id']
            # Shortest path supporting category, author, publisher, copies, loans, requests
            res = s.run('''
                MATCH p = shortestPath((b1:Book {book_id: $id1})-[:BELONGS_TO|WROTE|PUBLISHED_BY|HAS_COPY|FOR_COPY|BORROWED|FOR_BOOK*1..8]-(b2:Book {book_id: $id2}))
                RETURN p
            ''', {'id1': b1, 'id2': b2}).single()
            if res and res['p']:
                p = res['p']
                print(f"  Book {b1} -> Book {b2}: {len(p)} hops (Nodes: {len(p.nodes)})")
                summary = " -> ".join([list(n.labels)[0] + (f" ({n.get('title', n.get('name', ''))[:15]})" if n.get('title') or n.get('name') else "") for n in p.nodes])
                print(f"    Path: {summary}")
            else:
                print(f"  Book {b1} -> Book {b2}: No path")

    print("\nTesting Centrality Queries:")
    # 1. Author Centrality
    authors = s.run('''
        MATCH (a:Author)-[:WROTE]->(b:Book)-[:HAS_COPY]->(cp:Copy)<-[:FOR_COPY]-(l:Loan)
        RETURN a.first_name + ' ' + a.last_name AS author_name,
               count(l) AS total_borrowings,
               count(DISTINCT b) AS authored_books,
               count(DISTINCT cp) AS active_copies
        ORDER BY total_borrowings DESC
        LIMIT 5
    ''').data()
    print("  Top Authors by Borrowing Centrality:")
    for a in authors:
        print("   ", a)

    # 2. Book Degree Centrality
    book_centrality = s.run('''
        MATCH (b:Book)
        OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)
        OPTIONAL MATCH (cp)<-[:FOR_COPY]-(l:Loan)
        OPTIONAL MATCH (b)<-[:FOR_BOOK]-(lr:LoanRequest)
        RETURN b.book_id AS book_id, b.title AS title,
               count(DISTINCT cp) AS copies_count,
               count(DISTINCT l) AS loans_count,
               count(DISTINCT lr) AS requests_count,
               (count(DISTINCT cp) * 2 + count(DISTINCT l) * 3 + count(DISTINCT lr)) AS degree_score
        ORDER BY degree_score DESC
        LIMIT 5
    ''').data()
    print("  Top Books by Graph Degree Centrality:")
    for bc in book_centrality:
        print("   ", bc)

    # 3. Category Closeness
    cats = s.run('''
        MATCH (cat:Category)<-[:BELONGS_TO]-(b:Book)
        OPTIONAL MATCH (b)-[:HAS_COPY]->(cp:Copy)<-[:FOR_COPY]-(l:Loan)
        RETURN cat.name AS category_name,
               count(DISTINCT b) AS books_count,
               count(l) AS total_loans
        ORDER BY total_loans DESC
    ''').data()
    print("  Category Density & Loans:")
    for c in cats:
        print("   ", c)
