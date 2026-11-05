// Optional Node.js DOM logic regression checks; no npm packages.
// Run: node skills/development-pipeline/tests/test_index_dom.cjs
// These checks do not verify browser layout, responsive rendering, or file:// loading.
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert').strict;
const root = path.resolve(__dirname, '../assets/index');
const template = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const templateIds = [...template.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(new Set(templateIds).size, templateIds.length, 'Template IDs must remain unique');
for (const id of ['main', 'active-count', 'archive-count', 'attention-count', 'results', 'notice', 'search', 'list', 'count', 'theme']) assert(templateIds.includes(id), 'Missing UI hook: ' + id);
for (const target of template.matchAll(/\baria-(?:controls|labelledby)="([^"]+)"/g)) assert(templateIds.includes(target[1]), 'Missing ARIA target: ' + target[1]);
assert.deepEqual([...template.matchAll(/\bdata-tab="([^"]+)"/g)].map(match => match[1]), ['active', 'archive', 'unknown', 'all']);
assert(template.includes('href="#main"'));
assert(template.includes('<!-- index-style -->') && template.includes('<!-- index-app -->'));
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.attributes={};this.listeners={};this.className='';this._text='';this.value='';this.dataset={};this.classList={contains:n=>this.className.split(' ').includes(n),toggle:(n,force)=>{const s=new Set(this.className.split(' ').filter(Boolean));const on=force??!s.has(n);if(on)s.add(n);else s.delete(n);this.className=[...s].join(' ');return on;}};}
 set textContent(t){this._text=String(t);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 append(...items){for(const child of items){child.parent=this;this.children.push(child);}}replaceChildren(...items){this.children=[];this._text='';this.append(...items);}
 remove(){this.parent.children=this.parent.children.filter(x=>x!==this);}
 querySelector(s){return this.children.find(x=>x.tagName===s);}
 setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k]??null;}
 addEventListener(type,fn){this.listeners[type]=fn;}click(){this.listeners.click?.({target:this});}focus(){document.activeElement=this;}
}
for (const sink of ['innerHTML', 'outerHTML']) Object.defineProperty(Element.prototype,sink,{set(){throw Error('Unexpected unsafe HTML sink')}});
Element.prototype.insertAdjacentHTML = () => {throw Error('Unexpected unsafe HTML insertion')};
// Keep this intentionally small: the real HTML hooks above and JS behavior below
// are checked, but this is not a replacement for Chromium or accessibility QA.
const ids={};for(const name of ['active-count','archive-count','attention-count','results','notice','search','list','count','theme'])ids[name]=new Element();
const tabs=['active','archive','unknown','all'].map(key=>{const b=new Element('button');b.dataset.tab=key;b.append(new Element('small'));b.className='tab';return b});
const tabList=new Element();const body=new Element('body');let timer, delay;
const document={body,createElement:t=>new Element(t),getElementById:id=>ids[id]??body.children.find(x=>x.id===id),querySelector:s=>s==='.tabs'?tabList:ids[s.slice(1)],querySelectorAll:s=>s==='.tab'?tabs:[]};
const context={document,window:{},Date,setInterval:(fn,ms)=>{timer=fn;delay=ms}};
vm.runInNewContext(fs.readFileSync(root+'/app.js','utf8'),context,{timeout:1000});
assert.equal(delay,5000);assert.equal(body.children.length,1);assert.match(body.children[0].src,/^\.\/pipeline-index-data\.js\?t=/);
body.children[0].onerror();assert.match(ids.notice.textContent,/无法读取/);
tabs[1].click();assert.equal(ids.results.getAttribute('aria-labelledby'),'tab-archive');assert.equal(tabs[1].getAttribute('aria-selected'),'true');
const now=new Date().toISOString(), old=new Date(Date.now()-8*24*60*60*1000).toISOString();
const runs=['draft','running','needs_decision','consulting','blocked','completed'].map((status,i)=>({title:'测试任务 '+i,run_id:'run-'+i,project:'Pouch',round:'r-'+i,path:'run/'+i,status,updated_at:now,observer:'run%20'+i+'/observer/index.html',report:status==='completed'?'run-'+i+'/report.html':null}));
runs.push({title:'过期任务',status:'running',updated_at:old});runs.push({path:'broken/pipeline',error:'bad event'});runs.push({title:'<img src=x onerror="window.injected=1">',status:'draft',updated_at:now,demo:true});
const data={generated_at:now,runs},original=JSON.stringify(data);
context.window.pipelineIndexReceive(data);
assert.equal(ids['active-count'].textContent,'6');assert.equal(ids['archive-count'].textContent,'2');assert.equal(ids['attention-count'].textContent,'4');
assert.equal(ids.list.children.length,2);assert.match(ids.list.textContent,/已完成/);assert.match(ids.list.textContent,/过期/);
const key=(target,key)=>{let prevented=false;tabList.listeners.keydown({target,key,preventDefault(){prevented=true}});assert(prevented)};
key(tabs[1],'ArrowRight');assert.equal(document.activeElement,tabs[2]);assert.equal(ids.list.children.length,1);assert.match(ids.list.textContent,/读取失败/);
key(tabs[2],'End');assert.equal(ids.list.children.length,9);assert.equal(tabs[3].tabIndex,0);assert.equal(tabs[0].tabIndex,-1);
const pills=ids.list.children.map(x=>x.children[2].children[0]);assert(pills.find(p=>p.textContent==='已阻塞').className.includes('block'));assert(pills.find(p=>p.textContent==='已完成').className.includes('done'));assert(pills.find(p=>p.textContent==='等待决策').className.includes('wait'));
ids.search.value='pOuCh';ids.search.listeners.input();assert.equal(ids.list.children.length,6);ids.search.value='run-1';ids.search.listeners.input();assert.equal(ids.list.children.length,1);assert.equal(ids.list.children[0].children[4].children[0].href,'run%201/observer/index.html');
ids.search.value='no-matching-run';ids.search.listeners.input();assert.equal(ids.list.children[0].className,'empty');ids.search.value='';ids.search.listeners.input();
ids.theme.click();assert(body.classList.contains('dark'));assert.equal(ids.theme.getAttribute('aria-pressed'),'true');ids.theme.click();assert(!body.classList.contains('dark'));assert.equal(ids.theme.getAttribute('aria-pressed'),'false');
timer();assert.equal(body.children.length,1);body.children[0].onerror();assert.match(ids.notice.textContent,/上次成功加载/);assert.equal(ids.list.children.length,9);context.window.pipelineIndexReceive(data);assert(!ids.notice.textContent.includes('上次成功加载'));
key(tabs[3],'ArrowRight');assert.equal(document.activeElement,tabs[0]);assert.equal(ids.list.children.length,6);key(tabs[0],'ArrowLeft');assert.equal(document.activeElement,tabs[3]);key(tabs[3],'Home');assert.equal(document.activeElement,tabs[0]);
assert.equal(JSON.stringify(data),original);assert(ids.list.textContent.includes('<img src=x onerror="window.injected=1">'));assert.equal(context.window.injected,undefined);
console.log('PASS: DOM logic for 9 records, all statuses/counts, stale archive, safe text, search/empty results, links, keyboard tab wrapping/Home/End, labels/focus, theme ARIA, 5s refresh, script replacement, failed-data retention and recovery. No browser/layout claim.');
