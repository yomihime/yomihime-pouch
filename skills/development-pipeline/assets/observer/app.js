"use strict";

const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const labels = {draft:"规划中",running:"执行中",needs_decision:"等待决策",consulting:"顾问介入",blocked:"已阻塞",completed:"已完成",pending:"待执行",ready:"就绪",passed:"已通过",failed:"失败",skipped:"已跳过"};
const colors = {pending:"#aabbb6",ready:"#7198a9",running:"#3984b5",passed:"#2f9878",failed:"#c25d57",skipped:"#a88c5c"};
const kinds = {init:"初始化",plan:"计划更新",start:"开始执行",task:"任务更新",gate:"检查点更新",decide:"决策",note:"备注",consult:"顾问介入",return:"返回轮次",block:"阻塞"};
const POLL_INTERVAL_MS = 1500, REQUEST_TIMEOUT_MS = 8000, STALE_AFTER_MS = 10000;
let state = null, selected = null, lastRevision = null, lastRun = null, lastSuccess = null;
const config = JSON.parse($("observer-config")?.textContent || "{}");
let stopped = false, staleTimer = null;
const openEvents = new Set();
const text = (value, fallback = "—") => value === null || value === undefined || value === "" ? fallback : String(value);
const statusLabel = value => labels[value] || text(value);
function el(tag, className, value) { const node = document.createElement(tag); if (className) node.className = className; if (value !== undefined) node.textContent = value; return node; }
function svg(tag, attrs = {}, value) { const node = document.createElementNS(NS, tag); for (const [key, val] of Object.entries(attrs)) node.setAttribute(key, String(val)); if (value !== undefined) node.textContent = value; return node; }
function formatTime(value) { if (!value) return "—"; const date = new Date(value); return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("zh-CN", {hour12:false}); }
function clip(value, limit) { const chars = Array.from(text(value)); return chars.length > limit ? chars.slice(0, limit - 1).join("") + "…" : chars.join(""); }
function roundList() { return state && Array.isArray(state.rounds) ? state.rounds : []; }
function nodeById(id) { for (const round of roundList()) { for (const item of [...(Array.isArray(round.tasks) ? round.tasks : []), ...(Array.isArray(round.gates) ? round.gates : [])]) if (item.id === id) return {item, round, type:(round.tasks || []).includes(item) ? "任务" : "检查点"}; } return null; }

for (const key of ["pending","running","passed","failed","skipped"]) { const entry = el("span"); const dot = el("i"); dot.style.setProperty("--c", colors[key]); entry.append(dot, document.createTextNode(labels[key])); $("legend").append(entry); }

function renderSummary() {
  $("title").textContent = text(state.title, "未命名流水线");
  $("run-id").textContent = "运行 ID · " + text(state.run_id);
  $("project").textContent = state.project ? `项目 · ${text(state.project.name)} · ${text(state.project.root)}` : "项目身份未记录（旧版运行）";
  $("demo").hidden = !state.demo;
  $("run-status").textContent = statusLabel(state.status);
  const current = roundList().find(r => r.id === state.current_round);
  $("current-round").textContent = current ? text(current.title, text(current.id)) : text(state.current_round);
  $("attempt").textContent = text(state.attempt);
  $("revision").textContent = text(state.revision);
}

