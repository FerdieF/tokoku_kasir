#!/bin/sh
# Entrypoint container: isi data demo HANYA saat pertama kali (DB belum ada),
# lalu jalankan perintah utama (gunicorn). Dengan begitu, kalau folder /app/data
# dipersist lewat volume, data tidak ke-reset setiap kali container restart.
set -e

DB_FILE="/app/data/kasir.db"

if [ ! -f "$DB_FILE" ]; then
    echo "[entrypoint] Database belum ada — mengisi data demo (seed)…"
    python seed.py
else
    echo "[entrypoint] Database sudah ada — seeding dilewati."
fi

echo "[entrypoint] Menjalankan: $*"
exec "$@"
