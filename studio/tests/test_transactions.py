import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Projects, apply_proposal, sha, detect
from providers import Providers
from server import App, template_html
from runner import run_candidate


class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.original=self.root/'example.bin'
        self.original.write_bytes(b'original data')
        self.original.chmod(0o755)
        self.store=Projects(self.root/'projects')
        self.project=self.store.open(self.original)

    def tearDown(self):self.temp.cleanup()

    def test_open_protects_original(self):
        self.assertEqual(self.store.data(self.project['id']),b'original data')
        self.assertEqual(self.original.read_bytes(),b'original data')
        self.assertEqual(len(self.project['snapshots']),1)

    def test_staging_never_writes_original(self):
        p=self.store.snapshot(self.project['id'],b'new candidate','test',expected=self.project['current'])
        self.assertEqual(self.original.read_bytes(),b'original data')
        self.assertEqual(self.store.data(p['id']),b'new candidate')

    def test_accept_preserves_exact_backup_and_mode(self):
        p=self.store.snapshot(self.project['id'],b'accepted','test')
        p=self.store.accept(p['id'],p['current'])
        self.assertEqual(self.original.read_bytes(),b'accepted')
        self.assertEqual(Path(p['accepted']['backup']).read_bytes(),b'original data')
        self.assertEqual(self.original.stat().st_mode&0o777,0o755)

    def test_repeated_accept_keeps_both_backups(self):
        p=self.store.snapshot(self.project['id'],b'first','test')
        first=self.store.accept(p['id'],p['current'])
        p=self.store.snapshot(p['id'],b'second','test')
        second=self.store.accept(p['id'],p['current'])
        self.assertEqual(Path(first['accepted']['backup']).read_bytes(),b'original data')
        self.assertEqual(Path(second['accepted']['backup']).read_bytes(),b'first')

    def test_external_change_blocks_acceptance(self):
        p=self.store.snapshot(self.project['id'],b'candidate','test')
        self.original.write_bytes(b'external change')
        with self.assertRaisesRegex(ValueError,'outside Hexwise'):self.store.accept(p['id'],p['current'])
        self.assertEqual(self.original.read_bytes(),b'external change')

    def test_stale_snapshot_blocks_stage_and_accept(self):
        self.store.snapshot(self.project['id'],b'newer','test')
        with self.assertRaises(ValueError):self.store.snapshot(self.project['id'],b'stale','test',expected=self.project['current'])
        with self.assertRaises(ValueError):self.store.accept(self.project['id'],self.project['current'])

    def test_symlink_original_rejected(self):
        link=self.root/'link';link.symlink_to(self.original)
        with self.assertRaises(ValueError):self.store.open(link)
        p=self.store.snapshot(self.project['id'],b'candidate','test')
        self.original.unlink();self.original.symlink_to(link)
        with self.assertRaises(ValueError):self.store.accept(p['id'],p['current'])

    def test_snapshot_cannot_escape_project(self):
        with self.assertRaises(ValueError):self.store.data(self.project['id'],'../../secret')
        with self.assertRaises(ValueError):self.store.load('../secret')

    def test_patch_requires_hash_and_expected_bytes(self):
        data=b'abcdef'
        p={'base_sha256':sha(data),'edits':[{'offset':1,'before':'6263','after':'5859'}]}
        self.assertEqual(apply_proposal(data,p),b'aXYdef')
        p['base_sha256']='0'*64
        with self.assertRaises(ValueError):apply_proposal(data,p)
        p['base_sha256']=sha(data);p['edits'][0]['before']='0000'
        with self.assertRaises(ValueError):apply_proposal(data,p)

    def test_overlapping_and_resizing_patch_rejected(self):
        data=b'abcdef'
        for edits in [[{'offset':0,'before':'6162','after':'63'}],
                      [{'offset':0,'before':'6162','after':'6364'},{'offset':1,'before':'6263','after':'6465'}],
                      [{'offset':True,'before':'62','after':'63'}]]:
            with self.assertRaises(ValueError):apply_proposal(data,dict(base_sha256=sha(data),edits=edits))

    def test_complete_replacement_allows_new_file_length(self):
        self.assertEqual(apply_proposal(b'',dict(base_sha256=sha(b''),artifact={'hex':'4869'})),b'Hi')


