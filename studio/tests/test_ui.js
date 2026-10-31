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
 console.log('PASS: 3 confirmation regressions and 2 pane-size constraints');
})().catch(error=>{console.error(error);process.exitCode=1;});
