from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------
# BASE DE DATOS
# -------------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return redirect("/login")


# -------------------------
# REGISTRO
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            db.commit()
        except:
            return "Error: usuario ya existe"

        return redirect("/login")

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/dashboard")

        return "Credenciales incorrectas"

    return render_template("login.html")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    backups = db.execute(
        "SELECT * FROM backups WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    return render_template("dashboard.html", backups=backups)


# -------------------------
# SUBIR BACKUP
# -------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if "user_id" not in session:
        return redirect("/login")

    file = request.files["file"]

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    db = get_db()
    db.execute(
        "INSERT INTO backups (user_id, filename, filepath) VALUES (?, ?, ?)",
        (session["user_id"], file.filename, filepath)
    )
    db.commit()

    return redirect("/dashboard")


# -------------------------
# DESCARGAR BACKUP
# -------------------------
@app.route("/download/<int:id>")
def download(id):
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    backup = db.execute(
        "SELECT filepath, filename FROM backups WHERE id=? AND user_id=?",
        (id, session["user_id"])
    ).fetchone()

    if backup:
        return send_file(
            backup["filepath"],
            as_attachment=True,
            download_name=backup["filename"]
        )

    return "Archivo no encontrado", 404


# -------------------------
# BORRAR BACKUP
# -------------------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    backup = db.execute(
        "SELECT filepath FROM backups WHERE id=? AND user_id=?",
        (id, session["user_id"])
    ).fetchone()

    if backup:
        if os.path.exists(backup["filepath"]):
            os.remove(backup["filepath"])

        db.execute(
            "DELETE FROM backups WHERE id=?",
            (id,)
        )
        db.commit()

    return redirect("/dashboard")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)