// Optional Node.js 18+ DOM logic tests, no npm packages.
// Run: node tests/test_viewer_dom.cjs
// These are not browser/layout/file://CSP verification.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const base=path.resolve(__dirname, '..');
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.attributes={};this.listeners={};this.style={};this._text='';this.className='';this.clientWidth=800;this.value='';this.scrollTop=0;this.scrollLeft=0;this.disabled=false;this.hidden=false;this.open=false;this.classList={toggle:(name,force)=>{const set=new Set(this.className.split(' '));if(force)set.add(name);else set.delete(name);this.className=[...set].join(' ')},contains:name=>this.className.split(' ').includes(name)};}
 set textContent(text){this._text=String(text);this.children=[];} get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 appendChild(child){this.children.push(child);return child;}replaceChildren(...children){this.children=children;this._text='';}
 setAttribute(k,v){this.attributes[k]=String(v);if(k==='class')this.className=String(v);}getAttribute(k){return this.attributes[k]??null;}removeAttribute(k){delete this.attributes[k];}
 addEventListener(type,fn){this.listeners[type]=fn;}click(){if(!this.disabled)this.listeners.click?.({});}focus(){document.activeElement=this;}querySelector(tag){return all(this).find(x=>x.tagName===tag)||null;}
}
// Fail loudly on unsafe HTML sinks; a DOM mock does not parse injected HTML.
Object.defineProperty(Element.prototype,'innerHTML',{set(){throw new Error('Unsafe innerHTML sink');}});
Object.defineProperty(Element.prototype,'outerHTML',{set(){throw new Error('Unsafe outerHTML sink');}});
Element.prototype.insertAdjacentHTML=function(){throw new Error('Unsafe HTML insertion sink');};
function all(root){return [root,...root.children.flatMap(all)];}
const data=JSON.parse(fs.readFileSync(path.join(base,'assets/demo.json'),'utf8'));
// Exercise an ancestor context that really does own a drilldown target.
const leafView=data.views.find(view=>view.id==='module-transaction-detail');leafView.elementIds.push('orders');leafView.contextElementIds.push('orders');
// Changes with no element associations are valid and must remain reachable.
const hostileChangeText='</script><img src=x onerror=alert(1)> change detail stays plain text';
data.changes.push(
 {id:'test-change-contract-only',name:'Contract-only change',status:'proposed',description:'A contract association without any elementIds.',contractIds:['create-order'],decision:'accepted',verification:'unverified',progress:'completed',progressEvidence:[{path:'tests/progress-contract.json',lines:'2-3',note:'Contract progress source only'}],progressNote:hostileChangeText,evidence:[{path:'tests/design-contract.md',lines:'10-12',note:'Contract design evidence only'}],acceptance:['Contract-only acceptance criterion']},
 {id:'test-change-flow-only',name:'Flow-only change',status:'planned',description:'A flow association without any elementIds.',flowIds:['flow-submit'],decision:'draft',verification:'unverified',progress:'incomplete',progressEvidence:[{path:'tests/progress-flow.json',lines:'4',note:'Flow progress source only'}],progressNote:'Flow change work remains unfinished.',evidence:[{path:'tests/design-flow.md',lines:'8',note:'Flow design evidence only'}],acceptance:['Flow-only acceptance criterion']},
 {id:'test-change-unlinked',name:'Unlinked change',status:'unknown',description:'A valid change without element, contract, or flow associations.',acceptance:['Unlinked acceptance criterion']}
);
const unviewedFlow=JSON.parse(JSON.stringify(data.flows[0]));unviewedFlow.id='test-flow-unviewed';unviewedFlow.name='Flow without a view';data.flows.push(unviewedFlow);
data.changes.push({id:'test-change-flow-unviewed',name:'Change for an unviewed flow',status:'planned',description:'No matching flow view exists; the change and flow details must still be readable.',flowIds:['test-flow-unviewed'],acceptance:['Review the unviewed flow directly']});
const original=JSON.stringify(data);let parsedModel;
const root=new Element('root'),json=new Element('script'),meta=new Element('script');json.textContent=JSON.stringify(data);meta.textContent=JSON.stringify({warnings:['demo warning'],sourceName:'demo.json'});
const document={getElementById:id=>({'architecture-app':root,'architecture-data':json,'render-metadata':meta})[id],createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),activeElement:null,hidden:false,listeners:{},addEventListener(type,fn){this.listeners[type]=fn;}};
const media={matches:false,listeners:{},addEventListener(type,fn){this.listeners[type]=fn;}};const timers=new Map();let timerId=0;const frames=[];
const win={innerWidth:1500,matchMedia:()=>media,listeners:{},addEventListener(type,fn){this.listeners[type]=fn;}};
const context={document,window:win,ResizeObserver:class{observe(){}},requestAnimationFrame:fn=>frames.push(fn),setTimeout:fn=>{const id=++timerId;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),JSON:{parse:text=>{const value=JSON.parse(text);if(text===json.textContent)parsedModel=value;return value;},stringify:JSON.stringify},console};
vm.runInNewContext(fs.readFileSync(path.join(base,'assets/viewer.js'),'utf8'),context,{timeout:1000});
function flushFrames(){while(frames.length)frames.shift()();}function tick(){const first=timers.entries().next().value;if(first){timers.delete(first[0]);first[1]();}}
const byClass=cls=>all(root).filter(x=>x.classList.contains(cls));const one=cls=>byClass(cls)[0];const nodes=()=>byClass('node');const node=id=>nodes().find(x=>x.getAttribute('data-node-id')===id);const nav=()=>byClass('nav-button');const panel=()=>one('detail-panel');const main=()=>one('main');const input=()=>all(root).find(x=>x.tagName==='input');const visible=()=>byClass('trace-visible');
const openNav=id=>{nav().find(x=>x.textContent.includes(data.views.find(v=>v.id===id).name)).click();flushFrames();};
flushFrames();assert.equal(nav().length,data.views.length);assert.equal(nodes().length,data.views[0].elementIds.length);assert.equal(timers.size,0);assert(nodes().every(n=>n.getAttribute('aria-pressed')==='false'));
// Details stay accessible without triggering drilldown.
one('inspect-node').click();assert(panel().textContent.includes('订单模块'));assert(!main().textContent.includes('返回上一层'));assert.equal(all(panel()).filter(item=>item.classList.contains('drill-detail')).length,1);
const contract=all(panel()).find(n=>n.classList.contains('detail-link')&&n.textContent.includes('create-order'));assert(contract);contract.click();assert(panel().textContent.includes('输入 / INPUT'));assert(panel().textContent.includes('状态转移 / STATES'));one('back-button').click();
// Restore the complete prior view through two levels.
input().value='订单';input().listeners.input();all(root).find(n=>n.getAttribute('aria-label')==='放大图形').click();const savedZoom=one('zoom-readout').textContent;one('diagram-viewport').scrollLeft=31;one('diagram-viewport').scrollTop=77;
node('orders').click();flushFrames();assert(node('order-transaction'));assert.equal(document.activeElement.tagName,'h2');assert(one('breadcrumbs').textContent.includes('整体架构'));assert(one('node-context').textContent.includes('外部上下文'));
node('order-transaction').click();flushFrames();assert(node('txn-check'));assert(one('breadcrumbs').textContent.includes('订单内部'));one('breadcrumb-back').click();flushFrames();assert(node('order-transaction'));assert.equal(document.activeElement.getAttribute('data-node-id'),'order-transaction');one('breadcrumb-back').click();flushFrames();assert(node('orders'));assert.equal(input().value,'订单');assert.equal(one('zoom-readout').textContent,savedZoom);assert.equal(one('diagram-viewport').scrollTop,77);assert.equal(one('diagram-viewport').scrollLeft,31);assert.equal(document.activeElement.getAttribute('data-node-id'),'orders');assert.equal(node('orders').getAttribute('aria-pressed'),'true');
// A context node never drills, and direct module browsing can reach root.
openNav('module-transaction-detail');node('inventory').click();assert(node('txn-check'));assert(panel().textContent.includes('外部上下文'));node('orders').click();assert(node('txn-check'));assert(panel().textContent.includes('外部上下文'));assert.equal(all(panel()).filter(item=>item.classList.contains('drill-detail')).length,0);one('breadcrumb-back').click();flushFrames();assert(node('orders'));
// Search, keyboard, and mixed design/progress remain independent.
openNav('flow-view-submit');assert(node('validate').textContent.includes('已完成'));assert(node('reserve').textContent.includes('正在开发'));assert(node('commit').textContent.includes('未完成'));assert(node('reject').textContent.includes('进度未声明'));assert(node('notify').textContent.includes('提议'));node('notify').click();assert(panel().textContent.includes('步骤状态：提议'));assert(panel().textContent.includes('进度未声明'));
input().value='no-match';input().listeners.input();assert.equal(byClass('is-dimmed').length,nodes().length);input().value='';input().listeners.input();nodes()[0].focus();nodes()[0].listeners.keydown({key:'ArrowDown',preventDefault(){}});assert.equal(document.activeElement,nodes()[1]);nodes()[1].listeners.keydown({key:'Escape'});assert(nodes().every(n=>n.getAttribute('aria-pressed')==='false'));
// Static by default; step along one existing edge, then explicitly pick a branch.
assert.equal(timers.size,0);one('trace-step').click();assert.equal(visible().length,1);assert(one('trace-status').textContent.includes('解析与鉴权 → 预留库存'));one('trace-step').click();assert.equal(one('trace-branch').hidden,false);assert(one('trace-status').textContent.includes('已暂停'));assert.equal(visible().length,1);const branch=one('trace-branch-select');branch.value='2';branch.listeners.change();one('trace-step').click();assert(one('trace-status').textContent.includes('回滚并返回不足项'));assert.equal(visible().length,1);one('trace-step').click();assert(one('trace-status').textContent.includes('终点'));
// Play/pause is bounded and view change cancels the timer and all overlays.
one('trace-reset').click();assert.equal(visible().length,0);one('trace-play').click();assert.equal(timers.size,1);assert(one('diagram').classList.contains('motion-playing'));one('trace-pause').click();assert.equal(timers.size,0);assert(!one('diagram').classList.contains('motion-playing'));one('trace-reset').click();one('trace-play').click();tick();assert.equal(timers.size,0);assert.equal(one('trace-branch').hidden,false);one('trace-branch-select').value='1';one('trace-branch-select').listeners.change();one('trace-play').click();for(let i=0;i<10;i++)tick();assert.equal(timers.size,0);assert(one('trace-status').textContent.includes('已展示过的关系'));assert.equal(visible().length,1);
// Reduced motion, hidden pages, closed panel, and print always stop animation.
one('trace-reset').click();media.matches=true;media.listeners.change();assert.equal(one('trace-play').disabled,true);one('trace-step').click();assert.equal(visible().length,1);assert(!one('diagram').classList.contains('motion-playing'));media.matches=false;media.listeners.change();one('trace-reset').click();one('trace-play').click();document.hidden=true;document.listeners.visibilitychange();assert.equal(timers.size,0);document.hidden=false;
one('trace-reset').click();one('trace-play').click();win.listeners.beforeprint();assert.equal(timers.size,0);one('trace-reset').click();one('trace-play').click();one('trace-panel').listeners.toggle();assert.equal(timers.size,0);
one('trace-reset').click();one('trace-play').click();openNav('overview');assert.equal(timers.size,0);assert.equal(visible().length,0);
// Pending fit callbacks from an old view cannot overwrite current navigation.
node('orders').click();node('order-transaction').click();one('breadcrumb-back').click();flushFrames();assert(node('order-transaction'));
// Every legal change is available globally, even with no element or view link.
const changeEntry=(id,scope=root)=>all(scope).find(item=>item.tagName==='button'&&item.getAttribute('data-change-id')===id);
const detailSection=title=>all(panel()).find(item=>item.tagName==='section'&&item.children.some(child=>child.tagName==='h3'&&child.textContent===title));
const detailProgress=()=>all(panel()).find(item=>item.classList.contains('progress'));
const assertChange=(id,expectedProgress)=>{
 const source=data.changes.find(item=>item.id===id);const entry=changeEntry(id,one('changes-panel'));assert(entry,`Missing global change ${id}`);assert.equal(entry.type,'button');entry.click();
 assert(panel().classList.contains('change-detail'));assert.equal(panel().querySelector('h2').textContent,source.name);assert.equal(document.activeElement.tagName,'h2');assert.equal(detailProgress().textContent,expectedProgress);
 assert(panel().textContent.includes(source.description));assert(detailSection('验收标准 / ACCEPTANCE'));source.acceptance.forEach(value=>assert(panel().textContent.includes(value)));
 if(source.decision)assert(detailSection('决策与验证 / DECISION & VERIFICATION').textContent.includes(`(${source.decision})`));
 if(source.verification)assert(detailSection('决策与验证 / DECISION & VERIFICATION').textContent.includes(`(${source.verification})`));
 const progressBox=detailSection('开发进度 / PROGRESS');assert(progressBox);
 if(source.progressNote)assert(progressBox.textContent.includes(source.progressNote));
 (source.progressEvidence||[]).forEach(evidence=>{assert(progressBox.textContent.includes(evidence.path+(evidence.lines?':'+evidence.lines:'')));if(evidence.note)assert(progressBox.textContent.includes(evidence.note));});
 const evidenceBox=detailSection('证据 / EVIDENCE');
 if(source.evidence?.length){assert(evidenceBox);source.evidence.forEach(evidence=>{assert(evidenceBox.textContent.includes(evidence.path+(evidence.lines?':'+evidence.lines:'')));if(evidence.note)assert(evidenceBox.textContent.includes(evidence.note));assert(!progressBox.textContent.includes(evidence.path));});(source.progressEvidence||[]).forEach(evidence=>assert(!evidenceBox.textContent.includes(evidence.path)));}
 else assert(!evidenceBox,'A change must not inherit ordinary evidence from related objects');
};
for(const view of data.views){openNav(view.id);const catalog=one('changes-panel');assert(catalog);assert.equal(catalog.tagName,'details');assert(catalog.querySelector('summary'));assert.equal(all(catalog).filter(item=>item.getAttribute('data-change-id')).length,data.changes.length);}
openNav('overview');input().value='no-change-matches-this-filter';input().listeners.input();assert.equal(all(one('changes-panel')).filter(item=>item.getAttribute('data-change-id')).length,data.changes.length);input().value='';input().listeners.input();
assertChange('change-submit','正在开发');assert(detailSection('决策与验证 / DECISION & VERIFICATION').textContent.includes('(unverified)'));
assertChange('test-change-contract-only','已完成');assert(panel().textContent.includes('提议'));assert(panel().textContent.includes(hostileChangeText));assert(detailSection('决策与验证 / DECISION & VERIFICATION').textContent.includes('(unverified)'));
// Contract-only related entry and back navigation work independently of elementIds.
all(panel()).find(item=>item.classList.contains('detail-link')&&item.textContent.includes('create-order')).click();assert(panel().textContent.includes('输入 / INPUT'));assert(changeEntry('test-change-contract-only',panel()));changeEntry('test-change-contract-only',panel()).click();assert(panel().classList.contains('change-detail'));one('back-button').click();assert(panel().textContent.includes('输入 / INPUT'));
assertChange('test-change-flow-only','未完成');all(panel()).find(item=>item.classList.contains('detail-link')&&item.textContent.includes('flow-submit')).click();assert(panel().textContent.includes('已建模步骤 / STEPS'));assert(changeEntry('test-change-flow-only',panel()));assert(all(panel()).some(item=>item.tagName==='button'&&item.textContent.startsWith('打开流程图')));
// A flow view also exposes its own related changes, without element selection.
openNav('flow-view-submit');assert(changeEntry('test-change-flow-only',panel()));changeEntry('test-change-flow-only',panel()).click();assert.equal(detailProgress().textContent,'未完成');
assertChange('test-change-unlinked','进度未声明');assert(panel().textContent.includes('未关联具体构件、契约或流程'));assert(!detailSection('开发进度 / PROGRESS').textContent.includes('tests/progress-'));
assertChange('test-change-flow-unviewed','进度未声明');all(panel()).find(item=>item.classList.contains('detail-link')&&item.textContent.includes('test-flow-unviewed')).click();assert.equal(panel().querySelector('h2').textContent,'Flow without a view');assert(panel().textContent.includes('已建模步骤 / STEPS'));assert(changeEntry('test-change-flow-unviewed',panel()));assert(!all(panel()).some(item=>item.tagName==='button'&&item.textContent.startsWith('打开流程图')));one('back-button').click();assert(panel().classList.contains('change-detail'));assert.equal(detailProgress().textContent,'进度未声明');
// Global change access remains independent of graph search and selection.
openNav('overview');node('access').click();assert(changeEntry('change-submit',panel()));changeEntry('change-submit',panel()).click();assert.equal(detailProgress().textContent,'正在开发');
assert.equal(timers.size,0);assert.equal(all(root).filter(item=>['script','iframe','img','a'].includes(item.tagName)).length,0);
assert(parsedModel);assert.equal(JSON.stringify(parsedModel),original);assert.equal(json.textContent,original);assert.equal(JSON.stringify(data),original);assert.equal(all(root).filter(x=>['iframe','img','a'].includes(x.tagName)).length,0);
console.log('PASS: independent progress, 5 views, two-level drilldown/back/context/focus/search/zoom/scroll restoration, details/contracts, keyboard, explicit branch selection, static step, bounded animation play/pause/reset/cycle, timer cleanup, reduced-motion/visibility/print/closed-panel handling, all changes including contract-only/flow-only/unlinked/unviewed-flow, independent change progress/design evidence and safe plain text. DOM logic only; no browser/layout/CSP claim.');
