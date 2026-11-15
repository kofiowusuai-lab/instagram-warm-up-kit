import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))


class ReadinessTests(unittest.TestCase):
    def setUp(self): self.mod = importlib.import_module('mirroring_readiness')

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
