"""Exercise the real HTTP boundary and preview isolation on an ephemeral loopback server."""
import http.client,json,sys,tempfile,threading,time,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import App,Handler

class HTTP(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.server.app=App(cls.root/'workspace',cls.root/'data')
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()
 def request(self,path,payload=None,headers=None):
  conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
  conn.request('GET' if payload is None else 'POST',path,body=None if payload is None else json.dumps(payload),headers=headers or {})
  response=conn.getresponse();body=response.read();result=response.status,dict(response.getheaders()),body;conn.close();return result
 def api(self,route,value):return self.request('/api/'+route,value,{'X-Hexwise-Token':self.server.app.token})
 def test_auth_and_host(self):
  self.assertEqual(self.request('/api/bootstrap',{})[0],403)
  self.assertEqual(self.api('bootstrap',{})[0],200)
  self.assertEqual(self.request('/api/bootstrap',{}, {'X-Hexwise-Token':self.server.app.token,'Host':'evil.invalid'})[0],403)
 def test_bad_request_and_static_paths(self):
  self.assertEqual(self.api('bootstrap',[])[0],400)
  self.assertEqual(self.api('missing',{})[0],400)
  self.assertEqual(self.request('/../core.py')[0],404)
  self.assertEqual(self.request('/')[0],200)
  self.assertIn("object-src 'none'",self.request('/')[1]['Content-Security-Policy'])
 def test_preview_scoped_and_pinned(self):
  name='test-'+str(time.time_ns())+'.html'
  status,_,body=self.api('create',dict(name=name,template='grid',rows=1,columns=1));self.assertEqual(status,200);p=json.loads(body)
  status,_,body=self.api('preview',dict(project=p['id']));url=json.loads(body)['url']
  self.assertEqual(self.request('/preview/'+p['id'])[0],403)
  self.assertEqual(self.request('/preview/'+p['id']+'?token='+self.server.app.token)[0],403)
  status,headers,original=self.request(url);self.assertEqual(status,200)
  self.assertIn("connect-src 'none'",headers['Content-Security-Policy']);self.assertIn('sandbox allow-scripts',headers['Content-Security-Policy'])
  self.api('stage',dict(project=p['id'],snapshot=p['current'],hex='4142'))
  self.assertEqual(self.request(url)[2],original)
  self.server.app.preview_tokens[url.split('token=')[1]]['expires']=0
  self.assertEqual(self.request(url)[0],403)
 def test_contract_options_and_draft_over_http(self):
  status,_,body=self.api('contract-options',dict(profile='macos-arm64'));self.assertEqual(status,200)
  options=json.loads(body);self.assertEqual(options['profile_id'],'macos-arm64')
  self.assertIn('Ad-hoc signing',json.dumps(options))
  self.assertEqual(self.api('contract-options',dict(profile='unknown'))[0],400)
  _,_,body=self.api('create',dict(name='contract-test.bin'));project=json.loads(body)
  status,_,body=self.api('contract',dict(project=project['id'],profile='macos-arm64',contract=dict(operation='CREATE',kind='Complete native executable')))
  self.assertEqual(status,200);self.assertEqual(json.loads(body)['contract']['operation'],'CREATE')
 def test_api_transaction_roundtrip(self):
  path=self.server.app.workspace/'roundtrip.txt';path.write_bytes(b'AB')
  status,_,body=self.api('open',dict(path=str(path)));self.assertEqual(status,200);p=json.loads(body)
  status,_,body=self.api('stage',dict(project=p['id'],snapshot=p['current'],hex='4344'));self.assertEqual(status,200);p=json.loads(body)
  self.assertEqual(path.read_bytes(),b'AB')
  status,_,body=self.api('accept',dict(project=p['id'],snapshot=p['current']));self.assertEqual(status,200)
  p=json.loads(body);self.assertEqual(path.read_bytes(),b'CD');self.assertEqual(Path(p['accepted']['backup']).read_bytes(),b'AB')

if __name__=='__main__':unittest.main()
