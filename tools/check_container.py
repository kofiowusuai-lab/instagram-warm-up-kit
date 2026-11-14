#!/usr/bin/env python3
"""Check desktop HTTP, AliasMode API and preloaded scripts without logging in."""
import json
import os
import urllib.parse
import time
import urllib.request
from pathlib import Path

def check():
    with urllib.request.urlopen('http://127.0.0.1:6080/vnc.html', timeout=5) as r:
        assert r.status == 200
    with urllib.request.urlopen('http://127.0.0.1:50400/api/v1/status', timeout=5) as r:
        assert json.load(r)['code'] == 0
    matches = []
    page = 1
    while not matches:
        url = 'http://127.0.0.1:50400/api/v1/user/list?page_size=100&page=%d' % page
        with urllib.request.urlopen(url, timeout=5) as r:
            profiles = json.load(r)['data']['list']
        matches = [p for p in profiles if p['name'] == os.getenv('PROFILE_NAME', 'Instagram-Clips-01')]
        if len(profiles) < 100: break
        page += 1
    assert matches, 'Initial profile has not been created'
    query = urllib.parse.urlencode({'user_id':matches[0]['user_id']})
    with urllib.request.urlopen('http://127.0.0.1:50400/api/v1/browser/active?' + query, timeout=5) as r:
        state = json.load(r)
    assert state['code'] == 0 and state['data']['status'] == 'Active', 'Initial browser is not active'
    rows = json.loads(Path('/data/com.aliasmode.desktop/custom-scripts/local.json').read_text())
    assert {'ig-soft-warmup','ig-active-warmup','ig-soft-smoke-test'} <= {x['name'] for x in rows}

if __name__ == '__main__':
    for attempt in range(90):
        try:
            check()
            print('Desktop, AliasMode API, initial browser and all three scripts ready.')
            break
        except Exception:
            if attempt == 89: raise
            time.sleep(2)
