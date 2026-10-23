with open('templates/category_books.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''    /* Instant Client-side Search Filtering for Category Books */
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('bookSearchInput');
        const booksGrid = document.getElementById('booksGrid');
        const visibleCounter = document.getElementById('visibleBookCount');

        if (searchInput && booksGrid) {
            searchInput.addEventListener('input', function() {
                const query = this.value.toLowerCase().trim();
                const cards = booksGrid.querySelectorAll('.book-card');
                let visible = 0;

                cards.forEach(card => {
                    const title = card.getAttribute('data-title') || '';
                    const author = card.getAttribute('data-author') || '';
                    const isbn = card.getAttribute('data-isbn') || '';

                    if (!query || title.includes(query) || author.includes(query) || isbn.includes(query)) {
                        card.style.display = '';
                        visible++;
                    } else {
                        card.style.display = 'none';
                    }
                });

                if (visibleCounter) {
                    visibleCounter.textContent = visible;
                }
            });
        }
    });'''

replacement = '''    /* Instant Client-side Search Filtering for Category Books */
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('bookSearchInput');
        const booksGrid = document.getElementById('booksGrid');
        const visibleCounter = document.getElementById('visibleBookCount');
        if (!searchInput || !booksGrid) return;

        const cards = Array.from(booksGrid.querySelectorAll('.book-card'));

        // Client-side dynamic empty state panel
        let clientEmpty = document.getElementById('clientNoMatch');
        if (!clientEmpty) {
            clientEmpty = document.createElement('div');
            clientEmpty.id = 'clientNoMatch';
            clientEmpty.className = 'empty-state-panel';
            clientEmpty.style.display = 'none';
            clientEmpty.style.marginTop = '24px';
            clientEmpty.innerHTML = `
                <div class="empty-state-icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                </div>
                <h3 class="empty-state-title">No Books Match Search</h3>
                <p class="empty-state-sub" id="clientEmptyText">No books found matching your search.</p>
                <button type="button" class="btn btn-secondary" onclick="document.getElementById('bookSearchInput').value=''; document.getElementById('bookSearchInput').dispatchEvent(new Event('input'));">Clear Search</button>
            `;
            booksGrid.parentNode.insertBefore(clientEmpty, booksGrid.nextSibling);
        }

        function runLiveFilter() {
            const raw = searchInput.value.trim().toLowerCase();
            const terms = raw.split(/\\s+/).filter(Boolean);
            let visible = 0;

            cards.forEach(card => {
                if (terms.length === 0) {
                    card.style.display = '';
                    visible++;
                    return;
                }
                const title = card.getAttribute('data-title') || '';
                const author = card.getAttribute('data-author') || '';
                const isbn = card.getAttribute('data-isbn') || '';
                const cleanIsbn = isbn.replace(/[^a-z0-9]/gi, '');
                const publisher = card.getAttribute('data-publisher') || '';
                const year = card.getAttribute('data-year') || '';
                const fullText = `${title} ${author} ${isbn} ${cleanIsbn} ${publisher} ${year}`.toLowerCase();

                const matchesAll = terms.every(term => {
                    const cleanTerm = term.replace(/[^a-z0-9]/gi, '');
                    return fullText.includes(term) || (cleanTerm && fullText.includes(cleanTerm));
                });

                if (matchesAll) {
                    card.style.display = '';
                    visible++;
                } else {
                    card.style.display = 'none';
                }
            });

            if (visibleCounter) {
                visibleCounter.textContent = visible;
            }

            if (clientEmpty) {
                if (visible === 0 && terms.length > 0) {
                    clientEmpty.style.display = 'block';
                    document.getElementById('clientEmptyText').textContent = `No books found in this category matching "${searchInput.value.trim()}".`;
                } else {
                    clientEmpty.style.display = 'none';
                }
            }
        }

        searchInput.addEventListener('input', runLiveFilter);
        searchInput.addEventListener('keyup', runLiveFilter);
    });'''

# Normalize for replacement
text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
rep_norm = replacement.replace('\r\n', '\n')

if target_norm in text_norm:
    updated = text_norm.replace(target_norm, rep_norm)
    with open('templates/category_books.html', 'w', encoding='utf-8') as f:
        f.write(updated.replace('\n', '\r\n'))
    print('Successfully updated category_books.html with enhanced live search')
else:
    print('Target not found in text_norm')
