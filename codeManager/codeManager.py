import subprocess
import threading
import queue
import time
import json
import logging
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:6610", "http://localhost:5173", "http://127.0.0.1:6610"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Ensure INFO-level logs are emitted to stdout
app.logger.setLevel(logging.INFO)

# --- SSE subscriber registry ---
_subscribers = {}
_subs_lock = threading.Lock()

def _broadcast_to_user(user_id: str, event: dict):
    """Broadcast event to all SSE subscribers for the given user_id."""
    if not user_id:
        return
    with _subs_lock:
        queues = list(_subscribers.get(user_id, []))
    if not queues:
        return
    data = json.dumps(event)
    for q in queues:
        try:
            q.put_nowait(data)
        except Exception:
            # Ignore slow/broken clients
            pass

def execute_python_in_container(container_name, python_code):
    # Execute Python code by piping it to python3 stdin
    result = subprocess.run(
        [
            "docker", "exec", "-i", container_name, "python3"
        ],
        input=python_code.encode('utf-8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return {
        "stdout": result.stdout.decode("utf-8"),
        "stderr": result.stderr.decode("utf-8")
    }

def execute_python_with_streaming(container_name, python_code, output_queue):
    """Execute Python code with real-time streaming output"""
    process = subprocess.Popen(
        [
            "docker", "exec", "-i", container_name, "python3", "-u"  # -u: unbuffered
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,  # Unbuffered
        env={"PYTHONUNBUFFERED": "1"}  # Force unbuffered Python
    )
    
    # Send code as-is; -u and PYTHONUNBUFFERED already ensure unbuffered output
    enhanced_code = python_code
    
    # Send enhanced code to stdin
    process.stdin.write(enhanced_code)
    process.stdin.close()
    
    def read_output():
        """Read stdout in a separate thread"""
        try:
            while True:
                line = process.stdout.readline()
                if line:
                    output_queue.put(('stdout', line.rstrip()))
                else:
                    break
            
            # Read any remaining stderr
            error_line = process.stderr.readline()
            if error_line:
                output_queue.put(('stderr', error_line.rstrip()))
        except Exception as e:
            output_queue.put(('error', f"Error reading output: {str(e)}"))
    
    # Start reading output in a separate thread
    thread = threading.Thread(target=read_output)
    thread.daemon = True
    thread.start()
    
    return process


def create_container(user_id):
    container_name = f"code_runner_{user_id}"
    network_name = "batman"

    try:
        subprocess.run([
            'docker', 'run', '-d',
            '--name', container_name,
            '--rm',
            '--network', network_name,
            '-e', f'BLOCK_USER_ID={user_id}',
            'block-runner:latest',
            'tail', '-f', '/dev/null'
        ], check=True)
        print(f"Container {container_name} created successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error creating container {container_name}: {e}")
        raise


def is_container_running(container_name):
    result = subprocess.run(
        ['docker', 'ps', '--filter', f"name={container_name}", '--format', '{{.Names}}'],
        stdout=subprocess.PIPE,
        check=True
    ).stdout.decode('utf-8').strip()
    return bool(result)

def remove_container(container_name):
    try:
        result = subprocess.run(['docker', 'rm', '-f', container_name], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"Container {container_name} removed successfully")
        else:
            print(f"Warning: Could not remove container {container_name}: {result.stderr.decode()}")
    except Exception as e:
        print(f"Error removing container {container_name}: {e}")

def ensure_fresh_container(user_id):
    """Remove any existing container for the user and create a fresh one."""
    container_name = f"code_runner_{user_id}"
    # Best-effort removal; ignore errors
    remove_container(container_name)
    create_container(user_id)

def forward_to_container(user_id, code):
    # Always recreate to kill any lingering processes
    ensure_fresh_container(user_id)
    container_name = f"code_runner_{user_id}"
    if is_container_running(container_name):
        result = execute_python_in_container(container_name, code)
        return result
    else:
        return {"error": "Konteyner çalışmıyor."}


@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')
    print("kod:", code)

    if not user_id or not code:
        return jsonify({"error": "Kullanıcı ID ve kod gereklidir."}), 400

    result = forward_to_container(user_id, code)
    return jsonify(result)

@app.route('/run_code_streaming', methods=['POST'])
def run_code_streaming():
    """Execute code with real-time streaming output"""
    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')
    
    if not user_id or not code:
        return jsonify({"error": "Kullanıcı ID ve kod gereklidir."}), 400
    
    # Always recreate container to ensure no previous processes are running
    ensure_fresh_container(user_id)
    container_name = f"code_runner_{user_id}"

    if not is_container_running(container_name):
        return jsonify({"error": "Konteyner çalışmıyor."}), 500
    
    # Create output queue for streaming
    output_queue = queue.Queue()
    process = execute_python_with_streaming(container_name, code, output_queue)
    
    def generate():
        """Generate streaming response"""
        try:
            last_ping = time.time()
            while True:
                try:
                    # Get output from queue with timeout
                    output_type, line = output_queue.get(timeout=0.1)
                    yield f"data: {json.dumps({'type': output_type, 'line': line})}\n\n"
                except queue.Empty:
                    # Heartbeat to keep connection alive during long silences
                    now = time.time()
                    if process.poll() is None and (now - last_ping) >= 10:
                        yield "data: {\"type\": \"ping\"}\n\n"
                        last_ping = now
                    # Check if process is still running
                    if process.poll() is not None:
                        # Process finished, check for any remaining output
                        try:
                            while True:
                                output_type, line = output_queue.get_nowait()
                                yield f"data: {json.dumps({'type': output_type, 'line': line})}\n\n"
                        except queue.Empty:
                            pass
                        break
                    continue
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'line': str(e)})}\n\n"
                    break
        finally:
            # Cleanup: terminate process if still running
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    
    return Response(generate(), content_type='text/event-stream')


