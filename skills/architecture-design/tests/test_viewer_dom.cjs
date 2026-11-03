// Optional Node.js 18+ interaction test; no npm packages required.
// A small DOM mock, not real-browser, layout, file://, or CSP validation.
// Run: node tests/test_viewer_dom.cjs
const fs = require('fs'); const vm = require('vm'); const assert = require('assert');
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.attributes={};this.listeners={};this.style={};this._text='';this.className='';this.clientWidth=800;this.value='';this.classList={toggle:(name,force)=>{const set=new Set(this.className.split(' '));if(force)set.add(name);else set.delete(name);this.className=[...set].join(' ')},contains:name=>this.className.split(' ').includes(name)};}
 set textContent(text){this._text=String(text);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 appendChild(child){this.children.push(child);return child;}
 replaceChildren(...children){this.children=children;this._text='';}
 setAttribute(k,v){this.attributes[k]=String(v);if(k==='class')this.className=String(v);}
 getAttribute(k){return this.attributes[k]??null;}
 removeAttribute(k){delete this.attributes[k];}
 addEventListener(type,fn){this.listeners[type]=fn;}
 click(){this.listeners.click?.({});}
 focus(){document.activeElement=this;}
 querySelector(tag){return all(this).find(x=>x.tagName===tag)||null;}
}
function all(root){return [root,...root.children.flatMap(all)];}
const base=require('path').resolve(__dirname, '..');
const data=JSON.parse(fs.readFileSync(base+'/assets/demo.json','utf8'));
const root=new Element('root');const json=new Element('script');json.textContent=JSON.stringify(data);
const meta=new Element('script');meta.textContent=JSON.stringify({warnings:['demo warning'],sourceName:'demo.json',sourceSha256:'test',assetsSha256:'test'});
const document={getElementById:id=>({'architecture-app':root,'architecture-data':json,'render-metadata':meta})[id],createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),activeElement:null};
const context={document,window:{innerWidth:1500,addEventListener(){}},ResizeObserver:class{observe(){}},requestAnimationFrame:fn=>fn(),console};
vm.runInNewContext(fs.readFileSync(base+'/assets/viewer.js','utf8'),context);
const byClass=cls=>all(root).filter(x=>x.classList.contains(cls));
const nodes=()=>byClass('node');const nav=()=>byClass('nav-button');const panel=()=>byClass('detail-panel')[0];
assert.equal(nav().length,3);assert.equal(nodes().length,data.views[0].elementIds.length);assert(nodes().every(n=>n.getAttribute('aria-pressed')==='false'));
nodes()[1].click();assert.equal(nodes()[1].getAttribute('aria-pressed'),'true');assert(panel().textContent.includes(data.elements.find(x=>x.id===data.views[0].elementIds[1]).name));
nav()[1].click();assert.equal(nodes().length,data.views[1].elementIds.length);
nav()[2].click();assert.equal(nodes().length,data.flows[0].steps.length);
const proposedIndex=data.flows[0].steps.findIndex(x=>x.status==='proposed');assert(proposedIndex>=0);assert(nodes()[proposedIndex].textContent.includes('提议'));nodes()[proposedIndex].click();assert(panel().textContent.includes('步骤状态：提议'));
const search=all(root).find(x=>x.tagName==='input');search.value='no-match-should-exist';search.listeners.input();assert.equal(byClass('is-dimmed').length,nodes().length);search.value='';search.listeners.input();assert.equal(byClass('is-dimmed').length,0);
nodes()[0].focus();nodes()[0].listeners.keydown({key:'ArrowDown',preventDefault(){}});assert.equal(document.activeElement,nodes()[1]);nodes()[1].listeners.keydown({key:'Escape'});assert(nodes().every(n=>n.getAttribute('aria-pressed')==='false'));
nav()[1].click();nodes().find(n=>n.textContent.includes('订单模块')).click();const contract=all(panel()).find(n=>n.classList.contains('detail-link')&&n.textContent.includes('create-order'));assert(contract);contract.click();assert(panel().textContent.includes('输入 / INPUT'));assert(panel().textContent.includes('状态转移 / STATES'));assert.equal(document.activeElement.tagName,'h2');byClass('back-button')[0].click();assert(panel().textContent.includes('订单模块'));
const plus=all(root).find(n=>n.getAttribute('aria-label')==='放大图形');const before=byClass('zoom-readout')[0].textContent;plus.click();assert.notEqual(byClass('zoom-readout')[0].textContent,before);
assert.equal(all(root).filter(x=>['iframe','img','a'].includes(x.tagName)).length,0);
console.log('PASS: initialization, 3 views, selection, mixed statuses, search, keyboard navigation, Escape, contract drilldown, contract state transitions, back navigation, zoom, no dynamic external resources. DOM harness only, not browser visual QA.');
