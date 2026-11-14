"""Pinned AliasMode beta.74 authenticated local Scripts adapter; never log secrets."""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

class AliasModeScripts:
    def __init__(self, descriptor=None):
        if descriptor is None:
            home=Path.home()
            root=(home/'Library/Application Support' if sys.platform=='darwin' else Path(os.getenv('XDG_DATA_HOME',str(home/'.local/share'))))
            descriptor=root/'com.aliasmode.desktop/agent-runtime.json'
        value=json.loads(Path(descriptor).read_text())
        if value.get('appVersion')!='0.1.0-beta.74' or value.get('protocol')!='aliasmode-runtime-v1':
            raise RuntimeError('Unsupported AliasMode runtime; revalidate adapter before scheduling')
        if not re.fullmatch('[a-f0-9]{64}',value.get('nonce','')):raise RuntimeError('Invalid local runtime descriptor')
        port=value.get('port')
        if type(port) is not int or not 1<=port<=65535:raise RuntimeError('Invalid local runtime port')
        self.origin='http://127.0.0.1:'+str(port)
        self.nonce=value['nonce']
        health=self.request('/ui/api/health')
        if health.get('instance')!=value.get('generation') or health.get('version')!=value['appVersion']:
            raise RuntimeError('AliasMode runtime identity changed; retry on the next scheduled slot')
    def request(self,path,payload=None,method=None):
        data=json.dumps(payload).encode() if payload is not None else None
        request=urllib.request.Request(self.origin+path,data=data,method=method,
            headers={'Authorization':'Bearer '+self.nonce,'Content-Type':'application/json','Origin':self.origin})
        try:
            with urllib.request.urlopen(request,timeout=30) as response:result=json.load(response)
        except Exception as error:
            raise RuntimeError('AliasMode local Scripts request failed ('+type(error).__name__+')') from None
        if result.get('ok') is not True:raise RuntimeError('AliasMode rejected Scripts request')
        return result
    def status(self):return self.request('/ui/api/scripts/run')['run']
    def ensure_script(self,name,source):
        scripts=self.request('/ui/api/scripts')['scripts']
        found=next((x for x in scripts if x['name']==name),None)
        if found:
            full=self.request('/ui/api/scripts/'+found['id'])['script']
            if full['source']!=source:raise RuntimeError('Saved timed script differs; review it before enabling runs')
            return full['id']
        body={'name':name,'description':'Timed passive sessions with cooperative duration budget','language':'javascript','source':source}
        return self.request('/ui/api/scripts',body)['script']['id']
    def start(self,script_id,profile_id,inputs):
        return self.request('/ui/api/scripts/run',{'scriptId':script_id,'profileIds':[profile_id],
            'inputs':inputs,'useCredentials':False,'concurrency':1})['run']
    def log(self,run_id,offset):
        import urllib.parse
        return self.request('/ui/api/scripts/log?'+urllib.parse.urlencode({'runId':run_id,'offset':offset}))