@app.route('/stop_container', methods=['POST'])
def stop_container():
    """Force-stop and remove the current user's code runner container."""
    data = request.json or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "Kullanıcı ID gereklidir."}), 400

    container_name = f"code_runner_{user_id}"
    try:
        remove_container(container_name)
        return jsonify({"status": "stopped", "container": container_name}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/events', methods=['GET'])
def sse_events():
    """SSE stream per user_id. Client connects with /events?user_id=..."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id gereklidir."}), 400

    client_queue = queue.Queue(maxsize=100)

    with _subs_lock:
        _subscribers.setdefault(user_id, []).append(client_queue)
        app.logger.info("[sse] client subscribed user=%s total=%s", user_id, len(_subscribers[user_id]))

    @stream_with_context
    def event_stream():
        try:
            # Initial hello to open stream promptly
            yield f"data: {json.dumps({'type': 'hello', 'user_id': user_id})}\n\n"
            last_ping = time.time()
            while True:
                try:
                    item = client_queue.get(timeout=15)
                    yield f"data: {item}\n\n"
                except queue.Empty:
                    # heartbeat every ~15s
                    now = time.time()
                    if now - last_ping >= 15:
                        yield "data: {\"type\": \"ping\"}\n\n"
                        last_ping = now
                    continue
        finally:
            # Unsubscribe on disconnect
            with _subs_lock:
                lst = _subscribers.get(user_id, [])
                if client_queue in lst:
                    lst.remove(client_queue)
                if not lst:
                    _subscribers.pop(user_id, None)
            app.logger.info("[sse] client disconnected user=%s", user_id)

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',  # for some proxies
    }
    return Response(event_stream(), headers=headers)


@app.route('/block_update', methods=['POST'])
def block_update():
    """Handle block property change events from the code runner container."""
    data = request.json or {}

    display_id = data.get('display_id')
    user_id = data.get('user_id')
    block_x = data.get('block_x')
    block_y = data.get('block_y')
    property_name = data.get('property')
    value = data.get('value')
    timestamp = data.get('timestamp')

    app.logger.info(
        "[block_update] user=%s display=%s block=(%s,%s) %s=%s ts=%s",
        user_id, display_id, block_x, block_y, property_name, value, timestamp
    )

    # Broadcast to SSE subscribers for this user
    _broadcast_to_user(user_id, {
        'type': 'block_update',
        'user_id': user_id,
        'display_id': display_id,
        'block_x': block_x,
        'block_y': block_y,
        'property': property_name,
        'value': value,
        'timestamp': timestamp,
    })
    return jsonify({"status": "success"}), 200


@app.route('/display_create', methods=['POST'])
def display_create():
    """Notify that a new BlockDisplay has been created in the runner."""
    data = request.json or {}

    display_id = data.get('display_id')
    user_id = data.get('user_id')
    size = data.get('size') or {'width': 8, 'height': 8}
    timestamp = data.get('timestamp') or time.time()

    app.logger.info(
        "[display_create] user=%s display=%s size=%s ts=%s",
        user_id, display_id, size, timestamp
    )

    _broadcast_to_user(user_id, {
        'type': 'display_create',
        'user_id': user_id,
        'display_id': display_id,
        'size': size,
        'timestamp': timestamp,
    })
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
