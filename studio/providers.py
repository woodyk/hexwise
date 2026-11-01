"""HTTP provider adapters. Keys stay in server memory/environment, never in project files."""
import http.client
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

PRESETS = {
 'openai':dict(label='OpenAI',base='https://api.openai.com/v1',env='OPENAI_API_KEY',kind='responses'),
 'anthropic':dict(label='Anthropic',base='https://api.anthropic.com/v1',env='ANTHROPIC_API_KEY',kind='anthropic'),
 'gemini':dict(label='Google Gemini',base='https://generativelanguage.googleapis.com/v1beta',env='GEMINI_API_KEY',kind='gemini'),
 'ollama':dict(label='Ollama · local',base='http://127.0.0.1:11434',env='',kind='ollama'),
 'deepseek':dict(label='DeepSeek',base='https://api.deepseek.com',env='DEEPSEEK_API_KEY',kind='compatible'),
 'mistral':dict(label='Mistral',base='https://api.mistral.ai/v1',env='MISTRAL_API_KEY',kind='compatible'),
 'groq':dict(label='Groq',base='https://api.groq.com/openai/v1',env='GROQ_API_KEY',kind='compatible'),
 'xai':dict(label='xAI',base='https://api.x.ai/v1',env='XAI_API_KEY',kind='compatible'),
 'compatible':dict(label='OpenAI-compatible endpoint',base='http://127.0.0.1:1234/v1',env='HEXWISE_API_KEY',kind='compatible'),
}


# Three exclusive response shapes keep local decoding aligned with the host protocol.
RESPONSE_SCHEMA = {'oneOf': [{'type': 'object',
            'properties': {'message': {'type': 'string'},
                           'base_sha256': {'type': 'string'},
                           'edits': {'type': 'array',
                                     'items': {'type': 'object',
                                               'properties': {'offset': {'type': 'integer'},
                                                              'before': {'type': 'string'},
                                                              'after': {'type': 'string'}},
                                               'required': ['offset', 'before', 'after'],
                                               'additionalProperties': False}}},
            'required': ['message', 'base_sha256', 'edits'],
            'additionalProperties': False},
           {'type': 'object',
            'properties': {'message': {'type': 'string'},
                           'base_sha256': {'type': 'string'},
                           'artifact': {'type': 'object',
                                        'properties': {'hex': {'type': 'string'}},
                                        'required': ['hex'],
                                        'additionalProperties': False}},
            'required': ['message', 'base_sha256', 'artifact'],
            'additionalProperties': False},
           {'type': 'object',
            'properties': {'message': {'type': 'string'}, 'base_sha256': {'type': 'string'},
                           'status': {'type': 'string', 'enum': ['analysis','needs_input','unsupported']},
                           'missing': {'type': 'array', 'items': {'type': 'string'}}},
            'required': ['message', 'base_sha256'],
            'additionalProperties': False}]}


