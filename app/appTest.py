from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_socketio import SocketIO
from pymongo import MongoClient
import bcrypt
import uuid
from pylint import epylint as lint
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import tempfile
import os
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Pool, cpu_count

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

socketio = SocketIO(app)

# MongoDB bağlantısı
client = MongoClient("mongodb://admin:password@localhost:27017/")
db = client['user_db']
users = db['users']

# Çoklu işlem desteği
num_cores = cpu_count()

def is_os_linux():
    if os.name == "nt":
        return False
    return True

def process_error(error):
    """Formats error message into dictionary

        :param error: pylint error full text
        :return: dictionary of error as:
            {
                "code":...,
                "error": ...,
                "message": ...,
                "line": ...,
                "error_info": ...,
            }
    """
    # Return None if not an error or warning
    if error == " " or error is None:
        return None
    if error.find("Your code has been rated at") > -1:
        return None

    list_words = error.split()
    if len(list_words) < 3:
        return None

    # Detect OS
    line_num = None
    if is_os_linux():
        try:
            line_num = error.split(":")[1]
        except Exception as e:
            print(os.name + " not compatible: " + e)
    else:
        line_num = error.split(":")[2]

    # list_words.pop(0)
    error_yet, message_yet, first_time = False, False, True
    i, length = 0, len(list_words)
    # error_code=None
    while i < length:
        word = list_words[i]
        if (word == "error" or word == "warning") and first_time:
            error_yet = True
            first_time = False
            i += 1
            continue
        if error_yet:
            error_code = word[1:-1]
            error_string = list_words[i + 1][:-1]
            i = i + 3
            error_yet = False
            message_yet = True
            continue
        if message_yet:
            full_message = ' '.join(list_words[i:length - 1])
            break
        i += 1

    error_info = pylint_dict_final[error_code]

    return {
        "code": error_code,
        "error": error_string,
        "message": full_message,
        "line": line_num,
        "error_info": error_info,
    }

def format_errors(pylint_text):
    """Format errors into parsable nested dictionary

    :param pylint_text: original pylint output
    :return: dictionary of errors as:
        {
            {
                "code":...,
                "error": ...,
                "message": ...,
                "line": ...,
                "error_info": ...,
            }
            ...
        }
    """
    errors_list = pylint_text.splitlines(True)

    # If there is not an error, return nothing
    if "--------------------------------------------------------------------" in errors_list[1] and \
            "Your code has been rated at" in errors_list[2] and "module" not in errors_list[0]:
        return None

    errors_list.pop(0)

    pylint_dict = {}
    try:
        pool = Pool(num_cores)
        pylint_dict = pool.map(process_error, errors_list)
    finally:
        pool.close()
        pool.join()
        return pylint_dict

def evaluate_pylint(text):
    """Create temp files for pylint parsing on user code

    :param text: user code
    :return: dictionary of pylint errors:
        {
            {
                "code":...,
                "error": ...,
                "message": ...,
                "line": ...,
                "error_info": ...,
            }
            ...
        }
    """
    # Open temp file for specific session.
    # IF it doesn't exist (aka the key doesn't exist), create one
    if "file_name" in session:
        f = open(session["file_name"], "w")
        for t in text:
            f.write(t)
        f.flush()
    else:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            session["file_name"] = temp.name
            for t in text:
                temp.write(t.encode("utf-8"))
            temp.flush()

    try:
        ARGS = " -r n --disable=R,C"
        (pylint_stdout, pylint_stderr) = lint.py_run(
            session["file_name"] + ARGS, return_std=True)
    except Exception as e:
        raise Exception(e)

    if pylint_stderr.getvalue():
        raise Exception("Issue with pylint configuration")

    return format_errors(pylint_stdout.getvalue())

# Slow down if user clicks "Run" too many times
def slow():
    session["count"] += 1
    time = datetime.now() - session["time_now"]
    if float(session["count"]) / float(time.total_seconds()) > 5:
        return True

# Giriş sayfası
@app.route('/')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('code_editor'))
    return render_template('login.html')

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
        session['user_id'] = user['user_id']
        return jsonify({"message": "Giriş başarılı"}), 200
    else:
        return jsonify({"message": "Geçersiz kullanıcı adı veya şifre"}), 401

# Kod yazma sayfası
@app.route('/code_editor')
def code_editor():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    session["count"] = 0
    session["time_now"] = datetime.now()
    return render_template('code_editor.html')

# Çıkış işlemi
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

# Kod çalıştırma API'si
@app.route('/run_code', methods=['POST'])
def run_code():
    """Kod çalıştırma özelliği"""
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmanız gerekiyor"}), 401

    # Don't run too many times
    if slow():
        return jsonify("Running code too much within a short time period. Please wait a few seconds before clicking \"Run\" each time.")
    session["time_now"] = datetime.now()

    output = None
    if not "file_name" in session:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            session["file_name"] = temp.name
    cmd = 'python ' + session["file_name"]
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,
              stderr=STDOUT, close_fds=True)
    output = p.stdout.read()

    return jsonify(output.decode('utf-8'))

# Kod analizi ve renklendirme
@app.route('/check_code', methods=['POST'])
def check_code():
    """Run pylint on code and get output
        :return: JSON object of pylint errors
            {
                {
                    "code":...,
                    "error": ...,
                    "message": ...,
                    "line": ...,
                    "error_info": ...,
                }
                ...
            }

        For more customization, please look at Pylint's library code:
        https://github.com/PyCQA/pylint/blob/master/pylint/lint.py
    """
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmanız gerekiyor"}), 401

    session["code"] = request.form.get('code', '')
    output = evaluate_pylint(session["code"])
    return jsonify(output)

def remove_temp_code_file():
    os.remove(session["file_name"])

@socketio.on('disconnect', namespace='/check_disconnect')
def disconnect():
    """Remove temp file associated with current session"""
    remove_temp_code_file()


if __name__ == '__main__':
    socketio.run(app)
