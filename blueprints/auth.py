"""Login & logout (session-based)."""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    # Sudah login? langsung ke dashboard.
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            session["nama"] = user.nama
            return redirect(url_for("dashboard.index"))

        # Pesan generik: jangan bocorkan apakah username atau password yang salah.
        flash("Username atau password salah.", "error")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Anda telah keluar.", "success")
    return redirect(url_for("auth.login"))
