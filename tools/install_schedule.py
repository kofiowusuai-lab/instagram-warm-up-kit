#!/usr/bin/env python3
"""Install a user-level macOS minute tick. Schedule rules remain fixed GMT in settings."""
import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def install(account):
    if sys.platform!='darwin':raise RuntimeError('For Linux use scheduler.py --account PATH --loop under a user service')
    account=Path(account).resolve()
    if not (account/'settings.json').is_file():raise RuntimeError('Account settings not found')
    label='local.instagram-warmup.'+account.name
    directory=Path.home()/'Library/LaunchAgents';directory.mkdir(exist_ok=True)
    logs=account/'scheduler-service';logs.mkdir(exist_ok=True)
    path=directory/(label+'.plist')
    job={'Label':label,'ProgramArguments':[sys.executable,str(ROOT/'tools/scheduler.py'),'--account',str(account)],
         'StartInterval':60,'RunAtLoad':True,'WorkingDirectory':str(ROOT),
         'StandardOutPath':str(logs/'stdout.log'),'StandardErrorPath':str(logs/'stderr.log'),
         'ProcessType':'Background','EnvironmentVariables':{'PATH':'/usr/bin:/bin:/usr/sbin:/sbin'}}
    path.write_bytes(plistlib.dumps(job));path.chmod(0o600)
    domain='gui/'+str(os.getuid())
    subprocess.run(['launchctl','bootout',domain+'/'+label],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(['launchctl','bootstrap',domain,str(path)],check=True)
    print('Installed:',label)
    print('Inspect: launchctl print '+domain+'/'+label)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--account',type=Path,required=True)
    install(parser.parse_args().account)
