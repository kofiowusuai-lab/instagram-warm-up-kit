#!/usr/bin/env bash
set -euo pipefail
for attempt in {1..60}; do
  if xdpyinfo >/dev/null 2>&1; then
    exec /opt/aliasmode/bin/aliasmode
  fi
  sleep 1
done
echo 'X display did not start' >&2
exit 1
