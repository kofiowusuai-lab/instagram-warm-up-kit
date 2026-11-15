"""Small allowlisted bridge to the installed Phone Harness CLI, local iPhone only."""
import json
import os
import subprocess


PROGRAM = '''
# task: Run the user's authorized passive Instagram session on their own iPhone.
# step: Execute one bounded device operation and return structured observations.
import json
from phone_harness import helpers as h
request = json.loads(PAYLOAD)
op = request['op']
kw = request['kw']
if op == 'ensure':
    value = h.ensure_device()
else:
    if h.connection_state() != 'ready':
        raise RuntimeError('Personal iPhone is not ready; user connection required')
    if op == 'open':
        value = h.open_app('Instagram')
    elif op == 'observe':
        value = {'bounds': h.find_window(), 'boxes': h.screen()}
    elif op == 'anchor':
        bounds = h.find_window()
        calibration = kw['calibration']
        ratio = bounds['w'] / bounds['h']
        if abs(ratio / calibration['aspect_ratio'] - 1) > 0.03:
            raise RuntimeError('Mirroring layout changed; recalibrate')
        x, y = calibration[kw['name']]
        value = h.tap(bounds['x'] + bounds['w'] * x, bounds['y'] + bounds['h'] * y)
    elif op == 'scroll':
        value = h.scroll('down', amount=0.8)
    else:
        raise ValueError('Unsupported phone operation')
print('PH_RESULT ' + json.dumps({'value': value}))
'''


class PhoneHarnessClient:
    def __init__(self, executable):
        self.executable = executable

    def call(self, op, timeout, **kw):
        if op not in {'ensure', 'open', 'observe', 'anchor', 'scroll'}:
            raise ValueError('Unsupported phone operation')
        if timeout <= 0:
            raise TimeoutError('Phone session deadline reached')
        payload = json.dumps(json.dumps({'op': op, 'kw': kw}))
        source = PROGRAM.replace('PAYLOAD', payload)
        env = dict(os.environ, PHONE_HARNESS_PLATFORM='ios', DO_NOT_TRACK='1',
                   PHONE_HARNESS_TELEMETRY='0', PHONE_HARNESS_NO_UPDATE_CHECK='1')
        # Explicit ios bypasses any attached cloud session. Never select or start cloud phones.
        try:
            result = subprocess.run([self.executable], input=source, text=True,
                                    capture_output=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            raise TimeoutError('Phone Harness operation exceeded the remaining budget') from None
        except OSError:
            raise RuntimeError('Phone Harness executable unavailable; run the setup doctor') from None
        if result.returncode:
            # Raw helper errors may contain screen text. Keep them out of logs and stdout.
            raise RuntimeError('Phone Harness operation failed; check mirroring and run the setup doctor')
        for line in reversed(result.stdout.splitlines()):
            if line.startswith('PH_RESULT '):
                return json.loads(line[len('PH_RESULT '):])['value']
        raise RuntimeError('Phone Harness returned no structured result')
