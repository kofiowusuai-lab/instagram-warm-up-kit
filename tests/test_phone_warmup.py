import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))


def config():
    return {'execution_backend': 'phone-harness', 'account_label': 'fixture', 'topic': 'creator',
            'account_status': 'ready_for_authorized_soft_runs',
            'agent_engagement_enabled': True, 'schedule_approved': True,
            'reported_warning_status': 'none_reported',
            'timezone': 'UTC', 'warmup_start_date': '2026-01-01',
            'active_mode_enabled': False, 'scheduler_enabled': True,
            'schedule': {'session_minutes': 1},
            'phone': {'enabled': True, 'platform': 'ios', 'mode': 'soft',
                      'expected_username': 'fixture_account', 'harness_executable': '/usr/local/bin/phone-harness',
                      'dwell_seconds': 5, 'max_items': 2,
                      'calibration': {'aspect_ratio': 0.5,
                                      'profile': [0.9, 0.95], 'reels': [0.5, 0.95]}}}


def profile(username='fixture_account'):
    return [{'text': t, 'confidence': 0.99, 'x': 100, 'y': y, 'w': 30, 'h': 12}
            for t, y in [(username, 20), ('Posts', 100), ('Followers', 100), ('Following', 100), ('Edit profile', 180)]]


class Clock:
    def __init__(self): self.value = 0
    def now(self): return self.value
    def sleep(self, seconds): self.value += seconds


class Device:
    def __init__(self, user='fixture_account', feed=None):
        self.user = user; self.feed = feed; self.calls = []; self.view = 'profile'; self.sequence = 0
    def call(self, op, timeout, **kw):
        self.calls.append((op, kw, timeout))
        if op == 'ensure': return {'w': 200, 'h': 400, 'x': 0, 'y': 0}
        if op == 'open': return 'com.burbn.instagram'
        if op == 'anchor': self.view = kw['name']; return None
        if op == 'observe':
            if self.view == 'profile': return {'bounds': {'x': 0, 'y': 0, 'w': 200, 'h': 400}, 'boxes': profile(self.user)}
            return {'bounds': {'x': 0, 'y': 0, 'w': 200, 'h': 400},
                    'boxes': self.feed or [{'text': 'Reels', 'confidence': 0.99, 'x': 100, 'y': 20},
                                           {'text': 'creator ' + str(self.sequence), 'confidence': 0.99, 'x': 80, 'y': 220}]}
        if op == 'scroll': self.sequence += 1


class PhoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.phone = importlib.import_module('phone_warmup')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.account = Path(self.tmp.name) / 'account'; self.account.mkdir()
        for name in ['SOP.md', 'progress.md', 'schedule.md', 'warnings.md']:
            (self.account / name).write_text('Fixture\n')
        self.save(config()); self.clock = Clock(); self.device = Device()

    def save(self, c): (self.account / 'settings.json').write_text(json.dumps(c))
    def run_session(self):
        return self.phone.run_session(self.account, client=self.device,
                                      clock=self.clock.now, sleep=self.clock.sleep,
                                      lock_path=Path(self.tmp.name) / 'phone.lock')

    def test_paused_account_never_contacts_device(self):
        c = config(); c['account_status'] = 'paused_security_checkpoint'; self.save(c)
        result = self.run_session()
        self.assertEqual(result['status'], 'blocked'); self.assertEqual(self.device.calls, [])

    def test_preflight_verifies_account_without_reels_or_scroll(self):
        result = self.phone.run_session(self.account, client=self.device, preflight=True,
                                       clock=self.clock.now, sleep=self.clock.sleep,
                                       lock_path=Path(self.tmp.name) / 'phone.lock')
        self.assertEqual(result['status'], 'ready')
        self.assertFalse(any(op == 'scroll' or kw.get('name') == 'reels' for op, kw, _ in self.device.calls))

    def test_missing_approval_or_future_start_never_contacts_device(self):
        for change in [{'schedule_approved': False}, {'agent_engagement_enabled': False},
                       {'warmup_start_date': '2999-01-01'}, {'reported_warning_status': 'checkpoint'},
                       {'timezone': None}]:
            c = config(); c.update(change); self.save(c)
            self.assertEqual(self.run_session()['status'], 'blocked')
            self.assertEqual(self.device.calls, [])

    def test_active_or_missing_calibration_is_refused(self):
        for key, value in [('mode', 'active'), ('calibration', None), ('expected_username', '')]:
            c = config(); c['phone'][key] = value; self.save(c)
            self.assertEqual(self.run_session()['status'], 'blocked')
            self.assertEqual(self.device.calls, [])

    def test_wrong_account_never_enters_reels(self):
        self.device.user = 'different_account'
        result = self.run_session()
        self.assertEqual(result['status'], 'identity_mismatch')
        self.assertFalse(any(op == 'scroll' or kw.get('name') == 'reels' for op, kw, _ in self.device.calls))

    def test_resumed_feed_or_dm_screen_receives_no_tap(self):
        original = self.device.call
        def call(op, timeout, **kw):
            value = original(op, timeout, **kw)
            if op == 'observe':
                return {'bounds': {'x': 0, 'y': 0, 'w': 200, 'h': 400},
                        'boxes': [{'text': 'Messages', 'confidence': .99, 'y': 20}]}
            return value
        self.device.call = call
        self.assertEqual(self.run_session()['status'], 'identity_mismatch')
        self.assertFalse(any(op in ('anchor', 'scroll') for op, _, _ in self.device.calls))

    def test_feed_mention_is_not_profile_identity(self):
        self.assertFalse(self.phone.profile_matches(
            {'bounds': {'x': 0, 'y': 0, 'w': 200, 'h': 400},
             'boxes': [{'text': 'fixture_account', 'confidence': .99, 'y': 250}]}, 'fixture_account'))
        self.assertFalse(self.phone.profile_matches(
            {'bounds': {'x': 0, 'y': 0, 'w': 200, 'h': 400}, 'boxes': profile('fixture_account_extra')},
            'fixture_account'))

    def test_visiting_expected_users_public_profile_is_not_signed_in_identity(self):
        boxes = [box for box in profile() if box['text'] != 'Edit profile']
        self.assertFalse(self.phone.profile_matches(
            {'bounds': {'x': 0, 'y': 0, 'w': 200, 'h': 400}, 'boxes': boxes}, 'fixture_account'))

    def test_completed_passive_run_does_not_invent_reel_counts(self):
        result = self.run_session()
        self.assertEqual(result['status'], 'finished')
        self.assertEqual(result['observations']['dwell_seconds'], 10)
        self.assertIsNone(result['reported_counts']['reels'])
        for action in ['likes', 'follows', 'saves', 'comments', 'dms']:
            self.assertEqual(result['reported_counts'][action], 0)
        self.assertTrue((self.account / result['evidence']).is_file())
        self.assertNotIn('creator', (self.account / result['evidence']).read_text())

    def test_warning_pauses_before_any_scroll(self):
        self.device.feed = [{'text': 'We limit how often you can do certain things', 'confidence': .99, 'y': 30}]
        result = self.run_session()
        self.assertEqual(result['status'], 'paused_warning')
        self.assertFalse(any(op == 'scroll' for op, _, _ in self.device.calls))
        c = json.loads((self.account / 'settings.json').read_text())
        self.assertFalse(c['scheduler_enabled']); self.assertFalse(c['agent_engagement_enabled'])
        self.assertEqual(c['reported_warning_status'], 'possible_checkpoint')
        self.assertIn('possible', (self.account / 'warnings.md').read_text())

    def test_unrelated_content_does_not_receive_planned_dwell(self):
        c = config(); c['topic'] = 'GTA 6, Grand Theft Auto VI'; self.save(c)
        result = self.run_session()
        self.assertEqual(result['status'], 'no_topic_matches')
        self.assertEqual(result['observations']['dwell_seconds'], 0)
        self.assertEqual(result['observations']['topic_matches'], 0)

    def test_transport_timeout_is_incomplete_and_not_retried(self):
        def call(op, timeout, **kw):
            self.device.calls.append((op, kw, timeout))
            raise TimeoutError('operation timed out')
        self.device.call = call
        result = self.run_session()
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(len(self.device.calls), 1)
        self.assertIsNone(result['reported_counts']['reels'])

    def test_window_geometry_change_aborts_bridge_before_tap(self):
        mod = importlib.import_module('phone_harness_client')
        from types import ModuleType
        package = ModuleType('phone_harness'); helpers = ModuleType('phone_harness.helpers')
        helpers.connection_state = lambda: 'ready'
        helpers.find_window = lambda: {'x': 0, 'y': 0, 'w': 400, 'h': 400}
        helpers.tap = lambda *args: self.fail('Unexpected tap after layout change')
        package.helpers = helpers
        payload = json.dumps(json.dumps({'op': 'anchor', 'kw': {'name': 'reels', 'calibration': config()['phone']['calibration']}}))
        source = mod.PROGRAM.replace('PAYLOAD', payload).replace('COMPAT_DIR', repr(str(Path(__file__).parents[1] / 'tools')))
        with patch.dict(sys.modules, {'phone_harness': package, 'phone_harness.helpers': helpers}):
            with patch('mirroring_readiness.install', return_value=True):
                with self.assertRaisesRegex(RuntimeError, 'layout changed'):
                    exec(compile(source, '<bridge>', 'exec'), {})

    def test_mid_dwell_pause_stops_before_next_input(self):
        def sleep(seconds):
            self.clock.sleep(seconds)
            c = config(); c['agent_engagement_enabled'] = False; self.save(c)
        result = self.phone.run_session(self.account, client=self.device,
                                       clock=self.clock.now, sleep=sleep,
                                       lock_path=Path(self.tmp.name) / 'phone.lock')
        self.assertEqual(result['status'], 'paused')
        self.assertFalse(any(op == 'scroll' for op, _, _ in self.device.calls))

    def test_shared_lock_stops_second_account_before_device_access(self):
        path = Path(self.tmp.name) / 'phone.lock'
        with self.phone.device_lock(path):
            result = self.run_session()
        self.assertEqual(result['status'], 'device_busy'); self.assertEqual(self.device.calls, [])

    def test_deadline_bounds_transport_and_dwell(self):
        c = config(); c['schedule']['session_minutes'] = 0.1; self.save(c)
        result = self.run_session()
        self.assertEqual(result['status'], 'finished')
        self.assertLessEqual(self.clock.value, 6)
        self.assertTrue(all(0 < timeout <= 6 for _, _, timeout in self.device.calls))


