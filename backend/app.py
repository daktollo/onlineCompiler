from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import bcrypt
import uuid
import os
from datetime import datetime, timezone, timedelta
import requests
import json
import jwt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])  # Vue.js dev server
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000", "http://localhost:5173"])

# MongoDB connection
client = MongoClient("mongodb://admin:password@mongo_db:27017/")
db = client['user_db']
users = db['users']

# Rate limiting storage
user_requests = {}

@app.route('/')
def home():
    return jsonify({'message': 'Backend API is running!', 'status': 'success'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = users.find_one({'user_id': data['user_id']})
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def check_rate_limit(user_id):
    """Check if user is making too many requests"""
    now = datetime.now(timezone.utc)
    if user_id not in user_requests:
        user_requests[user_id] = {'count': 0, 'time': now}
    
    time_diff = now - user_requests[user_id]['time']
    if time_diff.total_seconds() > 60:  # Reset every minute
        user_requests[user_id] = {'count': 0, 'time': now}
    
    user_requests[user_id]['count'] += 1
    return user_requests[user_id]['count'] <= 30  # Max 30 requests per minute

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if users.find_one({"username": username}):
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(uuid.uuid4())

    users.insert_one({
        "user_id": user_id,
        "username": username,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc)
    })

    # Generate JWT token
    token = jwt.encode({
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': {'user_id': user_id, 'username': username}
    }), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = users.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['user_id'],
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {'user_id': user['user_id'], 'username': user['username']}
        }), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({
        'user': {'user_id': current_user['user_id'], 'username': current_user['username']}
    }), 200

# Code Execution Routes
@app.route('/api/code/execute', methods=['POST'])
@token_required
def execute_code(current_user):
    if not check_rate_limit(current_user['user_id']):
        return jsonify({'error': 'Rate limit exceeded. Please wait before making another request.'}), 429

    data = request.json
    code = data.get('code')
    
    if not code:
        return jsonify({'error': 'Code is required'}), 400

    try:
        response = requests.post(
            'http://manager:5001/run_code',
            json={'user_id': current_user['user_id'], 'code': code},
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
        return jsonify({"error": f"Code execution service error: {str(e)}"}), 500

# AI Error Handler Route
@app.route('/api/ai/error-handler', methods=['POST'])
@token_required
def ai_error_handler(current_user):
    data = request.json
    code = data.get("code", "")
    output = data.get("output", "")
    
    prompt = f"""
    Yazdığım kod:
    {code}
    
    Çıktım:
    {output}

    Sorunu bir cümle ile kısaca anlat.
    """
    
    url = "http://ollama:11433/api/generate"
    data = {
        "model": "qwen2.5-coder",
        "prompt": prompt,
    }

    def generate_stream():
        try:
            response = requests.post(url, json=data, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        result = json.loads(decoded_line)
                        generated_text = result.get("response", "")
                        yield f"data: {json.dumps({'response': generated_text})}\n\n"
            else:
                yield f"data: {json.dumps({'error': f'Error: {response.status_code}, {response.text}'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response
    return Response(generate_stream(), content_type='text/event-stream')

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
@token_required
def handle_join_room(current_user, data):
    room = data.get('room', current_user['user_id'])
    join_room(room)
    emit('joined_room', {'room': room})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
