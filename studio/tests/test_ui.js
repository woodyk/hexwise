/* Regression: replacing an open modal must not cancel its new confirmation. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Element extends EventTarget {
 constructor(){super();this.open=false;this.children=[];this.value='';this.classList={toggle(){},add(){},remove(){}};}
 set innerHTML(value){this.html=value;this.children=[];}
 get innerHTML(){return this.html||'';}
 append(element){this.children.push(element);}
 showModal(){this.open=true;}
 close(){this.open=false;queueMicrotask(()=>this.dispatchEvent(new Event('close')));}
}
const elements=new Map();
const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const paneStyle={'--left':'420px','--right':'650px','--composer':'440px'};
const context=vm.createContext({getComputedStyle:()=>({getPropertyValue:k=>paneStyle[k]}),document:{body:{style:{setProperty:(k,v)=>{paneStyle[k]=v;}}},getElementById:get,querySelectorAll:()=>[],addEventListener(){},createElement:()=>new Element()},window:{addEventListener(){}},location:{hash:'#fixture',pathname:'/'},sessionStorage:{getItem(){},setItem(){}},history:{replaceState(){}},setTimeout,clearTimeout,TextEncoder,TextDecoder,Uint8Array,DataView,console});
let source=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8').replace('safe(init)();','');
vm.runInContext(source,context);
(async()=>{
 get('dialog').showModal();let settled=false;
 const confirmation=vm.runInContext("confirmAction('Replace?','Review details','Accept')",context);
 confirmation.then(()=>{settled=true;});
 await new Promise(setImmediate);
 assert.equal(settled,false,'old modal close must not resolve new confirmation');
 get('dialogFooter').children[1].dispatchEvent(new Event('click'));
 assert.equal(await confirmation,true);
 const cancelled=vm.runInContext("confirmAction('Replace?','Review details','Accept')",context);
 get('dialog').close();assert.equal(await cancelled,false,'Escape/close cancels');
 const explicit=vm.runInContext("confirmAction('Replace?','Review details','Accept')",context);
 get('dialogFooter').children[0].dispatchEvent(new Event('click'));assert.equal(await explicit,false);
 context.window.innerHeight=720;get('workspace').clientWidth=1100;vm.runInContext('fitPanes()',context);
 assert.ok(parseFloat(paneStyle['--left'])+parseFloat(paneStyle['--right'])<=635,'panes must leave space for the editor');
 assert.ok(parseFloat(paneStyle['--composer'])<=270,'composer must leave space for hex editing');
 const legacy=JSON.stringify({status:'needs_input',reason:'Which behavior?',missing:['artifact_kind']});
 context.clarification=legacy;
 const readable=vm.runInContext('assistantText(clarification)',context);
 assert.ok(readable.includes('Which behavior?')&&readable.includes('artifact kind')&&readable.includes('Reply below'));
 assert.ok(!readable.includes('"status"'),'legacy protocol must render as readable questions');
 context.clarification=JSON.stringify({message:'Choose a target',status:'needs_input'});
 assert.ok(vm.runInContext('assistantText(clarification)',context).includes('Choose a target'));
 context.clarification='A plain explanation';
 assert.equal(vm.runInContext('assistantText(clarification)',context),'A plain explanation');
 const choice=vm.runInContext("contractField({key:'kind',label:'Artifact kind',control:'select',choices:['Raw function payload','Complete native executable'],help:'Choose an artifact.'},'Complete native executable')",context);
 assert.ok(choice.includes('Complete native executable')&&choice.includes('selected')&&choice.includes('Decide in chat'));
 const custom=vm.runInContext("contractField({key:'version',label:'Runtime',choices:['macOS 14.0'],help:'Pin the version.'},'custom & version')",context);
 assert.ok(custom.includes('datalist')&&custom.includes('macOS 14.0')&&custom.includes('custom &amp; version'));
 const escaped=vm.runInContext("contractField({key:'behavior',label:'Behavior',control:'textarea',choices:[],help:'Describe behavior.'},'</textarea><script>bad()</script>')",context);
 assert.ok(!escaped.includes('<script>')&&escaped.includes('&lt;script&gt;'));
 const calls=[];
 context.api=async(route,payload)=>{calls.push({route,payload});return route==='contract-options'?{label:'macOS ARM64',fields:[{key:'operation',label:'Operation',control:'select',choices:['CREATE'],help:'Choose.'},{key:'abi',label:'ABI',choices:['Apple ARM64'],default:'Apple ARM64',help:'Known ABI.'}]}:{id:'form-test',contract:payload.contract};};
 vm.runInContext("state.project={id:'form-test',contract:{details:'Retain extra details'}}",context);
 get('profileSelect').value='macos-arm64';await vm.runInContext('targetContract()',context);
 assert.ok(get('dialogBody').innerHTML.includes('Apple ARM64')&&get('dialogBody').innerHTML.includes('Blank fields remain unknown'));
 get('contract_operation').value='CREATE';get('contract_abi').value='Apple ARM64';
 get('dialogFooter').children[0].dispatchEvent(new Event('click'));await new Promise(setImmediate);
 assert.equal(calls.at(-1).route,'contract');assert.equal(calls.at(-1).payload.profile,'macos-arm64');
 assert.equal(calls.at(-1).payload.contract.details,'Retain extra details');
 console.log('PASS: 13 UI checks including contract choices, escaping, defaults and save flow');
})().catch(error=>{console.error(error);process.exitCode=1;});
