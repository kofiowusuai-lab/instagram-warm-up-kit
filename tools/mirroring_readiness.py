"""Phone Harness 0.3.3 compatibility for native iPhone Mirroring toolbar controls.

Keep structural session guards: only identified window chrome is ignored. Native
prompts, unknown controls, inaccessible trees and unmatched windows remain blocked.
No OCR is used to override connection state.
"""
import importlib.metadata
import sys

TOOLBAR_IDS = frozenset(('app.grid.3x3', 'iphone.app.switcher'))
CHROME_SUBROLES = frozenset(('AXCloseButton', 'AXMinimizeButton', 'AXZoomButton', 'AXFullScreenButton'))
CONTAINERS = frozenset(('AXWindow', 'AXGroup', 'AXToolbar', 'AXSplitGroup', 'AXLayoutArea'))
LEAVES = frozenset(('AXStaticText', 'AXButton', 'AXTextField', 'AXSecureTextField', 'AXImage'))


def select_main_window(windows, pid):
    # The hover toolbar is also a layer-zero window owned by this process.
    # The main window title equals the localized application name. Do not
    # guess by front-to-back order or size (Stage Manager changes both).
    matches = [w for w in windows if w.get('kCGWindowOwnerPID') == pid
               and w.get('kCGWindowLayer') == 0
               and w.get('kCGWindowOwnerName')
               and w.get('kCGWindowName') == w.get('kCGWindowOwnerName')]
    if len(matches) != 1: return None
    w = matches[0]; b = w['kCGWindowBounds']
    return {'x': b['X'], 'y': b['Y'], 'w': b['Width'], 'h': b['Height'],
            'id': int(w['kCGWindowNumber'])}


def install_window_selection(mirror):
    def find_window(on_screen=True):
        app = mirror.running_app()
        if app is None: return None
        q = mirror.Quartz
        option = q.kCGWindowListOptionOnScreenOnly if on_screen else q.kCGWindowListOptionAll
        return select_main_window(q.CGWindowListCopyWindowInfo(option, q.kCGNullWindowID) or [],
                                  app.processIdentifier())
    mirror.find_window = find_window
    def owns_point(x, y):
        win = find_window()
        if not win: return False
        q = mirror.Quartz
        windows = q.CGWindowListCopyWindowInfo(q.kCGWindowListOptionOnScreenOnly, q.kCGNullWindowID) or []
        return main_owns_point(windows, win['id'], x, y)
    mirror.window_owns_point = owns_point
    if not getattr(mirror.tap, '_instagram_target_guard', False):
        original_tap = mirror.tap
        def tap(x, y):
            before = find_window()
            mirror.activate()
            if not before or find_window() != before:
                raise RuntimeError('Phone window moved before tap; recompute the target')
            if not owns_point(x, y):
                raise RuntimeError('Main phone window is covered at the tap target')
            return original_tap(x, y)
        tap._instagram_target_guard = True
        mirror.tap = tap
    background = sys.modules.get('phone_harness.background')
    if background is not None:
        background.find_window = lambda: find_window(on_screen=False)


def main_owns_point(windows, window_id, x, y):
    for w in windows:
        if w.get('kCGWindowLayer', 1) != 0: continue
        b = w.get('kCGWindowBounds', {})
        if (b.get('X', 0) <= x < b.get('X', 0) + b.get('Width', 0)
                and b.get('Y', 0) <= y < b.get('Y', 0) + b.get('Height', 0)):
            return w.get('kCGWindowNumber') == window_id
    return False


def classify_native_window(identifier, nodes, complete=True):
    if not complete or identifier != 'iphone-mirroring-main': return 'blocked'
    for node in nodes:
        if node.get('role') == 'AXButton':
            if node.get('identifier') in TOOLBAR_IDS: continue
            if node.get('subrole') in CHROME_SUBROLES: continue
        return 'blocked'
    return 'ready'


def native_state(mirror):
    app = mirror.running_app()
    if app is None: return 'not-running'
    win = mirror.find_window(on_screen=False)
    if win is None: return 'no-window'
    target = mirror._ax_window_element(app, win)
    if target is None: return 'blocked'

    def attribute(node, name, optional=False):
        error, value = mirror._AS.AXUIElementCopyAttributeValue(node, name, None)
        # AXErrorAttributeUnsupported and AXErrorNoValue mean absent optional
        # metadata, not denied accessibility. Required attributes stay strict.
        if error and not (optional and error in (-25205, -25212)):
            raise RuntimeError('Native accessibility tree is unavailable')
        return value

    try:
        identifier = attribute(target, 'AXIdentifier')
        children = attribute(target, 'AXChildren')
        if not children: return 'blocked'  # Empty launch windows are not live proof.
        nodes = []; visited = 0; hosting_view = False

        def walk(node, depth=0):
            nonlocal visited, hosting_view
            visited += 1
            if visited > 250 or depth > 12:
                raise RuntimeError('Native accessibility tree exceeds inspection limit')
            role = attribute(node, 'AXRole')
            subrole = attribute(node, 'AXSubrole', optional=True)
            if role == 'AXGroup' and subrole == 'AXHostingView': hosting_view = True
            if role not in CONTAINERS:
                nodes.append({'role': role,
                              'identifier': attribute(node, 'AXIdentifier', optional=True),
                              'subrole': subrole})
            kids = attribute(node, 'AXChildren', optional=role in LEAVES)
            for child in kids or []: walk(child, depth + 1)

        walk(target)
        toolbar = any(node['role'] == 'AXButton' and node['identifier'] in TOOLBAR_IDS for node in nodes)
        if not hosting_view and not toolbar: return 'blocked'
        return classify_native_window(identifier, nodes)
    except Exception:
        return 'blocked'


def install():
    """Install in this Python process, preserving IPhone's before/after action guards."""
    if sys.platform != 'darwin': return False
    if importlib.metadata.version('phone-harness') != '0.3.3':
        raise RuntimeError('Revalidate mirroring compatibility for this Phone Harness version')
    from phone_harness import mirror
    install_window_selection(mirror)
    if getattr(mirror.ax_session_hint, '_instagram_readiness_compat', False): return True

    def state(): return native_state(mirror)
    state._instagram_readiness_compat = True
    mirror.ax_session_hint = state
    # background exports an alias, not a forwarding function. Patch both references.
    background = sys.modules.get('phone_harness.background')
    if background is not None: background.ax_session_hint = state
    return True
