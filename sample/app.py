from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from functools import wraps
import random

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# ---------- DATABASE ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "typing_speed_db"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ---------- TYPING PASSAGES ----------
PASSAGES = [
    {
        "id": "govt_notice",
        "title": "Government Notice",
        "difficulty": "easy",
        "text": "The candidate must carry a valid photo identity card. Reporting time is mandatory. Late entry is not permitted."
    },
    {
        "id": "bank_letter",
        "title": "Bank Letter",
        "difficulty": "easy",
        "text": "Dear customer your account statement is ready. Please visit your nearest branch for further assistance."
    },
    {
        "id": "office_email",
        "title": "Office Email",
        "difficulty": "medium",
        "text": "Hi team please review the updated project schedule and confirm your availability for tomorrow meeting."
    },
    {
        "id": "cyber_security",
        "title": "Cyber Security",
        "difficulty": "hard",
        "text": "Never share passwords or OTP codes with anyone. Always verify the authenticity of suspicious emails."
    },
    {
        "id": "railway_announcement",
        "title": "Railway Announcement",
        "difficulty": "easy",
        "text": "Attention please the train will arrive shortly on platform number two. Passengers are requested to stay behind the yellow line."
    },
    {
        "id": "school_notice",
        "title": "School Notice",
        "difficulty": "easy",
        "text": "All students must wear their identity cards. The library will remain closed on Saturday."
    },
    {
        "id": "office_circular",
        "title": "Office Circular",
        "difficulty": "medium",
        "text": "This is to inform all staff that system maintenance will be conducted tonight. Please save your work."
    }
]


# ---------- LOGIN REQUIRED ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ---------- ADMIN REQUIRED ----------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "username" not in session:
            return redirect(url_for("login"))

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute(
            "SELECT is_admin FROM users WHERE username=%s",
            (session["username"],)
        )

        user = cur.fetchone()

        cur.close()
        db.close()

        if not user or user["is_admin"] != 1:
            return "Access Denied (Admin Only)", 403

        return f(*args, **kwargs)

    return wrapper


# ---------- HOME ----------
@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session["username"])


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )

        user = cur.fetchone()

        cur.close()
        db.close()

        if user:
            session["username"] = user["username"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        try:
            db = get_db()
            cur = db.cursor()

            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s,%s)",
                (username, password)
            )

            db.commit()

            cur.close()
            db.close()

            return redirect(url_for("login"))

        except mysql.connector.errors.IntegrityError:
            return render_template("register.html", error="Username already exists")

    return render_template("register.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


# ---------- GET TYPING PASSAGE ----------
@app.route("/api/get_passage")
@login_required
def get_passage():

    difficulty = request.args.get("difficulty")

    pool = PASSAGES

    if difficulty:
        pool = [p for p in PASSAGES if p["difficulty"] == difficulty]

    if not pool:
        return jsonify({"message": "No passage found"}), 404

    return jsonify(random.choice(pool))


# ---------- SAVE RESULT ----------
@app.route("/api/save_result", methods=["POST"])
@login_required
def save_result():

    data = request.get_json(force=True)
    username = session["username"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO results
        (username, wpm, accuracy, correct_chars, wrong_chars, seconds, word_count, typed_text)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        username,
        int(data["wpm"]),
        float(data["accuracy"]),
        int(data["correct_chars"]),
        int(data["wrong_chars"]),
        int(data["seconds"]),
        int(data["word_count"]),
        data["typed_text"]
    ))

    db.commit()

    cur.close()
    db.close()

    return jsonify({"message": "Result Saved Successfully"})


# ---------- USER RESULTS ----------
@app.route("/results")
@login_required
def results():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM results WHERE username=%s ORDER BY id DESC",
        (session["username"],)
    )

    data = cur.fetchall()

    cur.close()
    db.close()

    return render_template("results.html", results=data)


# ---------- ADMIN PANEL ----------
@app.route("/admin")
@admin_required
def admin_panel():

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id,username,is_admin FROM users ORDER BY id DESC")
    users = cur.fetchall()

    cur.execute("SELECT * FROM results ORDER BY id DESC")
    results = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin.html", users=users, results=results)


# ---------- DELETE USER ----------
@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()

    cur.close()
    db.close()

    return redirect(url_for("admin_panel"))


# ---------- DELETE RESULT ----------
@app.route("/admin/delete_result/<int:rid>", methods=["POST"])
@admin_required
def delete_result(rid):

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM results WHERE id=%s", (rid,))
    db.commit()

    cur.close()
    db.close()

    return redirect(url_for("admin_panel"))


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(debug=True)