"""Dashboard: ringkasan penjualan hari ini + stok menipis + produk terlaris."""

from datetime import date, datetime

from sqlalchemy import func

from extensions import db
from flask import Blueprint, render_template
from models import Produk, Transaksi, TransaksiItem
from utils import login_required

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    awal_hari = datetime.combine(date.today(), datetime.min.time())

    transaksi_hari_ini = Transaksi.query.filter(Transaksi.waktu >= awal_hari).all()
    total_hari_ini = sum(t.total_akhir for t in transaksi_hari_ini)
    jumlah_transaksi = len(transaksi_hari_ini)

    produk_aktif = Produk.query.filter_by(aktif=True).count()

    stok_menipis = (
        Produk.query.filter(Produk.aktif.is_(True), Produk.stok <= 5)
        .order_by(Produk.stok.asc())
        .all()
    )

    # Top 5 produk terlaris sepanjang waktu (agregat qty dari snapshot item).
    top_rows = (
        db.session.query(
            TransaksiItem.nama_produk,
            func.sum(TransaksiItem.qty).label("total_qty"),
        )
        .group_by(TransaksiItem.nama_produk)
        .order_by(func.sum(TransaksiItem.qty).desc())
        .limit(5)
        .all()
    )
    max_qty = top_rows[0].total_qty if top_rows else 0

    return render_template(
        "dashboard/index.html",
        total_hari_ini=total_hari_ini,
        jumlah_transaksi=jumlah_transaksi,
        produk_aktif=produk_aktif,
        stok_menipis=stok_menipis,
        top_produk=top_rows,
        max_qty=max_qty,
    )
