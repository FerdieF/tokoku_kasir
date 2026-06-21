"""Halaman POS + checkout + struk.

Checkout sengaja TIDAK mempercayai angka dari client: harga & stok divalidasi
ulang dari DB, dan semua perubahan (buat transaksi + kurangi stok) terjadi dalam
satu transaction DB sehingga kalau gagal di tengah, tidak ada yang setengah jadi.
"""

from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
)

from extensions import db
from models import Produk, Transaksi, TransaksiItem
from utils import generate_no_transaksi, login_required

bp = Blueprint("kasir", __name__, url_prefix="/kasir")


@bp.route("/")
@login_required
def index():
    produk = (
        Produk.query.filter_by(aktif=True)
        .order_by(Produk.kategori.asc(), Produk.nama.asc())
        .all()
    )
    kategori = sorted({p.kategori for p in produk})
    return render_template("kasir/index.html", produk=produk, kategori=kategori)


@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    data = request.get_json(silent=True) or {}
    items = data.get("items")

    if not isinstance(items, list) or not items:
        return jsonify({"error": "Keranjang kosong."}), 400

    try:
        bayar = int(data.get("bayar", 0))
        diskon = int(data.get("diskon", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Nilai bayar/diskon tidak valid."}), 400

    if bayar < 0 or diskon < 0:
        return jsonify({"error": "Nilai bayar/diskon tidak boleh negatif."}), 400

    # --- Validasi ulang tiap item dari DB (jangan percaya harga/qty dari client) ---
    total = 0
    baris = []  # (produk, qty, subtotal)
    for it in items:
        produk_id = it.get("produk_id")
        try:
            qty = int(it.get("qty", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "Qty tidak valid."}), 400
        if qty <= 0:
            return jsonify({"error": "Qty harus lebih dari 0."}), 400

        produk = db.session.get(Produk, produk_id)
        if produk is None or not produk.aktif:
            return jsonify({"error": "Produk tidak ditemukan / nonaktif."}), 400
        if qty > produk.stok:
            return jsonify(
                {"error": f"Stok '{produk.nama}' tidak cukup (tersisa {produk.stok})."}
            ), 400

        subtotal = produk.harga * qty
        total += subtotal
        baris.append((produk, qty, subtotal))

    if diskon > total:
        return jsonify({"error": "Diskon melebihi total belanja."}), 400

    net = total - diskon
    if bayar < net:
        return jsonify({"error": "Jumlah bayar kurang dari total."}), 400

    # --- Semua valid: tulis dalam satu transaction DB ---
    trx = Transaksi(
        no_transaksi=generate_no_transaksi(),
        waktu=datetime.now(),
        total=total,
        diskon=diskon,
        bayar=bayar,
        kembalian=bayar - net,
        kasir_id=session["user_id"],
    )
    db.session.add(trx)
    db.session.flush()  # dapatkan trx.id sebelum insert child rows

    for produk, qty, subtotal in baris:
        db.session.add(
            TransaksiItem(
                transaksi_id=trx.id,
                produk_id=produk.id,
                nama_produk=produk.nama,    # snapshot
                harga_satuan=produk.harga,  # snapshot
                qty=qty,
                subtotal=subtotal,
            )
        )
        produk.stok -= qty  # kurangi stok

    db.session.commit()
    return jsonify({"transaksi_id": trx.id})


@bp.route("/struk/<int:id>")
@login_required
def struk(id):
    trx = db.get_or_404(Transaksi, id)
    return render_template("kasir/struk.html", trx=trx)
