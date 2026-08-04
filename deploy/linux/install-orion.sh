#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/musicclean}"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
CONFIG_DIR="${CONFIG_DIR:-/etc/musicclean}"
STATE_DIR="${STATE_DIR:-/var/lib/musicclean}"
LOG_DIR="${LOG_DIR:-/var/log/musicclean}"
SERVICE_NAME="${SERVICE_NAME:-musicclean-orion}"

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "This installer must run as root." >&2
        exit 1
    fi
}

ensure_user() {
    if ! id musicclean >/dev/null 2>&1; then
        useradd --system --create-home --shell /usr/sbin/nologin musicclean
    fi
}

ensure_directories() {
    install -d -o musicclean -g musicclean "$APP_DIR" "$STATE_DIR" "$LOG_DIR"
    install -d -o root -g root "$CONFIG_DIR"
}

install_runtime() {
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    "$VENV_DIR/bin/python" -m pip install "$APP_DIR[orion-runtime]"
}

install_config_if_missing() {
    if [[ ! -f "$CONFIG_DIR/orion.env" ]]; then
        install -m 0600 "$APP_DIR/deploy/orion.env.example" "$CONFIG_DIR/orion.env"
        echo "Created $CONFIG_DIR/orion.env; review API key and host settings before production use."
    fi
}

install_service() {
    install -m 0644 \
        "$APP_DIR/deploy/systemd/musicclean-orion.service" \
        "/etc/systemd/system/${SERVICE_NAME}.service"
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
}

verify_health() {
    local url="${ORION_HEALTH_URL:-http://127.0.0.1:8765/v1/health}"
    "$VENV_DIR/bin/python" - "$url" <<'PY'
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=5) as response:
    if response.status != 200:
        raise SystemExit(f"health check failed with HTTP {response.status}")
PY
}

main() {
    require_root
    ensure_user
    ensure_directories
    install_runtime
    install_config_if_missing
    install_service
    systemctl restart "$SERVICE_NAME"
    verify_health
    echo "Orion deployment completed successfully."
}

main "$@"
