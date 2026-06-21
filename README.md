# TokoKu Kasir — Aplikasi Kasir (POS) Web

Aplikasi **Point of Sale** sederhana untuk toko/UMKM kecil (warung, kafe). Kasir bisa login, memilih produk, melakukan transaksi, mencetak struk, dan melihat riwayat penjualan — lengkap dengan manajemen produk dan dashboard ringkasan. Dibuat dengan Flask + server-rendered Jinja2, tanpa framework CSS, dengan tema visual "struk kasir".

> Server-rendered, bukan SPA — sengaja dibuat agar scope realistis dan mudah di-review langsung dari source code.

## Tangkapan layar

> **TODO:** tambahkan screenshot setelah dijalankan. Halaman yang paling layak difoto:
> - `/kasir` — panel keranjang bergaya struk thermal (halaman signature)
> - `/` — dashboard dengan bar chart produk terlaris
> - `/kasir/struk/<id>` — struk siap cetak
>
> Letakkan gambar di `docs/` lalu tautkan di sini, mis. `![Halaman Kasir](docs/kasir.png)`.

## Fitur

- **Login / logout** berbasis session, password di-hash (`werkzeug.security`).
- **Manajemen produk** — list, pencarian, tambah, edit (kode dikunci), dan *soft-delete* agar riwayat lama tetap valid.
- **Kasir / POS** — grid produk yang bisa difilter per kategori & dicari, keranjang bergaya struk dengan *dotted leader*, diskon, tombol nominal cepat, dan kembalian dihitung langsung.
- **Checkout aman** — stok, harga, dan jumlah bayar **divalidasi ulang di server**; pembuatan transaksi + pengurangan stok berjalan dalam satu transaction DB.
- **Struk** siap cetak (`window.print()` + CSS `@media print`, navbar otomatis disembunyikan).
- **Riwayat transaksi** — daftar + filter tanggal + halaman detail, dengan harga & nama produk disimpan sebagai *snapshot*.
- **Dashboard** — penjualan hari ini, jumlah transaksi, produk aktif, peringatan stok menipis, dan Top 5 produk terlaris (bar chart CSS murni, tanpa library).

### Fitur tambahan (stretch goals)

- **Role admin vs kasir** — hanya admin yang bisa mengelola produk; kasir hanya bertransaksi (dipaksa di server, akses ditolak → 403).
- **Export riwayat ke CSV** (mengikuti filter tanggal yang aktif).
- **Diskon per transaksi** (ikut tercatat & tampil di struk).
- **Dark mode** dengan preferensi disimpan di browser.

## Tech stack

| Bagian     | Teknologi                                              |
|------------|--------------------------------------------------------|
| Backend    | Python, Flask (app factory + Blueprints)               |
| Database   | SQLite via Flask-SQLAlchemy                            |
| Auth       | Session-based, `werkzeug.security` untuk hash password |
| Frontend   | Jinja2 server-rendered + CSS murni + vanilla JS        |
| Font       | Space Grotesk, IBM Plex Sans, IBM Plex Mono            |

## Cara menjalankan

```bash
# 1. Clone
git clone <url-repo-anda> tokoku-kasir
cd tokoku-kasir

# 2. Virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependency
pip install -r requirements.txt

# 4. Isi data demo (user + produk + transaksi contoh)
python seed.py

# 5. Jalankan
flask run
# atau: python app.py
```

Buka **http://127.0.0.1:5000**.

## Menjalankan dengan Docker

Cara paling cepat (memakai `docker-compose.yml` yang sudah disediakan):

```bash
docker compose up --build
```

Atau pakai Docker langsung tanpa compose:

```bash
docker build -t tokoku-kasir .
docker run -p 5000:5000 -v kasir-data:/app/data tokoku-kasir
```

Lalu buka **http://localhost:5000**.

Catatan:

- Data demo otomatis di-*seed* saat container **pertama kali** dijalankan (lihat `docker-entrypoint.sh`). Saat restart, data tidak di-reset.
- Database SQLite disimpan di volume `kasir-data` (`/app/data`) supaya persist antar-restart. Hapus volume itu (`docker volume rm kasir-data`) bila ingin mulai dari nol.
- Server dijalankan dengan **gunicorn** (bukan dev server Flask), dan sebagai user non-root.
- Atur `SECRET_KEY` lewat environment variable untuk produksi (sudah disiapkan di `docker-compose.yml`).

## Kredensial demo

| Username | Password   | Role  | Bisa kelola produk? |
|----------|------------|-------|---------------------|
| `admin`  | `admin123` | admin | Ya                  |
| `kasir`  | `kasir123` | kasir | Tidak (hanya transaksi) |

## Struktur folder

```
tokoku-kasir/
├── app.py              # app factory + entry point
├── config.py
├── extensions.py       # instance db = SQLAlchemy()
├── models.py           # User, Produk, Transaksi, TransaksiItem
├── utils.py            # login_required, role_required, format_rupiah, generate_no_transaksi
├── seed.py             # data demo
├── requirements.txt
├── Dockerfile          # image (gunicorn, user non-root)
├── docker-compose.yml  # port 5000 + volume data
├── docker-entrypoint.sh
├── blueprints/         # auth, dashboard, produk, kasir, riwayat
├── templates/          # base + halaman (Jinja2)
└── static/             # css/style.css, js/kasir.js
```

## Catatan desain

- **Snapshot harga** — `TransaksiItem` menyimpan `nama_produk` dan `harga_satuan` saat transaksi terjadi, bukan join langsung ke `Produk`. Jadi kalau harga produk berubah nanti, riwayat lama tetap akurat.
- **Soft-delete** — produk dinonaktifkan (`aktif = False`), tidak dihapus permanen, supaya FK dari transaksi lama tidak rusak.
- **Jangan percaya client** — angka dari JavaScript hanya untuk tampilan; semua dihitung ulang dari DB saat checkout.

## Roadmap (undone)

- Belum ada **proteksi CSRF** pada form & endpoint checkout (diabaikan demi menjaga scope tetap ringkas).
- Belum ada **multi-cabang / multi-toko**.
- Belum ada **manajemen user dari UI** (user dibuat lewat `seed.py`).
- Belum ada **laporan periodik / export ke Excel** (baru CSV sederhana).
- Belum ada **pagination** di riwayat (dibatasi 200 transaksi terbaru).
- Belum ada **test otomatis** terpisah (validasi diverifikasi manual saat pengembangan).

## Lisensi

Bebas dipakai sebagai referensi / portfolio.
