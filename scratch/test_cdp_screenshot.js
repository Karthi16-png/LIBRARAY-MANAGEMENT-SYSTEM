const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function testCapture() {
    const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const profileDir = path.join(__dirname, 'chrome_test_profile');
    if (!fs.existsSync(profileDir)) fs.mkdirSync(profileDir, { recursive: true });

    console.log('Launching headless Chrome...');
    const chromeProc = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9222',
        `--user-data-dir=${profileDir}`,
        '--window-size=1440,960',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check'
    ]);

    // Wait 1.5s for Chrome to bind port
    await new Promise(r => setTimeout(r, 1500));

    try {
        const verRes = await fetch('http://127.0.0.1:9222/json/version');
        const verJson = await verRes.json();
        console.log('CDP connected:', verJson.webSocketDebuggerUrl);

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

        // Create target
        const target = await send('Target.createTarget', { url: 'about:blank' });
        const targetId = target.result.targetId;

        // Connect to target session
        const session = await send('Target.attachToTarget', { targetId, flatten: true });
        const sessionId = session.result.sessionId;

        function sendSession(method, params = {}) {
            return new Promise((resolve) => {
                const id = idCounter++;
                pending.set(id, resolve);
                ws.send(JSON.stringify({ id, sessionId, method, params }));
            });
        }

        await sendSession('Page.enable');
        await sendSession('Network.enable');

        console.log('Navigating to http://127.0.0.1:5000/login ...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
        await new Promise(r => setTimeout(r, 1500));

        console.log('Capturing screenshot...');
        const shot = await sendSession('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
        const outPath = path.join(__dirname, 'test_login.png');
        fs.writeFileSync(outPath, Buffer.from(shot.result.data, 'base64'));
        console.log('Screenshot saved to:', outPath);

        ws.close();
    } catch (e) {
        console.error('Error during test capture:', e);
    } finally {
        chromeProc.kill('SIGKILL');
    }
}

testCapture().then(() => process.exit(0));
