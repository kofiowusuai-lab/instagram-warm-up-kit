#!/usr/bin/env bash
set -euo pipefail
umask 077
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
chmod 700 "$XDG_RUNTIME_DIR"
python3 /opt/kit/tools/seed_scripts.py --target /data/com.aliasmode.desktop/custom-scripts/local.json
exec dbus-run-session -- supervisord -n -c /opt/kit/container/supervisord.conf
