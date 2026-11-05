// Node.js 18+ DOM security regression, no npm dependencies.
// Executes only the repository's fixed app.js, never untrusted code. The vm
// context is a test double, not a security sandbox or a real browser/CSP test.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert').strict;
const source = fs.readFileSync(path.join(__dirname, '../assets/observer/app.js'), 'utf8');
const hostile = '</script><img src=x onerror="window.injected=1"> & javascript:alert(1)';
const walk = node => [node, ...node.children.flatMap(walk)];
class Element {
  constructor(tag) {
    this.tagName = tag; this.children = []; this.listeners = {}; this.attributes = {};
    this.className = ''; this._text = ''; this.scrollLeft = 17; this.scrollTop = 31;
    this.style = {setProperty() {}};
    this.classList = {toggle: (name, force) => {
      const classes = new Set(this.className.split(' '));
      if (force) classes.add(name); else classes.delete(name);
      this.className = [...classes].join(' ');
    }};
  }
  set textContent(value) {this._text = String(value); this.children = [];}
  get textContent() {return this._text + this.children.map(child => child.textContent).join('');}
  append(...children) {for (const child of children) {child.parent = this; this.children.push(child);}}
  replaceChildren(...children) {this._text = ''; this.children = []; this.append(...children);}
  setAttribute(name, value) {
    assert(!/^on/i.test(name), 'Event-handler attributes are forbidden');
    assert(!['href', 'src', 'xlink:href'].includes(name), 'Observer data must not become URLs');
    this.attributes[name] = String(value);
    if (name === 'class') this.className = String(value);
  }
  addEventListener(name, fn) {this.listeners[name] = fn;}
  querySelectorAll(selector) {return walk(this).filter(node => node.className.split(' ').includes(selector.slice(1)));}
  remove() {this.parent.children = this.parent.children.filter(child => child !== this);}
}
for (const sink of ['innerHTML', 'outerHTML']) {
  Object.defineProperty(Element.prototype, sink, {set() {throw Error('Unsafe HTML sink: ' + sink);}});
}
Element.prototype.insertAdjacentHTML = () => {throw Error('Unsafe HTML insertion');};
function fixture() {
  return {version: 1, revision: 1, run_id: 'safe-run', project: {id: 'safe-project', name: hostile, root: hostile},
    title: hostile, status: 'running', current_round: 'r', attempt: 1,
    rounds: [{id: 'r', title: hostile, status: 'running', tasks: [{id: 't', title: hostile, status: 'running', role: hostile, note: hostile, writes: [hostile], resources: [hostile], evidence: [{path: hostile, sha256: hostile}]}], gates: [{id: 'g', title: 'Gate', status: 'failed', return_to: 'r'}]}],
    events: [{seq: 1, kind: 'note', note: hostile, entity_id: 't', candidate: hostile, evidence: [{path: hostile}]}]};
}
function setup(config) {
  const ids = {};
  for (const id of ['legend', 'title', 'run-id', 'project', 'demo', 'run-status', 'current-round', 'attempt', 'revision', 'graph', 'graph-scroll', 'details-content', 'timeline', 'event-count', 'connection-dot', 'connection', 'asof', 'observer-config']) ids[id] = new Element('div');
  ids['observer-config'].textContent = JSON.stringify(config);
  const head = new Element('head'), timeouts = new Map(), intervals = new Map(), requests = [];
  let next = 0;
  const document = {head, getElementById: id => ids[id], createElement: tag => new Element(tag),
    createElementNS: (_, tag) => new Element(tag), createTextNode: value => {const node = new Element('#text'); node.textContent = value; return node;},
    createDocumentFragment: () => new Element('#fragment')};
  const window = {setTimeout: (fn, delay) => {const id = ++next; timeouts.set(id, {fn, delay}); return id;},
    clearTimeout: id => timeouts.delete(id), setInterval: (fn, delay) => {const id = ++next; intervals.set(id, {fn, delay}); return id;}, clearInterval: id => intervals.delete(id)};
  const context = vm.createContext({document, window, console, Date, AbortController,
    fetch: (url, options) => {requests.push({url, options}); return Promise.resolve({ok: true, json: () => Promise.resolve(fixture())});}});
  vm.runInContext(source, context, {filename: 'observer/app.js', timeout: 1000});
  // Test-only export of trusted functions, not evaluation of any fixture text.
  const api = vm.runInContext('({acceptState, validState, loadScriptState, poll, checkStale})', context, {timeout: 1000});
  return {ids, head, timeouts, intervals, requests, window, api};
}
(async () => {
  const state = fixture(), before = JSON.stringify(state);
  const snapshot = setup({transport: 'snapshot', run_id: 'safe-run', project_id: 'safe-project', state});
  assert.equal(snapshot.ids.title.textContent, hostile);
  assert(snapshot.ids.timeline.textContent.includes(hostile));
  const node = walk(snapshot.ids.graph).find(item => item.className.includes('graph-node'));
  node.listeners.click();
  assert(snapshot.ids['details-content'].textContent.includes(hostile));
  assert(snapshot.ids['details-content'].textContent.includes('证据指针（仅展示，不读取文件）'));
  node.listeners.keydown({key: 'Enter', preventDefault() {}});
  assert.equal(snapshot.ids['graph-scroll'].scrollLeft, 17);
  assert.equal(snapshot.ids['graph-scroll'].scrollTop, 31);
  assert.equal(snapshot.timeouts.size + snapshot.intervals.size, 0);
  assert.equal(JSON.stringify(state), before);
  for (const element of Object.values(snapshot.ids)) {
    assert.equal(walk(element).filter(item => ['script', 'img', 'a', 'iframe'].includes(item.tagName)).length, 0);
  }
  assert.equal(snapshot.window.injected, undefined);
  for (const patch of [{revision: 0}, {run_id: 'foreign'}, {project: {id: 'foreign'}}, {rounds: [null]}, {events: [null]}, {version: 2}]) {
    assert.throws(() => snapshot.api.acceptState({...fixture(), ...patch}));
    assert.equal(snapshot.ids.title.textContent, hostile, 'Rejected state must preserve the last screen');
  }
  const revised = fixture(); revised.revision = 2; revised.title = 'Updated';
  snapshot.api.acceptState(revised); assert.equal(snapshot.ids.title.textContent, 'Updated');
  const invalid = setup({transport: 'snapshot', state: {}});
  assert(invalid.ids.connection.textContent.includes('静态报告无效'));

  // Local-script transport only uses its fixed sibling URL, cleans up a timed
  // out element, disables the callback, and reports failure without injection.
  const scripted = setup({transport: 'snapshot', state: fixture()});
  const pending = scripted.api.loadScriptState();
  const script = scripted.head.children[0];
  assert.match(script.src, /^\.\/state\.js\?revision=\d+$/);
  const timeout = [...scripted.timeouts.values()][0]; assert.equal(timeout.delay, 8000);
  timeout.fn(); await assert.rejects(pending, /读取超时/);
  assert.equal(scripted.head.children.length, 0); assert.equal(scripted.timeouts.size, 0);
  scripted.window.pipelineReceive({title: hostile}); assert.equal(scripted.ids.title.textContent, hostile);
  const success = scripted.api.loadScriptState();
  scripted.window.pipelineReceive(fixture()); scripted.head.children[0].onload();
  assert.equal((await success).run_id, 'safe-run'); assert.equal(scripted.head.children.length, 0);

  const live = setup({run_id: 'safe-run', project_id: 'safe-project'});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(live.requests.length, 1); assert.equal(live.requests[0].url, '/api/state');
  assert.equal(live.requests[0].options.cache, 'no-store');
  assert(live.requests[0].options.signal instanceof AbortSignal);
  assert([...live.timeouts.values()].some(value => value.delay === 1500));
  live.api.acceptState({...fixture(), revision: 2, status: 'completed'});
  assert.equal(live.intervals.size, 0);
  for (const timer of [...live.timeouts.values()]) if (timer.delay === 1500) await timer.fn();
  assert.equal(live.requests.length, 1, 'Completion stops subsequent polling');
  console.log('PASS: observer hostile plain text, fixed transport URLs, identity/revision/shape rejection, retained screen, immutable input, details/keyboard/scroll, snapshot failure, script timeout cleanup/recovery, completion stops polling. DOM logic only; no real browser, CSP or layout claim.');
})().catch(error => {console.error(error); process.exitCode = 1;});
