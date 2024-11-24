import subprocess
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Docker konteyneri başlat
def create_container(user_id):
    container_name = f"code_runner_{user_id}"
    subprocess.run(['docker', 'run', '-d', '--name', container_name, 'python:3.10-slim'])

# Kodun Docker konteynerinde çalıştırılması
def run_code_in_container(user_id, code):
    container_name = f"code_runner_{user_id}"
    
    # Öğrenci kodunu geçici dosyaya yaz
    with open(f'/tmp/{user_id}_code.py', 'w') as f:
        f.write(code)
    
    # Kodu konteyner içinde çalıştır
    result = subprocess.run(
        ['docker', 'exec', container_name, 'python', f'/tmp/{user_id}_code.py'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')

# Kod çalıştırma isteğini yöneten endpoint
@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')

    # Eğer konteyner yoksa, oluştur
    container_name = f"code_runner_{user_id}"
    running_containers = subprocess.run(
        ['docker', 'ps', '--filter', f"name={container_name}", '--format', '{{.Names}}'],
        stdout=subprocess.PIPE
    ).stdout.decode('utf-8').strip()

    if not running_containers:
        create_container(user_id)

    # Kodu çalıştır ve sonucu al
    output, error = run_code_in_container(user_id, code)

    if error:
        return jsonify({"error": error}), 400
    else:
        return jsonify({"output": output}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5001, debug=True)