class Integration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.app=App(self.root/'workspace',self.root/'state')
    def tearDown(self):self.temp.cleanup()

    def test_gui_template_and_project_created(self):
        p=self.app.dispatch('create',dict(name='app.html',template='grid',rows=4,columns=4))
        raw=self.app.projects.data(p['id'])
        self.assertEqual(raw.count(b'class="card"'),16)
        self.assertEqual(p['profile'],'web-document')
        with self.assertRaises(ValueError):self.app.dispatch('create',dict(name='app.html'))

    def test_new_file_path_cannot_traverse(self):
        with self.assertRaises(ValueError):self.app.dispatch('create',dict(name='../escape'))

    def test_prompt_library_available_and_composable(self):
        boot=self.app.dispatch('bootstrap',{})
        self.assertEqual(len(boot['profiles']),32)
        self.assertIn('windows-x64',self.app.profile('windows-x64'))
        with self.assertRaises(ValueError):self.app.profile('../other')

    def test_chain_snapshots_each_applied_step(self):
        p=self.app.dispatch('create',dict(name='file.txt'))
        self.app.projects.snapshot(p['id'],b'AB','seed')
        p=self.app.projects.load(p['id'])
        responses=[json.dumps(dict(message='First',base_sha256=sha(b'AB'),edits=[dict(offset=0,before='41',after='43')])),
                   json.dumps(dict(message='Second',base_sha256=sha(b'CB'),edits=[dict(offset=1,before='42',after='44')]))]
        with patch.object(self.app.providers,'chat',side_effect=responses):
            result=self.app.chat(dict(project=p['id'],snapshot=p['current'],text='Make changes',profile='web-document',
                                     provider='ollama',model='test',chain=['layout','accessibility']))
        self.assertEqual(self.app.projects.data(p['id']),b'CD')
        self.assertEqual(len(result['snapshots']),4)
        self.assertEqual([m['outcome'] for m in result['messages'] if m['role']=='assistant'],['applied','applied'])
        self.assertEqual(Path(p['original']).read_bytes(),b'')

    def test_stale_ai_proposal_retained_not_applied(self):
        p=self.app.dispatch('create',dict(name='file.txt'))
        response=json.dumps(dict(message='Wrong base',base_sha256='0'*64,artifact={'hex':'41'}))
        with patch.object(self.app.providers,'chat',return_value=response):
            result=self.app.chat(dict(project=p['id'],snapshot=p['current'],text='Make a change',profile='web-document',provider='ollama',model='test'))
        self.assertEqual(len(result['snapshots']),1)
        self.assertTrue(any(m['role']=='system' for m in result['messages']))

    def test_extensions_persist_without_secret_settings(self):
        self.app.dispatch('extensions',dict(extensions=[dict(id='custom',name='Feature',prompt='Add it')]))
        self.assertEqual(self.app.extensions()[0]['id'],'custom')
        self.app.providers.configure('openai',key='test-session-secret')
        for file in (self.root/'state').rglob('*'):
            if file.is_file():self.assertNotIn(b'test-session-secret',file.read_bytes())

    def test_keys_not_sent_to_unrelated_hosts(self):
        with self.assertRaises(ValueError):self.app.providers.configure('openai',base='https://unrelated.invalid/v1')
        with self.assertRaises(ValueError):self.app.providers.configure('compatible',base='http://unrelated.invalid/v1')

    def test_provider_wire_shapes(self):
        providers=Providers()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test','ANTHROPIC_API_KEY':'test','GEMINI_API_KEY':'test'}):
            with patch('providers.request',return_value={'output':[{'content':[{'type':'output_text','text':'OK'}]}]}) as call:
                self.assertEqual(providers.chat('openai','model','system',[{'role':'user','content':'hello'}]),'OK')
                self.assertEqual(call.call_args.args[1]['instructions'],'system')
            with patch('providers.request',return_value={'content':[{'type':'text','text':'OK'}]}) as call:
                self.assertEqual(providers.chat('anthropic','model','system',[{'role':'user','content':'hello'}]),'OK')
                self.assertEqual(call.call_args.args[1]['system'],'system')
            with patch('providers.request',return_value={'candidates':[{'content':{'parts':[{'text':'OK'}]}}]}) as call:
                self.assertEqual(providers.chat('gemini','model','system',[{'role':'user','content':'hello'}]),'OK')
                self.assertIn('systemInstruction',call.call_args.args[1])
            with patch('providers.request',return_value={'message':{'content':'OK'}}) as call:
                self.assertEqual(providers.chat('ollama','model','system',[{'role':'user','content':'hello'}]),'OK')
                self.assertEqual(len(call.call_args.args[1]['format']['oneOf']),3)
                self.assertEqual(call.call_args.args[1]['options']['num_ctx'],32768)
                self.assertEqual(call.call_args.args[1]['options']['num_predict'],8192)

    def test_runner_rejects_other_platforms_without_execution(self):
        with self.assertRaisesRegex(ValueError,'Linux x86-64'):
            run_candidate(b'code','macos-arm64','image',[],self.root)

    def test_runner_rejects_raw_payload_without_execution(self):
        with self.assertRaisesRegex(ValueError,'complete Linux ELF'):
            run_candidate(b'code','linux-x86_64','image',[],self.root)

    def test_target_contract_retained(self):
        p=self.app.dispatch('create',dict(name='target.bin'))
        result=self.app.dispatch('contract',dict(project=p['id'],profile='linux-x86_64',
                                               contract={'signature':'int main(void)','acceptance':'exit 0'}))
        self.assertEqual(result['contract']['acceptance'],'exit 0')

    def test_preview_token_is_scoped_and_distinct_from_api_token(self):
        p=self.app.dispatch('create',dict(name='preview.html',template='grid',rows=1,columns=1))
        result=self.app.dispatch('preview',dict(project=p['id']))
        token=result['url'].split('token=')[1]
        self.assertNotEqual(token,self.app.token)
        self.assertEqual(self.app.preview_tokens[token]['project'],p['id'])
        self.assertEqual(self.app.preview_tokens[token]['snapshot'],p['current'])


if __name__=='__main__':unittest.main()
