"""Model database.

Catatan desain penting:
- TransaksiItem menyimpan `nama_produk` dan `harga_satuan` sebagai SNAPSHOT
  saat transaksi terjadi, bukan join langsung ke Produk. Jadi kalau harga
  produk berubah nanti, riwayat transaksi lama tetap akurat.
- Produk pakai soft-delete (`aktif`) supaya FK dari transaksi lama tidak rusak.
"""

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="kasir")  # "admin" / "kasir"

    transaksi = db.relationship("Transaksi", backref="kasir", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Produk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(30), unique=True, nullable=False)
    nama = db.Column(db.String(120), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    harga = db.Column(db.Integer, nullable=False)  # rupiah utuh, tanpa desimal
    stok = db.Column(db.Integer, nullable=False, default=0)
    aktif = db.Column(db.Boolean, nullable=False, default=True)  # soft-delete
    dibuat_pada = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Produk {self.kode} {self.nama}>"


class Transaksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    no_transaksi = db.Column(db.String(30), unique=True, nullable=False)  # TRX-YYYYMMDD-0001
    waktu = db.Column(db.DateTime, nullable=False, default=datetime.now)
    total = db.Column(db.Integer, nullable=False)        # subtotal kotor (sebelum diskon)
    diskon = db.Column(db.Integer, nullable=False, default=0)
    bayar = db.Column(db.Integer, nullable=False)
    kembalian = db.Column(db.Integer, nullable=False)
    kasir_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    items = db.relationship(
        "TransaksiItem", backref="transaksi", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def total_akhir(self):
        """Total yang harus dibayar setelah diskon."""
        return self.total - self.diskon

    @property
    def jumlah_item(self):
        return sum(item.qty for item in self.items)

    def __repr__(self):
        return f"<Transaksi {self.no_transaksi}>"


class TransaksiItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaksi_id = db.Column(db.Integer, db.ForeignKey("transaksi.id"), nullable=False)
    produk_id = db.Column(db.Integer, db.ForeignKey("produk.id"), nullable=False)
    nama_produk = db.Column(db.String(120), nullable=False)   # snapshot
    harga_satuan = db.Column(db.Integer, nullable=False)      # snapshot
    qty = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<TransaksiItem {self.nama_produk} x{self.qty}>"
