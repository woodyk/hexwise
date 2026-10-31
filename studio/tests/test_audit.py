"""Regression checks for recovery, prompt execution and format boundaries."""
import io,json,os,struct,sys,tempfile,threading,unittest,urllib.error,subprocess
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import sha
from server import App
from providers import Providers,request
from preferences import session_settings
from validation import check_candidate

class Audit(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.app=App(self.root/'workspace',self.root/'data')
 def tearDown(self):self.temp.cleanup()
 def project(self,data=b'AB',name='file.txt'):
  path=self.app.workspace/name;path.write_bytes(data);return self.app.dispatch('open',dict(path=str(path)))
 def task(self,p,**kwargs):return dict(project=p['id'],snapshot=p['current'],text='Change A to C',profile='web-document',provider='ollama',model='test',**kwargs)
 def test_slow_file_read_does_not_block_other_projects(self):
  p=self.project();blocked=self.app.workspace/'delayed.bin';blocked.write_bytes(b'XX')
  started=threading.Event();release=threading.Event();saved=threading.Event();original_open=Path.open;errors=[]
  class SlowFile:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,*args):started.set();release.wait(5);return b'XX'
  def intercepted(path,*args,**kwargs):
   if path==blocked and args and args[0]=='rb':return SlowFile()
   return original_open(path,*args,**kwargs)
  def stage():
   try:self.app.projects.snapshot(p['id'],b'CD','Other session');saved.set()
   except Exception as error:errors.append(error)
  with patch.object(Path,'open',intercepted):
   opening=threading.Thread(target=lambda:self.app.projects.open(blocked));opening.start();self.assertTrue(started.wait(2))
   staging=threading.Thread(target=stage);staging.start()
   try:independent=saved.wait(1)
   finally:release.set();opening.join(5);staging.join(5)
  self.assertTrue(independent,'external reads must not hold the project lock');self.assertFalse(errors)
 def test_preferences_survive_restart_and_reject_secrets(self):
  values=dict(folder=str(self.app.workspace),paneSizes={'--left':230},provider='ollama',models={'ollama':'local/model:q4'},bytesPerRow=8,rightPanel='prompts',contextBytes=65536)
  self.app.dispatch('preferences',values);self.assertEqual(App(self.app.workspace,self.app.data_dir).dispatch('bootstrap',{})['preferences'],values)
  for bad in ({'api_key':'secret'},{'paneSizes':{'--left':100000}},{'contextBytes':32}):
   with self.assertRaises(ValueError):self.app.dispatch('preferences',bad)
 def test_project_settings_survive_reopen(self):
  p=self.project();settings=dict(provider='ollama',model='local:q4',profile='linux-aarch64',chain=['search','layout'],layout=dict(template='grid',rows=4,columns=4))
  self.app.dispatch('session',dict(project=p['id'],session=settings));restored=App(self.app.workspace,self.app.data_dir).dispatch('project',dict(project=p['id']))
  self.assertEqual(restored['session'],settings);self.assertEqual(restored['profile'],'linux-aarch64')
 def test_every_baked_profile_loads(self):
  profiles=self.app.dispatch('bootstrap',{})['profiles']
  self.assertEqual(len(profiles),32)
  for profile in profiles:self.assertGreater(len(self.app.profile(profile['id'])),100)
 def test_bad_chain_and_layout_rejected(self):
  for settings in ({'chain':['search']*9},{'chain':['search','search']},{'chain':['missing']},{'layout':{'template':'grid','rows':2.5,'columns':4}}):
   with self.assertRaises(ValueError):session_settings(settings,{'layout','search'})
 def test_four_templates_have_distinct_controls(self):
  markers={'grid':b'Explore panel','sidebar':b"showView('library'",'master-detail':b'saveNote()','studio':b'previewDocument()'};contents=[]
  for name,marker in markers.items():
   p=self.app.dispatch('create',dict(name=name+'.html',template=name,rows=4,columns=4));raw=self.app.projects.data(p['id']);self.assertIn(marker,raw);contents.append(raw)
  self.assertEqual(len(set(contents)),4)
  for n in (0,9,2.5,True):
   with self.assertRaises(ValueError):self.app.dispatch('create',dict(name='invalid.html',template='grid',rows=n))
 def test_restore_export_and_tampering(self):
  p=self.project();p2=self.app.dispatch('stage',dict(project=p['id'],snapshot=p['current'],hex='4344'));p3=self.app.dispatch('restore',dict(project=p['id'],snapshot=p2['current'],restore=p['current']))
  self.assertEqual(len(p3['snapshots']),3);out=self.root/'export';self.app.dispatch('export',dict(project=p['id'],path=str(out)));self.assertEqual(out.read_bytes(),b'AB')
  with self.assertRaises(ValueError):self.app.dispatch('export',dict(project=p['id'],path=str(out)))
  (self.app.projects.folder(p['id'])/'snapshots'/(p3['current']+'.bin')).write_bytes(b'XX')
  with self.assertRaisesRegex(ValueError,'integrity'):self.app.projects.data(p['id'])
 def test_partial_context_blocks_unseen_edits_and_replacement(self):
  for i,proposal in enumerate((dict(artifact={'hex':'43'}),dict(edits=[dict(offset=0,before='41',after='43')]))):
   p=self.project(name=str(i)+'.txt');response=json.dumps(dict(message='Edit',base_sha256=sha(b'AB'),**proposal))
   with patch.object(self.app.providers,'chat',return_value=response):result=self.app.chat(self.task(p,offset=1))
   self.assertEqual(self.app.projects.data(p['id']),b'AB');self.assertEqual(len(result['snapshots']),1)
 def test_context_size_and_analysis_only(self):
  p=self.project(b'A'*20000);seen=[]
  def reply(provider,model,system,messages):
   task=json.loads(messages[-1]['content']);seen.append(task);return json.dumps(dict(message='Must not edit',base_sha256=task['base_sha256'],edits=[dict(offset=0,before='41',after='43')]))
  with patch.object(self.app.providers,'chat',side_effect=reply):result=self.app.chat(self.task(p,chain=['tests'],context_bytes=16384))
  self.assertEqual(len(bytes.fromhex(seen[0]['context_hex'])),16384);self.assertEqual(len(result['snapshots']),1);self.assertIn('analysis-only',result['messages'][-1]['text'])
 def test_cancel_and_concurrent_request(self):
  p=self.project();started=threading.Event();release=threading.Event();results=[]
  def reply(*args):
   started.set();release.wait(3);return json.dumps(dict(message='Edit',base_sha256=sha(b'AB'),edits=[dict(offset=0,before='41',after='43')]))
  with patch.object(self.app.providers,'chat',side_effect=reply):
   thread=threading.Thread(target=lambda:results.append(self.app.chat(self.task(p,chain=['search','settings']))));thread.start()
   try:
    self.assertTrue(started.wait(2))
    with self.assertRaisesRegex(ValueError,'already running'):self.app.chat(self.task(p))
    self.assertTrue(self.app.dispatch('cancel',dict(project=p['id']))['cancel_requested'])
   finally:release.set();thread.join(5)
  self.assertFalse(thread.is_alive());self.assertEqual(self.app.projects.data(p['id']),b'AB');self.assertEqual(len(results[0]['messages']),3);self.assertEqual(results[0]['messages'][1]['outcome'],'cancelled')
 def test_analysis_response_retains_explicit_outcome(self):
  p=self.project()
  with patch.object(self.app.providers,'chat',return_value=json.dumps(dict(message='Analysis only',base_sha256=sha(b'AB')))):
   result=self.app.chat(self.task(p))
  self.assertEqual(result['messages'][-1]['outcome'],'analysis');self.assertEqual(len(result['snapshots']),1)
 def test_provider_failure_retained(self):
  p=self.project()
  with patch.object(self.app.providers,'chat',side_effect=ValueError('Provider HTTP 429')):
   with self.assertRaises(ValueError):self.app.chat(self.task(p))
  self.assertIn('429',self.app.projects.load(p['id'])['messages'][-1]['text']);self.assertEqual(self.app.projects.data(p['id']),b'AB')
 def test_compatible_providers(self):
  providers=Providers()
  with patch.dict(os.environ,{k:'test' for k in ('DEEPSEEK_API_KEY','MISTRAL_API_KEY','GROQ_API_KEY','XAI_API_KEY')}):
   for name in ('deepseek','mistral','groq','xai','compatible'):
    with patch('providers.request',return_value={'choices':[{'message':{'content':'OK'}}]}) as call:
     self.assertEqual(providers.chat(name,'org/model:q4','system',[dict(role='user',content='Hi')]),'OK');self.assertTrue(call.call_args.args[0].endswith('/chat/completions'))
   with patch('providers.request',return_value={'models':[{'name':'local:q4'}]}):self.assertEqual(providers.models('ollama'),['local:q4'])
 def test_error_body_does_not_echo_keys(self):
  error=urllib.error.HTTPError('https://example.invalid',429,'error',{},io.BytesIO(b'{"error":{"code":"insufficient_quota","message":"secret-123"}}'))
  with patch('urllib.request.urlopen',side_effect=error):
   with self.assertRaises(ValueError) as caught:request('https://example.invalid')
  self.assertIn('insufficient_quota',str(caught.exception));self.assertNotIn('secret-123',str(caught.exception))
 def test_git_commit_branch_and_local_remote(self):
  repo=self.root/'repo';repo.mkdir();remote=self.root/'remote.git'
  def git(*args):return subprocess.run(['git',*map(str,args)],check=True,capture_output=True)
  git('init','--bare',remote);self.app.git('init',repo,{})
  git('-C',repo,'config','user.name','Hexwise Test');git('-C',repo,'config','user.email','hexwise@example.invalid');(repo/'file').write_text('test')
  self.assertTrue(self.app.git('stage',repo,{})['ok']);self.assertTrue(self.app.git('commit',repo,dict(message='Fixture commit'))['ok']);self.assertTrue(self.app.git('branch',repo,dict(name='feature/test'))['ok'])
  git('-C',repo,'remote','add','origin',remote);git('-C',repo,'config','push.default','current')
  for action in ('push','fetch','status','diff','log'):self.assertTrue(self.app.git(action,repo,{})['ok'])
 def test_runner_resource_controls_and_expected_output(self):
  import io
  from runner import run_candidate
  header=b'\x7fELF'+bytes([2,1,1])+bytes(9)+struct.pack('<HHIQQQIHHHHHH',2,62,1,0,64,0,0,64,56,1,64,0,0)+struct.pack('<IIQQQQQQ',1,5,0,0,0,120,120,4096)
  class Process:
   stdout=io.BytesIO(b'expected\n');returncode=0
   def wait(self,timeout=None):return 0
  with patch('runner.shutil.which',return_value='/test/docker'),patch('runner.subprocess.Popen',return_value=Process()) as start,patch('runner.subprocess.run') as cleanup:
   result=run_candidate(header,'linux-x86_64','test:local',['argument'],self.root/'runs','expected\n')
  self.assertTrue(result['expected_stdout_matches']);command=start.call_args.args[0]
  for flag in ('--read-only','--cap-drop','--security-opt','--memory','--pids-limit','--user','--network'):self.assertIn(flag,command)
  self.assertEqual(command[command.index('--network')+1],'none');self.assertEqual(command[command.index('--pull')+1],'never')
  self.assertEqual(cleanup.call_args.args[0][-1],command[command.index('--name')+1])
  with self.assertRaisesRegex(ValueError,'architecture'):run_candidate(header,'linux-aarch64','image',[],self.root)
 def test_github_draft_pr_shape(self):
  self.app.github_key='fixture-token'
  with patch('server.request',return_value={'ok':True}) as call:
   self.app.dispatch('github',dict(action='create_pr',repository='owner/repo',title='Test',head='feature',base='main'));self.assertEqual(call.call_args.args[0],'https://api.github.com/repos/owner/repo/pulls');self.assertTrue(call.call_args.args[1]['draft']);self.assertEqual(call.call_args.args[2]['Authorization'],'Bearer fixture-token')
 def test_bad_extension_objects(self):
  for library in ([None],[dict(id='ok',name=1,prompt='text')],[dict(id='ok',name='Text',prompt='x',category=[])]):
   with self.assertRaises(ValueError):self.app.dispatch('extensions',dict(extensions=library))

