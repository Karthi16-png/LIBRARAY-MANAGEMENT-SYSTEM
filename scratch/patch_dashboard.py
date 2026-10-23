with open("templates/dashboard.html", "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for student table
old_student_table = """            <thead>
                <tr>
                    <th>Request Ref</th>
                    <th>Book Title</th>
                    <th>Requested On</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% if data.loan_requests %}
                    {% for req in data.loan_requests %}
                    <tr>
                        <td style="font-family: var(--font-mono); font-size: 0.8rem;">#REQ-{{ req.request_id }}</td>
                        <td class="book-title-cell">{{ req.book_title }}</td>
                        <td>{{ req.request_date.strftime('%b %d, %Y') if req.request_date else 'N/A' }}</td>
                        <td>
                            {% if req.status == 'Pending' %}
                                <span class="badge badge-warning">Awaiting Approval</span>
                            {% elif req.status == 'Approved' %}
                                <span class="badge badge-success">Approved & Issued</span>
                            {% else %}
                                <span class="badge badge-danger">Rejected</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="4" class="empty-state">No loan requests submitted. You can request books from the Catalog.</td>
                    </tr>
                {% endif %}
            </tbody>"""

new_student_table = """            <thead>
                <tr>
                    <th>Request Ref</th>
                    <th>Book Title</th>
                    <th>Requested On</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% if data.loan_requests %}
                    {% for req in data.loan_requests %}
                    <tr>
                        <td style="font-family: var(--font-mono); font-size: 0.8rem;">#REQ-{{ req.request_id }}</td>
                        <td class="book-title-cell">{{ req.book_title }}</td>
                        <td>{{ req.request_date.strftime('%b %d, %Y') if req.request_date else 'N/A' }}</td>
                        <td>
                            {% if req.status == 'Pending' %}
                                <span class="badge badge-warning">Awaiting Approval</span>
                            {% elif req.status == 'Awaiting Pickup' %}
                                <span class="badge badge-info" style="background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.35);">Approved &ndash; Ready for Pickup</span>
                            {% elif req.status == 'Approved' or req.status == 'Fulfilled' %}
                                <span class="badge badge-success">Approved &amp; Issued</span>
                            {% elif req.status == 'Rejected' %}
                                <span class="badge badge-danger">Rejected</span>
                            {% else %}
                                <span class="badge badge-secondary">{{ req.status }}</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if req.status == 'Rejected' and req.book_id %}
                                <form method="POST" action="{{ url_for('request_loan', book_id=req.book_id) }}" style="display: inline; margin: 0;">
                                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                    <input type="hidden" name="from_dashboard" value="1"/>
                                    <button type="submit" class="btn btn-sm" style="padding: 4px 10px; font-size: 0.76rem; font-weight: 700; background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.35); border-radius: var(--radius-sm); cursor: pointer;" onclick="return confirm('Submit new loan request for \\'{{ req.book_title|escape }}\\'?');">
                                        ↻ Request Again
                                    </button>
                                </form>
                            {% elif req.status == 'Awaiting Pickup' %}
                                <span style="font-size: 0.76rem; color: #60A5FA; font-weight: 600;">Collect at Desk</span>
                            {% elif req.status == 'Pending' %}
                                <span style="font-size: 0.76rem; color: var(--text-muted);">In Queue</span>
                            {% else %}
                                <span style="font-size: 0.76rem; color: var(--text-muted);">&mdash;</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="5" class="empty-state">No loan requests submitted. You can request books from the Catalog.</td>
                    </tr>
                {% endif %}
            </tbody>"""

# Normalize CRLF for matching
content_normalized = content.replace("\r\n", "\n")
old_normalized = old_student_table.replace("\r\n", "\n")
new_normalized = new_student_table.replace("\r\n", "\n")

count = content_normalized.count(old_normalized)
print(f"Matches found: {count}")

if count > 0:
    content_updated = content_normalized.replace(old_normalized, new_normalized)
    # Restore original line endings (CRLF)
    content_final = content_updated.replace("\n", "\r\n")
    with open("templates/dashboard.html", "w", encoding="utf-8") as f:
        f.write(content_final)
    print("Successfully patched dashboard.html")
else:
    print("No match found, check formatting.")
