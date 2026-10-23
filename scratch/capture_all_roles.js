const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PROFILE_DIR = path.join(__dirname, 'chrome_audit_profile');
if (!fs.existsSync(PROFILE_DIR)) {
    fs.mkdirSync(PROFILE_DIR, { recursive: true });
}

// Route configurations per role
const SECTIONS_CONFIG = [
    {
        roleName: 'Public',
        auth: null,
        pages: [
            { id: '01_public_login', name: 'Login Authentication Portal', path: '/login', waitMs: 1000 },
            { id: '02_public_register', name: 'Patron Registration Portal', path: '/register', waitMs: 1000 }
        ]
    },
    {
        roleName: 'Admin',
        auth: { u: 'admin', p: 'Admin@123' },
        pages: [
            { id: '03_admin_dashboard', name: 'Executive Dashboard & System Metrics', path: '/dashboard', waitMs: 2000 },
            { id: '04_admin_catalog', name: 'Central Book Catalog', path: '/books', waitMs: 1500 },
            { id: '05_admin_category_books', name: 'Category Curricula & Academic Graph View', path: '/category_books/1', waitMs: 1500 },
            { id: '06_admin_issue_loan', name: 'Circulation Desk - Direct Book Issuance', path: '/issue_loan', waitMs: 1500 },
            { id: '07_admin_loan_requests', name: 'Loan Requests Queue & Collection Desk', path: '/loan_requests', waitMs: 1500 },
            { id: '08_admin_manage_users', name: 'User Administration & Access Governance', path: '/manage_users', waitMs: 1500 },
            { id: '09_admin_learning_paths', name: 'Academic Learning Roadmaps & Hierarchy', path: '/learning_paths', waitMs: 1500 },
            { id: '10_admin_ai_recommendations', name: 'AI Collaborative Filtering Recommendations', path: '/recommendations', waitMs: 2000 },
            { id: '11_admin_graph_visualizer', name: 'Global Knowledge Graph Explorer', path: '/graph_visualizer', waitMs: 2500 },
            { id: '12_admin_book_bridge', name: 'Book Bridge - Shortest Path Separation', path: '/book_bridge', waitMs: 1500 },
            { id: '13_admin_centrality_analytics', name: 'Centrality Analytics & Influencer Lab', path: '/library_analytics', waitMs: 2000 },
            { id: '14_admin_change_password', name: 'Security Credentials & Password Management', path: '/change_password', waitMs: 1200 }
        ]
    },
    {
        roleName: 'Librarian',
        auth: { u: 'librarian', p: 'Lib@12345' },
        pages: [
            { id: '15_librarian_dashboard', name: 'Circulation Desk Dashboard', path: '/dashboard', waitMs: 2000 },
            { id: '16_librarian_catalog', name: 'Catalog & Inventory Management', path: '/books', waitMs: 1500 },
            { id: '17_librarian_category_books', name: 'Category Curricula & Prerequisites', path: '/category_books/1', waitMs: 1500 },
            { id: '18_librarian_issue_loan', name: 'Circulation Desk - Issue Book Loan', path: '/issue_loan', waitMs: 1500 },
            { id: '19_librarian_loan_requests', name: 'Loan Requests & Collection Handover', path: '/loan_requests', waitMs: 1500 },
            { id: '20_librarian_learning_paths', name: 'Learning Roadmaps & Course Hierarchy', path: '/learning_paths', waitMs: 1500 },
            { id: '21_librarian_ai_recommendations', name: 'Graph Recommendations & Circulation Trends', path: '/recommendations', waitMs: 2000 },
            { id: '22_librarian_graph_visualizer', name: 'System Circulation Knowledge Graph', path: '/graph_visualizer', waitMs: 2500 },
            { id: '23_librarian_book_bridge', name: 'Book Bridge Shortest Path Degrees', path: '/book_bridge', waitMs: 1500 },
            { id: '24_librarian_centrality_analytics', name: 'Centrality Analytics & Influencer Lab', path: '/library_analytics', waitMs: 2000 },
            { id: '25_librarian_change_password', name: 'Security Credentials & Password Management', path: '/change_password', waitMs: 1200 }
        ]
    },
    {
        roleName: 'Staff',
        auth: { u: 'staff', p: 'Staff@123' },
        pages: [
            { id: '26_staff_dashboard', name: 'Faculty & Staff Academic Dashboard', path: '/dashboard', waitMs: 2000 },
            { id: '27_staff_search_books', name: 'Catalog Search & Academic Materials', path: '/books', waitMs: 1500 },
            { id: '28_staff_category_books', name: 'Category Curricula & Academic Graph View', path: '/category_books/1', waitMs: 1500 },
            { id: '29_staff_learning_paths', name: 'Departmental Learning Roadmaps', path: '/learning_paths', waitMs: 1500 },
            { id: '30_staff_recommendations', name: 'Recommended For You (Research & Curriculum)', path: '/recommendations', waitMs: 2000 },
            { id: '31_staff_my_fines', name: 'Staff Fines & Dues Summary', path: '/my_fines', waitMs: 1500 },
            { id: '32_staff_graph_visualizer', name: 'Live Academic Knowledge Graph', path: '/graph_visualizer', waitMs: 2500 },
            { id: '33_staff_book_bridge', name: 'Book Bridge - Shortest Path Traversal', path: '/book_bridge', waitMs: 1500 },
            { id: '34_staff_centrality_analytics', name: 'Centrality Analytics & Influencer Lab', path: '/library_analytics', waitMs: 2000 },
            { id: '35_staff_change_password', name: 'Security Credentials & Password Management', path: '/change_password', waitMs: 1200 }
        ]
    },
    {
        roleName: 'Student',
        auth: { u: 'student', p: 'Student@1' },
        pages: [
            { id: '36_student_dashboard', name: 'Student Academic Dashboard & Borrowings', path: '/dashboard', waitMs: 2000 },
            { id: '37_student_search_books', name: 'Book Catalog & Reservation Desk', path: '/books', waitMs: 1500 },
            { id: '38_student_category_books', name: 'Course Prerequisites & Curricula Catalog', path: '/category_books/1', waitMs: 1500 },
            { id: '39_student_learning_paths', name: 'Student Learning Roadmaps & Study Tracks', path: '/learning_paths', waitMs: 1500 },
            { id: '40_student_recommendations', name: 'AI Recommended Books & Study Partners', path: '/recommendations', waitMs: 2000 },
            { id: '41_student_my_fines', name: 'Personal Overdue Fines & Payment History', path: '/my_fines', waitMs: 1500 },
            { id: '42_student_graph_visualizer', name: 'Personal Learning Graph Visualizer', path: '/graph_visualizer', waitMs: 2500 },
            { id: '43_student_book_bridge', name: 'Book Bridge Degrees of Separation', path: '/book_bridge', waitMs: 1500 },
            { id: '44_student_change_password', name: 'Security Credentials & Password Management', path: '/change_password', waitMs: 1200 }
        ]
    }
];

