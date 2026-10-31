"""Validated non-secret preferences, independent of ephemeral browser origins."""
import json
import re
import threading
from pathlib import Path
from core import atomic
from providers import PRESETS


def session_settings(value, extension_ids):
    if not isinstance(value,dict) or set(value)-{'provider','model','profile','chain','layout'}:
        raise ValueError('Invalid session settings.')
    provider=value.get('provider','openai')
    model=value.get('model','')
    if provider not in PRESETS or not isinstance(model,str) or len(model)>200:
        raise ValueError('Invalid provider or model setting.')
    chain=value.get('chain',[])
    if not isinstance(chain,list) or len(chain)>8 or any(not isinstance(i,str) or i not in extension_ids for i in chain) or len(set(chain))!=len(chain):
        raise ValueError('Prompt chains require up to eight unique known extensions.')
    layout=value.get('layout')
    if layout is not None:
        if not isinstance(layout,dict) or set(layout)!={'template','rows','columns'}:
            raise ValueError('Invalid layout settings.')
        if layout['template'] not in ('grid','sidebar','master-detail','studio') or any(type(layout[k]) is not int or not 1<=layout[k]<=8 for k in ('rows','columns')):
            raise ValueError('Invalid layout settings.')
    profile=value.get('profile','')
    if not isinstance(profile,str) or len(profile)>120:raise ValueError('Invalid target profile.')
    return dict(provider=provider,model=model,profile=profile,chain=chain,layout=layout if 'layout' in chain else None)


class Preferences:
    def __init__(self,path):
        self.path=Path(path);self.lock=threading.RLock()

    def load(self):
        try:
            value=json.loads(self.path.read_text())
            return value if isinstance(value,dict) else {}
        except (OSError,ValueError):return {}

    def update(self,value):
        if not isinstance(value,dict) or set(value)-{'folder','paneSizes','provider','models','activeProject','bytesPerRow','rightPanel','contextBytes'}:
            raise ValueError('Only non-secret workspace preferences can be stored.')
        for k in ('folder','activeProject'):
            if k in value and (not isinstance(value[k],str) or len(value[k])>4096):raise ValueError('Invalid workspace path or identity.')
        if value.get('activeProject') and not re.fullmatch('[a-f0-9]{32}',value['activeProject']):raise ValueError('Invalid project identity.')
        if 'provider' in value and value['provider'] not in PRESETS:raise ValueError('Invalid provider.')
        if 'models' in value:
            if not isinstance(value['models'],dict) or any(k not in PRESETS or not isinstance(v,str) or len(v)>200 for k,v in value['models'].items()):raise ValueError('Invalid saved models.')
        for field,allowed in [('bytesPerRow',(8,16)),('rightPanel',('chat','history','prompts')),('contextBytes',(4096,16384,65536))]:
            if field in value and value[field] not in allowed:raise ValueError('Invalid workspace setting: '+field)
        if 'paneSizes' in value:
            ranges={'--left':(160,420),'--right':(270,650),'--composer':(165,440)}
            if not isinstance(value['paneSizes'],dict):raise ValueError('Invalid pane sizes.')
            for k,v in value['paneSizes'].items():
                if k not in ranges or type(v) not in (int,float) or not ranges[k][0]<=v<=ranges[k][1]:raise ValueError('Invalid pane size.')
        with self.lock:
            result={**self.load(),**value};atomic(self.path,json.dumps(result,indent=2).encode());return result
