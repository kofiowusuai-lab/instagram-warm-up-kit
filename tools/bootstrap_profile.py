#!/usr/bin/env python3
"""Create/open one initial local Firefox profile; never handle Instagram credentials."""
import json
import os
import time
import urllib.parse
import urllib.request

ORIGIN = 'http://127.0.0.1:50400'

def api(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(ORIGIN + path, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    if body.get('code') != 0:
        raise RuntimeError(body.get('msg', 'AliasMode API error'))
    return body.get('data', {})

def ensure_profile(name, call=api):
    page = 1
    while True:
        rows = call('/api/v1/user/list?page=%d&page_size=100' % page).get('list', [])
        matches = [row for row in rows if row.get('name') == name]
        if matches:
            return matches[0]['user_id']
        if len(rows) < 100: break
        page += 1
    result = call('/api/v1/user/create', {'name':name, 'engine':'firefox', 'domain_name':'instagram.com'})
    profile_id = result.get('id') or result.get('user_id')
    if not profile_id: raise RuntimeError('Profile created but no profile ID returned; inspect AliasMode before retrying')
    return profile_id

def main():
    for attempt in range(120):
        try:
            api('/api/v1/status')
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError('AliasMode API is not ready. Open its desktop and finish local-mode onboarding, then rerun bootstrap.')
    name = os.getenv('PROFILE_NAME', 'Instagram-Clips-01')
    profile_id = ensure_profile(name)
    # The URL is a normal browser launch argument, not a cookie or credential.
    params = urllib.parse.urlencode({'user_id':profile_id, 'launch_args':json.dumps(['https://www.instagram.com/'])})
    api('/api/v1/browser/start?' + params)
    print('Instagram profile ready:', name, flush=True)

if __name__ == '__main__': main()
