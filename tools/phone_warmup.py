#!/usr/bin/env python3
"""Opt-in local iPhone passive sessions; no credentials, active engagement or cloud fallback."""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
import uuid
from zoneinfo import ZoneInfo

from phone_harness_client import PhoneHarnessClient

FILES = ('SOP.md', 'progress.md', 'schedule.md', 'warnings.md', 'settings.json')
LOCK = Path.home() / '.instagram-warmup' / 'personal-iphone.lock'
READY = 'ready_for_authorized_soft_runs'
WARNING = re.compile(r'we limit how often|try again later|confirm (?:that )?it.s you|'
                     r'unusual activity|account (?:has been )?suspended|challenge required|'
                     r'you can.t make this change|verify your identity|use face scan|'
                     r'enter (?:the |your )?(?:security|confirmation|authentication) code', re.I)


class StopSession(Exception):
    def __init__(self, status): self.status = status


def atomic_json(path, value):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.phone-')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2); f.write('\n')
        os.chmod(tmp, 0o600); os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def load_account(account):
    for name in FILES: (account / name).read_text()
    return json.loads((account / 'settings.json').read_text())


def validate(config):
    phone = config.get('phone', {})
    if config.get('execution_backend') != 'phone-harness':
        raise ValueError('Choose execution_backend phone-harness explicitly')
    if (config.get('account_status') != READY or config.get('agent_engagement_enabled') is not True
            or config.get('schedule_approved') is not True):
        raise ValueError('Account is paused or lacks explicit routine authorization')
    if config.get('reported_warning_status') not in ('none_reported', 'resolved'):
        raise ValueError('Resolve the recorded warning through the official flow before resuming')
    if not config.get('timezone') or not config.get('warmup_start_date'):
        raise ValueError('Confirm account timezone and start date')
    today = datetime.now(ZoneInfo(config['timezone'])).date()
    if date.fromisoformat(config['warmup_start_date']) > today:
        raise ValueError('Account routine has not started')
    if (phone.get('enabled') is not True or phone.get('platform') != 'ios'
            or phone.get('mode') != 'soft' or config.get('active_mode_enabled')):
        raise ValueError('Phone backend supports explicitly enabled local iOS soft mode only')
    username = phone.get('expected_username', '')
    if not re.fullmatch(r'[A-Za-z0-9._]{1,30}', username):
        raise ValueError('Set the exact Instagram username, without @')
    if not isinstance(config.get('topic'), str) or not config['topic'].strip():
        raise ValueError('Set comma-separated topic phrases for selective dwell')
    executable = phone.get('harness_executable', '')
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        raise ValueError('Set an absolute Phone Harness executable path')
    calibration = phone.get('calibration') or {}
    ratio = calibration.get('aspect_ratio', 0)
    if not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or not 0.3 < ratio < 0.9:
        raise ValueError('Calibrate the portrait mirroring layout first')
    for name in ('profile', 'reels'):
        point = calibration.get(name)
        if (not isinstance(point, list) or len(point) != 2
                or any(type(v) not in (float, int) or not math.isfinite(v) for v in point)
                or not 0 < point[0] < 1 or not 0.85 < point[1] < 1):
            raise ValueError('Calibrate bottom-navigation Profile and Reels icon positions')
    minutes = config.get('schedule', {}).get('session_minutes', 0)
    dwell = phone.get('dwell_seconds', 15)
    max_items = phone.get('max_items', 60)
    if type(minutes) not in (int, float) or not math.isfinite(minutes) or not 0 < minutes <= 20:
        raise ValueError('Session budget must be greater than zero and at most 20 minutes')
    if type(dwell) not in (int, float) or not math.isfinite(dwell) or not 5 <= dwell <= 60:
        raise ValueError('dwell_seconds must be 5..60')
    if type(max_items) is not int or not 1 <= max_items <= 100:
        raise ValueError('max_items must be 1..100')
    return phone


@contextmanager
def device_lock(path=LOCK):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        os.chmod(path, 0o600)
        try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise StopSession('device_busy') from None
        try: yield
        finally: fcntl.flock(handle, fcntl.LOCK_UN)


def texts(observation):
    return [b['text'].strip() for b in observation.get('boxes', [])
            if isinstance(b.get('text'), str) and b.get('confidence', 0) >= 0.8]


def profile_matches(observation, username):
    bounds = observation.get('bounds') or {}
    if not bounds.get('h'): return False
    labels = {t.lower() for t in texts(observation)}
    if not all(name in labels for name in ('posts', 'followers', 'following', 'edit profile')): return False
    # A feed mention or display name alone never establishes the signed-in account.
    top = [b for b in observation.get('boxes', [])
           if b.get('confidence', 0) >= 0.9
           and bounds.get('y', 0) <= b.get('y', -1) < bounds.get('y', 0) + bounds['h'] * .3]
    matches = [b for b in top if b.get('text', '').strip().lower().lstrip('@') == username.lower()]
    return len(matches) == 1


def fingerprint(observation):
    return hashlib.sha256(json.dumps(texts(observation)).encode()).hexdigest()


def topic_matches(observation, topic):
    visible = ' '.join(texts(observation)).casefold()
    return any(re.search(r'(?<!\w)' + re.escape(phrase.strip().casefold()) + r'(?!\w)', visible)
               for phrase in topic.split(',') if phrase.strip())


def pause_warning(account):
    # Re-read rather than overwriting user edits made while a session was running.
    c = load_account(account)
    c.update(account_status='paused_possible_phone_warning', reported_warning_status='possible_checkpoint',
             agent_engagement_enabled=False, scheduler_enabled=False)
    atomic_json(account / 'settings.json', c)
    with (account / 'warnings.md').open('a') as f:
        f.write('\n## Phone session possible warning — ' + datetime.now(timezone.utc).isoformat()
                + '\n\nOCR observed possible restriction/authentication text. Automation paused; '
                'review the phone and follow Instagram official instructions. This is not a confirmed '
                'restriction; raw screen text is intentionally not retained. No automatic recovery.\n')


