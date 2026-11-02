#!/usr/bin/env python3
"""Opt-in live prompt evaluation. Uses disposable files, real providers and independent checks.

No keys are written. Run with --out outside the repository. HTML behavior needs a real
browser check; it is deliberately recorded as pending rather than inferred from source.
"""
import argparse,concurrent.futures,json,random,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import App
from core import sha

CASES={
 'counter':dict(profile='web-document',filename='counter.html',request='Create a standalone accessible counter application. Its heading is Hexwise Counter. An output with id=count shows 0 initially and is an aria-live region. Three real buttons named Increment, Decrement and Reset change the integer by +1, -1, and back to 0. Negative counts are allowed. Keep UTF-8 HTML under 2400 bytes. No external dependencies, imports, assets, network calls or persistence. Supply the complete document bytes, not a plan.',contract=dict(operation='CREATE',kind='Standalone HTML document',production='source-document',version='HTML with inline ECMAScript 2020 in the host browser',abi='HTML / JavaScript / CSS; no native ABI',signature='Single HTML document; entry is browser load',dependencies='No imports or external assets',layout='Document layout; no native addresses',signing='Not applicable; source document',limits='<= 2400 UTF-8 bytes',behavior='A working integer counter with Increment, Decrement, Reset and live count output.',acceptance='Initially 0; increment twice -> 2; decrement -> 1; reset -> 0; decrement -> -1. All buttons keyboard accessible.',retained='New artifact; no previous behavior.',evaluation='Independent browser interactions; no tests have run yet.')),
 'wasm-add':dict(profile='wasm32-browser',filename='add.wasm',request='Create a complete WebAssembly core module exporting only add(a:i32,b:i32)->i32, returning a+b modulo 2^32. Use MVP instructions, no imports, no start function, no memory, tables or globals. Supply all module bytes. Native address/signature policies do not apply to this module.',contract=dict(operation='CREATE',kind='WebAssembly core module',production='direct-complete',version='WebAssembly core MVP; wasm32 integer semantics; Node WebAssembly runtime',abi='Export add with two i32 parameters and one i32 result',signature='add(i32,i32)->i32',dependencies='No imports',layout='Core module sections; no memory, start, tables, globals or native load address',signing='No native code signature; host validates exact bytes',limits='<= 512 bytes; external child timeout 5 seconds',behavior='Return modular i32 sum.',acceptance='Validate, instantiate without imports, export only add, pass boundary and independently chosen integer pairs.',retained='New artifact; no previous behavior.',evaluation='Independent Node WebAssembly engine and JavaScript integer reference.')),
 'arm64-add7':dict(profile='macos-arm64',filename='add7.bin',request='Create an 8-byte raw ARM64 leaf function, exactly one unshifted ADD-immediate X0,X0 instruction followed by RET X30. It returns x+7 modulo 2^64. It must not access memory, change SP, call helpers, use other registers or alter flags. Emit payload bytes only. A separately authored Clang harness will package and test these exact bytes; do not emit Mach-O, source or assembly text.',contract=dict(operation='CREATE',kind='Raw function payload',production='payload-with-packager',version='macOS 26.6.2 on Apple Silicon; baseline A64; no arm64e/PAC',abi='Apple ARM64, LP64',signature='uint64_t hexwise_generated(uint64_t x); X0 input/output; return through valid X30',dependencies='No imports, memory, helpers or runtime calls in the payload',layout='Position independent, entry offset 0, exactly 8 bytes, no relocations',signing='Payload is not independently signed; generic harness is linked and ad-hoc signed by host tools',limits='Exactly 8 bytes; test process timeout 5 seconds',behavior='Unsigned x + 7 modulo 2^64; only X0 changes.',acceptance='Pass independent boundary/random input cases in actual native execution. Decode must match allowed ADD-immediate/RET shape.',retained='All other registers, SP and flags remain unchanged; no existing artifact.',evaluation='Independent native C reference with fixed compiler harness; tools clang, codesign and otool.',details='Packager writes supplied bytes using .byte directives under a single exported function symbol, links a fixed C CLI driver, verifies shape before execution, and records this as payload-with-packager, never direct-complete executable generation.'))}

def command(args,timeout=20):
 r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise ValueError('Check failed: '+str(args[0])+' (exit '+str(r.returncode)+'): '+r.stderr[-1200:])
 return r.stdout

