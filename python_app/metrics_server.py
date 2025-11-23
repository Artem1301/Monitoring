# auth.py
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import jwt  # PyJWT
import os
import threading
import random
import time
from prometheus_client import start_http_server, Gauge

# ======== Конфіг ========
SECRET_KEY = os.environ.get("SECRET_KEY", "replace-this-with-secure-random-value")
DB_PATH = os.environ.get("AUTH_DB", "auth.db")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

METRICS_PORT = 8000  # порт для Prometheus метрик

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# ======== DB ========
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """)
    db.commit()
    db.close()

# ======== JWT ========
def create_access_token(identity: str, expires_delta: timedelta | None = None):
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": identity,
        "iat": now.timestamp(),
        "exp": (now + expires_delta).timestamp()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "token_expired"}
    except jwt.InvalidTokenError:
        return {"error": "invalid_token"}

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            return jsonify({"error": "Authorization header must be Bearer <token>"}), 401
        token = parts[1]
        payload = decode_token(token)
        if "error" in payload:
            return jsonify({"error": payload["error"]}), 401
        g.current_user = payload.get("sub")
        return f(*args, **kwargs)
    return decorated

# ======== Prometheus метрики ========
metrics_started = False
sensor_value = Gauge("sensor_value", "Random sensor value from Python app")

def generate_metrics():
    """Фоновий потік для оновлення метрик кожну секунду"""
    while True:
        val = random.randint(0, 100)
        sensor_value.set(val)
        time.sleep(1)

def start_metrics_server_once():
    global metrics_started
    if not metrics_started:
        start_http_server(METRICS_PORT)
        thread = threading.Thread(target=generate_metrics, daemon=True)
        thread.start()
        metrics_started = True
        print(f"Prometheus metrics server started on port {METRICS_PORT}")

# ======== Routes ========
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    password_hash = generate_password_hash(password)
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now(timezone.utc).timestamp())
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "username_taken"}), 409

    return jsonify({"message": "user_created", "username": username}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "invalid_credentials"}), 401

    token = create_access_token(identity=username)

    # --- запуск генерації метрик після логіну ---
    start_metrics_server_once()

    return jsonify({"access_token": token, "token_type": "bearer", "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES})

@app.route("/authorize", methods=["GET"])
@jwt_required
def authorize():
    return jsonify({"authorized": True, "user": g.get("current_user")})

@app.route("/debug/users", methods=["GET"])
def debug_users():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, created_at FROM users")
    rows = cur.fetchall()
    users = [{"id": r["id"], "username": r["username"], "created_at": r["created_at"]} for r in rows]
    return jsonify(users)

# ======== Run ========
if __name__ == "__main__":
    init_db()
    print(f"Using DB at: {DB_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=True)