def run_session(account, client=None, clock=time.monotonic, sleep=time.sleep, lock_path=LOCK, preflight=False):
    account = Path(account).resolve()
    started = datetime.now(timezone.utc).isoformat()
    result = {'status': 'blocked', 'started_at': started, 'backend': 'phone-harness',
              'counts_source': 'observed_phone_ui_not_verified_playback',
              'reported_counts': {'reels': None, 'likes': 0, 'follows': 0, 'saves': 0,
                                  'comments': 0, 'dms': 0, 'profile_visits': None, 'stories': None},
              'observations': {'screens_observed': 0, 'feed_changes': 0, 'dwell_seconds': 0,
                               'topic_matches': 0, 'topic_misses': 0}}
    try:
        initial = load_account(account); phone = validate(initial)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result['reason'] = str(error); return result
    client = client or PhoneHarnessClient(phone['harness_executable'])
    deadline = clock() + initial['schedule']['session_minutes'] * 60
    original = json.dumps(initial, sort_keys=True)

    def guard():
        if clock() >= deadline: raise StopSession('finished')
        try: fresh = load_account(account); validate(fresh)
        except (ValueError, KeyError, TypeError, OSError): raise StopSession('paused') from None
        if json.dumps(fresh, sort_keys=True) != original:
            raise StopSession('paused')  # No identity/mode/calibration changes mid-session.

    def call(op, **kw):
        guard()
        return client.call(op, timeout=min(30, deadline - clock()), **kw)

    def observe():
        observation = call('observe')
        if WARNING.search(' '.join(texts(observation))):
            pause_warning(account)  # Persist before another device call can fail.
            raise StopSession('paused_warning')
        if not texts(observation): raise StopSession('ambiguous_screen')
        result['observations']['screens_observed'] += 1
        return observation

    def dwell(seconds):
        end = min(deadline, clock() + seconds)
        while clock() < end:
            guard(); before = clock(); sleep(min(1, end - before))
            result['observations']['dwell_seconds'] += clock() - before

    try:
        with device_lock(lock_path):
            call('ensure'); call('open')
            previous = None
            for _ in range(phone.get('max_items', 60)):
                # Never tap an arbitrary resumed screen (it might be a DM composer).
                # The user leaves their own Profile open; completed cycles return there.
                if not profile_matches(observe(), phone['expected_username']):
                    raise StopSession('identity_mismatch')
                if preflight: raise StopSession('ready')
                call('anchor', name='reels', calibration=phone['calibration'])
                feed = observe()
                if 'reels' not in {t.lower() for t in texts(feed)}:
                    raise StopSession('ambiguous_screen')
                if previous is not None:
                    call('scroll'); feed = observe()
                    if 'reels' not in {t.lower() for t in texts(feed)}:
                        raise StopSession('ambiguous_screen')
                current = fingerprint(feed)
                if current == previous: raise StopSession('unchanged_screen')
                if previous is not None: result['observations']['feed_changes'] += 1
                previous = current
                if topic_matches(feed, initial['topic']):
                    result['observations']['topic_matches'] += 1
                    dwell(phone.get('dwell_seconds', 15))
                else:
                    result['observations']['topic_misses'] += 1
                after = observe()  # Catch a warning during dwell before any next input.
                if 'reels' not in {t.lower() for t in texts(after)}:
                    raise StopSession('ambiguous_screen')
                call('anchor', name='profile', calibration=phone['calibration'])
                if not profile_matches(observe(), phone['expected_username']):
                    raise StopSession('identity_mismatch')
            result['status'] = 'finished' if result['observations']['topic_matches'] else 'no_topic_matches'
    except StopSession as stop:
        result['status'] = stop.status
    except TimeoutError:
        result['status'] = 'incomplete'; result['reason'] = 'Device operation timed out; no retry'
    except Exception:
        result['status'] = 'failed'; result['reason'] = 'Device unavailable or unsupported layout; inspect phone and run doctor'
    result['finished_at'] = datetime.now(timezone.utc).isoformat()
    if result['status'] == 'device_busy': return result
    result['evidence'] = 'phone-runs/' + uuid.uuid4().hex + '.json'
    directory = account / 'phone-runs'; directory.mkdir(mode=0o700, exist_ok=True)
    atomic_json(account / result['evidence'], result)
    with (account / 'progress.md').open('a') as f:
        f.write('\n## Passive phone session — ' + started + '\n\nOutcome: ' + result['status']
                + '. Evidence: ' + result['evidence'] + '. Reels watched remain unreported; '
                'observed dwell and screen changes do not prove playback. No active actions attempted.\n')
    return result


def check_account(account):
    config = load_account(Path(account).resolve()); validate(config)
    return {'status': 'configured', 'backend': 'phone-harness',
            'device_verified': False, 'next': 'Run phone-harness doctor ios, then read-only phone preflight'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Validate private settings only; no device calls')
    parser.add_argument('--preflight', action='store_true', help='Open Instagram and verify own profile; no feed browsing')
    args = parser.parse_args()
    try: result = check_account(args.account) if args.check else run_session(args.account, preflight=args.preflight)
    except (ValueError, OSError, KeyError) as error: result = {'status': 'blocked', 'reason': str(error)}
    print(json.dumps(result, indent=2))
    return 0 if result['status'] in ('configured', 'finished', 'ready') else 1


if __name__ == '__main__': raise SystemExit(main())
