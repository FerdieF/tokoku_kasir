"""Helper bersama: decorator auth, format rupiah, generator nomor transaksi."""

from datetime import datetime
from functools import wraps

from flask import abort, flash, redirect, session, url_for


def login_required(view):
    """Redirect ke login kalau belum ada user di session."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    """Batasi akses route hanya untuk role tertentu (mis. admin).

    Tetap mewajibkan login lebih dulu; kalau role tidak cocok -> 403.
    """

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Silakan login terlebih dahulu.", "error")
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def format_rupiah(nilai):
    """1500000 -> 'Rp 1.500.000' (pemisah ribuan gaya Indonesia)."""
    try:
        nilai = int(nilai)
    except (TypeError, ValueError):
        return "Rp 0"
    return "Rp " + f"{nilai:,}".replace(",", ".")


def generate_no_transaksi():
    """Buat nomor transaksi unik berformat TRX-YYYYMMDD-0001 (urut per hari)."""
    # Import lokal supaya tidak terjadi circular import saat modul dimuat.
    from models import Transaksi

    hari_ini = datetime.now().strftime("%Y%m%d")
    prefix = f"TRX-{hari_ini}-"
    terakhir = (
        Transaksi.query.filter(Transaksi.no_transaksi.like(prefix + "%"))
        .order_by(Transaksi.no_transaksi.desc())
        .first()
    )
    urutan = 1
    if terakhir:
        urutan = int(terakhir.no_transaksi.split("-")[-1]) + 1
    return f"{prefix}{urutan:04d}"
