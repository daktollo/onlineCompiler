import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

def execute_python_in_container(container_name, python_code):
    result = subprocess.run(
        [
            "docker", "exec", container_name, "python3", "-c", python_code
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return {
        "stdout": result.stdout.decode("utf-8"),
        "stderr": result.stderr.decode("utf-8")
    }


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
