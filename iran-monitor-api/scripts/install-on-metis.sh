#!/bin/bash
# Deploy iran-monitor-api on the Metis VPS.
# Idempotent — safe to re-run.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api}"
SYSTEMD_DIR="/etc/systemd/system"
ENV_FILE="$HOME/.config/iran-monitor-api.env"

if [[ ! -d "$REPO_DIR" ]]; then
    echo "ERROR: $REPO_DIR not found. Pull jf-private first." >&2
    exit 1
fi

cd "$REPO_DIR"
echo "==> Installing dependencies via uv"
uv sync

echo "==> Provisioning signing key (if missing)"
mkdir -p "$REPO_DIR/keys"
if [[ ! -f "$REPO_DIR/keys/signing-key.bin" ]]; then
    uv run iran-monitor-generate-key
else
    echo "    signing key already present"
fi

echo "==> Provisioning env file (if missing)"
mkdir -p "$(dirname "$ENV_FILE")"
if [[ ! -f "$ENV_FILE" ]]; then
    cat > "$ENV_FILE" <<'EOF'
# Iran Monitor Inference API — env
IRAN_API_HOST=127.0.0.1
IRAN_API_PORT=8080
IRAN_API_BASE_DIR=/home/deploy/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api/data
IRAN_API_SIGNING_KEY_PATH=/home/deploy/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api/keys/signing-key.bin
IRAN_API_SIGNING_PUB_KEY_PATH=/home/deploy/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api/keys/signing-key.pub
IRAN_API_IRAN_MONITOR_REPO=/home/deploy/jf-private/jf-thought/sgept-analytics/iran-monitor

# Replace with SOPS-decrypted JSON in production
IRAN_API_API_KEYS_JSON={"REPLACE-WITH-PILOT-KEY":"REPLACE-WITH-ORG-ID"}
EOF
    chmod 600 "$ENV_FILE"
    echo "    wrote $ENV_FILE — populate API_KEYS_JSON before starting!"
fi

echo "==> Installing systemd units"
sudo cp "$REPO_DIR/systemd/iran-monitor-api.service" "$SYSTEMD_DIR/"
sudo cp "$REPO_DIR/systemd/iran-monitor-worker.service" "$SYSTEMD_DIR/"
sudo systemctl daemon-reload

echo "==> Done. To activate:"
echo "    sudo systemctl enable --now iran-monitor-api iran-monitor-worker"
echo "    sudo systemctl status iran-monitor-api iran-monitor-worker"
echo
echo "Hook the cron's Phase 6 to seal intel-base hash:"
echo "    cd /home/deploy/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api"
echo "    uv run iran-monitor-seal-intel-base"
