import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))


class ReadinessTests(unittest.TestCase):
    def setUp(self): self.mod = importlib.import_module('mirroring_readiness')

    def test_main_window_selected_behind_toolbar_and_localized(self):
        for name in ['iPhone Mirroring', 'iPhone镜像']:
            windows = [
                {'kCGWindowOwnerPID': 42, 'kCGWindowLayer': 0, 'kCGWindowName': 'Window',
                 'kCGWindowOwnerName': name, 'kCGWindowNumber': 1,
                 'kCGWindowBounds': {'X': 11, 'Y': 10, 'Width': 66, 'Height': 20}},
                {'kCGWindowOwnerPID': 42, 'kCGWindowLayer': 0, 'kCGWindowName': name,
                 'kCGWindowOwnerName': name, 'kCGWindowNumber': 2,
                 'kCGWindowBounds': {'X': 5, 'Y': 1, 'Width': 348, 'Height': 766}}]
            self.assertEqual(self.mod.select_main_window(windows, 42),
                             {'x': 5, 'y': 1, 'w': 348, 'h': 766, 'id': 2})

    def test_main_window_does_not_guess_from_size_or_other_owner(self):
        overlay = {'kCGWindowOwnerPID': 42, 'kCGWindowLayer': 0,
                   'kCGWindowName': 'Window', 'kCGWindowOwnerName': 'iPhone Mirroring',
                   'kCGWindowNumber': 1, 'kCGWindowBounds': {'X': 0, 'Y': 0, 'Width': 348, 'Height': 766}}
        self.assertIsNone(self.mod.select_main_window([overlay], 42))
        overlay['kCGWindowName'] = 'iPhone Mirroring'
        self.assertIsNone(self.mod.select_main_window([overlay], 99))
        self.assertIsNone(self.mod.select_main_window([overlay, overlay], 42))

    def test_point_must_belong_to_main_window_not_covering_same_app_toolbar(self):
        main = {'kCGWindowLayer': 0, 'kCGWindowNumber': 2,
                'kCGWindowBounds': {'X': 0, 'Y': 0, 'Width': 350, 'Height': 760}}
        toolbar = dict(main, kCGWindowNumber=1)
        self.assertTrue(self.mod.main_owns_point([main], 2, 100, 100))
        self.assertFalse(self.mod.main_owns_point([toolbar, main], 2, 100, 100))
        self.assertFalse(self.mod.main_owns_point([main], 2, 400, 100))

    def test_window_selection_preserves_background_offscreen_default_and_rejects_moved_tap(self):
        window = {'kCGWindowOwnerPID': 42, 'kCGWindowLayer': 0,
                  'kCGWindowName': 'iPhone Mirroring', 'kCGWindowOwnerName': 'iPhone Mirroring',
                  'kCGWindowNumber': 2, 'kCGWindowBounds': {'X': 0, 'Y': 0, 'Width': 350, 'Height': 760}}
        options = []; taps = []
        def windows(option, unused):
            options.append(option); return [window]
        q = SimpleNamespace(kCGWindowListOptionOnScreenOnly=1, kCGWindowListOptionAll=0,
                            kCGNullWindowID=0, CGWindowListCopyWindowInfo=windows)
        def activate(): window['kCGWindowBounds']['X'] = 50
        mirror = SimpleNamespace(Quartz=q, running_app=lambda: SimpleNamespace(processIdentifier=lambda: 42),
                                 activate=activate, tap=lambda x, y: taps.append((x, y)))
        background = SimpleNamespace()
        with patch.dict(sys.modules, {'phone_harness.background': background}):
            self.mod.install_window_selection(mirror)
            background.find_window()
            self.assertEqual(options[-1], 0)
            with self.assertRaisesRegex(RuntimeError, 'moved'):
                mirror.tap(100, 100)
            self.assertEqual(taps, [])

    def test_live_toolbar_buttons_do_not_block_stream(self):
        nodes = [{'role': 'AXButton', 'identifier': 'app.grid.3x3', 'label': 'Home Screen'},
                 {'role': 'AXButton', 'identifier': 'iphone.app.switcher', 'label': 'App Switcher'},
                 {'role': 'AXButton', 'subrole': 'AXCloseButton'}]
        self.assertEqual(self.mod.classify_native_window('iphone-mirroring-main', nodes), 'ready')

    def test_unknown_buttons_are_not_whitelisted_by_label(self):
        for label in ['Home Screen', 'App Switcher', 'Connect', 'Try Again', 'Unlock', '']:
            self.assertEqual(self.mod.classify_native_window('iphone-mirroring-main',
                [{'role': 'AXButton', 'identifier': 'unknown', 'label': label}]), 'blocked')

    def test_real_interstitials_and_login_fields_still_block(self):
        for role in ['AXStaticText', 'AXImage', 'AXTextField', 'AXSecureTextField', 'AXSheet', 'AXCheckBox']:
            self.assertEqual(self.mod.classify_native_window('iphone-mirroring-main',
                [{'role': role, 'label': 'Any language, including unknown future prompts'}]), 'blocked')

    def test_empty_validated_live_window_is_ready(self):
        self.assertEqual(self.mod.classify_native_window('iphone-mirroring-main', []), 'ready')

    def test_missing_window_identity_or_incomplete_ax_walk_blocks(self):
        for identifier in [None, '', 'iphone-mirroring-onboarding']:
            self.assertEqual(self.mod.classify_native_window(identifier, []), 'blocked')
        self.assertEqual(self.mod.classify_native_window('iphone-mirroring-main', [], complete=False), 'blocked')

    def fake_mirror(self, root, fail=False, missing_error=-25205):
        def attr(node, name, _):
            if fail: return -25211, None
            return (0, node[name]) if name in node else (missing_error, None)
        return SimpleNamespace(running_app=lambda: object(), find_window=lambda **kw: {'x': 0, 'y': 0},
                               _ax_window_element=lambda app, win: root,
                               _AS=SimpleNamespace(AXUIElementCopyAttributeValue=attr))

    def test_native_reader_distinguishes_toolbar_from_blocking_ui(self):
        root = {'AXRole': 'AXWindow', 'AXIdentifier': 'iphone-mirroring-main', 'AXChildren': [
            {'AXRole': 'AXButton', 'AXIdentifier': 'app.grid.3x3', 'AXChildren': []}]}
        self.assertEqual(self.mod.native_state(self.fake_mirror(root)), 'ready')
        root['AXChildren'].append({'AXRole': 'AXStaticText', 'AXValue': 'iCloud is not syncing'})
        self.assertEqual(self.mod.native_state(self.fake_mirror(root)), 'blocked')

    def test_native_reader_ax_permission_error_or_missing_target_is_not_ready(self):
        root = {'AXRole': 'AXWindow', 'AXIdentifier': 'iphone-mirroring-main', 'AXChildren': []}
        self.assertEqual(self.mod.native_state(self.fake_mirror(root, fail=True)), 'blocked')
        self.assertEqual(self.mod.native_state(self.fake_mirror(None)), 'blocked')

    def test_empty_launch_window_does_not_count_as_connected(self):
        root = {'AXRole': 'AXWindow', 'AXIdentifier': 'iphone-mirroring-main', 'AXChildren': []}
        self.assertEqual(self.mod.native_state(self.fake_mirror(root)), 'blocked')

    def test_nested_empty_or_chrome_only_window_is_not_live_evidence(self):
        for child in [{'AXRole': 'AXGroup', 'AXChildren': []},
                      {'AXRole': 'AXButton', 'AXSubrole': 'AXCloseButton'}]:
            root = {'AXRole': 'AXWindow', 'AXIdentifier': 'iphone-mirroring-main', 'AXChildren': [child]}
            self.assertEqual(self.mod.native_state(self.fake_mirror(root)), 'blocked')

    def test_observed_live_hosting_view_with_hidden_toolbar_is_ready(self):
        root = {'AXRole': 'AXWindow', 'AXIdentifier': 'iphone-mirroring-main', 'AXChildren': [
            {'AXRole': 'AXGroup', 'AXSubrole': 'AXHostingView', 'AXChildren': []}]}
        self.assertEqual(self.mod.native_state(self.fake_mirror(root)), 'ready')

    def test_native_no_value_for_optional_toolbar_metadata_is_not_permission_failure(self):
        root = {'AXRole': 'AXWindow', 'AXIdentifier': 'iphone-mirroring-main', 'AXChildren': [
            {'AXRole': 'AXGroup', 'AXSubrole': 'AXHostingView', 'AXChildren': [
                {'AXRole': 'AXButton', 'AXSubrole': 'AXCloseButton'},
                {'AXRole': 'AXButton', 'AXIdentifier': 'app.grid.3x3'},
                {'AXRole': 'AXButton', 'AXIdentifier': 'iphone.app.switcher'}]}]}
        self.assertEqual(self.mod.native_state(self.fake_mirror(root, missing_error=-25212)), 'ready')


if __name__ == '__main__': unittest.main()
