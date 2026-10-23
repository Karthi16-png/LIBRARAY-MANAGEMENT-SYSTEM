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

        // 1. Login as Student
        console.log('Navigating to login as student...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
        await new Promise(r => setTimeout(r, 1000));

        await sendSession('Runtime.evaluate', {
            expression: `
                document.querySelector('input[name="username"]').value = 'student';
                document.querySelector('input[name="password"]').value = 'Student@123';
                document.querySelector('button[type="submit"]').click();
            `
        });
        await new Promise(r => setTimeout(r, 1500));

        // 2. Navigate to /recommendations
        console.log('Navigating to /recommendations as student...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/recommendations' });
        await new Promise(r => setTimeout(r, 1200));

        const snapStudent = await sendSession('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(__dirname, 'student_recommendations_clean.png'), Buffer.from(snapStudent.result.data, 'base64'));
        console.log('Saved student_recommendations_clean.png');

        // 3. Login as Admin
        console.log('Logging in as admin...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/logout' });
        await new Promise(r => setTimeout(r, 600));

        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
        await new Promise(r => setTimeout(r, 800));

        await sendSession('Runtime.evaluate', {
            expression: `
                document.querySelector('input[name="username"]').value = 'admin';
                document.querySelector('input[name="password"]').value = 'Admin@123';
                document.querySelector('button[type="submit"]').click();
            `
        });
        await new Promise(r => setTimeout(r, 1500));

        // 4. Navigate to /recommendations as Admin
        console.log('Navigating to /recommendations as admin...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/recommendations' });
        await new Promise(r => setTimeout(r, 1200));

        const snapAdmin = await sendSession('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(__dirname, 'admin_recommendations_clean.png'), Buffer.from(snapAdmin.result.data, 'base64'));
        console.log('Saved admin_recommendations_clean.png');

        ws.close();
        chromeProc.kill();
        console.log('Done capturing recommendations screenshots.');
    } catch (err) {
        console.error('Error during capture:', err);
        chromeProc.kill();
    }
}

capture();
