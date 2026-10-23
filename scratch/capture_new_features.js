const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function capture() {
    const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const profileDir = path.join(__dirname, 'chrome_audit_profile');
    if (!fs.existsSync(profileDir)) fs.mkdirSync(profileDir, { recursive: true });

    const chromeProc = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9222',
        `--user-data-dir=${profileDir}`,
        '--window-size=1440,960',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check'
    ]);

    await new Promise(r => setTimeout(r, 1500));

    try {
        const verRes = await fetch('http://127.0.0.1:9222/json/version');
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
            return new Promise((resolve) => {
                const id = idCounter++;
                pending.set(id, resolve);
                ws.send(JSON.stringify({ id, method, params }));
            });
        }

        await new Promise(r => ws.onopen = r);

        const target = await send('Target.createTarget', { url: 'about:blank' });
        const session = await send('Target.attachToTarget', { targetId: target.result.targetId, flatten: true });
        const sessionId = session.result.sessionId;

        function sendSession(method, params = {}) {
            return new Promise((resolve) => {
                const id = idCounter++;
                pending.set(id, resolve);
                ws.send(JSON.stringify({ id, sessionId, method, params }));
            });
        }

        await sendSession('Page.enable');
        await sendSession('Runtime.enable');
        await sendSession('Emulation.setDeviceMetricsOverride', {
            width: 1440,
            height: 960,
            deviceScaleFactor: 1,
            mobile: false
        });

        // 1. Login as Admin
        console.log('Navigating to login...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
        await new Promise(r => setTimeout(r, 1000));

        await sendSession('Runtime.evaluate', {
            expression: `
                document.querySelector('input[name="username"]').value = 'admin';
                document.querySelector('input[name="password"]').value = 'Admin@123';
                document.querySelector('button[type="submit"]').click();
            `
        });
        await new Promise(r => setTimeout(r, 1500));

        // 2. Navigate to /manage_users
        console.log('Navigating to /manage_users...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/manage_users' });
        await new Promise(r => setTimeout(r, 1000));

        const snapUsers = await sendSession('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(__dirname, 'admin_manage_users_protected.png'), Buffer.from(snapUsers.result.data, 'base64'));
        console.log('Saved admin_manage_users_protected.png');

        // 3. Navigate to /issue_loan
        console.log('Navigating to /issue_loan...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/issue_loan' });
        await new Promise(r => setTimeout(r, 1000));

        // Type "mar" into patron search to trigger dropdown
        await sendSession('Runtime.evaluate', {
            expression: `
                const input = document.getElementById('patron_quick_search');
                input.focus();
                input.value = 'mar';
                input.dispatchEvent(new Event('input', { bubbles: true }));
            `
        });
        await new Promise(r => setTimeout(r, 600));

        const snapDropdown = await sendSession('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(__dirname, 'issue_loan_patron_dropdown.png'), Buffer.from(snapDropdown.result.data, 'base64'));
        console.log('Saved issue_loan_patron_dropdown.png');

        // Close Chrome
        ws.close();
        chromeProc.kill();
        console.log('Done capturing verification screenshots.');
    } catch (err) {
        console.error('Error during capture:', err);
        chromeProc.kill();
    }
}

capture();
