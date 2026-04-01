from flask import Flask, request, jsonify
import secrets
from functions import *

app = Flask(__name__)
UPLOAD_FOLDER = "received_files"

load_ids()



@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    token = request.form.get("token")
    save_path = upload_image(token, file.filename)
    if not save_path:
        return jsonify({"status": "error", "message": "Invalid token"})
    file.save(save_path)
    print(f"Saved: {save_path} ({os.path.getsize(save_path)} bytes)")
    return jsonify({"status": "ok", "filename": file.filename})


@app.route("/sign_in", methods=["POST"])
def sign_in():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(username, password)

    if username in ids:
        return jsonify({"status": "error", "message": "Username already exists"})

    add_user(username, password)
    return jsonify({"status": "ok", "message": "Login saved"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(username, password)
    if not check_login(username, password):
        return jsonify({"status": "error", "message": "Invalid username or password"})

    token = secrets.token_hex(16)
    tokens[token]=username
    return jsonify({"status": "ok", "token": token})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)
save_ids()