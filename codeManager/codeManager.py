import subprocess
import threading
import queue
import time
import json
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

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
    
    # Add automatic flush after each print statement
    enhanced_code = python_code.replace('print(', 'print(').replace('print (', 'print(')
    # Add flush after each print statement
    import re
    enhanced_code = re.sub(r'print\(([^)]+)\)', r'print(\1); sys.stdout.flush()', enhanced_code)
    
    # Add sys import if not present
    if 'import sys' not in enhanced_code:
        enhanced_code = 'import sys\n' + enhanced_code
    
    # Send enhanced code to stdin
    process.stdin.write(enhanced_code)
    process.stdin.close()
    
    def read_output():
        """Read stdout in a separate thread"""
        while True:
            line = process.stdout.readline()
            if line:
                output_queue.put(('stdout', line.rstrip()))
                # Force flush to ensure immediate output
                import sys
                sys.stdout.flush()
            else:
                break
        
        # Read any remaining stderr
        error_line = process.stderr.readline()
        if error_line:
            output_queue.put(('stderr', error_line.rstrip()))
    
    # Start reading output in a separate thread
    thread = threading.Thread(target=read_output)
    thread.daemon = True
    thread.start()
    
    return process


def create_container(user_id):
    container_name = f"code_runner_{user_id}"
    network_name = "batman"

    subprocess.run([
        'docker', 'run', '-d',
        '--name', container_name,
        '--rm',
        '--network', network_name,
        'python:3.10',
        'tail', '-f', '/dev/null'
    ], check=True)


def is_container_running(container_name):
    result = subprocess.run(
        ['docker', 'ps', '--filter', f"name={container_name}", '--format', '{{.Names}}'],
        stdout=subprocess.PIPE,
        check=True
    ).stdout.decode('utf-8').strip()
    return bool(result)

def remove_container(container_name):
    subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def forward_to_container(user_id, code):
    container_name = f"code_runner_{user_id}"
    if not is_container_running(container_name):
        remove_container(container_name)
        create_container(user_id)
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
    
    container_name = f"code_runner_{user_id}"
    if not is_container_running(container_name):
        remove_container(container_name)
        create_container(user_id)
    
    if not is_container_running(container_name):
        return jsonify({"error": "Konteyner çalışmıyor."}), 500
    
    # Create output queue for streaming
    output_queue = queue.Queue()
    process = execute_python_with_streaming(container_name, code, output_queue)
    
    def generate():
        """Generate streaming response"""
        while True:
            try:
                # Get output from queue with timeout
                output_type, line = output_queue.get(timeout=0.1)
                yield f"data: {json.dumps({'type': output_type, 'line': line})}\n\n"
            except queue.Empty:
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
    
    return Response(generate(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
