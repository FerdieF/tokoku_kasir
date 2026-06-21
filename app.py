"""Entry point + app factory.

Jalankan dev server:  flask run     (atau)  python app.py
Sebelum pertama kali jalan, isi data demo:  python seed.py
"""

from flask import Flask, g, render_template, session

from config import Config
from extensions import db
from utils import format_rupiah


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Filter Jinja: {{ harga|rupiah }} -> "Rp 18.000"
    app.jinja_env.filters["rupiah"] = format_rupiah

    # Muat user yang sedang login ke g untuk tiap request (dipakai di template).
    from models import User

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}

    # Daftarkan blueprint.
    from blueprints.auth import bp as auth_bp
    from blueprints.dashboard import bp as dashboard_bp
    from blueprints.kasir import bp as kasir_bp
    from blueprints.produk import bp as produk_bp
    from blueprints.riwayat import bp as riwayat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(produk_bp)
    app.register_blueprint(kasir_bp)
    app.register_blueprint(riwayat_bp)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    # Buat tabel kalau belum ada (aman dipanggil berkali-kali).
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
