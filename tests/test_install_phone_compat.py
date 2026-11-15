import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))


class InstallTests(unittest.TestCase):
    def test_registration_preserves_helpers_backs_up_and_is_idempotent(self):
        mod = importlib.import_module('install_phone_compat')
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            helper = workspace / 'agent_helpers.py'
            original = 'def existing_helper():\n    return 42\n'
            helper.write_text(original)
            backup = mod.register(workspace)
            self.assertEqual(backup.read_text(), original)
            self.assertTrue(helper.read_text().startswith(original))
            self.assertIn('mirroring_readiness.py', helper.read_text())
            self.assertIsNone(mod.register(workspace))
            self.assertEqual(len(list(workspace.glob('*.bak'))), 1)

    def test_missing_workspace_or_helper_is_not_silently_created(self):
        mod = importlib.import_module('install_phone_compat')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError): mod.register(Path(directory))


if __name__ == '__main__': unittest.main()
