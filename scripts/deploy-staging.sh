#!/usr/bin/env bash
#
# Deploy staging — pulls the latest main on the VPS and restarts the Flask service.
#
# Triggered by .github/workflows/deploy-staging.yml on push to main.
# Manual deploy reference: docs/OPERATIONS-VPS.md
#
# Required env vars:
#   STAGING_SSH_KEY  Private SSH key (multiline PEM) for $STAGING_SSH_USER@$STAGING_HOST.
#   STAGING_HOST     Hostname of the VPS, e.g. srv844849.hstgr.cloud.
#
# Optional env vars (defaults from docs/OPERATIONS-VPS.md):
#   STAGING_SSH_USER       SSH user (default: root).
#   STAGING_SSH_PORT       SSH port (default: 22).
#   STAGING_REPO_PATH      Repo path on the VPS (default: /home/training/treini).
#   STAGING_REPO_OWNER     Local user that owns the repo (default: training).
#   STAGING_SERVICE_NAME   systemd unit name (default: training-web).
#   STAGING_BRANCH         Branch to pull (default: main).

set -euo pipefail

: "${STAGING_SSH_KEY:?STAGING_SSH_KEY is required}"
: "${STAGING_HOST:?STAGING_HOST is required}"

SSH_USER="${STAGING_SSH_USER:-root}"
SSH_PORT="${STAGING_SSH_PORT:-22}"
REPO_PATH="${STAGING_REPO_PATH:-/home/training/treini}"
REPO_OWNER="${STAGING_REPO_OWNER:-training}"
SERVICE_NAME="${STAGING_SERVICE_NAME:-training-web}"
BRANCH="${STAGING_BRANCH:-main}"

SSH_DIR="$(mktemp -d)"
trap 'rm -rf "$SSH_DIR"' EXIT

KEY_FILE="$SSH_DIR/id_deploy"
KNOWN_HOSTS="$SSH_DIR/known_hosts"

umask 077
printf '%s' "$STAGING_SSH_KEY" >"$KEY_FILE"
# Some secret stores strip the trailing newline. OpenSSH prefers a final
# newline on private keys; add one if missing.
[ -z "$(tail -c 1 "$KEY_FILE")" ] || printf '\n' >>"$KEY_FILE"
chmod 600 "$KEY_FILE"

echo "==> Capturing host key for $STAGING_HOST:$SSH_PORT (TOFU)"
ssh-keyscan -p "$SSH_PORT" -t ed25519,rsa,ecdsa -H "$STAGING_HOST" >"$KNOWN_HOSTS" 2>/dev/null
if [ ! -s "$KNOWN_HOSTS" ]; then
    echo "ERROR: ssh-keyscan returned no host keys for $STAGING_HOST:$SSH_PORT" >&2
    exit 2
fi

SSH_OPTS=(
    -i "$KEY_FILE"
    -p "$SSH_PORT"
    -o "UserKnownHostsFile=$KNOWN_HOSTS"
    -o "StrictHostKeyChecking=yes"
    -o "BatchMode=yes"
    -o "ConnectTimeout=15"
    -o "ServerAliveInterval=30"
)

REMOTE="$SSH_USER@$STAGING_HOST"

echo "==> Deploying branch '$BRANCH' to $REMOTE:$REPO_PATH (service: $SERVICE_NAME)"

# Locals are expanded into the heredoc; \$(...) defers to the remote shell.
ssh "${SSH_OPTS[@]}" "$REMOTE" bash -s <<REMOTE_SCRIPT
set -euo pipefail

echo "--- git pull (as $REPO_OWNER) ---"
sudo -u "$REPO_OWNER" git -C "$REPO_PATH" fetch --prune origin
sudo -u "$REPO_OWNER" git -C "$REPO_PATH" checkout "$BRANCH"
sudo -u "$REPO_OWNER" git -C "$REPO_PATH" pull --ff-only origin "$BRANCH"
echo "HEAD now at: \$(sudo -u "$REPO_OWNER" git -C "$REPO_PATH" rev-parse HEAD)"

echo "--- pip install -r requirements.txt (idempotent; OPERATIONS-VPS.md step 3) ---"
sudo -u "$REPO_OWNER" "$REPO_PATH/.venv/bin/pip" install --quiet -r "$REPO_PATH/requirements.txt"

echo "--- setup_db.py (idempotent db.create_all; OPERATIONS-VPS.md step 4) ---"
sudo -u "$REPO_OWNER" bash -c "cd '$REPO_PATH' && set -a && . ./.env && set +a && '$REPO_PATH/.venv/bin/python' setup_db.py"

echo "--- systemctl restart $SERVICE_NAME ---"
systemctl restart "$SERVICE_NAME"

echo "--- systemctl is-active $SERVICE_NAME ---"
systemctl is-active "$SERVICE_NAME"
REMOTE_SCRIPT

echo "==> Deploy completed successfully."
