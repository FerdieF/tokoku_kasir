"""CRUD produk. Seluruh modul ini dibatasi untuk role admin (stretch goal).

Kasir tidak bisa mengelola maupun melihat daftar produk; akses langsung via
URL akan ditolak dengan 403, konsisten dengan menu yang disembunyikan di navbar.
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from extensions import db
from models import Produk
from utils import role_required

bp = Blueprint("produk", __name__, url_prefix="/produk")


def _validasi_form(form, kode_lama=None):
    """Validasi input form produk. Return (data_bersih, list_error)."""
    errors = []
    kode = form.get("kode", "").strip()
    nama = form.get("nama", "").strip()
    kategori = form.get("kategori", "").strip()
    harga_raw = form.get("harga", "").strip()
    stok_raw = form.get("stok", "").strip()

    if not kode:
        errors.append("Kode produk wajib diisi.")
    elif kode != kode_lama:
        # Pastikan kode unik (kecuali memang kode lama saat edit).
        if Produk.query.filter_by(kode=kode).first():
            errors.append(f"Kode '{kode}' sudah dipakai produk lain.")

    if not nama:
        errors.append("Nama produk wajib diisi.")
    if not kategori:
        errors.append("Kategori wajib diisi.")

    harga = 0
    try:
        harga = int(harga_raw)
        if harga < 0:
            errors.append("Harga tidak boleh negatif.")
    except (TypeError, ValueError):
        errors.append("Harga harus berupa angka.")

    stok = 0
    try:
        stok = int(stok_raw)
        if stok < 0:
            errors.append("Stok tidak boleh negatif.")
    except (TypeError, ValueError):
        errors.append("Stok harus berupa angka.")

    data = {"kode": kode, "nama": nama, "kategori": kategori, "harga": harga, "stok": stok}
    return data, errors


@bp.route("/")
@role_required("admin")
def list():
    q = request.args.get("q", "").strip()
    query = Produk.query.filter_by(aktif=True)
    if q:
        query = query.filter(Produk.nama.ilike(f"%{q}%"))
    produk = query.order_by(Produk.nama.asc()).all()
    return render_template("produk/list.html", produk=produk, q=q)


@bp.route("/tambah", methods=["GET", "POST"])
@role_required("admin")
def tambah():
    if request.method == "POST":
        data, errors = _validasi_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("produk/form.html", mode="tambah", produk=data)

        produk = Produk(**data)
        db.session.add(produk)
        db.session.commit()
        flash(f"Produk '{produk.nama}' ditambahkan.", "success")
        return redirect(url_for("produk.list"))

    return render_template("produk/form.html", mode="tambah", produk=None)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit(id):
    produk = db.get_or_404(Produk, id)

    if request.method == "POST":
        # Kode tidak boleh diubah setelah dibuat -> pakai kode lama.
        data, errors = _validasi_form(request.form, kode_lama=produk.kode)
        if errors:
            for e in errors:
                flash(e, "error")
            data["kode"] = produk.kode  # kunci kode di form
            data["id"] = produk.id
            return render_template("produk/form.html", mode="edit", produk=data)

        produk.nama = data["nama"]
        produk.kategori = data["kategori"]
        produk.harga = data["harga"]
        produk.stok = data["stok"]
        db.session.commit()
        flash(f"Produk '{produk.nama}' diperbarui.", "success")
        return redirect(url_for("produk.list"))

    return render_template("produk/form.html", mode="edit", produk=produk)


@bp.route("/<int:id>/hapus", methods=["POST"])
@role_required("admin")
def hapus(id):
    """Soft-delete: set aktif=False agar riwayat transaksi lama tetap valid."""
    produk = db.get_or_404(Produk, id)
    produk.aktif = False
    db.session.commit()
    flash(f"Produk '{produk.nama}' dinonaktifkan.", "success")
    return redirect(url_for("produk.list"))
