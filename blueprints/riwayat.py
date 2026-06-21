"""Riwayat transaksi: daftar + filter tanggal + detail + export CSV (stretch)."""

import csv
import io
from datetime import datetime

from flask import (
    Blueprint,
    Response,
    render_template,
    request,
)

from extensions import db
from models import Transaksi
from utils import login_required

bp = Blueprint("riwayat", __name__, url_prefix="/riwayat")


def _filter_by_tanggal(query, tanggal_str):
    """Terapkan filter tanggal (YYYY-MM-DD) bila valid; abaikan kalau tidak."""
    if not tanggal_str:
        return query
    try:
        d = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
    except ValueError:
        return query
    awal = datetime.combine(d, datetime.min.time())
    akhir = datetime.combine(d, datetime.max.time())
    return query.filter(Transaksi.waktu >= awal, Transaksi.waktu <= akhir)


@bp.route("/")
@login_required
def list():
    tanggal = request.args.get("tanggal", "").strip()
    query = _filter_by_tanggal(Transaksi.query, tanggal)
    transaksi = query.order_by(Transaksi.waktu.desc()).limit(200).all()
    return render_template("riwayat/list.html", transaksi=transaksi, tanggal=tanggal)


@bp.route("/export.csv")
@login_required
def export_csv():
    tanggal = request.args.get("tanggal", "").strip()
    query = _filter_by_tanggal(Transaksi.query, tanggal)
    transaksi = query.order_by(Transaksi.waktu.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["No Transaksi", "Waktu", "Kasir", "Subtotal", "Diskon", "Total", "Bayar", "Kembalian", "Jumlah Item"]
    )
    for t in transaksi:
        writer.writerow(
            [
                t.no_transaksi,
                t.waktu.strftime("%Y-%m-%d %H:%M"),
                t.kasir.nama if t.kasir else "-",
                t.total,
                t.diskon,
                t.total_akhir,
                t.bayar,
                t.kembalian,
                t.jumlah_item,
            ]
        )

    nama_file = "riwayat-transaksi"
    if tanggal:
        nama_file += f"-{tanggal}"
    nama_file += ".csv"

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nama_file}"},
    )


@bp.route("/<int:id>")
@login_required
def detail(id):
    trx = db.get_or_404(Transaksi, id)
    return render_template("riwayat/detail.html", trx=trx)
