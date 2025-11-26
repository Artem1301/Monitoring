from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from jwt_utils import create_access_token, jwt_required
from metrics import start_metrics_server_once
from queue_utils import send_to_queue
from datetime import datetime, timezone
import json

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), datetime.now(timezone.utc).timestamp())
        )
        db.commit()
    except:
        return jsonify({"error": "username_taken"}), 409

    return jsonify({"message": "user_created", "username": username}), 201

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    db = get_db()
    row = db.execute("SELECT password_hash FROM users WHERE username=?", (username,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "invalid_credentials"}), 401

    token = create_access_token(username)

    send_to_queue(json.dumps({
        "type": "login_event",
        "username": username,
        "timestamp": datetime.now(timezone.utc).timestamp()
    }))

    start_metrics_server_once()

    return jsonify({
        "access_token": token,
        "token_type": "bearer"
    })

@auth_bp.get("/authorize")
@jwt_required
def authorize():
    return jsonify({"authorized": True, "user": g.current_user})
