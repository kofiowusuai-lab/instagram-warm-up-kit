#!/usr/bin/env python3
"""Register the version-pinned readiness fix in an existing Phone Harness workspace."""
import argparse
import os
from pathlib import Path
import tempfile
import uuid

MARKER = '# Instagram warm-up mirroring readiness compatibility'


def register(workspace):
    workspace = Path(workspace).resolve()
    target = workspace / 'agent_helpers.py'
    if not target.is_file() or target.is_symlink():
        raise ValueError('Select the existing Phone Harness workspace with a regular agent_helpers.py')
    original = target.read_text()
    module = Path(__file__).resolve().with_name('mirroring_readiness.py')
    block = f'''{MARKER}
import importlib.util as _ig_import_util
_ig_spec = _ig_import_util.spec_from_file_location('_ig_mirroring_readiness', {str(module)!r})
_ig_module = _ig_import_util.module_from_spec(_ig_spec)
_ig_spec.loader.exec_module(_ig_module)
_ig_module.install()
'''
    if MARKER in original:
        if block not in original: raise ValueError('Existing compatibility registration differs; review before editing')
        return None
    updated = original.rstrip() + '\n\n' + block
    compile(updated, str(target), 'exec')
    backup = workspace / ('agent_helpers.pre-readiness-' + uuid.uuid4().hex + '.bak')
    backup.write_text(original); backup.chmod(0o600)
    fd, temporary = tempfile.mkstemp(dir=workspace, prefix='.readiness-')
    try:
        with os.fdopen(fd, 'w') as f: f.write(updated)
        os.chmod(temporary, 0o600); os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return backup


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    backup = register(parser.parse_args().workspace)
    print('Registered; rollback backup: ' + str(backup) if backup else 'Already registered; no changes')
