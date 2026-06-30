from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3, pickle, os, hashlib

app = Flask(__name__)
app.secret_key = "university_feedback_secret_2024"

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE, "data", "feedback.db")
MDL_PATH  = os.path.join(BASE, "model", "model.pkl")
VEC_PATH  = os.path.join(BASE, "model", "vectorizer.pkl")

# ── Load NLP model ─────────────────────────────────────────────────────────────
with open(MDL_PATH, "rb") as f:  model      = pickle.load(f)
with open(VEC_PATH, "rb") as f:  vectorizer = pickle.load(f)

# ── DB helpers ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role     TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student    TEXT NOT NULL,
                faculty    TEXT NOT NULL,
                course     TEXT NOT NULL,
                feedback   TEXT NOT NULL,
                sentiment  TEXT,
                rating     INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Seed users (password = sha256 of "123")
        pw = hashlib.sha256(b"123").hexdigest()
        users = [
            ("student1", pw, "student"), ("student2", pw, "student"), ("student3", pw, "student"),
            ("VENKATARAMANA V", pw, "teacher"), ("SHENDE AMIT", pw, "teacher"), ("PRAVEEN", pw, "teacher"),
            ("admin", pw, "admin"),
        ]
        db.executemany("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)", users)
        db.commit()

# ── Sentiment ──────────────────────────────────────────────────────────────────
def predict_sentiment(text):
    if not text.strip():
        return "Neutral"
    vec  = vectorizer.transform([text.strip().lower()])
    pred = model.predict(vec)[0]
    return {1: "Positive", 0: "Negative", 2: "Neutral"}.get(pred, "Neutral")

# ── Auth decorator ─────────────────────────────────────────────────────────────
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                return jsonify({"error": "Unauthorized"}), 401
            if role and session.get("role") != role:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ── Page routes ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", role=session["role"], user=session["user"])

# ── API: Auth ──────────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username", "").strip()
    password  = data.get("password", "")
    role      = data.get("role", "")
    pw_hash   = hashlib.sha256(password.encode()).hexdigest()

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (username, pw_hash, role)
        ).fetchone()

    if not user:
        return jsonify({"success": False, "message": "Invalid credentials or wrong role."}), 401

    session["user"] = user["username"]
    session["role"] = user["role"]
    return jsonify({"success": True, "role": user["role"], "user": user["username"]})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data     = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role     = data.get("role", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    if len(password) < 3:
        return jsonify({"success": False, "message": "Password must be at least 3 characters."}), 400
    if role not in ("student", "teacher", "admin"):
        return jsonify({"success": False, "message": "Invalid role selected."}), 400

    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    with get_db() as db:
        existing = db.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
        if existing:
            return jsonify({"success": False, "message": "Username already taken. Try logging in instead."}), 409

        db.execute(
            "INSERT INTO users (username,password,role) VALUES (?,?,?)",
            (username, pw_hash, role)
        )
        db.commit()

    session["user"] = username
    session["role"] = role
    return jsonify({"success": True, "role": role, "user": username})

# ── API: Feedback ──────────────────────────────────────────────────────────────
COURSES = [
    {"faculty": "VENKATARAMANA V", "course": "NLP"},
    {"faculty": "SHENDE AMIT",     "course": "Smart Farming"},
    {"faculty": "PRAVEEN",         "course": "Data Structures"},
]

@app.route("/api/courses")
@login_required()
def api_courses():
    return jsonify(COURSES)

@app.route("/api/feedback", methods=["POST"])
@login_required(role="student")
def api_submit_feedback():
    data      = request.json
    faculty   = data.get("faculty", "")
    course    = data.get("course", "")
    text      = data.get("feedback", "").strip()
    rating    = int(data.get("rating", 3))

    if not text:
        return jsonify({"success": False, "message": "Feedback text is required."}), 400

    sentiment = predict_sentiment(text)

    with get_db() as db:
        db.execute(
            "INSERT INTO feedback (student,faculty,course,feedback,sentiment,rating) VALUES (?,?,?,?,?,?)",
            (session["user"], faculty, course, text, sentiment, rating)
        )
        db.commit()

    label_map = {"Positive": "Good 😊", "Negative": "Bad 😠", "Neutral": "Neutral 😐"}
    return jsonify({"success": True, "sentiment": label_map.get(sentiment, sentiment)})

@app.route("/api/teacher/feedback")
@login_required(role="teacher")
def api_teacher_feedback():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM feedback WHERE faculty=? ORDER BY created_at DESC",
            (session["user"],)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/feedback")
@login_required(role="admin")
def api_admin_feedback():
    with get_db() as db:
        rows = db.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/stats")
@login_required(role="admin")
def api_admin_stats():
    with get_db() as db:
        total    = db.execute("SELECT COUNT(*) as c FROM feedback").fetchone()["c"]
        avg_rat  = db.execute("SELECT ROUND(AVG(rating),2) as a FROM feedback").fetchone()["a"] or 0
        sentiment= db.execute("SELECT sentiment, COUNT(*) as c FROM feedback GROUP BY sentiment").fetchall()
        faculty  = db.execute("SELECT faculty, ROUND(AVG(rating),2) as avg FROM feedback GROUP BY faculty").fetchall()
        ratings  = db.execute("SELECT rating, COUNT(*) as c FROM feedback GROUP BY rating").fetchall()
    return jsonify({
        "total": total, "avg_rating": avg_rat,
        "sentiment": [dict(r) for r in sentiment],
        "faculty":   [dict(r) for r in faculty],
        "ratings":   [dict(r) for r in ratings],
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