class BridgeTests(unittest.TestCase):
    def test_bridge_forces_personal_iphone_and_sanitizes_failures(self):
        mod = importlib.import_module('phone_harness_client')
        with patch.object(mod.subprocess, 'run') as run:
            run.return_value.stdout = 'PH_RESULT {"value": {"w": 200}}\n'
            run.return_value.returncode = 0
            client = mod.PhoneHarnessClient('/path with spaces/phone-harness')
            self.assertEqual(client.call('ensure', timeout=3), {'w': 200})
            args, kw = run.call_args
            self.assertEqual(args[0], ['/path with spaces/phone-harness'])
            self.assertEqual(kw['env']['PHONE_HARNESS_PLATFORM'], 'ios')
            self.assertEqual(kw['env']['DO_NOT_TRACK'], '1')
            self.assertEqual(kw['timeout'], 3)
            run.return_value.returncode = 1; run.return_value.stderr = 'secret screen contents'
            with self.assertRaisesRegex(RuntimeError, 'Phone Harness') as error:
                client.call('ensure', timeout=3)
            self.assertNotIn('secret', str(error.exception))


class DispatchTests(unittest.TestCase):
    def setUp(self): self.scheduler = importlib.import_module('scheduler')

    def test_phone_dispatch_never_constructs_aliasmode_client(self):
        with tempfile.TemporaryDirectory() as directory:
            account = Path(directory); state = {'runs': {'slot': {'status': 'starting'}}}
            with patch('phone_warmup.run_session', return_value={'status': 'finished', 'evidence': 'phone-runs/fixture.json'}) as run:
                with patch('aliasmode_scripts.AliasModeScripts', side_effect=AssertionError('Browser contacted')):
                    self.scheduler.execute_backend(config(), account, 'slot', state)
            run.assert_called_once_with(account)
            self.assertEqual(state['runs']['slot']['backend'], 'phone-harness')
            self.assertEqual(state['runs']['slot']['status'], 'finished')

    def test_unknown_backend_fails_closed(self):
        c = config(); c['execution_backend'] = 'typo'
        with self.assertRaisesRegex(ValueError, 'backend'):
            self.scheduler.execute_backend(c, Path('/unused'), 'slot', {'runs': {'slot': {}}})


if __name__ == '__main__': unittest.main()
