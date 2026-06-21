"""Isi database dengan data demo.

Jalankan: python seed.py

Membuat:
- 2 user: admin (kelola semua) + kasir (hanya transaksi)
- 9 produk lintas kategori (Minuman / Makanan / Snack)
- Beberapa transaksi contoh selama seminggu terakhir, supaya dashboard &
  riwayat langsung berisi saat aplikasi pertama dibuka.

PERINGATAN: script ini meng-DROP semua tabel lebih dulu (reset penuh).
"""

from datetime import datetime, timedelta

from app import create_app
from extensions import db
from models import Produk, Transaksi, TransaksiItem, User

app = create_app()

# Counter nomor transaksi per tanggal (TRX-YYYYMMDD-0001, 0002, ...)
_counter = {}


def _no_transaksi(waktu):
    key = waktu.strftime("%Y%m%d")
    _counter[key] = _counter.get(key, 0) + 1
    return f"TRX-{key}-{_counter[key]:04d}"


def _round_up(nilai, kelipatan):
    """Bulatkan ke atas ke kelipatan terdekat (untuk nominal bayar realistis)."""
    if nilai % kelipatan == 0:
        return nilai
    return nilai + (kelipatan - nilai % kelipatan)


def buat_transaksi(waktu, kasir, keranjang, diskon=0):
    """keranjang = [(produk, qty), ...]. Hitung total, kurangi stok, simpan."""
    total = sum(p.harga * qty for p, qty in keranjang)
    net = total - diskon
    bayar = _round_up(net, 10000)
    trx = Transaksi(
        no_transaksi=_no_transaksi(waktu),
        waktu=waktu,
        total=total,
        diskon=diskon,
        bayar=bayar,
        kembalian=bayar - net,
        kasir_id=kasir.id,
    )
    db.session.add(trx)
    db.session.flush()
    for p, qty in keranjang:
        db.session.add(
            TransaksiItem(
                transaksi_id=trx.id,
                produk_id=p.id,
                nama_produk=p.nama,
                harga_satuan=p.harga,
                qty=qty,
                subtotal=p.harga * qty,
            )
        )
        p.stok -= qty
    return trx


def seed():
    with app.app_context():
        print("Reset database…")
        db.drop_all()
        db.create_all()

        # --- Users ---
        admin = User(nama="Admin Toko", username="admin", role="admin")
        admin.set_password("admin123")
        kasir = User(nama="Siti (Kasir)", username="kasir", role="kasir")
        kasir.set_password("kasir123")
        db.session.add_all([admin, kasir])
        db.session.flush()

        # --- Produk (kode: nama, kategori, harga, stok) ---
        data_produk = [
            ("MIN-001", "Kopi Susu Gula Aren", "Minuman", 18000, 40),
            ("MIN-002", "Es Teh Manis", "Minuman", 6000, 80),
            ("MIN-003", "Americano", "Minuman", 16000, 35),
            ("MIN-004", "Matcha Latte", "Minuman", 22000, 28),
            ("MKN-001", "Nasi Goreng Spesial", "Makanan", 25000, 30),
            ("MKN-002", "Mie Goreng", "Makanan", 22000, 25),
            ("MKN-003", "Roti Bakar Coklat Keju", "Makanan", 15000, 20),
            ("SNK-001", "Kentang Goreng", "Snack", 13000, 50),
            ("SNK-002", "Pisang Goreng (3 pcs)", "Snack", 10000, 3),   # stok menipis
            ("SNK-003", "Singkong Keju", "Snack", 12000, 5),           # stok menipis
        ]
        produk = {}
        for kode, nama, kat, harga, stok in data_produk:
            p = Produk(kode=kode, nama=nama, kategori=kat, harga=harga, stok=stok)
            produk[kode] = p
            db.session.add(p)
        db.session.flush()

        # --- Transaksi contoh selama 6 hari terakhir + hari ini ---
        # (produk stok menipis sengaja tidak dijual agar tetap muncul di peringatan)
        P = produk
        sekarang = datetime.now()

        def waktu(hari_lalu, jam, menit):
            d = (sekarang - timedelta(days=hari_lalu)).replace(
                hour=jam, minute=menit, second=0, microsecond=0
            )
            return d

        rencana = [
            (6, 8, 15, kasir, [(P["MIN-001"], 2), (P["MKN-003"], 1)], 0),
            (6, 12, 30, admin, [(P["MKN-001"], 1), (P["MIN-002"], 2)], 0),
            (5, 9, 5, kasir, [(P["MIN-003"], 1), (P["SNK-001"], 1)], 0),
            (5, 16, 40, kasir, [(P["MIN-001"], 3), (P["MIN-004"], 1)], 2000),
            (4, 11, 20, admin, [(P["MKN-002"], 2), (P["MIN-002"], 2), (P["SNK-001"], 1)], 0),
            (3, 10, 0, kasir, [(P["MIN-001"], 1), (P["MIN-003"], 2)], 0),
            (3, 19, 10, kasir, [(P["MKN-001"], 2), (P["MKN-003"], 2), (P["MIN-002"], 3)], 5000),
            (2, 13, 45, admin, [(P["MIN-004"], 2), (P["SNK-001"], 2)], 0),
            (1, 8, 50, kasir, [(P["MIN-001"], 2), (P["MIN-002"], 1)], 0),
            (1, 15, 25, kasir, [(P["MKN-002"], 1), (P["MIN-003"], 1), (P["SNK-001"], 1)], 0),
            (0, 9, 30, kasir, [(P["MIN-001"], 2), (P["MKN-003"], 1)], 0),
            (0, 11, 15, admin, [(P["MKN-001"], 1), (P["MIN-002"], 2), (P["MIN-004"], 1)], 0),
            (0, 13, 5, kasir, [(P["MIN-003"], 1), (P["SNK-001"], 1)], 0),
        ]

        for hari_lalu, jam, menit, who, keranjang, diskon in rencana:
            buat_transaksi(waktu(hari_lalu, jam, menit), who, keranjang, diskon)

        db.session.commit()

        jml_trx = Transaksi.query.count()
        jml_produk = Produk.query.count()
        print("Selesai.")
        print(f"  Users   : admin / admin123  (admin)")
        print(f"            kasir / kasir123  (kasir)")
        print(f"  Produk  : {jml_produk}")
        print(f"  Transaksi: {jml_trx}")


if __name__ == "__main__":
    seed()