def evaluate(case,data,folder):
 if case=='counter':
  text=data.decode('utf-8')
  if len(data)>2400 or '<html' not in text.lower() or not ('<script' in text.lower() or 'onclick' in text.lower()):raise ValueError('Counter must be a complete HTML application <=2400 bytes with actual script behavior.')
  return dict(status='pending_browser',scope='Document emitted; behavior and keyboard access require actual browser checks.')
 if case=='wasm-add':
  if len(data)>512:raise ValueError('Module exceeds byte budget.')
  position=8
  while position<len(data):
   section=data[position];position+=1;size=0;shift=0
   while True:
    if position>=len(data) or shift>=35:raise ValueError('Invalid WASM section length.')
    byte=data[position];position+=1;size|=(byte&127)<<shift;shift+=7
    if not byte&128:break
   if section not in (0,1,3,7,10):raise ValueError('Task prohibits imports, memory, start, tables, globals and data sections.')
   if position+size>len(data):raise ValueError('WASM section exceeds file.')
   position+=size
  script=folder/'verify-wasm.cjs'
  script.write_text("""const fs=require('node:fs'),assert=require('node:assert/strict');
const bytes=fs.readFileSync(process.argv[2]);
const module_=new WebAssembly.Module(bytes);assert.deepEqual(WebAssembly.Module.imports(module_),[]);
assert.deepEqual(WebAssembly.Module.exports(module_),[{name:'add',kind:'function'}]);
const add=new WebAssembly.Instance(module_,{}).exports.add;
const cases=[[0,0],[1,2],[-1,1],[2147483647,1],[-2147483648,-1],[-2147483648,-2147483648]];
let seed=0x48585749;for(let i=0;i<64;i++){seed=(Math.imul(seed,1664525)+1013904223)|0;const a=seed;seed=(Math.imul(seed,1664525)+1013904223)|0;cases.push([a,seed]);}
for(const [a,b] of cases)assert.equal(add(a,b),(a+b)|0);
console.log(JSON.stringify({status:'passed',cases:cases.length,runtime:process.version,scope:'Complete model-generated module; native WebAssembly validation and behavior, no source compiler.'}));
""")
  return json.loads(command(['node','--max-old-space-size=64',script,folder/'candidate.wasm'],5))
 if case=='arm64-add7':
  if len(data)!=8:raise ValueError('Native payload must be exactly 8 bytes.')
  add,ret=struct.unpack('<II',data)
  if add&0xffc003ff!=0x91000000 or ret!=0xd65f03c0 or ((add>>10)&0xfff)!=7:raise ValueError('Payload is outside the declared ADD X0,X0,#7; RET shape. Not executed.')
  asm=folder/'payload.S';driver=folder/'driver.c';binary=folder/'native-add7'
  asm.write_text('.text\n.p2align 2\n.globl _hexwise_generated\n_hexwise_generated:\n.byte '+','.join(str(b) for b in data)+'\n')
  driver.write_text('#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\nextern uint64_t hexwise_generated(uint64_t);\nint main(int argc,char **argv){if(argc!=2)return 2;uint64_t x=strtoull(argv[1],0,10);printf("%llu\\n",(unsigned long long)hexwise_generated(x));return 0;}\n')
  command(['clang','-arch','arm64',asm,driver,'-o',binary]);command(['codesign','--force','--sign','-',binary])
  (folder/'disassembly.txt').write_text(command(['otool','-tvV',binary]))
  rng=random.Random(0x48585749);cases=[0,1,2,7,2**63-1,2**63,2**64-8,2**64-7,2**64-1]+[rng.getrandbits(64) for _ in range(32)]
  for x in cases:
   if int(command([binary,str(x)],5))!=(x+7)%(2**64):raise ValueError('Native behavior mismatch for input '+str(x))
  return dict(status='passed',cases=len(cases),scope='Model-generated payload in separately authored, compiled and signed CLI harness; actual ARM64 execution. Not a model-generated whole executable.')

def run_case(out,provider,model,case,attempts):
 spec=CASES[case];folder=out/(provider+'-'+case);folder.mkdir()
 app=App(folder/'workspace',folder/'state');path=app.workspace/spec['filename'];path.write_bytes(b'')
 project=app.dispatch('open',dict(path=str(path)))
 app.dispatch('contract',dict(project=project['id'],profile=spec['profile'],contract=spec['contract']))
 record=dict(provider=provider,model=model,case=case,request=spec['request'],contract=spec['contract'],attempts=[])
 text=spec['request']
 for attempt in range(1,attempts+1):
  start=time.monotonic();item=dict(attempt=attempt)
  try:
   project=app.projects.load(project['id'])
   result=app.chat(dict(project=project['id'],snapshot=project['current'],profile=spec['profile'],provider=provider,model=model,chain=[],text=text))
   data=app.projects.data(project['id']);suffix='.wasm' if case=='wasm-add' else '.html' if case=='counter' else '.bin'
   candidate=folder/('candidate'+suffix);candidate.write_bytes(data)
   (folder/('response-'+str(attempt)+'.json')).write_text(json.dumps(result['messages'],indent=2))
   item.update(bytes=len(data),sha256=sha(data),original_unchanged=path.read_bytes()==b'',outcome=next((m.get('outcome') for m in reversed(result['messages']) if m['role']=='assistant'),None))
   if not data:raise ValueError(next((m['text'] for m in reversed(result['messages']) if m['role']=='system'),'No candidate emitted; outcome '+str(item['outcome'])))
   item['evaluation']=evaluate(case,data,folder)
  except Exception as error:item['evaluation']=dict(status='failed',reason=str(error).replace(str(out),'<evaluation-output>')[:2000])
  item['elapsed_seconds']=round(time.monotonic()-start,2);record['attempts'].append(item)
  print(json.dumps(dict(provider=provider,case=case,**item)),flush=True)
  if item['evaluation']['status']!='failed':break
  text='The fixed task and acceptance criteria are unchanged. The independent evaluator reported: '+item['evaluation'].get('reason','')+'. Repair the candidate within the same target and byte budget. Do not claim the tests passed.'
 record['status']=record['attempts'][-1]['evaluation']['status']
 (folder/'result.json').write_text(json.dumps(record,indent=2));return record

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--provider',action='append',help='provider:model; may be repeated');parser.add_argument('--case',action='append',choices=list(CASES));parser.add_argument('--attempts',type=int,choices=[1,2],default=1)
 args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
 providers=[s.split(':',1) for s in (args.provider or ['gemini:gemini-3.1-flash-lite','ollama:llama3.2:latest'])]
 jobs=[(p,m,c) for p,m in providers for c in (args.case or CASES)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  records=list(pool.map(lambda job:run_case(out,*job,args.attempts),jobs))
 report=dict(scope='Bounded live prompt acceptance; raw failures retained. Pending browser is not pass.',records=records)
 (out/'report.json').write_text(json.dumps(report,indent=2))
 return 1 if any(r['status']=='failed' for r in records) else 2 if any(r['status']=='pending_browser' for r in records) else 0
if __name__=='__main__':raise SystemExit(main())