function renderGraph() {
  const host = $("graph"), scroll = $("graph-scroll"), left = scroll.scrollLeft, top = scroll.scrollTop;
  const rounds = roundList();
  if (!rounds.length) { host.replaceChildren(el("div", "empty", "计划尚无轮次。计划事件上报后将在此逐步呈现。")); return; }
  const col = 250, cardW = 205, cardH = 55, gap = 12, startY = 100;
  const maxRows = Math.max(...rounds.map(r => (Array.isArray(r.tasks) ? r.tasks.length : 0) + (Array.isArray(r.gates) ? r.gates.length : 0)), 1);
  const returnCount = rounds.reduce((n,r) => n + (Array.isArray(r.gates) ? r.gates.filter(g => g.return_to && rounds.some(target => target.id === g.return_to)).length : 0),0);
  const width = Math.max(280, rounds.length * col + 32), height = startY + maxRows * (cardH + gap) + 55 + returnCount * 26;
  const root = svg("svg", {width, height, viewBox:`0 0 ${width} ${height}`, role:"img", "aria-label":"轮次流程图"});
  const defs = svg("defs"); const marker = svg("marker", {id:"arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:6,markerHeight:6,orient:"auto-start-reverse"}); marker.append(svg("path", {d:"M 0 0 L 10 5 L 0 10 z",fill:"#b4c9c2"})); defs.append(marker); const returnArrow = svg("marker",{id:"return-arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:6,markerHeight:6,orient:"auto"}); returnArrow.append(svg("path",{d:"M 0 0 L 10 5 L 0 10 z",fill:"#c57a68"})); defs.append(returnArrow); root.append(defs);
  const edgeLayer = svg("g"), nodeLayer = svg("g"); root.append(edgeLayer,nodeLayer);
  let returnIndex = 0;
  rounds.forEach((round, i) => {
    const x = 22 + i * col, tasks = Array.isArray(round.tasks) ? round.tasks : [], gates = Array.isArray(round.gates) ? round.gates : [];
    nodeLayer.append(svg("text", {x,y:30,class:"round-meta"}, `ROUND ${String(i + 1).padStart(2,"0")} · ${statusLabel(round.status)}`));
    nodeLayer.append(svg("text", {x,y:51,class:"round-label"}, clip(round.title || round.id, 17)));
    nodeLayer.append(svg("text", {x,y:70,class:"round-meta"}, `${tasks.length} 个并行任务 · ${gates.length} 个检查点`));
    if (i < rounds.length - 1) edgeLayer.append(svg("path", {d:`M ${x + cardW + 4} 45 H ${x + col - 8}`,class:"edge","marker-end":"url(#arrow)"}));
    const all = [...tasks.map(item => ({item,type:"任务"})),...gates.map(item => ({item,type:"检查点"}))];
    if (tasks.length) {
      const branchX = x - 9, firstY = startY + cardH / 2, lastY = startY + (tasks.length - 1) * (cardH + gap) + cardH / 2;
      const mergeX = x + cardW + 9;
      edgeLayer.append(svg("path",{d:`M ${branchX} ${firstY} V ${lastY} M ${mergeX} ${firstY} V ${lastY}`,class:"edge"}));
      if (gates.length) edgeLayer.append(svg("path",{d:`M ${mergeX} ${lastY} V ${startY + tasks.length * (cardH + gap) - 7} H ${x + cardW / 2} V ${startY + tasks.length * (cardH + gap)}`,class:"edge","marker-end":"url(#arrow)"}));
    }
    all.forEach(({item,type}, j) => {
      const y = startY + j * (cardH + gap), status = text(item.status,"pending"), color = colors[status] || colors.pending;
      if (type === "任务") edgeLayer.append(svg("path",{d:`M ${x - 9} ${y + cardH / 2} H ${x} M ${x + cardW} ${y + cardH / 2} H ${x + cardW + 9}`,class:"edge"}));
      else if (j > tasks.length) edgeLayer.append(svg("path", {d:`M ${x + cardW / 2} ${y - gap} V ${y}`,class:"edge","marker-end":"url(#arrow)"}));
      const group = svg("g", {class:"graph-node" + (selected === item.id ? " selected" : ""),tabindex:0,role:"button","aria-label":`${type} ${text(item.title, text(item.id))}，${statusLabel(status)}`,"aria-pressed":selected === item.id});
      group.append(svg("rect",{x,y,width:cardW,height:cardH,rx:9,fill:"#fff",stroke:"#d8e5df",class:"node-box"}));
      group.append(svg("circle",{cx:x+15,cy:y+18,r:4,fill:color}));
      group.append(svg("text",{x:x+27,y:y+22,class:"node-title"},clip(item.title || item.id,16)));
      group.append(svg("text",{x:x+15,y:y+42,class:"node-meta"},`${type} · ${statusLabel(status)}${item.attempt != null ? " · 尝试 " + item.attempt : ""}`));
      const choose = () => { selected = item.id; root.querySelectorAll(".graph-node").forEach(n => { const active = n === group; n.classList.toggle("selected",active); n.setAttribute("aria-pressed",String(active)); }); renderDetails(); };
      group.addEventListener("click", choose); group.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); choose(); } }); nodeLayer.append(group);
      if (type === "检查点" && item.return_to) { const target = rounds.findIndex(r => r.id === item.return_to); if (target >= 0 && target <= i) { const lineY = startY + maxRows * (cardH + gap) + 35 + returnIndex++ * 26; const tx = 22 + target * col + cardW / 2; edgeLayer.append(svg("path",{d:`M ${x + cardW} ${y + cardH / 2} H ${x + cardW + 18} V ${lineY} H ${tx} V ${startY + 4}`,class:"return-edge","marker-end":"url(#return-arrow)"})); edgeLayer.append(svg("text",{x:Math.min(tx,x + cardW)+5,y:lineY-5,class:"return-label"},`失败返回 ${clip(rounds[target].title || item.return_to,12)}`)); } }
    });
    if (!all.length) nodeLayer.append(svg("text",{x,y:startY+22,class:"round-meta"},"尚未定义任务或检查点"));
  });
  host.replaceChildren(root); scroll.scrollLeft = left; scroll.scrollTop = top;
}