async function run() {
    console.log('=== STARTING MULTI-ROLE SCREENSHOT CAPTURE ===');
    console.log(`Target Screenshot Directory: ${SCREENSHOT_DIR}`);

    const chromeProc = spawn(CHROME_PATH, [
        '--headless=new',
        '--remote-debugging-port=9224',
        `--user-data-dir=${PROFILE_DIR}`,
        '--window-size=1440,960',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check'
    ]);

    await new Promise(r => setTimeout(r, 1500));

    const verRes = await fetch('http://127.0.0.1:9224/json/version');
    const verJson = await verRes.json();
    const ws = new WebSocket(verJson.webSocketDebuggerUrl);

    let idCounter = 1;
    const pending = new Map();
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.id && pending.has(data.id)) {
            pending.get(data.id)(data);
            pending.delete(data.id);
        }
    };

    function send(method, params = {}) {
        return new Promise(resolve => {
            const id = idCounter++;
            pending.set(id, resolve);
            ws.send(JSON.stringify({ id, method, params }));
        });
    }

    await new Promise(r => ws.onopen = r);

    const target = await send('Target.createTarget', { url: 'about:blank' });
    const targetId = target.result.targetId;
    const session = await send('Target.attachToTarget', { targetId, flatten: true });
    const sessionId = session.result.sessionId;

    function sendSession(method, params = {}) {
        return new Promise(resolve => {
            const id = idCounter++;
            pending.set(id, resolve);
            ws.send(JSON.stringify({ id, sessionId, method, params }));
        });
    }

    await sendSession('Page.enable');
    await sendSession('Network.enable');

    const manifest = [];

    for (const group of SECTIONS_CONFIG) {
        console.log(`\n--------------------------------------------------`);
        console.log(`Processing Role / Group: [${group.roleName}]`);

        // If authentication is needed, clear cookies, visit login, and submit
        if (group.auth) {
            console.log(`Logging in as ${group.auth.u}...`);
            await sendSession('Network.clearBrowserCookies');
            await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
            await new Promise(r => setTimeout(r, 1200));

            await sendSession('Runtime.evaluate', {
                expression: `
                    (function() {
                        const u = document.querySelector('input[name="username"]');
                        const p = document.querySelector('input[name="password"]');
                        if (u) u.value = '${group.auth.u}';
                        if (p) p.value = '${group.auth.p}';
                        const f = document.querySelector('form');
                        if (f) f.submit();
                    })();
                `
            });
            await new Promise(r => setTimeout(r, 2000));
        } else {
            await sendSession('Network.clearBrowserCookies');
        }

        for (const page of group.pages) {
            const url = `http://127.0.0.1:5000${page.path}`;
            console.log(`  -> Navigating to ${page.id} (${url})...`);
            await sendSession('Page.navigate', { url });
            await new Promise(r => setTimeout(r, page.waitMs));

            // Capture screenshot
            const shot = await sendSession('Page.captureScreenshot', {
                format: 'png',
                captureBeyondViewport: false
            });

            const fileName = `${page.id}.png`;
            const filePath = path.join(SCREENSHOT_DIR, fileName);
            fs.writeFileSync(filePath, Buffer.from(shot.result.data, 'base64'));
            console.log(`     Captured: ${fileName} (${fs.statSync(filePath).size} bytes)`);

            manifest.push({
                id: page.id,
                fileName,
                filePath,
                role: group.roleName,
                name: page.name,
                urlPath: page.path
            });
        }
    }

    // Save manifest for PDF generator
    const manifestPath = path.join(SCREENSHOT_DIR, 'manifest.json');
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    console.log(`\nManifest written to: ${manifestPath}`);

    ws.close();
    chromeProc.kill();
    try {
        execSync(`taskkill /pid ${chromeProc.pid} /f /t 2>nul`);
    } catch (e) {}

    console.log('=== SCREENSHOT CAPTURE COMPLETE ===');
}

run().catch(err => {
    console.error('Fatal error during capture:', err);
    process.exit(1);
});
