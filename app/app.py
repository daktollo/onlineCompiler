from flask import Flask, request, jsonify, render_template, redirect, url_for, session, Response
from flask_socketio import SocketIO
from pymongo import MongoClient
import bcrypt
import uuid
import os
from datetime import datetime, timezone
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Pool, cpu_count
import subprocess
import requests
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

socketio = SocketIO(app)

client = MongoClient("mongodb://admin:password@mongo_db:27017/")
db = client['user_db']
users = db['users']
num_cores = cpu_count()


def is_os_linux():
    if os.name == "nt":
        return False
    return True


def slow():
    session["count"] += 1
    time = datetime.now(timezone.utc) - session["time_now"] 
    if float(session["count"]) / float(time.total_seconds()) > 5:
        return True

@app.route('/')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('code_editor'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        session['user_id'] = user['user_id']
        return jsonify({"message": "Giriş başarılı", "user_id": user['user_id']}), 200
    else:
        return jsonify({"message": "Geçersiz kullanıcı adı veya şifre"}), 401
    
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')
    
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if users.find_one({"username": username}):
        return jsonify({"message": "Kullanıcı adı zaten alınmış."}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(uuid.uuid4())

    users.insert_one({
        "user_id": user_id,
        "username": username,
        "password": hashed_password
    })

    return jsonify({"message": "Kayıt başarılı", "user_id": user_id}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Çıkış yapıldı"}), 200



@app.route('/submit_code', methods=['POST'])
def submit_code():
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmanız gerekiyor"}), 401
    
    if slow():
        return jsonify({"error": "Çok sık çalıştırıyorsunuz. Lütfen bekleyin."}), 429
    session["time_now"] = datetime.now(timezone.utc)

    code = request.json.get('text')
    if not code:
        return jsonify({"error": "Kod gönderilmedi."}), 400

    try:
        response = requests.post(
            'http://manager:5001/run_code',
            json={'user_id': session["user_id"], 'code': code},
            timeout=10
        )
        response.raise_for_status()

        output = response.json()
        stdout = output.get('stdout', '')
        stderr = output.get('stderr', '')

        if not stdout and stderr:
            result = {"error": stderr}
        else:
            result = {"output": stdout}

        return jsonify(result)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Kod çalıştırma servisinde bir hata oluştu: {str(e)}"}), 500

    

@app.route('/run_code', methods=['POST'])
def run_code():
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmanız gerekiyor"}), 401

    if slow():
        return jsonify({"error": "Çok sık çalıştırıyorsunuz. Lütfen bekleyin."}), 429
    session["time_now"] = datetime.now(timezone.utc)

    user_code = request.json.get('text', '')
    print("user_code:",user_code)

    try:
        result = subprocess.run(
            ['python', '-c', user_code],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
    except subprocess.CalledProcessError as e:
        output = e.stderr

    return jsonify({"output": output})



@app.route('/code_editor')
def code_editor():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    session["count"] = 0
    session["time_now"] = datetime.now(timezone.utc)
    return render_template('code_editor.html')


@app.route('/api/ai_error_handler', methods=['POST'])
def ai_error_handler():
    data = request.json

    code = data.get("message", "")
    output = data.get("output", "")
    prompt = f"""
    yazıdığım kod:
    {code}
    
    Çıktım:
    {output}

    Sorunu bir cümle ile kısaca anlat.
    """
    
    print("prompt:", prompt)

    url = "http://ollama:11433/api/generate"

    data = {
        "model": "qwen2.5-coder",
        "prompt": prompt,
    }

    def generate_stream():
        response = requests.post(url, json=data, stream=True)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    result = json.loads(decoded_line)
                    generated_text = result.get("response", "")
                    yield f"{generated_text}"
        else:
            yield f"data: Error: {response.status_code}, {response.text}\n\n"

    return Response(generate_stream(), content_type='text/event-stream')

def remove_temp_code_file():
    os.remove(session["file_name"])

@socketio.on('disconnect', namespace='/check_disconnect')
def disconnect():
    """Remove temp file associated with current session"""
    remove_temp_code_file()


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5200, debug=False, allow_unsafe_werkzeug=True)
