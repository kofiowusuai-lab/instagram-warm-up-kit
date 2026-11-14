import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('seed', Path(__file__).parents[1] / 'tools/seed_scripts.py')
seed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seed)

class SeedTests(unittest.TestCase):
    def test_local_mode_initialized_without_overwriting_existing_config(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'config.json'
            seed.initialize_local_config(target)
            self.assertEqual(json.loads(target.read_text())['mode'], 'local')
            cloud = {'version':1,'mode':'cloud','cloudUrl':'https://example.com','localAnalytics':False}
            target.write_text(json.dumps(cloud))
            seed.initialize_local_config(target)
            self.assertEqual(json.loads(target.read_text()), cloud)

    def test_fresh_install_preloads_modes_with_topic(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'custom-scripts/local.json'
            seed.seed(target, 'GTA 6, GTA VI')
            rows = json.loads(target.read_text())
            self.assertEqual(len(rows), 3)
            self.assertEqual({r['name'] for r in rows}, {'ig-soft-warmup', 'ig-active-warmup', 'ig-soft-smoke-test'})
            self.assertTrue(all('const TOPIC = "GTA 6, GTA VI";' in r['source'] for r in rows))
            seed.seed(target, 'changed topic')
            self.assertEqual(json.loads(target.read_text()), rows)

    def test_preserves_existing_custom_scripts_and_edits(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'local.json'
            original = [{'id':'mine', 'name':'ig-soft-warmup', 'source':'user edit'}]
            target.write_text(json.dumps(original))
            seed.seed(target, 'GTA 6')
            self.assertEqual(json.loads(target.read_text())[0], original[0])

    def test_rejects_corrupt_store_without_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'local.json'
            target.write_text('broken')
            with self.assertRaises(ValueError): seed.seed(target, 'GTA 6')
            self.assertEqual(target.read_text(), 'broken')

if __name__ == '__main__': unittest.main()
