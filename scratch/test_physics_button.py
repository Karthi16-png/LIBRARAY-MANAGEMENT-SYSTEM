import urllib.request
import urllib.parse
import http.cookiejar
import re

BASE_URL = "http://127.0.0.1:5000"

def test_physics_button_template():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    resp = opener.open(f"{BASE_URL}/login")
    login_html = resp.read().decode("utf-8")
    m = re.search(r'name="csrf_token" value="([^"]+)"', login_html)
    csrf = m.group(1) if m else ''

    login_data = urllib.parse.urlencode({
        "username": "admin",
        "password": "Admin@123",
        "csrf_token": csrf
    }).encode("utf-8")
    login_req = urllib.request.Request(f"{BASE_URL}/login", data=login_data)
    with opener.open(login_req) as resp:
        assert resp.status == 200, "Admin login failed"

    gv_req = urllib.request.Request(f"{BASE_URL}/graph_visualizer")
    with opener.open(gv_req) as resp:
        assert resp.status == 200, "Failed to load /graph_visualizer"
        html = resp.read().decode("utf-8")

    # 1. Verify button exists
    assert 'id="physicsToggleBtn"' in html, "physicsToggleBtn not found in HTML"

    # 2. Verify on initial load, physicsToggleBtn starts with Pause icon and active class
    btn_match = re.search(r'<button[^>]*id="physicsToggleBtn"[^>]*>(.*?)</button>', html, re.DOTALL)
    assert btn_match, "Could not match physicsToggleBtn in HTML"
    btn_html = btn_match.group(1)
    
    assert 'rect x="6"' in btn_html, f"Expected Pause icon rects in initial HTML, got: {btn_html}"
    assert 'rect x="14"' in btn_html, f"Expected Pause icon rects in initial HTML, got: {btn_html}"
    assert 'polygon' not in btn_html, "Play icon polygon should NOT be present in initial active HTML"

    # 3. Verify title and aria-label
    assert 'title="Pause Physics Simulation (Freeze Layout)"' in html, "Pause physics tooltip missing"
    assert 'aria-label="Pause Physics Simulation"' in html, "Aria-label missing"

    # 4. Verify updatePhysicsBtnUI function exists
    assert 'function updatePhysicsBtnUI' in html, "updatePhysicsBtnUI function missing"
    assert 'PLAY_ICON_SVG' in html, "PLAY_ICON_SVG missing"
    assert 'PAUSE_ICON_SVG' in html, "PAUSE_ICON_SVG missing"
    assert 'reStabilizeBtn' in html, "reStabilizeBtn id missing"

    # 5. Verify reStabilize checks isPhysicsActive
    assert 'if (!isPhysicsActive)' in html, "reStabilize must check and re-enable isPhysicsActive"

    # 6. Verify 0 nodes hiding logic
    assert 'btn.style.display = "none"' in html, "Hidden state for 0 nodes missing"

    print("=== [PASS] All static HTML and JS checks for physics button succeeded! ===")

if __name__ == "__main__":
    test_physics_button_template()
