# ---- TokoKu Kasir — image untuk menjalankan aplikasi via Docker ----
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////app/data/kasir.db

WORKDIR /app

# 1) Install dependency dulu agar layer cache awet bila hanya kode yang berubah.
#    gunicorn dipasang di sini (server produksi), bukan di requirements.txt,
#    supaya alur clone-and-run biasa tetap ringkas.
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn==23.0.0

# 2) Salin kode aplikasi.
COPY . .

# 3) Siapkan folder data untuk file SQLite (dipisah agar mudah dipersist via
#    volume) dan jalankan sebagai user non-root demi keamanan.
RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/data \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Entrypoint mengisi data demo saat pertama kali jalan, lalu menjalankan server.
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
