const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function testGraphPhysics() {
    const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const profileDir = path.join(__dirname, 'chrome_graph_physics_profile');
    if (!fs.existsSync(profileDir)) fs.mkdirSync(profileDir, { recursive: true });

    console.log('Launching headless Chrome...');
    const chromeProc = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9223',
        `--user-data-dir=${profileDir}`,
        '--window-size=1440,960',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check'
    ]);

    await new Promise(r => setTimeout(r, 1500));

    try {
        const verRes = await fetch('http://127.0.0.1:9223/json/version');
        const verJson = await verRes.json();
        console.log('CDP connected to:', verJson.webSocketDebuggerUrl);

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
        const targetId = target.result.targetId;

        const session = await send('Target.attachToTarget', { targetId, flatten: true });
        const sessionId = session.result.sessionId;

        function sendSession(method, params = {}) {
            return new Promise((resolve) => {
                const id = idCounter++;
                pending.set(id, resolve);
                ws.send(JSON.stringify({ id, sessionId, method, params }));
            });
        }

        async function evalInPage(expr) {
            const res = await sendSession('Runtime.evaluate', {
                expression: expr,
                returnByValue: true
            });
            if (res.result && res.result.result) {
                return res.result.result.value;
            }
            return null;
        }

        await sendSession('Page.enable');
        await sendSession('Runtime.enable');
        await sendSession('Network.enable');

        // 1. Navigate to login
        console.log('Navigating to login...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/login' });
        await new Promise(r => setTimeout(r, 1500));

        // 2. Perform login
        await evalInPage(`
            document.querySelector('input[name="username"]').value = 'admin';
            document.querySelector('input[name="password"]').value = 'Admin@123';
            document.querySelector('form').submit();
        `);
        await new Promise(r => setTimeout(r, 2000));

        // 3. Navigate to graph_visualizer
        console.log('Navigating to /graph_visualizer ...');
        await sendSession('Page.navigate', { url: 'http://127.0.0.1:5000/graph_visualizer' });
        await new Promise(r => setTimeout(r, 3500)); // wait for Vis.js to load nodes

        // 4. Test initial state
        const initialVal = await evalInPage(`
            (() => {
                const btn = document.getElementById("physicsToggleBtn");
                return {
                    isPhysicsActive: typeof isPhysicsActive !== 'undefined' ? isPhysicsActive : null,
                    hasActiveCls: btn ? btn.classList.contains("active") : false,
                    innerHTML: btn ? btn.innerHTML : "",
                    title: btn ? btn.getAttribute("title") : "",
                    display: btn ? window.getComputedStyle(btn).display : ""
                };
            })()
        `);
        console.log('Initial State:', JSON.stringify(initialVal, null, 2));

        if (!initialVal.isPhysicsActive) {
            throw new Error("Expected isPhysicsActive to be true on load");
        }
        if (!initialVal.innerHTML.includes("<rect")) {
            throw new Error("Expected Pause icon (<rect>) on active state");
        }
        if (initialVal.innerHTML.includes("<polygon")) {
            throw new Error("Play icon (<polygon>) should NOT be shown when physics is active");
        }
        console.log('PASS: Initial state correctly displays PAUSE icon while physics is actively running.');

        // Take screenshot of toolbar showing Pause icon
        const shot1 = await sendSession('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(__dirname, 'graph_physics_active.png'), Buffer.from(shot1.result.data, 'base64'));

        // 5. Click the button to toggle physics (pause / freeze)
        console.log('Clicking #physicsToggleBtn to pause physics...');
        await evalInPage(`document.getElementById("physicsToggleBtn").click();`);
        await new Promise(r => setTimeout(r, 500));

        const pausedVal = await evalInPage(`
            (() => {
                const btn = document.getElementById("physicsToggleBtn");
                return {
                    isPhysicsActive: isPhysicsActive,
                    hasActiveCls: btn.classList.contains("active"),
                    innerHTML: btn.innerHTML,
                    title: btn.getAttribute("title"),
                    display: window.getComputedStyle(btn).display
                };
            })()
        `);
        console.log('Paused State:', JSON.stringify(pausedVal, null, 2));

        if (pausedVal.isPhysicsActive) {
            throw new Error("Expected isPhysicsActive to be false after toggle");
        }
        if (!pausedVal.innerHTML.includes("<polygon")) {
            throw new Error("Expected Play icon (<polygon>) on paused state");
        }
        if (pausedVal.innerHTML.includes("<rect")) {
            throw new Error("Pause icon (<rect>) should NOT be shown when physics is paused");
        }
        console.log('PASS: Clicking correctly froze physics and displayed PLAY icon to allow unfreezing.');

        // Take screenshot of toolbar showing Play icon
        const shot2 = await sendSession('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(__dirname, 'graph_physics_paused.png'), Buffer.from(shot2.result.data, 'base64'));

        // 6. Test reStabilize while physics was paused
        console.log('Testing reStabilize while paused...');
        await evalInPage(`reStabilize();`);
        await new Promise(r => setTimeout(r, 500));

        const restabilizedVal = await evalInPage(`
            (() => {
                const btn = document.getElementById("physicsToggleBtn");
                return {
                    isPhysicsActive: isPhysicsActive,
                    hasActiveCls: btn.classList.contains("active"),
                    innerHTML: btn.innerHTML,
                    title: btn.getAttribute("title")
                };
            })()
        `);
        console.log('Restabilized State:', JSON.stringify(restabilizedVal, null, 2));

        if (!restabilizedVal.isPhysicsActive) {
            throw new Error("reStabilize should have reactivated isPhysicsActive");
        }
        if (!restabilizedVal.innerHTML.includes("<rect")) {
            throw new Error("Expected Pause icon (<rect>) after reStabilize");
        }
        console.log('PASS: reStabilize correctly reactivated physics and updated button to PAUSE icon.');

        // 7. Test 0 nodes state: turn off all filters
        console.log('Testing 0 nodes state (turning off all group filters)...');
        await evalInPage(`
            activeGroups.clear();
            renderNetwork(allNodes, allEdges);
        `);
        await new Promise(r => setTimeout(r, 500));

        const emptyNodesVal = await evalInPage(`
            (() => {
                const btn = document.getElementById("physicsToggleBtn");
                const reBtn = document.getElementById("reStabilizeBtn");
                return {
                    btnDisplay: window.getComputedStyle(btn).display,
                    reBtnDisplay: window.getComputedStyle(reBtn).display,
                    nodesCount: document.getElementById("statNodesCount").textContent
                };
            })()
        `);
        console.log('Empty Nodes State:', JSON.stringify(emptyNodesVal, null, 2));

        if (emptyNodesVal.btnDisplay !== 'none') {
            throw new Error("Expected physics button to be hidden (display: none) when 0 nodes are visible");
        }
        console.log('PASS: Play/pause button is successfully hidden/removed when there are 0 nodes (not useful).');

        // 8. Turn filters back on
        console.log('Restoring filters...');
        await evalInPage(`
            activeGroups = new Set(["User", "Book", "Author", "Category", "Publisher", "Copy", "Loan", "Fine", "LoanRequest", "CurrentUser", "SharedBook", "RecommendedBook", "PeerUser"]);
            renderNetwork(allNodes, allEdges);
        `);
        await new Promise(r => setTimeout(r, 500));

        const restoredVal = await evalInPage(`
            (() => {
                const btn = document.getElementById("physicsToggleBtn");
                return {
                    btnDisplay: window.getComputedStyle(btn).display,
                    nodesCount: document.getElementById("statNodesCount").textContent
                };
            })()
        `);
        console.log('Restored State:', JSON.stringify(restoredVal, null, 2));

        if (restoredVal.btnDisplay === 'none') {
            throw new Error("Expected physics button to become visible again when nodes are present");
        }
        console.log('PASS: Button reappears when nodes are visible.');

        console.log('\n=============================================');
        console.log('ALL PLAY/PAUSE PHYSICS BUTTON CHECKS PASSED 100%!');
        console.log('=============================================');

        ws.close();
    } catch (e) {
        console.error('Test Failed:', e);
        process.exitCode = 1;
    } finally {
        chromeProc.kill('SIGKILL');
    }
}

testGraphPhysics().then(() => {
    if (process.exitCode === 1) process.exit(1);
    process.exit(0);
});
