import sqlite3
import ssl
import uuid
import json
import os
from datetime import datetime, timedelta
from base64 import urlsafe_b64encode, urlsafe_b64decode

from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Soporte opcional para Postgres (Neon/Supabase) si psycopg está instalado.
try:
    import psycopg2
    import psycopg2.pool
    _HAS_PG = True
except ImportError:
    _HAS_PG = False

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "licenses.db")
# Si DATABASE_URL está configurado, se usa Postgres externo (persistente).
# Respaldo hardcodeado para que funcione sin tocar variables de entorno.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_8IEZhSiMnwH3@ep-patient-block-acbpl692.sa-east-1.aws.neon.tech/neondb?sslmode=require",
)
SECRET_KEY = os.environ.get(
    "LICENSE_SECRET",
    "cambia-esta-clave-por-una-segura-en-produccion-32bytes!"
)
SALT = b"license-salt-muy-segura"
TOKEN_TTL_HOURS = 2

PG_POOL = None


def get_pg_pool():
    global PG_POOL
    if PG_POOL is None:
        PG_POOL = psycopg2.pool.SimpleConnectionPool(
            1, 10, dsn=DATABASE_URL, sslmode="require"
        )
    return PG_POOL


def _derive_fernet_key() -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=480000,
    )
    key = urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key


def get_cipher() -> Fernet:
    return Fernet(_derive_fernet_key())


USE_PG = bool(DATABASE_URL) and _HAS_PG


def _pg_exec(conn, raw_sql, args=None, fetch=None):
    """Ejecuta SQL cruda en Postgres y normaliza el resultado a dicts."""
    cur = conn.cursor()
    cur.execute(raw_sql, args or ())
    if fetch == "one":
        cols = [d[0] for d in cur.description] if cur.description else []
        row = cur.fetchone()
        result = dict(zip(cols, row)) if row else None
    elif fetch == "all":
        cols = [d[0] for d in cur.description] if cur.description else []
        result = [dict(zip(cols, r)) for r in cur.fetchall()]
    else:
        result = None
    cur.close()
    conn.commit()
    return result


def get_db():
    """Devuelve una conexión (Postgres si está configurado, si no SQLite)."""
    if USE_PG:
        return get_pg_pool().getconn()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def close_db(conn):
    if USE_PG:
        get_pg_pool().putconn(conn)
    else:
        conn.close()


def init_db():
    if USE_PG:
        conn = get_db()
        try:
            _pg_exec(conn, """
                CREATE TABLE IF NOT EXISTS licenses (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    client_name TEXT NOT NULL DEFAULT '',
                    start_date TEXT NOT NULL,
                    duration_days DOUBLE PRECISION NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active'
                )
            """)
        finally:
            close_db(conn)
        return

    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL DEFAULT '',
            start_date TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------------------------
# Admin: generar una nueva licencia
# ---------------------------------------------------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    # Fallback a query params si no hay JSON body
    if not data:
        duration = request.args.get("duration_days", "365")
        client_name = request.args.get("client_name", "")
    else:
        duration = data.get("duration_days", 365)
        client_name = data.get("client_name", "")

    try:
        duration = float(duration)
    except (ValueError, TypeError):
        return jsonify({"error": "duration_days debe ser numérico"}), 400

    license_key = str(uuid.uuid4()).upper()
    start = datetime.utcnow()

    conn = get_db()
    try:
        if USE_PG:
            _pg_exec(conn, """
                INSERT INTO licenses (key, client_name, start_date, duration_days, status)
                VALUES (%s, %s, %s, %s, 'active')
            """, (license_key, client_name, start.isoformat(), duration))
        else:
            conn.execute(
                "INSERT INTO licenses (key, client_name, start_date, duration_days, status) VALUES (?, ?, ?, ?, 'active')",
                (license_key, client_name, start.isoformat(), duration),
            )
            conn.commit()
    except Exception:
        close_db(conn)
        return jsonify({"error": "No se pudo guardar la key"}), 500
    close_db(conn)

    expires = start + timedelta(days=duration)

    return jsonify({
        "key": license_key,
        "start_date": start.isoformat(),
        "expiration_date": expires.isoformat(),
        "duration_days": duration,
        "client_name": client_name,
        "status": "active",
    }), 201


# ---------------------------------------------------------------------------
# Validación pública (la llama el cliente)
# ---------------------------------------------------------------------------
@app.route("/validate", methods=["GET"])
def validate():
    license_key = request.args.get("key", "").strip().upper()
    if not license_key:
        return jsonify({"error": "Parámetro 'key' requerido"}), 400

    conn = get_db()
    if USE_PG:
        row = _pg_exec(conn, "SELECT * FROM licenses WHERE key = %s", (license_key,), fetch="one")
    else:
        row = conn.execute(
            "SELECT * FROM licenses WHERE key = ?", (license_key,)
        ).fetchone()
    close_db(conn)

    if row is None:
        return jsonify({"valid": False, "reason": "KEY_NOT_FOUND"}), 404

    if row["status"] != "active":
        return jsonify({"valid": False, "reason": "KEY_DISABLED"}), 403

    start = datetime.fromisoformat(row["start_date"])
    expiration = start + timedelta(days=row["duration_days"])
    now = datetime.utcnow()

    if now > expiration:
        return jsonify({"valid": False, "reason": "EXPIRED"}), 403

    # --- Construir token firmado -------------------------------------------
    token_payload = {
        "key": row["key"],
        "client_name": row["client_name"],
        "issued_at": now.isoformat(),
        "expiration_date": expiration.isoformat(),
        "valid": True,
    }

    cipher = get_cipher()
    token = cipher.encrypt(json.dumps(token_payload).encode()).decode()

    return jsonify({
        "valid": True,
        "token": token,
        "expiration_date": expiration.isoformat(),
    })


# ---------------------------------------------------------------------------
# El cliente puede verificar el token localmente si quiere
# ---------------------------------------------------------------------------
@app.route("/verify-token", methods=["POST"])
def verify_token():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    if not token:
        return jsonify({"error": "Parámetro 'token' requerido"}), 400

    try:
        cipher = get_cipher()
        payload_bytes = cipher.decrypt(token.encode())
        payload = json.loads(payload_bytes.decode())
        return jsonify({"valid": True, "payload": payload})
    except Exception:
        return jsonify({"valid": False, "reason": "TOKEN_INVALID_OR_TAMPERED"}), 403


# ---------------------------------------------------------------------------
# Desactivar todas las keys existentes
# ---------------------------------------------------------------------------
@app.route("/disable-all", methods=["POST"])
def disable_all():
    conn = get_db()
    if USE_PG:
        _pg_exec(conn, "UPDATE licenses SET status = 'disabled' WHERE status = 'active'")
        count = _pg_exec(conn, "SELECT count(*) AS c FROM licenses WHERE status = 'disabled'", fetch="one")["c"]
    else:
        conn.execute("UPDATE licenses SET status = 'disabled' WHERE status = 'active'")
        count = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
    close_db(conn)
    return jsonify({"status": "ok", "disabled_keys": count})


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
