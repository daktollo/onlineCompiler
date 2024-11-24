from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import bcrypt
import uuid
import subprocess
import os
import requests


app = Flask(__name__)

# MongoDB'ye bağlan
client = MongoClient("mongodb://admin:password@mongo_db:27017/")
db = client['user_db']
users = db['users']

# Ana sayfa (frontend)
@app.route('/')
def index():
    return render_template('index.html')

# Kayıt API'si
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

# Giriş API'si
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({"message": "Giriş başarılı", "user_id": user['user_id']}), 200
    else:
        return jsonify({"message": "Geçersiz kullanıcı adı veya şifre"}), 401

# Kod çalıştırma isteği API'si
@app.route('/submit_code', methods=['POST'])
def submit_code():
    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')

    # CodeRunner servisine kod gönder
    response = requests.post('http://coderunner:5001/run_code', json={'user_id': user_id, 'code': code})

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Kod çalıştırılamadı"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
