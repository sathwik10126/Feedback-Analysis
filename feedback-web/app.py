"""
University Feedback System — Flask Backend
============================================
Authentication policy:
  - Every account MUST use an official college email (@college.edu).
  - Role is derived automatically from the email's local-part:
        Student  -> roll-number format   (e.g. 21CS045@college.edu)
        Faculty  -> name-only format     (e.g. johnpaul@college.edu)
  - Admin access is NEVER self-assigned at signup. An existing admin must
    explicitly promote a faculty/student account via the Admin Panel.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3, pickle, os, hashlib

from auth_utils import validate_and_detect_role, EmailValidationError, is_valid_college_domain

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "university_feedback_secret_2024")

# ── Paths ────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE, "data", "feedback.db")
MDL_PATH = os.path.join(BASE, "model", "model.pkl")
VEC_PATH = os.path.join(BASE, "model", "vectorizer.pkl")

# ── Load NLP model ───────────────────────────────────────────────────────────
with open(MDL_PATH, "rb") as f:  model      = pickle.load(f)
with open(VEC_PATH, "rb") as f:  vectorizer = pickle.load(f)

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT UNIQUE NOT NULL,
                display_name  TEXT NOT NULL,
                password      TEXT NOT NULL,
                role          TEXT NOT NULL CHECK(role IN ('student','faculty','admin')),
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        # Seed one bootstrap admin account so the system is usable on first run.
        # Password = "Admin@123" — MUST be changed immediately in production.
        pw = hashlib.sha256(b"Admin@123").hexdigest()
        db.execute(
            "INSERT OR IGNORE INTO users (email, display_name, password, role) VALUES (?,?,?,?)",
            ("admin@college.edu", "System Administrator", pw, "admin")
        )

        # Seed faculty (matches the COURSES table below)
        faculty_seed = [
            ("venkataramanav@college.edu", "Venkataramana V"),
            ("shendeamit@college.edu",     "Shende Amit"),
            ("praveen@college.edu",        "Praveen"),
        ]
        for email, name in faculty_seed:
            db.execute(
                "INSERT OR IGNORE INTO users (email, display_name, password, role) VALUES (?,?,?,?)",
                (email, name, pw, "faculty")
            )
        db.commit()

# ── Sentiment (NLP) ──────────────────────────────────────────────────────────
def predict_sentiment(text):
    if not text.strip():
        return "Neutral"
    vec  = vectorizer.transform([text.strip().lower()])
    pred = model.predict(vec)[0]
    return {1: "Positive", 0: "Negative", 2: "Neutral"}.get(pred, "Neutral")

# ── Auth decorator ───────────────────────────────────────────────────────────
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

# ── Page routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template(
        "dashboard.html",
        role=session["role"],
        user=session["display_name"],
        email=session["user"],
    )

# ── API: Auth ────────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    data     = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, pw_hash)
        ).fetchone()

    if not user:
        return jsonify({"success": False, "message": "Invalid college email or password."}), 401

    session["user"]         = user["email"]
    session["role"]         = user["role"]
    session["display_name"] = user["display_name"]
    return jsonify({"success": True, "role": user["role"], "user": user["display_name"]})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/signup", methods=["POST"])
def api_signup():
    """
    Self-service registration is restricted to students and faculty only.
    Role is derived strictly from the official college email format —
    the client never sends a role, and any role value submitted by the
    client is ignored. Admin accounts cannot be created through signup.
    """
    data        = request.json or {}
    email       = data.get("email", "").strip().lower()
    password    = data.get("password", "")
    display_name = data.get("name", "").strip()

    if not email or not password or not display_name:
        return jsonify({"success": False, "message": "Name, college email, and password are all required."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

    try:
        role = validate_and_detect_role(email)
    except EmailValidationError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    with get_db() as db:
        existing = db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            return jsonify({"success": False, "message": "An account with this college email already exists."}), 409

        db.execute(
            "INSERT INTO users (email, display_name, password, role) VALUES (?,?,?,?)",
            (email, display_name, pw_hash, role)
        )
        db.commit()

    session["user"]         = email
    session["role"]         = role
    session["display_name"] = display_name
    return jsonify({"success": True, "role": role, "user": display_name})


@app.route("/api/admin/promote", methods=["POST"])
@login_required(role="admin")
def api_admin_promote():
    """Existing admin grants admin privileges to another college-domain account."""
    data  = request.json or {}
    email = data.get("email", "").strip().lower()

    if not is_valid_college_domain(email):
        return jsonify({"success": False, "message": "Target must be a valid @college.edu account."}), 400

    with get_db() as db:
        target = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not target:
            return jsonify({"success": False, "message": "No account found with that email."}), 404
        db.execute("UPDATE users SET role='admin' WHERE email=?", (email,))
        db.commit()

    return jsonify({"success": True, "message": f"{email} has been granted admin access."})


# ── API: Feedback ────────────────────────────────────────────────────────────
COURSES = [
    {"faculty": "Venkataramana V", "course": "NLP"},
    {"faculty": "Shende Amit",     "course": "Smart Farming"},
    {"faculty": "Praveen",         "course": "Data Structures"},
]

@app.route("/api/courses")
@login_required()
def api_courses():
    return jsonify(COURSES)

@app.route("/api/feedback", methods=["POST"])
@login_required(role="student")
def api_submit_feedback():
    data    = request.json or {}
    faculty = data.get("faculty", "")
    course  = data.get("course", "")
    text    = data.get("feedback", "").strip()
    rating  = int(data.get("rating", 3))

    if not text:
        return jsonify({"success": False, "message": "Feedback text is required."}), 400

    sentiment = predict_sentiment(text)

    with get_db() as db:
        db.execute(
            "INSERT INTO feedback (student,faculty,course,feedback,sentiment,rating) VALUES (?,?,?,?,?,?)",
            (session["display_name"], faculty, course, text, sentiment, rating)
        )
        db.commit()

    label_map = {"Positive": "Good 😊", "Negative": "Bad 😠", "Neutral": "Neutral 😐"}
    return jsonify({"success": True, "sentiment": label_map.get(sentiment, sentiment)})

@app.route("/api/teacher/feedback")
@login_required(role="faculty")
def api_teacher_feedback():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM feedback WHERE faculty=? ORDER BY created_at DESC",
            (session["display_name"],)
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
        total     = db.execute("SELECT COUNT(*) as c FROM feedback").fetchone()["c"]
        avg_rat   = db.execute("SELECT ROUND(AVG(rating),2) as a FROM feedback").fetchone()["a"] or 0
        sentiment = db.execute("SELECT sentiment, COUNT(*) as c FROM feedback GROUP BY sentiment").fetchall()
        faculty   = db.execute("SELECT faculty, ROUND(AVG(rating),2) as avg FROM feedback GROUP BY faculty").fetchall()
        ratings   = db.execute("SELECT rating, COUNT(*) as c FROM feedback GROUP BY rating").fetchall()
    return jsonify({
        "total": total, "avg_rating": avg_rat,
        "sentiment": [dict(r) for r in sentiment],
        "faculty":   [dict(r) for r in faculty],
        "ratings":   [dict(r) for r in ratings],
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)