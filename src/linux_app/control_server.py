import http.server
import socketserver
import urllib.parse
import threading
from arduino.app_utils import *

class RobotControlHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        command = None
        if path == '/forward': command = 'forward'
        elif path == '/reverse': command = 'reverse'
        elif path == '/left': command = 'left'
        elif path == '/right': command = 'right'
        elif path == '/stop': command = 'stop'
        elif path == '/mode': command = 'mode'
        elif path == '/suction': command = 'suction'
        elif path == '/test_shake': command = 'test_shake'
        elif path == '/test_arc': command = 'test_arc'
            
        if command:
            try:
                Bridge.call(command)
                print(f"Called RPC method: {command}")
            except Exception as e:
                print(f"Failed to call {command}: {e}")
            # Send a quick JSON response instead of a redirect
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
            padding: 12px 18px;
            font-size: 13px;
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
        .btn-dir {
            width: 72px; height: 72px;
            font-size: 24px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .btn-stop {
            width: 72px; height: 72px;
            font-size: 11px;
            font-weight: 700;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            border-color: #3a1a1a;
            color: #ff3333;
            border-radius: 50%;
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
        .grid-container {
            display: grid;
            grid-template-columns: 72px 72px 72px;
            gap: 8px;
            justify-content: center;
            margin: 18px 0;
        }
        .grid-item {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .section {
            margin-top: 22px;
            padding-top: 18px;
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

    <div class="grid-container">
        <div class="grid-item"></div>
        <div class="grid-item">
            <button class="btn btn-dir" onclick="send('forward')">&#9650;</button>
        </div>
        <div class="grid-item"></div>
        <div class="grid-item">
            <button class="btn btn-dir" onclick="send('left')">&#9664;</button>
        </div>
        <div class="grid-item">
            <button class="btn btn-stop" onclick="send('stop')">STOP</button>
        </div>
        <div class="grid-item">
            <button class="btn btn-dir" onclick="send('right')">&#9654;</button>
        </div>
        <div class="grid-item"></div>
        <div class="grid-item">
            <button class="btn btn-dir" onclick="send('reverse')">&#9660;</button>
        </div>
        <div class="grid-item"></div>
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

        function log(cmd, ok, ms) {
            const e = document.createElement('div');
            e.className = 'log-entry';
            e.innerHTML = '<span class="t">'+ts()+'</span>'
                +'<span class="c">'+cmd.toUpperCase()+'</span> '
                +(ok?'<span class="ok">ACK</span>':'<span class="er">ERR</span>')
                +'<span class="ms">'+ms+'ms</span>';
            logBody.insertBefore(e, logBody.firstChild);
            if (logBody.children.length > 50) logBody.removeChild(logBody.lastChild);
        }

        function send(cmd) {
            const t0 = performance.now();
            fetch('/'+cmd)
                .then(r => r.json())
                .then(() => log(cmd, true, Math.round(performance.now()-t0)))
                .catch(() => log(cmd, false, Math.round(performance.now()-t0)));
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
            send('mode');
            modeOn = !modeOn;
            updateSwitch('mode', modeOn);
        });

        document.getElementById('suction-card').addEventListener('click', function(e) {
            e.preventDefault();
            send('suction');
            suctionOn = !suctionOn;
            updateSwitch('suction', suctionOn);
        });

        function toggleLog() {
            const p = document.getElementById('logPanel');
            const b = document.getElementById('logToggle');
            p.classList.toggle('collapsed');
            b.textContent = p.classList.contains('collapsed') ? '[+]' : '[_]';
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
    with socketserver.TCPServer(("", PORT), RobotControlHandler) as httpd:
        print(f"Serving web control at port {PORT}")
        httpd.serve_forever()

# Run the HTTP server in a background thread
server_thread = threading.Thread(target=start_http_server, daemon=True)
server_thread.start()

# App.run() keeps the bridge connection alive
App.run()
