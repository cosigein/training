#!/usr/bin/env bash
set -euo pipefail

VPS_HOST="srv844849.hstgr.cloud"
VPS_USER="training"
VPS_PATH="/home/training/treini"

echo "🚀 Deploy a staging — $(date '+%Y-%m-%d %H:%M:%S')"

ssh -o StrictHostKeyChecking=no \
    -i <(echo "$STAGING_SSH_KEY") \
    "${VPS_USER}@${VPS_HOST}" bash <<'REMOTE'
set -euo pipefail

cd /home/training/treini

echo "📥 git pull..."
git pull --ff-only origin main

echo "📦 pip install..."
.venv/bin/pip install -q -r requirements.txt

echo "🛠️  setup_db (idempotente)..."
.venv/bin/python setup_db.py

echo "🔄 flask db stamp head..."
.venv/bin/flask db stamp head

echo "♻️  reiniciando servicio..."
sudo systemctl restart training-web

echo "✅ deploy listo"
REMOTE
