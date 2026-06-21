"""Konfigurasi aplikasi.

SECRET_KEY diambil dari environment kalau ada (untuk produksi), kalau tidak
pakai nilai default supaya aplikasi tetap jalan langsung setelah clone.
Database adalah file SQLite di root project (kasir.db).
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-ganti-di-produksi")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "kasir.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