class Formats(unittest.TestCase):
 def test_elf_bounds(self):
  header=b'\x7fELF'+bytes([2,1,1])+bytes(9)+struct.pack('<HHIQQQIHHHHHH',2,62,1,0,0,0,0,64,56,0,64,0,0)
  self.assertEqual(check_candidate(header)['structural'],'basic_checks_passed');bad=bytearray(header);struct.pack_into('<Q',bad,32,64);struct.pack_into('<H',bad,56,1)
  self.assertEqual(check_candidate(bad)['structural'],'failed');self.assertEqual(check_candidate(b'\x7fELF')['structural'],'failed')
 def test_macho_and_pe_truncation(self):
  for data in (b'\xcf\xfa\xed\xfe',b'MZ'+bytes(62)):self.assertEqual(check_candidate(data)['structural'],'failed')
 def test_wasm_and_documents(self):
  self.assertEqual(check_candidate(b'\0asm\x01\0\0\0')['structural'],'basic_checks_passed');self.assertEqual(check_candidate(b'\0asm\x01\0\0\0\x01\x05x')['structural'],'failed')
  self.assertEqual(check_candidate(b'{"a":1}','test.json','web-document')['structural'],'basic_checks_passed');self.assertEqual(check_candidate(b'{','test.json','web-document')['structural'],'failed');self.assertEqual(check_candidate(b'print(','test.py','web-document')['structural'],'failed')

if __name__=='__main__':unittest.main()
