import http.server
import socketserver
import urllib.parse
import threading
from arduino.app_utils import *

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class RobotControlHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress repetitive HTTP request logs to keep terminal responsive
        pass

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        command = None
        if path == '/forward': command = 'forward'
        elif path == '/reverse': command = 'reverse'
        elif path == '/left': command = 'left'
        elif path == '/right': command = 'right'
        elif path == '/forward_left': command = 'forward_left'
        elif path == '/forward_right': command = 'forward_right'
        elif path == '/reverse_left': command = 'reverse_left'
        elif path == '/reverse_right': command = 'reverse_right'
        elif path == '/stop': command = 'stop'
        elif path == '/mode': command = 'mode'
        elif path == '/suction': command = 'suction'
        elif path == '/test_shake': command = 'test_shake'
        elif path == '/test_arc': command = 'test_arc'
            
        if command:
            try:
                Bridge.call(command)
            except Exception as e:
                print(f"Failed to call {command}: {e}")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return
            
        # Serve the HTML page for root path
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <title>Cleo // Terminal</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            text-align: center;
            background: #0a0a0a;
            color: #33ff33;
            min-height: 100vh;
            padding: 15px;
            padding-bottom: 210px;
        }
        h1 {
            font-size: 1.4em;
            margin: 8px 0 4px;
            color: #33ff33;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        .subtitle {
            font-size: 0.7em;
            color: #1a7a1a;
            letter-spacing: 2px;
            margin-bottom: 18px;
        }
        .status {
            font-size: 0.75em;
            color: #1a7a1a;
            margin-bottom: 15px;
        }
        .status .dot {
            display: inline-block;
            width: 7px; height: 7px;
            border-radius: 50%;
            background: #33ff33;
            margin-right: 6px;
            box-shadow: 0 0 6px #33ff33;
            animation: blink 2s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* Toggle Switches */
        .toggle-row {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .toggle-card {
            background: #0f0f0f;
            border: 1px solid #1a3a1a;
            border-radius: 6px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            user-select: none;
            -webkit-user-select: none;
            touch-action: manipulation;
        }
        .toggle-card:active { border-color: #33ff33; }
        .toggle-label {
            font-size: 11px;
            font-weight: 600;
            color: #33ff33;
            text-align: left;
            min-width: 70px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .toggle-label .state {
            display: block;
            font-size: 10px;
            font-weight: 400;
            margin-top: 3px;
        }
        .toggle-label .state.on { color: #33ff33; }
        .toggle-label .state.off { color: #444; }
        .sw-track {
            position: relative;
            width: 44px;
            height: 22px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 22px;
            transition: all 0.25s;
        }
        .sw-track.on {
            background: #0a2a0a;
            border-color: #33ff33;
            box-shadow: 0 0 8px rgba(51, 255, 51, 0.2);
        }
        .sw-knob {
            position: absolute;
            width: 16px; height: 16px;
            top: 2px; left: 2px;
            background: #444;
            border-radius: 50%;
            transition: all 0.25s;
        }
        .sw-track.on .sw-knob {
            left: 24px;
            background: #33ff33;
            box-shadow: 0 0 6px #33ff33;
        }

        /* Buttons */
        .btn {
            font-family: 'JetBrains Mono', monospace;
            padding: 10px 16px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 4px;
            border: 1px solid #1a3a1a;
            color: #33ff33;
            background: #0f0f0f;
            transition: all 0.1s;
            touch-action: manipulation;
            user-select: none;
            -webkit-user-select: none;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:active {
            background: #1a3a1a;
            border-color: #33ff33;
            box-shadow: 0 0 10px rgba(51, 255, 51, 0.2);
        }
        .btn-stop {
            width: 80px;
            padding: 8px 0;
            font-size: 11px;
            font-weight: 700;
            border-color: #3a1a1a;
            color: #ff3333;
            border-radius: 20px;
        }
        .btn-stop:active {
            background: #2a0a0a;
            border-color: #ff3333;
            box-shadow: 0 0 10px rgba(255, 51, 51, 0.3);
        }
        .btn-anim {
            border-color: #3a3a1a;
            color: #aaaa33;
        }
        .btn-anim:active {
            background: #1a1a0a;
            border-color: #aaaa33;
            box-shadow: 0 0 10px rgba(170, 170, 51, 0.2);
        }

        /* Virtual Joystick */
        .joystick-section {
            margin: 10px auto 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            user-select: none;
            -webkit-user-select: none;
            touch-action: none;
        }
        .joystick-wrapper {
            position: relative;
            width: 220px;
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            touch-action: none;
        }
        .joystick-base {
            position: absolute;
            width: 210px;
            height: 210px;
            border-radius: 50%;
            background: radial-gradient(circle, #0e1a0e 0%, #080d08 70%, #040804 100%);
            border: 2px solid #1a4a1a;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(51, 255, 51, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            touch-action: none;
            cursor: grab;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .joystick-base:active {
            cursor: grabbing;
        }
        .joystick-base.active {
            border-color: #33ff33;
            box-shadow: 0 0 25px rgba(51, 255, 51, 0.25), inset 0 0 20px rgba(51, 255, 51, 0.15);
        }
        .joystick-crosshair-h, .joystick-crosshair-v {
            position: absolute;
            background: #153515;
            pointer-events: none;
        }
        .joystick-crosshair-h {
            width: 100%;
            height: 1px;
            top: 50%;
            left: 0;
        }
        .joystick-crosshair-v {
            width: 1px;
            height: 100%;
            top: 0;
            left: 50%;
        }
        .joystick-ring {
            position: absolute;
            width: 110px;
            height: 110px;
            border-radius: 50%;
            border: 1px dashed #1a4a1a;
            pointer-events: none;
        }
        .dir-indicator {
            position: absolute;
            font-size: 13px;
            color: #1a4a1a;
            transition: color 0.12s, text-shadow 0.12s, transform 0.12s;
            pointer-events: none;
            font-weight: 700;
        }
        .dir-indicator.up { top: 8px; left: 50%; transform: translateX(-50%); }
        .dir-indicator.upright { top: 20px; right: 24px; }
        .dir-indicator.right { top: 50%; right: 8px; transform: translateY(-50%); }
        .dir-indicator.downright { bottom: 20px; right: 24px; }
        .dir-indicator.down { bottom: 8px; left: 50%; transform: translateX(-50%); }
        .dir-indicator.downleft { bottom: 20px; left: 24px; }
        .dir-indicator.left { top: 50%; left: 8px; transform: translateY(-50%); }
        .dir-indicator.upleft { top: 20px; left: 24px; }

        .dir-indicator.lit {
            color: #33ff33;
            text-shadow: 0 0 10px #33ff33, 0 0 20px #33ff33;
            transform: scale(1.4);
        }
        .dir-indicator.up.lit, .dir-indicator.down.lit {
            transform: translateX(-50%) scale(1.4);
        }
        .dir-indicator.left.lit, .dir-indicator.right.lit {
            transform: translateY(-50%) scale(1.4);
        }
        .joystick-knob {
            position: absolute;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: radial-gradient(circle at 35% 35%, #1f3f1f, #0c1a0c 60%, #050a05 100%);
            border: 2px solid #2d6b2d;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.9), 0 0 10px rgba(51, 255, 51, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
            transform: translate3d(0, 0, 0);
            will-change: transform;
            transition: transform 0.05s ease-out;
        }
        .joystick-knob.spring {
            transition: transform 0.22s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .joystick-knob-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #33ff33;
            box-shadow: 0 0 8px #33ff33;
        }
        .vector-hud {
            margin-top: 8px;
            font-size: 11px;
            color: #1a7a1a;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .vector-hud .val {
            color: #33ff33;
            font-weight: 700;
        }
        .btn-stop-bar {
            margin-top: 8px;
            display: flex;
            justify-content: center;
        }

        .section {
            margin-top: 16px;
            padding-top: 14px;
            border-top: 1px solid #1a1a1a;
        }
        .section h3 {
            color: #1a7a1a;
            font-size: 0.75em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .anim-bar {
            display: flex;
            gap: 8px;
            justify-content: center;
            flex-wrap: wrap;
        }

        /* Command Log */
        .log-panel {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            background: #050505;
            border-top: 1px solid #1a3a1a;
            max-height: 200px;
            transition: max-height 0.3s;
        }
        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 7px 15px;
            background: #0a0f0a;
            cursor: pointer;
            user-select: none;
            border-bottom: 1px solid #0f1f0f;
        }
        .log-header h4 {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: #1a7a1a;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .log-header .tog {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: #33ff33;
            font-weight: 600;
        }
        .log-body {
            overflow-y: auto;
            max-height: 158px;
            padding: 4px 0;
        }
        .log-entry {
            font-size: 11px;
            padding: 2px 15px;
            text-align: left;
            color: #1a7a1a;
            border-bottom: 1px solid #0a0f0a;
        }
        .log-entry .t { color: #333; margin-right: 6px; }
        .log-entry .c { color: #33ff33; }
        .log-entry .ok { color: #1a7a1a; }
        .log-entry .er { color: #ff3333; }
        .log-entry .ms { color: #333; margin-left: 4px; }
        .log-panel.collapsed .log-body { display: none; }
        .log-panel.collapsed { max-height: 30px; }
    </style>
</head>
<body>
    <h1>&gt; Cleo</h1>
    <div class="subtitle">robot control terminal</div>
    <div class="status"><span class="dot"></span> LINK ACTIVE</div>

    <div class="toggle-row">
        <div class="toggle-card" id="mode-card">
            <div class="toggle-label">
                Auto
                <span class="state on" id="mode-state">ON</span>
            </div>
            <div class="sw-track on" id="mode-track">
                <div class="sw-knob"></div>
            </div>
        </div>
        <div class="toggle-card" id="suction-card">
            <div class="toggle-label">
                Suction
                <span class="state on" id="suction-state">ON</span>
            </div>
            <div class="sw-track on" id="suction-track">
                <div class="sw-knob"></div>
            </div>
        </div>
    </div>

    <!-- Virtual Joystick Control -->
    <div class="joystick-section">
        <div class="joystick-wrapper">
            <div class="joystick-base" id="joyBase">
                <div class="joystick-crosshair-h"></div>
                <div class="joystick-crosshair-v"></div>
                <div class="joystick-ring"></div>
                <div class="dir-indicator up" id="indUp">&#9650;</div>
                <div class="dir-indicator upright" id="indUpRight">&#8599;</div>
                <div class="dir-indicator right" id="indRight">&#9654;</div>
                <div class="dir-indicator downright" id="indDownRight">&#8600;</div>
                <div class="dir-indicator down" id="indDown">&#9660;</div>
                <div class="dir-indicator downleft" id="indDownLeft">&#8601;</div>
                <div class="dir-indicator left" id="indLeft">&#9664;</div>
                <div class="dir-indicator upleft" id="indUpLeft">&#8598;</div>
                <div class="joystick-knob" id="joyKnob">
                    <div class="joystick-knob-dot"></div>
                </div>
            </div>
        </div>
        <div class="vector-hud">STATUS: <span class="val" id="hudVal">STOP</span></div>
        <div class="btn-stop-bar">
            <button class="btn btn-stop" onclick="resetJoystick(); send('stop');">HALT</button>
        </div>
    </div>

    <div class="section">
        <h3>// animations</h3>
        <div class="anim-bar">
            <button class="btn btn-anim" onclick="send('test_arc')">Inv. Arc</button>
            <button class="btn btn-anim" onclick="send('test_shake')">Frust. Shake</button>
        </div>
    </div>

    <div class="log-panel" id="logPanel">
        <div class="log-header" onclick="toggleLog()">
            <h4>// stdout</h4>
            <span class="tog" id="logToggle">[_]</span>
        </div>
        <div class="log-body" id="logBody"></div>
    </div>

    <script>
        let modeOn = true;
        let suctionOn = true;
        const logBody = document.getElementById('logBody');

        function ts() {
            const d = new Date();
            const p = n => String(n).padStart(2,'0');
            return p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds())+'.'+String(d.getMilliseconds()).padStart(3,'0');
        }

        let activeRequest = false;
        let pendingCommand = null;
        let lastLoggedCmd = '';

        function log(cmd, ok, ms) {
            if (cmd === lastLoggedCmd && cmd !== 'stop') return;
            lastLoggedCmd = cmd;
            const e = document.createElement('div');
            e.className = 'log-entry';
            e.innerHTML = '<span class="t">'+ts()+'</span>'
                +'<span class="c">'+cmd.toUpperCase()+'</span> '
                +(ok?'<span class="ok">ACK</span>':'<span class="er">ERR</span>')
                +'<span class="ms">'+ms+'ms</span>';
            logBody.insertBefore(e, logBody.firstChild);
            if (logBody.children.length > 50) logBody.removeChild(logBody.lastChild);
        }

        function send(cmd, force = false) {
            if (activeRequest && !force) {
                pendingCommand = cmd;
                return;
            }
            activeRequest = true;
            const t0 = performance.now();
            fetch('/'+cmd)
                .then(r => r.json())
                .then(() => log(cmd, true, Math.round(performance.now()-t0)))
                .catch(() => log(cmd, false, Math.round(performance.now()-t0)))
                .finally(() => {
                    activeRequest = false;
                    if (pendingCommand !== null) {
                        const next = pendingCommand;
                        pendingCommand = null;
                        if (next !== cmd || isDragging) {
                            send(next);
                        }
                    }
                });
        }

        function updateSwitch(id, isOn) {
            const st = document.getElementById(id+'-state');
            const tr = document.getElementById(id+'-track');
            st.textContent = isOn ? 'ON' : 'OFF';
            st.className = 'state ' + (isOn ? 'on' : 'off');
            if (isOn) tr.classList.add('on');
            else tr.classList.remove('on');
        }

        document.getElementById('mode-card').addEventListener('click', function(e) {
            e.preventDefault();
            send('mode', true);
            modeOn = !modeOn;
            updateSwitch('mode', modeOn);
        });

        document.getElementById('suction-card').addEventListener('click', function(e) {
            e.preventDefault();
            send('suction', true);
            suctionOn = !suctionOn;
            updateSwitch('suction', suctionOn);
        });

        function toggleLog() {
            const p = document.getElementById('logPanel');
            const b = document.getElementById('logToggle');
            p.classList.toggle('collapsed');
            b.textContent = p.classList.contains('collapsed') ? '[+]' : '[_]';
        }

        // Virtual Joystick Controller
        const base = document.getElementById('joyBase');
        const knob = document.getElementById('joyKnob');
        const hudVal = document.getElementById('hudVal');
        const indicators = {
            'forward': document.getElementById('indUp'),
            'forward_right': document.getElementById('indUpRight'),
            'right': document.getElementById('indRight'),
            'reverse_right': document.getElementById('indDownRight'),
            'reverse': document.getElementById('indDown'),
            'reverse_left': document.getElementById('indDownLeft'),
            'left': document.getElementById('indLeft'),
            'forward_left': document.getElementById('indUpLeft')
        };

        let isDragging = false;
        let joyCenterX = 0;
        let joyCenterY = 0;
        const maxRadius = 58;
        const deadzone = 16;
        let currentCommand = 'stop';
        let heartbeatInterval = null;

        function updateBaseCenter() {
            const rect = base.getBoundingClientRect();
            joyCenterX = rect.left + rect.width / 2;
            joyCenterY = rect.top + rect.height / 2;
        }

        window.addEventListener('resize', updateBaseCenter);
        window.addEventListener('scroll', updateBaseCenter);

        function setIndicators(dir) {
            for (const key in indicators) {
                if (indicators[key]) {
                    indicators[key].classList.toggle('lit', key === dir);
                }
            }
        }

        function startContinuousStream() {
            if (heartbeatInterval) clearInterval(heartbeatInterval);
            heartbeatInterval = setInterval(() => {
                if (isDragging && currentCommand !== 'stop') {
                    send(currentCommand);
                }
            }, 100);
        }

        function stopContinuousStream() {
            if (heartbeatInterval) {
                clearInterval(heartbeatInterval);
                heartbeatInterval = null;
            }
        }

        function handleJoystickMove(clientX, clientY) {
            let dx = clientX - joyCenterX;
            let dy = clientY - joyCenterY;
            const dist = Math.hypot(dx, dy);

            if (dist > maxRadius) {
                const angle = Math.atan2(dy, dx);
                dx = Math.cos(angle) * maxRadius;
                dy = Math.sin(angle) * maxRadius;
            }

            knob.style.transform = `translate(${dx}px, ${dy}px)`;

            let nextCommand = 'stop';
            if (dist > deadzone) {
                // Angle in degrees: 0 deg = Right, 90 deg = Up (dy is inverted), 180 deg = Left, 270 deg = Down
                let angle = Math.atan2(-dy, dx) * 180 / Math.PI;
                if (angle < 0) angle += 360;

                if (angle >= 67.5 && angle < 112.5) nextCommand = 'forward';
                else if (angle >= 22.5 && angle < 67.5) nextCommand = 'forward_right';
                else if (angle >= 112.5 && angle < 157.5) nextCommand = 'forward_left';
                else if (angle >= 247.5 && angle < 292.5) nextCommand = 'reverse';
                else if (angle >= 292.5 && angle < 337.5) nextCommand = 'reverse_right';
                else if (angle >= 202.5 && angle < 247.5) nextCommand = 'reverse_left';
                else if (angle >= 157.5 && angle < 202.5) nextCommand = 'left';
                else nextCommand = 'right';
            }

            hudVal.textContent = nextCommand.replace('_', ' ').toUpperCase();
            setIndicators(nextCommand);

            if (nextCommand !== currentCommand) {
                currentCommand = nextCommand;
                send(currentCommand, true);
            }
        }

        function resetJoystick() {
            if (!isDragging && currentCommand === 'stop') return;
            isDragging = false;
            stopContinuousStream();
            knob.classList.add('spring');
            knob.style.transform = 'translate(0px, 0px)';
            base.classList.remove('active');
            setIndicators('stop');
            hudVal.textContent = 'STOP';

            currentCommand = 'stop';
            pendingCommand = null;
            send('stop', true);
        }

        base.addEventListener('pointerdown', (e) => {
            e.preventDefault();
            base.setPointerCapture(e.pointerId);
            updateBaseCenter();
            isDragging = true;

            // Automatically switch out of auto mode into manual control
            if (modeOn) {
                modeOn = false;
                updateSwitch('mode', false);
            }

            knob.classList.remove('spring');
            base.classList.add('active');
            handleJoystickMove(e.clientX, e.clientY);
            startContinuousStream();
        });

        base.addEventListener('pointermove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            handleJoystickMove(e.clientX, e.clientY);
        });

        window.addEventListener('pointermove', (e) => {
            if (!isDragging) return;
            handleJoystickMove(e.clientX, e.clientY);
        }, { passive: false });

        base.addEventListener('pointerup', (e) => {
            e.preventDefault();
            resetJoystick();
        });

        window.addEventListener('pointerup', () => {
            if (isDragging) resetJoystick();
        });

        base.addEventListener('pointercancel', (e) => {
            e.preventDefault();
            resetJoystick();
        });

        // Keyboard Arrow Keys
        const keys = {};
        window.addEventListener('keydown', (e) => {
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
                keys[e.key] = true;
                processKeyboard();
            }
        });

        window.addEventListener('keyup', (e) => {
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
                delete keys[e.key];
                processKeyboard();
            }
        });

        function processKeyboard() {
            let kx = 0;
            let ky = 0;
            if (keys['ArrowUp']) ky -= 1;
            if (keys['ArrowDown']) ky += 1;
            if (keys['ArrowLeft']) kx -= 1;
            if (keys['ArrowRight']) kx += 1;

            if (kx === 0 && ky === 0) {
                resetJoystick();
                return;
            }

            if (modeOn) {
                modeOn = false;
                updateSwitch('mode', false);
            }

            isDragging = true;
            updateBaseCenter();
            knob.classList.remove('spring');
            base.classList.add('active');
            const mag = Math.hypot(kx, ky);
            handleJoystickMove(joyCenterX + (kx / mag) * maxRadius, joyCenterY + (ky / mag) * maxRadius);
            startContinuousStream();
        }

        log('sys.init', true, 0);
    </script>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

PORT = 8000

def start_http_server():
    with ThreadedTCPServer(("", PORT), RobotControlHandler) as httpd:
        print(f"Serving web control at port {PORT}")
        httpd.serve_forever()

# Run the HTTP server in a background thread
server_thread = threading.Thread(target=start_http_server, daemon=True)
server_thread.start()

# App.run() keeps the bridge connection alive
App.run()
