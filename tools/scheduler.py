#!/usr/bin/env python3
"""UTC scheduled passive sessions. No LLM, credentials, catch-up runs or active engagement."""
import argparse
import fcntl
import json
import os
import random
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.state-')
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2);f.write('\n')
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def claim_slot(config,state,now,sample=random.SystemRandom().sample):
    if not config.get('scheduler_enabled') or config.get('account_status','').startswith(('paused','restricted','needs_login')):
        return None
    if config.get('reported_warning_status') in ('restriction','checkpoint','suspended','active_restriction'):return None
    schedule=config['schedule']
    if schedule['timezone']!='UTC':raise ValueError('GMT schedule must use fixed UTC, not daylight-saving local time')
    if not 0<schedule['session_minutes']<=20:raise ValueError('Session must be at most 20 minutes')
    count=schedule.get('skip_days_per_week',1)
    if type(count) is not int or not 0<=count<=6:raise ValueError('skip_days_per_week must be 0..6')
    now=now.astimezone(timezone.utc);today=now.date()
    monday=today-timedelta(days=today.weekday());week=monday.isoformat()
    weeks=state.setdefault('weeks',{});runs=state.setdefault('runs',{})
    if week not in weeks:
        # Never mark dates before the scheduler's first observation as randomly skipped.
        choices=[(monday+timedelta(days=i)).isoformat() for i in range(7) if monday+timedelta(days=i)>=today]
        weeks[week]=sorted(sample(choices,min(count,len(choices))))
    for slot in sorted(schedule['times']):
        hour,minute=map(int,slot.split(':'))
        due=now.replace(hour=hour,minute=minute,second=0,microsecond=0)
        if now<due:continue
        key=today.isoformat()+'@'+slot
        if key in runs:continue
        if today.isoformat() in weeks[week]:
            runs[key]={'status':'skipped','reason':'persisted_random_skip_day'};continue
        if (now-due).total_seconds()>=300:
            runs[key]={'status':'missed','reason':'outside_five_minute_start_window'};continue
        runs[key]={'status':'starting','claimed_at':now.isoformat()}
        return key
    return None

def record_warning(text,config,account,key,log_name):
    if not re.search(r'STOPPED:|confirm it.s you|we limit how often|unusual activity',text,re.I):return False
    already=config.get('account_status')=='paused_restriction'
    config.update(account_status='paused_restriction',reported_warning_status='active_restriction',scheduler_enabled=False)
    write_json(account/'settings.json',config)
    if not already:
        with (account/'warnings.md').open('a') as f:
            f.write('\n## Scheduler warning '+key+'\n\nScript reported a limit/challenge; automatic runs paused. See scheduled-runs/'+log_name+'.\n')
    return True

