#!/usr/bin/env python3
"""Check desktop HTTP, AliasMode API and preloaded scripts without logging in."""
import json
import time
import urllib.request
from pathlib import Path

def check():
    with urllib.request.urlopen('http://127.0.0.1:6080/vnc.html', timeout=5) as r:
        assert r.status == 200
    with urllib.request.urlopen('http://127.0.0.1:50400/api/v1/status', timeout=5) as r:
        assert json.load(r)['code'] == 0
    rows = json.loads(Path('/data/com.aliasmode.desktop/custom-scripts/local.json').read_text())
    assert {'ig-soft-warmup','ig-active-warmup','ig-soft-smoke-test'} <= {x['name'] for x in rows}

if __name__ == '__main__':
    for attempt in range(90):
        try:
            check()
            print('Desktop, AliasMode API and all three scripts ready.')
            break
        except Exception:
            if attempt == 89: raise
            time.sleep(2)
