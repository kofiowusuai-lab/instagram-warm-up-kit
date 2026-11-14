import importlib.util
import unittest
from pathlib import Path
SPEC = importlib.util.spec_from_file_location('bootstrap', Path(__file__).parents[1] / 'tools/bootstrap_profile.py')
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)

class ProfileTests(unittest.TestCase):
    def test_existing_profile_reused_without_creating(self):
        calls=[]
        def api(path,payload=None):
            calls.append((path,payload))
            return {'list':[{'name':'Clips-01','user_id':'existing'}]}
        self.assertEqual(bootstrap.ensure_profile('Clips-01',api),'existing')
        self.assertEqual(len(calls),1)

    def test_creation_explicitly_uses_firefox_and_no_credentials(self):
        calls=[]
        def api(path,payload=None):
            calls.append((path,payload))
            return {'list':[]} if payload is None else {'id':'new'}
        self.assertEqual(bootstrap.ensure_profile('Clips-01',api),'new')
        self.assertEqual(calls[-1][1],{'name':'Clips-01','engine':'firefox','domain_name':'instagram.com'})

    def test_searches_later_pages_before_creating(self):
        def api(path,payload=None):
            if 'page=1&' in path: return {'list':[{'name':'other','user_id':str(i)} for i in range(100)]}
            if 'page=2&' in path: return {'list':[{'name':'Clips-01','user_id':'second-page'}]}
            self.fail('Unexpected creation')
        self.assertEqual(bootstrap.ensure_profile('Clips-01',api),'second-page')

if __name__=='__main__': unittest.main()