function renderDetails() {
  const host = $("details-content"), found = nodeById(selected);
  if (!found) { host.replaceChildren(el("div","empty",selected ? "该节点不在当前计划中。" : "尚未选择节点")); return; }
  const {item,round,type} = found, title = el("div","detail-heading",text(item.title,text(item.id))), badge = el("span","detail-status",statusLabel(item.status));
  badge.style.color = colors[item.status] || "#627a73";
  const fragment = document.createDocumentFragment(); fragment.append(title,badge);
  function row(label,value) { const box=el("div","detail-row"); box.append(el("div","detail-label",label),el("div","detail-value",text(value))); fragment.append(box); }
  row("类型 / ID",`${type} · ${text(item.id)}`); row("所属轮次",text(round.title,text(round.id))); row("尝试 / 更新时间",`${text(item.attempt)} · ${formatTime(item.updated_at)}`);
  row(type === "任务" ? "角色" : "检查类型",type === "任务" ? item.role : item.kind); row("是否必需",item.required === false ? "非必需" : item.required === true ? "必需" : "—");
  if (type === "检查点") row("失败返回",item.return_to);
  if (type === "任务") { row("写入范围",Array.isArray(item.writes) && item.writes.length ? item.writes.join("\n") : "—"); row("资源",Array.isArray(item.resources) && item.resources.length ? item.resources.join("\n") : "—"); }
  row("候选",item.candidate); row("备注",item.note);
  const box = el("div","detail-row"); box.append(el("div","detail-label","证据指针（仅展示，不读取文件）"));
  if (Array.isArray(item.evidence) && item.evidence.length) item.evidence.forEach(e => box.append(el("div","evidence",`${text(e && e.path)}${e && e.sha256 ? "\nSHA-256 " + e.sha256 : ""}`))); else box.append(el("div","detail-value","—"));
  fragment.append(box); host.replaceChildren(fragment);
}

function renderTimeline() {
  const host = $("timeline"), events = Array.isArray(state.events) ? state.events : [], fragment = document.createDocumentFragment();
  $("event-count").textContent = `${events.length} 条事件`;
  if (!events.length) fragment.append(el("div","empty","尚无事件记录"));
  [...events].reverse().forEach(event => {
    const failed = event.status === "failed" || event.result === "failed" || event.state === "failed";
    const row = el("div","event" + (failed ? " failed" : "")), time = el("div","event-time",formatTime(event.time));
    const decisionNames = {consult:"顾问介入",return:"返回轮次",block:"阻塞"};
    const eventName = event.kind === "decide" ? (decisionNames[event.decision] || "决策") : (kinds[event.kind] || text(event.kind,"事件"));
    const target = roundList().find(r => r.id === event.round_id);
    const targetText = event.kind === "decide" && event.decision === "return" ? `目标：${target ? text(target.title,text(target.id)) : text(event.round_id)}` : text(event.entity_id, text(event.round_id,"流水线"));
    const body = el("div","event-body"), heading = el("div","event-title"), tag = el("span","event-tag",eventName);
    heading.append(tag,document.createTextNode(`#${text(event.seq)} · ${targetText}${event.status ? " · " + statusLabel(event.status) : ""}${event.attempt != null ? " · 尝试 " + event.attempt : ""}`));
    body.append(heading); if (event.note) body.append(el("div","event-note",String(event.note)));
    const details = el("details","event-details"), summary = el("summary",null,"查看历史信息"); details.append(summary);
    const fields = [["候选",event.candidate],["决策",event.decision ? (decisionNames[event.decision] || event.decision) : null],["目标轮次",event.kind === "decide" && event.round_id ? targetText : null],["已确认交接",typeof event.quiesced === "boolean" ? (event.quiesced ? "是" : "否") : null]];
    fields.forEach(([label,value]) => { if (value !== null && value !== undefined && value !== "") details.append(el("div","event-extra",`${label}：${value}`)); });
    if (Array.isArray(event.evidence)) event.evidence.forEach(e => { if (e && typeof e === "object") details.append(el("div","event-extra",`证据：${text(e.path)}${e.sha256 ? "\nSHA-256 " + e.sha256 : ""}`)); });
    if (details.children.length === 1) details.append(el("div","event-extra","无附加信息"));
    const key = String(event.seq); details.open = openEvents.has(key); details.addEventListener("toggle",() => { if (details.open) openEvents.add(key); else openEvents.delete(key); });
    body.append(details); row.append(time,body); fragment.append(row);
  });
  host.replaceChildren(fragment);
}

