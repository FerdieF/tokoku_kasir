"""Instance ekstensi dipisah dari app factory untuk menghindari circular import."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
