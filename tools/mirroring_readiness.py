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
    if getattr(mirror.ax_session_hint, '_instagram_readiness_compat', False): return True

    def state(): return native_state(mirror)
    state._instagram_readiness_compat = True
    mirror.ax_session_hint = state
    # background exports an alias, not a forwarding function. Patch both references.
    background = sys.modules.get('phone_harness.background')
    if background is not None: background.ax_session_hint = state
    return True
