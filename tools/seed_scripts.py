#!/usr/bin/env python3
"""Preload private script copies before AliasMode starts; never overwrite edits."""
import argparse
import datetime
import json
import os
import re
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def seed(target, topic):
    target = Path(target)
    rows = json.loads(target.read_text()) if target.exists() else []
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError('Script store must be a JSON list of objects; refusing to overwrite')
    names = {row.get('name') for row in rows}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    for name in ('ig-soft-warmup', 'ig-active-warmup', 'ig-soft-smoke-test'):
        if name in names:
            continue
        source = (ROOT / 'scripts' / (name + '.mjs')).read_text()
        replacement = 'const TOPIC = ' + json.dumps(topic, ensure_ascii=True) + ';'
        source = re.sub(r'^const TOPIC = .*?;$', lambda _: replacement, source, count=1, flags=re.M)
        rows.append(dict(name=name, description='Preloaded by Instagram AliasMode Kit', language='javascript',
                         source=source, id=str(uuid.uuid4()), revision=1, createdAt=now, updatedAt=now))
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix='.scripts-', suffix='.json')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(rows, stream, indent=2)
            stream.write('\n')
        os.chmod(tmp, 0o600)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--topic', default=os.getenv('TOPIC', 'GTA 6, GTA VI, Grand Theft Auto VI, Rockstar Games'))
    args = parser.parse_args()
    seed(args.target, args.topic)
    print('Scripts ready; existing copies preserved.')
