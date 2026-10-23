with open("templates/dashboard.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Approved &amp; Issued badge to Collected &amp; Issued
old_badge = '<span class="badge badge-success">Approved &amp; Issued</span>'
new_badge = '<span class="badge badge-success">✓ Collected &amp; Issued</span>'
assert old_badge in content, "old_badge not found"
content = content.replace(old_badge, new_badge)

# 2. Update Collect at Desk to include Copy ID if present
old_desk = '<span style="font-size: 0.76rem; color: #60A5FA; font-weight: 600;">Collect at Desk</span>'
new_desk = '<span style="font-size: 0.76rem; color: #60A5FA; font-weight: 600;">{% if req.copy_id %}Copy #{{ req.copy_id }} &bull; {% endif %}Collect at Desk</span>'
assert old_desk in content, "old_desk not found"
content = content.replace(old_desk, new_desk)

with open("templates/dashboard.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully patched templates/dashboard.html")
