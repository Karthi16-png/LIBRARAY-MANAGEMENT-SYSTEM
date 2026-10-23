const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PROFILE_DIR = path.join(__dirname, 'chrome_audit_profile_cat');
if (!fs.existsSync(PROFILE_DIR)) {
    fs.mkdirSync(PROFILE_DIR, { recursive: true });
}

const ROLES = [
    { u: 'admin', p: 'Admin@123', fileName: '05_admin_category_books.png' },
    { u: 'librarian', p: 'Lib@12345', fileName: '17_librarian_category_books.png' },
    { u: 'staff', p: 'Staff@123', fileName: '28_staff_category_books.png' },
    { u: 'student', p: 'Student@1', fileName: '38_student_category_books.png' }
];

async function run() {
    console.log('Recapturing category screenshots with /category/1 ...');
    const chromeProc = spawn(CHROME_PATH, [
        '--headless=new',
        '--remote-debugging-port=9225',
        `--user-data-dir=${PROFILE_DIR}`,
        '--window-size=1440,960',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check'
    ]);

    await new Promise(r => setTimeout(r, 1500));

    const verRes = await fetch('http://127.0.0.1:9225/json/version');
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

    for (const r of ROLES) {
        console.log(`Logging in as ${r.u}...`);
        await sendSession('Network.clearBrowserCookies');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
        await new Promise(res => setTimeout(res, 1200));

        await sendSession('Runtime.evaluate', {
            expression: `
                (function() {
                    const u = document.querySelector('input[name="username"]');
                    const p = document.querySelector('input[name="password"]');
                    if (u) u.value = '${r.u}';
                    if (p) p.value = '${r.p}';
                    const f = document.querySelector('form');
                    if (f) f.submit();
                })();
            `
        });
        await new Promise(res => setTimeout(res, 2000));

        console.log(`Navigating to /category/1 for ${r.u}...`);
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/category/1' });
        await new Promise(res => setTimeout(res, 2000));

        const shot = await sendSession('Page.captureScreenshot', {
            format: 'png',
            captureBeyondViewport: false
        });

        const filePath = path.join(SCREENSHOT_DIR, r.fileName);
        fs.writeFileSync(filePath, Buffer.from(shot.result.data, 'base64'));
        console.log(`Saved ${r.fileName} (${fs.statSync(filePath).size} bytes)`);
    }

    // Also update manifest.json so urlPath says /category/1
    const manifestPath = path.join(SCREENSHOT_DIR, 'manifest.json');
    if (fs.existsSync(manifestPath)) {
        const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
        for (const item of manifest) {
            if (item.urlPath === '/category_books/1') {
                item.urlPath = '/category/1';
            }
        }
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    }

    ws.close();
    chromeProc.kill();
    try {
        execSync(`taskkill /pid ${chromeProc.pid} /f /t 2>nul`);
    } catch (e) {}

    console.log('Recapture complete!');
}

run().catch(err => {
    console.error('Error during recapture:', err);
    process.exit(1);
});