def request(url, payload=None, headers=None):
    req = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={'Content-Type':'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read(8 * 1024 * 1024))
    except urllib.error.HTTPError as error:
        # Read only a constrained error code; provider messages may echo prompts/keys.
        code=''
        try:
            detail=json.loads(error.read(65536)).get('error',{})
            value=detail.get('code') or detail.get('type') or detail.get('status')
            if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',value):code=' ('+value+')'
        except (ValueError,AttributeError):pass
        reason={401:'Authentication was rejected.',403:'The key or project lacks permission.',
                404:'The model or endpoint was not found.',429:'A rate limit or API quota was reached.'}.get(error.code,'Check model access and request compatibility.')
        raise ValueError(f'Provider returned HTTP {error.code}{code}. {reason}') from None
    except (json.JSONDecodeError,UnicodeDecodeError):
        raise ValueError('Provider returned an invalid JSON response.') from None
    except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
        raise ValueError('Provider connection failed or timed out. Check endpoint and local service.') from None


class Providers:
    def __init__(self):
        self.sessions = {}

    def config(self, name):
        if name not in PRESETS:
            raise ValueError('Unknown provider.')
        p = {**PRESETS[name], **self.sessions.get(name,{})}
        key = p.get('key') or os.environ.get(p['env'],'')
        if name == 'gemini':
            key = key or os.environ.get('GOOGLE_API_KEY','')
        return p, key

    def configure(self, name, base=None, key=None):
        preset, _ = self.config(name)
        config = self.sessions.setdefault(name,{})
        if base:
            parsed = urllib.parse.urlparse(base)
            if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError('Use an HTTP(S) endpoint without embedded credentials or query strings.')
            if parsed.scheme == 'http' and parsed.hostname not in ('localhost','127.0.0.1','::1'):
                raise ValueError('Remote providers require HTTPS.')
            # Do not forward a provider environment secret to an unrelated custom host.
            if parsed.hostname != urllib.parse.urlparse(preset['base']).hostname and name != 'compatible':
                raise ValueError('Use the custom endpoint provider for a different host.')
            config['base'] = base.rstrip('/')
        if key:
            config['key'] = key
        return self.status()

    def status(self):
        return [dict(id=n,label=p['label'],base=self.config(n)[0]['base'],
                     configured=bool(self.config(n)[1]) or n=='ollama') for n,p in PRESETS.items()]

    def headers(self, p, key):
        if p['kind'] == 'anthropic':
            return {'x-api-key':key,'anthropic-version':'2023-06-01'}
        if p['kind'] == 'gemini':
            return {'x-goog-api-key':key}
        return {'Authorization':'Bearer '+key} if key else {}

    def models(self, name):
        p,key = self.config(name)
        if not key and p['kind'] not in ('ollama','compatible'):
            raise ValueError('No credential is configured for this provider.')
        data = request(p['base'] + ('/api/tags' if p['kind']=='ollama' else '/models'),headers=self.headers(p,key))
        if p['kind']=='ollama':
            return [m['name'] for m in data.get('models',[])]
        if p['kind']=='gemini':
            return [m['name'].removeprefix('models/') for m in data.get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[])]
        return [m['id'] for m in data.get('data',[])]

    def chat(self, name, model, system, messages):
        if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,199}',model):
            raise ValueError('Choose a valid model ID.')
        p,key = self.config(name)
        if not key and p['kind'] not in ('ollama','compatible'):
            raise ValueError('No credential is configured for this provider.')
        headers=self.headers(p,key)
        kind=p['kind']
        if kind=='responses':
            data=request(p['base']+'/responses',dict(model=model,instructions=system,input=messages,max_output_tokens=8192),headers)
            return '\n'.join(c.get('text','') for item in data.get('output',[]) for c in item.get('content',[]) if c.get('type')=='output_text')
        if kind=='anthropic':
            data=request(p['base']+'/messages',dict(model=model,system=system,messages=messages,max_tokens=8192),headers)
            return '\n'.join(c.get('text','') for c in data.get('content',[]) if c.get('type')=='text')
        if kind=='gemini':
            body=dict(systemInstruction={'parts':[{'text':system}]},contents=[{'role':'model' if m['role']=='assistant' else 'user',
                'parts':[{'text':m['content']}]} for m in messages],generationConfig={'maxOutputTokens':8192})
            data=request(p['base']+'/models/'+urllib.parse.quote(model,safe='')+':generateContent',body,headers)
            return '\n'.join(p.get('text','') for c in data.get('candidates',[]) for p in c.get('content',{}).get('parts',[]) if not p.get('thought'))
        full=[{'role':'system','content':system}]+messages
        if kind=='ollama':
            return request(p['base']+'/api/chat',dict(model=model,messages=full,stream=False,format=RESPONSE_SCHEMA,options={'temperature':0}),headers).get('message',{}).get('content','')
        data=request(p['base']+'/chat/completions',dict(model=model,messages=full,max_tokens=8192),headers)
        return data['choices'][0]['message'].get('content','')