def execute(config,account,key,state,client):
    run_dir=account/'scheduled-runs';run_dir.mkdir(exist_ok=True)
    record=state['runs'][key]
    existing=client.status()
    if existing and existing['status']!='finished':
        record.update(status='not_run',reason='another_aliasmode_script_is_running');return
    source=(ROOT/'scripts/ig-soft-timed.mjs').read_text()
    script_id=client.ensure_script('ig-soft-timed-v1',source)
    started=datetime.now(timezone.utc)
    end=started+timedelta(minutes=config['schedule']['session_minutes'])
    run=client.start(script_id,config['aliasmode_profile_id'],{
        'topic':config['topic'],'durationMinutes':config['schedule']['session_minutes'],
        'accountSettingsPath':str(account/'settings.json')})
    record.update(status='running',run_id=run['id'],started_at=started.isoformat())
    write_json(account/'scheduler-state.json',state)
    offset=0;parts=[];status='running';log_path=run_dir/(key.replace(':','-')+'.log')
    warning=False
    try:
        with log_path.open('w') as log:
            while True:
                chunk=client.log(run['id'],offset);offset=chunk['nextOffset']
                text=chunk['text'];parts.append(text);log.write(text);log.flush()
                warning=record_warning(''.join(parts),config,account,key,log_path.name) or warning
                current=client.status()
                if not current or current['id']!=run['id']:
                    raise RuntimeError('Run identity changed; refusing to control another run')
                if current['status']=='finished':
                    statuses=[p['status'] for p in current['profiles']]
                    status='finished' if statuses and all(x=='succeeded' for x in statuses) else 'failed'
                    break
                fresh=json.loads((account/'settings.json').read_text())
                if (not fresh.get('scheduler_enabled') or fresh.get('account_status','').startswith(('paused','restricted'))
                    or fresh.get('reported_warning_status') in ('restriction','checkpoint','suspended','active_restriction')):
                    status='paused'  # The script reads settings and closes only its own tab.
                if datetime.now(timezone.utc)>=end+timedelta(seconds=90):
                    config.update(scheduler_enabled=False,account_status='paused_runtime_overrun')
                    write_json(account/'settings.json',config)
                    status='overrun';break
                time.sleep(2)
            # Drain the final output written during shutdown.
            chunk=client.log(run['id'],offset);parts.append(chunk['text']);log.write(chunk['text'])
    finally:
        # Do not call the global stop endpoint: it cannot atomically validate a run ID.
        pass
    text=''.join(parts)
    warning=record_warning(text,config,account,key,log_path.name) or warning
    if warning:
        status='paused_warning'
    elif 'stopped: not logged in' in text:
        status='needs_login';config.update(account_status='needs_login',scheduler_enabled=False)
        write_json(account/'settings.json',config)
    elif status=='finished' and 'session ended' not in text:
        status='incomplete'
    summaries=re.findall(r'did: (\d+) reels, (\d+) likes, (\d+) profile visits, (\d+) follows, (\d+) saves, (\d+) stories',text)
    record.update(status=status,finished_at=datetime.now(timezone.utc).isoformat(),
        log='scheduled-runs/'+log_path.name,counts_source='script_reported_not_independently_verified')
    if summaries:
        record['reported_counts']=dict(zip(('content_items','likes','profile_visits','follows','saves','stories'),map(int,summaries[-1])))
    else:record['reported_counts']=None
    with (account/'progress.md').open('a') as f:
        f.write('\n## Automated scheduled session '+key+' GMT\n\nOutcome: '+status+'. Evidence: '+record['log']+'. Reported counts: '+json.dumps(record['reported_counts'])+'. Interrupted actions without counters remain unreported.\n')

def execute_backend(config,account,key,state):
    backend=config.get('execution_backend','aliasmode')
    if backend=='phone-harness':
        from phone_warmup import run_session
        result=run_session(account)
        state['runs'][key].update(result,backend=backend)
    elif backend=='aliasmode':
        from aliasmode_scripts import AliasModeScripts
        helper=config.get('aliasmode_helper')
        if helper:
            import subprocess
            subprocess.run([helper,'profiles','list'],check=True,timeout=180,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        execute(config,account,key,state,AliasModeScripts())
    else:raise ValueError('Unknown execution backend; refusing to fall back to another device')

def tick(account,check=False):
    account=Path(account).resolve()
    with (account/'.scheduler.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'locked'}
        config=json.loads((account/'settings.json').read_text())
        for name in ('SOP.md','progress.md','schedule.md','warnings.md'):
            (account/name).read_text()
        if check:
            backend=config.get('execution_backend','aliasmode')
            if backend=='phone-harness':
                from phone_warmup import check_account
                return check_account(account)
            if backend!='aliasmode':raise ValueError('Unknown execution backend')
            from aliasmode_scripts import AliasModeScripts
            client=AliasModeScripts();current=client.status()
            return {'status':'ready','schedule':config.get('schedule'),'another_script_running':bool(current and current['status']!='finished')}
        state_path=account/'scheduler-state.json'
        state=json.loads(state_path.read_text()) if state_path.exists() else {}
        key=claim_slot(config,state,datetime.now(timezone.utc))
        write_json(state_path,state)
        if not key:return {'status':'no_due_session'}
        try:
            execute_backend(config,account,key,state)
        except Exception as error:
            fresh=json.loads((account/'settings.json').read_text())
            status='paused_warning' if fresh.get('account_status')=='paused_restriction' else 'failed'
            state['runs'][key].update(status=status,error=type(error).__name__+': '+str(error))
        finally:write_json(state_path,state)
        return {'status':state['runs'][key]['status'],'slot':key}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account',type=Path,required=True)
    parser.add_argument('--check',action='store_true',help='Read-only runtime check; never starts a session')
    parser.add_argument('--loop',action='store_true',help='Portable foreground minute loop')
    args=parser.parse_args()
    while True:
        try:print(json.dumps(tick(args.account,args.check)),flush=True)
        except Exception as e:print(json.dumps({'status':'error','error':type(e).__name__+': '+str(e)}),flush=True)
        if not args.loop:break
        time.sleep(60)
