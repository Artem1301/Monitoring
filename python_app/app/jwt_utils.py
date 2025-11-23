import jwt
import os
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, g
from functools import wraps

SECRET_KEY = os.environ.get("SECRET_KEY", "replace-this")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(identity: str, expires_delta=None):
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": identity,
        "iat": now.timestamp(),
        "exp": (now + expires_delta).timestamp()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    return token if isinstance(token, str) else token.decode()

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return {"error": "token_expired"}
    except jwt.InvalidTokenError:
        return {"error": "invalid_token"}

def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"error": "Authorization header missing"}), 401

        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header must be Bearer <token>"}), 401

        payload = decode_token(parts[1])
        if "error" in payload:
            return jsonify({"error": payload["error"]}), 401

        g.current_user = payload.get("sub")
        return f(*args, **kwargs)
    return wrapper
