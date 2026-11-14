import importlib.util
import unittest
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('scheduler',Path(__file__).parents[1]/'tools/scheduler.py')
scheduler=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scheduler)

class SchedulerTests(unittest.TestCase):
    def config(self):
        return {'scheduler_enabled':True,'account_status':'ready_for_authorized_soft_runs',
                'schedule':{'timezone':'UTC','times':['07:00','21:00'],'session_minutes':20,'skip_days_per_week':0}}
    def dt(self,stamp):return datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)
    def test_two_gmt_slots_including_summer(self):
        for stamp in ['2027-07-01T07:00:00','2027-07-01T21:00:00']:
            self.assertIsNotNone(scheduler.claim_slot(self.config(),{},self.dt(stamp)))
        self.assertIsNone(scheduler.claim_slot(self.config(),{},self.dt('2027-07-01T06:00:00')))
    def test_no_duplicate_claim(self):
        state={};now=self.dt('2027-07-01T07:00:00')
        self.assertIsNotNone(scheduler.claim_slot(self.config(),state,now))
        self.assertIsNone(scheduler.claim_slot(self.config(),state,now))
    def test_old_slots_are_recorded_missed_not_caught_up(self):
        state={}
        self.assertIsNone(scheduler.claim_slot(self.config(),state,self.dt('2027-07-01T08:00:00')))
        self.assertEqual(state['runs']['2027-07-01@07:00']['status'],'missed')
    def test_one_skip_date_is_persisted_not_resampled(self):
        config=self.config();config['schedule']['skip_days_per_week']=1
        state={};calls=[]
        def pick(days,n):calls.append(1);return [days[-1]]
        scheduler.claim_slot(config,state,self.dt('2027-06-28T07:00:00'),pick)
        scheduler.claim_slot(config,state,self.dt('2027-06-28T21:00:00'),pick)
        self.assertEqual(len(calls),1)
        self.assertEqual(len(state['weeks']['2027-06-28']),1)
        self.assertIsNone(scheduler.claim_slot(config,state,self.dt('2027-07-04T07:00:00'),pick))
        self.assertEqual(state['runs']['2027-07-04@07:00']['status'],'skipped')
    def test_paused_or_disabled_does_not_claim(self):
        config=self.config();config['account_status']='paused'
        self.assertIsNone(scheduler.claim_slot(config,{},self.dt('2027-07-01T07:00:00')))
        config=self.config();config['scheduler_enabled']=False
        self.assertIsNone(scheduler.claim_slot(config,{},self.dt('2027-07-01T07:00:00')))
    def test_started_claim_survives_restart_without_retry(self):
        state={'runs':{'2027-07-01@07:00':{'status':'starting'}}}
        self.assertIsNone(scheduler.claim_slot(self.config(),state,self.dt('2027-07-01T07:01:00')))
    def test_non_utc_schedule_is_rejected(self):
        config=self.config();config['schedule']['timezone']='Europe/London'
        with self.assertRaises(ValueError):scheduler.claim_slot(config,{},self.dt('2027-07-01T07:00:00'))

class WarningPersistenceTests(unittest.TestCase):
    def test_warning_is_persisted_before_later_status_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            account=Path(directory)
            config={'schedule':{'session_minutes':20},'scheduler_enabled':True,
                    'aliasmode_profile_id':'test-profile','topic':'GTA 6'}
            (account/'settings.json').write_text(json.dumps(config))
            (account/'warnings.md').write_text('Warnings\n')
            class Client:
                calls=0
                def status(self):
                    self.calls+=1
                    if self.calls==1:return None
                    raise RuntimeError('status connection lost')
                def ensure_script(self,*args):return 'script'
                def start(self,*args):return {'id':'owned'}
                def log(self,*args):return {'text':'STOPPED: instagram showed a limit or challenge','nextOffset':50}
            state={'runs':{'slot':{'status':'starting'}}}
            with self.assertRaises(RuntimeError):scheduler.execute(config,account,'slot',state,Client())
            result=json.loads((account/'settings.json').read_text())
            self.assertFalse(result['scheduler_enabled'])
            self.assertEqual(result['account_status'],'paused_restriction')
            self.assertIn('limit/challenge',(account/'warnings.md').read_text())

if __name__=='__main__':unittest.main()