function render() { renderSummary(); renderGraph(); renderDetails(); renderTimeline(); }
function connection(ok, message) { $("connection-dot").className = "dot " + (ok ? "online" : "offline"); $("connection").textContent = message; $("asof").textContent = lastSuccess ? "数据截至 " + formatTime(lastSuccess) : "尚无成功数据"; }
function checkStale() { if (!stopped && lastSuccess && Date.now() - Date.parse(lastSuccess) >= STALE_AFTER_MS) connection(false,"读取异常 · 保留上次画面"); }
function validState(data) {
  const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
  return object(data) && data.version === 1 && Number.isInteger(data.revision) && Array.isArray(data.rounds) && Array.isArray(data.events)
    && data.rounds.every(round => object(round) && Array.isArray(round.tasks) && Array.isArray(round.gates) && [...round.tasks,...round.gates].every(object))
    && data.events.every(object);
}
function acceptState(data) {
  if (!validState(data)) throw new Error("状态格式无效");
  if ((config.run_id && data.run_id !== config.run_id) || (config.project_id && data.project?.id !== config.project_id) || (lastRun && data.run_id !== lastRun)) throw new Error("项目或运行身份不匹配");
  if (lastRevision !== null && data.revision < lastRevision) throw new Error("拒绝过期版本");
  lastSuccess = new Date().toISOString();
  if (lastRevision !== data.revision || lastRun !== data.run_id) { state = data; lastRevision = data.revision; lastRun = data.run_id; render(); }
  stopped = data.status === "completed" || config.transport === "snapshot";
  if (stopped && staleTimer !== null) window.clearInterval(staleTimer);
  connection(true, stopped ? "运行已结束 · 静态留存" : "读取正常");
}
function loadScriptState() {
  return new Promise((resolve,reject) => {
    const script = document.createElement("script");
    let received = null;
    window.pipelineReceive = data => { received = data; };
    const finish = error => { window.clearTimeout(timeout); script.remove(); window.pipelineReceive = () => {}; error ? reject(error) : resolve(received); };
    const timeout = window.setTimeout(() => finish(new Error("读取超时")), REQUEST_TIMEOUT_MS);
    script.onload = () => finish(received ? null : new Error("数据文件无有效回报"));
    script.onerror = () => finish(new Error("无法读取数据文件"));
    script.src = "./state.js?revision=" + Date.now();
    document.head.append(script);
  });
}
async function poll() {
  if (stopped) return;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    let data;
    if (config.transport === "script") data = await loadScriptState();
    else { const response = await fetch("/api/state", {cache:"no-store",headers:{Accept:"application/json"},signal:controller.signal}); if (!response.ok) throw new Error("HTTP " + response.status); data = await response.json(); }
    acceptState(data);
  } catch (error) { connection(false,"读取异常 · 保留上次画面"); }
  finally { window.clearTimeout(timeout); if (!stopped) window.setTimeout(poll, POLL_INTERVAL_MS); }
}
if (config.transport === "snapshot") { try { acceptState(config.state); } catch (error) { connection(false,"静态报告无效"); } }
else { staleTimer = window.setInterval(checkStale, 1000); poll(); }
