/* Architecture viewer: intentionally dependency-free, read-only and offline. */
(() => {
  'use strict';
  const root = document.getElementById('architecture-app');
  const dom = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  };
  const append = (parent, ...children) => { children.filter(Boolean).forEach(child => parent.appendChild(child)); return parent; };
  const array = value => Array.isArray(value) ? value : [];
  const stringify = value => typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  const button = (text, className, action) => {
    const result = dom('button', className, text);
    result.type = 'button';
    result.addEventListener('click', action);
    return result;
  };
  let data, metadata;
  try {
    data = JSON.parse(document.getElementById('architecture-data').textContent);
    metadata = JSON.parse(document.getElementById('render-metadata').textContent);
    if (!data || !Array.isArray(data.elements) || !Array.isArray(data.views)) throw new Error('缺少 elements 或 views');
  } catch (error) {
    append(root, dom('p', 'fatal', `无法读取架构数据：${error.message}。请从已验证的设计数据重新生成此文件。`));
    return;
  }
  const elements = new Map(array(data.elements).map(item => [item.id, item]));
  const contracts = new Map(array(data.contracts).map(item => [item.id, item]));
  const relationships = new Map(array(data.relationships).map(item => [item.id, item]));
  const flows = new Map(array(data.flows).map(item => [item.id, item]));
  const statusLabels = { current: '当前', planned: '已规划', proposed: '提议', unknown: '待确认' };
  const viewLabels = { overview: '架构总览', module: '模块设计', flow: '业务流程' };
  const kindLabels = { system: '系统', service: '服务', module: '模块', component: '组件', database: '数据存储', storage: '数据存储', worker: '后台任务', store: '数据存储', queue: '消息队列', external: '外部系统', actor: '参与者', client: '客户端', boundary: '边界', interface: '接口' };
  const outcomeLabels = { normal: '正常路径', failure: '失败路径', recovery: '恢复路径' };
  const flowState = (item, flow) => ({ ...item, status: item.status || flow?.status, evidence: item.evidence || (item.status ? [] : flow?.evidence) });
  const status = value => dom('span', `status status-${Object.hasOwn(statusLabels, value) ? value : 'unknown'}`, statusLabels[value] || statusLabels.unknown);
  const warningText = warning => typeof warning === 'string' ? warning : [warning.path, warning.message || warning.code].filter(Boolean).join(' · ');
  const app = dom('div', 'app');
  const sidebar = dom('aside', 'sidebar');
  const brandText = dom('div', '', '架构设计');
  append(brandText, dom('small', '', 'ARCHITECTURE ATLAS'));
  append(sidebar, append(dom('div', 'brand'), dom('span', 'brand-icon', '◈'), brandText));
  const nav = dom('nav', 'nav'); nav.setAttribute('aria-label', '架构视图');
  append(sidebar, nav);
  append(sidebar, append(dom('div', 'sidebar-footer'), dom('p', '', '结构 · 边界 · 协作'), dom('p', '', '离线设计快照 / 只读'), dom('p', '', '设计状态不等于实现状态。')));
  const shell = dom('div', 'shell');
  const header = dom('header', 'project-header');
  append(header, dom('div', 'eyebrow', 'PROJECT ARCHITECTURE / 项目架构'));
  append(header, append(dom('div', 'title-line'), dom('h1', '', data.title || '项目架构'), dom('span', 'read-only', '只读设计快照')));
  if (data.summary) append(header, dom('p', 'project-summary', data.summary));
  const metaRow = dom('div', 'project-meta');
  append(metaRow, dom('span', 'meta-chip', `REV ${data.revision || '—'}`), dom('span', '', `${elements.size} 个构件`), dom('span', '', `${contracts.size} 个契约`), dom('span', '', `${flows.size} 条流程`));
  if (data.architecture && data.architecture.style) append(metaRow, dom('span', 'meta-chip', data.architecture.style));
  append(header, metaRow);
  const workspace = dom('div', 'workspace');
  const main = dom('main', 'main'); main.id = 'main'; main.tabIndex = -1;
  const detail = dom('aside', 'detail-panel'); detail.setAttribute('aria-label', '所选项目详情');
  const announcer = dom('div', 'sr-only'); announcer.setAttribute('role', 'status'); announcer.setAttribute('aria-live', 'polite');
  append(workspace, main, detail); append(shell, header, workspace); append(app, sidebar, shell, announcer); append(root, app);
  document.title = `${data.title || '项目架构'} · 架构设计`;
  let currentView, currentGraph, selected, previousSelection, zoom = 1, autoFit = true;
  let graph, space, viewport, zoomText, searchResult, searchInput;
  let nodeButtons = new Map();
  const navButtons = new Map();
  const announce = message => { announcer.textContent = message; };

  function section(title) {
    const result = dom('section', 'detail-section'); append(result, dom('h3', '', title)); append(detail, result); return result;
  }
  function listSection(title, values) {
    if (!array(values).length) return;
    const list = dom('ul', 'detail-list');
    array(values).forEach(value => append(list, dom('li', '', value)));
    append(section(title), list);
  }
  function evidenceSection(item) {
    const evidence = array(item.evidence);
    if (!evidence.length) {
      if (item.status === 'current') append(detail, dom('p', 'warning-note', '此项标记为当前状态，但没有实现证据。请核实源码或测试，不应仅凭图示认定已实现。'));
      return;
    }
    const box = section('证据 / EVIDENCE');
    evidence.forEach(entry => {
      const block = dom('div', 'evidence');
      append(block, dom('div', 'evidence-path', `${entry.path}${entry.lines ? `:${entry.lines}` : ''}`));
      if (entry.note) append(block, dom('p', '', entry.note));
      append(box, block);
    });
  }
  function detailLink(parent, name, subtitle, action) {
    const link = button(name, 'detail-link', () => {
      action();
      const heading = detail.querySelector('h2');
      if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
    });
    if (subtitle) append(link, dom('small', '', subtitle));
    append(parent, link);
  }
  function contractSection(ids) {
    if (!array(ids).length) return;
    const box = section('接口契约 / CONTRACTS');
    array(ids).forEach(id => {
      const contract = contracts.get(id);
      if (contract) detailLink(box, contract.name, `${id} · ${statusLabels[contract.status] || '待确认'}`, () => select({ type: 'contract', item: contract }, true));
      else append(box, dom('p', 'warning-note', `未找到契约：${id}`));
    });
  }
  function detailsHeader(item, kind) {
    append(detail, append(dom('div', 'detail-kicker'), dom('span', '', kind), dom('span', '', 'READ ONLY')));
    if (selected && selected.type === 'contract' && previousSelection) append(detail, button('← 返回所选项目', 'back-button', () => { const prior = previousSelection; previousSelection = null; select(prior); }));
    if (item.status) append(detail, status(item.status));
    append(detail, dom('h2', '', item.name || item.title || '设计说明'));
    if (item.id) append(detail, dom('div', 'detail-id', item.id));
    if (item.description) append(detail, dom('p', 'detail-description', item.description));
  }
  function renderFields(title, fields) {
    const box = section(title);
    if (!array(fields).length) { append(box, dom('p', 'contracts-empty', '未定义字段')); return; }
    array(fields).forEach(field => {
      const card = dom('div', 'field');
      append(card, dom('div', 'field-title', field.name), dom('div', 'field-type', `${field.type} · ${field.required === true ? '必填' : field.required === false ? '可选' : '必填性未声明'}`));
      if (field.description) append(card, dom('p', '', field.description));
      if (array(field.constraints).length) append(card, dom('p', '', `约束：${field.constraints.join('；')}`));
      append(box, card);
    });
  }
  function showContract(item) {
    detailsHeader(item, '接口契约 / CONTRACT');
    renderFields('输入 / INPUT', item.inputs); renderFields('输出 / OUTPUT', item.outputs);
    if (array(item.errors).length) {
      const box = section('错误与恢复 / ERRORS');
      item.errors.forEach(error => {
        const card = append(dom('div', 'field'), dom('div', 'field-title', error.code), dom('p', '', error.description));
        if (error.recovery) append(card, dom('p', '', `恢复：${error.recovery}`));
        append(box, card);
      });
    }
    listSection('契约规则 / RULES', item.rules);
    if (array(item.stateTransitions).length) {
      const box = section('状态转移 / STATES');
      item.stateTransitions.forEach(transition => append(box, append(dom('div', 'field'), dom('div', 'field-title', `${transition.from} → ${transition.to}`), dom('p', '', `触发：${transition.trigger}`), transition.description ? dom('p', '', transition.description) : null)));
    }
    if (array(item.examples).length) {
      const box = section('示例 / EXAMPLES');
      item.examples.forEach(example => append(box, append(dom('div', 'example'), dom('strong', '', example.name), dom('div', '', '输入'), dom('pre', '', stringify(example.input)), dom('div', '', '输出'), dom('pre', '', stringify(example.output)))));
    }
    evidenceSection(item);
  }
  function showElement(item) {
    detailsHeader(item, `${kindLabels[item.kind] || item.kind || '构件'} / ELEMENT`);
    if (item.parentId) {
      const parent = elements.get(item.parentId);
      if (parent) detailLink(section('所属边界 / PARENT'), parent.name, parent.id, () => select({ type: 'element', item: parent }));
    }
    listSection('职责 / RESPONSIBILITIES', item.responsibilities);
    listSection('业务规则 / RULES', item.rules);
    contractSection(item.contractIds);
    const connected = array(data.relationships).filter(edge => edge.from === item.id || edge.to === item.id);
    if (connected.length) {
      const box = section('协作关系 / RELATIONSHIPS');
      connected.forEach(edge => detailLink(box, edge.label, `${elements.get(edge.from)?.name || edge.from} → ${elements.get(edge.to)?.name || edge.to}`, () => select({ type: 'relationship', item: edge })));
    }
    const changes = array(data.changes).filter(change => array(change.elementIds).includes(item.id));
    if (changes.length) {
      const box = section('设计变更 / CHANGES');
      changes.forEach(change => {
        const card = append(dom('div', 'change'), dom('strong', '', change.name), status(change.status), dom('p', '', change.description));
        if (change.decision || change.verification) append(card, dom('p', '', [change.decision && `决策：${change.decision}`, change.verification && `验证：${change.verification}`].filter(Boolean).join(' · ')));
        array(change.acceptance).forEach(value => append(card, dom('p', '', `验收：${value}`)));
        append(box, card);
      });
    }
    evidenceSection(item);
  }
  function showStep(item) {
    const flow = flows.get(currentView.flowId);
    detailsHeader(flowState(item, flow), '流程步骤 / STEP');
    append(detail, dom('p', 'detail-description', `流程状态：${statusLabels[flow?.status] || '待确认'}；步骤状态：${statusLabels[item.status || flow?.status] || '待确认'}${item.status ? '（显式声明）' : '（继承流程）'}`));
    evidenceSection(flowState(item, flow));
    if (item.outcome) append(detail, dom('p', 'detail-description', outcomeLabels[item.outcome] || item.outcome));
    const element = elements.get(item.elementId);
    if (element) detailLink(section('执行构件 / ELEMENT'), element.name, `${element.id} · ${statusLabels[element.status] || '待确认'}`, () => select({ type: 'element', item: element }));
    contractSection(item.contractIds);
    const transitions = array(flow?.transitions).filter(edge => edge.from === item.id || edge.to === item.id);
    if (transitions.length) {
      const steps = new Map(array(flow.steps).map(step => [step.id, step]));
      const box = section('路径与条件 / TRANSITIONS');
      transitions.forEach(edge => detailLink(box, `${steps.get(edge.from)?.name || edge.from} → ${steps.get(edge.to)?.name || edge.to}`, [edge.label, edge.condition, outcomeLabels[edge.outcome]].filter(Boolean).join(' · '), () => select({ type: 'transition', item: edge })));
    }
  }
  function showRelationship(item, transition) {
    const flow = transition ? flows.get(currentView.flowId) : null;
    detailsHeader({ ...(transition ? flowState(item, flow) : item), name: item.label || (transition ? '流程转移' : '协作关系') }, transition ? '路径 / TRANSITION' : '协作关系 / RELATIONSHIP');
    const map = transition ? new Map(array(flow?.steps).map(step => [step.id, step])) : elements;
    const box = section('方向 / DIRECTION');
    ['from', 'to'].forEach((key, i) => {
      const endpoint = map.get(item[key]);
      if (endpoint) detailLink(box, `${i ? '到' : '从'}：${endpoint.name}`, endpoint.id, () => select({ type: transition ? 'step' : 'element', item: endpoint }));
    });
    if (item.condition) append(section('触发条件 / CONDITION'), dom('p', 'detail-description', item.condition));
    if (item.outcome) append(section('路径类型 / OUTCOME'), dom('p', 'detail-description', outcomeLabels[item.outcome] || item.outcome));
    if (item.kind) append(section('协作方式 / KIND'), dom('p', 'detail-description', item.kind));
    contractSection(item.contractIds); evidenceSection(transition ? flowState(item, flow) : item);
  }
  function showView() {
    const flow = currentView.kind === 'flow' ? flows.get(currentView.flowId) : null;
    detailsHeader(flow || currentView, `${viewLabels[currentView.kind] || '视图'} / VIEW`);
    append(detail, dom('p', 'detail-description', '选择图中的构件或流程步骤，查看职责、规则、接口契约和证据。使用 Tab 键选择，Enter 或空格打开详情。'));
    if (flow) evidenceSection(flow);
    if (data.architecture) {
      append(section('架构选择 / ARCHITECTURE'), dom('p', 'detail-description', data.architecture.style), dom('p', 'detail-description', data.architecture.rationale));
      if (array(data.architecture.alternatives).length) {
        const box = section('备选方案 / ALTERNATIVES');
        data.architecture.alternatives.forEach(alternative => append(box, append(dom('div', 'field'), dom('strong', '', alternative.style), dom('p', '', alternative.reason))));
      }
    }
    if (currentGraph.nodes.length === 0) append(detail, dom('p', 'warning-note', '此视图没有可显示的构件。请检查源数据的视图引用。'));
  }
  function select(selection, remember = false) {
    if (remember) previousSelection = selected;
    else if (selection?.type !== 'contract') previousSelection = null;
    selected = selection; detail.replaceChildren();
    nodeButtons.forEach((node, id) => node.setAttribute('aria-pressed', String(Boolean(selection && ((selection.type === 'step' || selection.type === 'element') && selection.item.id === id)))));
    if (!selection) showView();
    else if (selection.type === 'contract') showContract(selection.item);
    else if (selection.type === 'element') showElement(selection.item);
    else if (selection.type === 'step') showStep(selection.item);
    else showRelationship(selection.item, selection.type === 'transition');
    announce(selection ? `已选择：${selection.item.name || selection.item.label || '路径'}。详情已更新。` : `${currentView.name}，${currentGraph.nodes.length} 个节点。`);
  }

  // Collapse strongly connected components first: cycles remain visible without
  // pushing every downstream node into one enormous rank or looping forever.
  function layout(nodes, edges) {
    const ids = new Set(nodes.map(node => node.id));
    const adjacency = new Map(nodes.map(node => [node.id, []]));
    edges.forEach(edge => { if (ids.has(edge.from) && ids.has(edge.to)) adjacency.get(edge.from).push(edge.to); });
    let index = 0; const stack = [], onStack = new Set(), indices = new Map(), low = new Map(), components = [];
    function visit(id) {
      indices.set(id, index); low.set(id, index++); stack.push(id); onStack.add(id);
      adjacency.get(id).forEach(next => {
        if (!indices.has(next)) { visit(next); low.set(id, Math.min(low.get(id), low.get(next))); }
        else if (onStack.has(next)) low.set(id, Math.min(low.get(id), indices.get(next)));
      });
      if (low.get(id) === indices.get(id)) {
        const group = []; let next;
        do { next = stack.pop(); onStack.delete(next); group.push(next); } while (next !== id);
        components.push(group);
      }
    }
    nodes.forEach(node => { if (!indices.has(node.id)) visit(node.id); });
    const componentOf = new Map(); components.forEach((group, i) => group.forEach(id => componentOf.set(id, i)));
    const links = components.map(() => new Set()), degree = components.map(() => 0), rank = components.map(() => 0);
    edges.forEach(edge => {
      const a = componentOf.get(edge.from), b = componentOf.get(edge.to);
      if (a !== undefined && b !== undefined && a !== b && !links[a].has(b)) { links[a].add(b); degree[b]++; }
    });
    const queue = degree.flatMap((value, i) => value === 0 ? [i] : []);
    for (let i = 0; i < queue.length; i++) links[queue[i]].forEach(next => { rank[next] = Math.max(rank[next], rank[queue[i]] + 1); if (--degree[next] === 0) queue.push(next); });
    const ranks = new Map(); nodes.forEach(node => { const r = rank[componentOf.get(node.id)]; if (!ranks.has(r)) ranks.set(r, []); ranks.get(r).push(node); });
    const nodeWidth = 224, nodeHeight = 162, gapX = 62, gapY = 100, padding = 42;
    const columns = Math.min(3, Math.max(1, ...Array.from(ranks.values(), group => group.length)));
    const width = padding * 2 + columns * nodeWidth + (columns - 1) * gapX;
    let y = padding;
    const positions = new Map();
    [...ranks.keys()].sort((a, b) => a - b).forEach(r => {
      const group = ranks.get(r);
      for (let start = 0; start < group.length; start += columns) {
        const row = group.slice(start, start + columns); const rowWidth = row.length * nodeWidth + (row.length - 1) * gapX;
        row.forEach((node, i) => positions.set(node.id, { x: (width - rowWidth) / 2 + i * (nodeWidth + gapX), y, width: nodeWidth, height: nodeHeight }));
        y += nodeHeight + gapY;
      }
    });
    return { positions, width, height: Math.max(300, y - gapY + padding) };
  }
  const svgNode = (tag, attributes, text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attributes || {}).forEach(([key, value]) => node.setAttribute(key, String(value)));
    if (text !== undefined) node.textContent = String(text);
    return node;
  };
  function updateZoom() {
    if (!graph || !currentGraph.layout) return;
    graph.style.transform = `scale(${zoom})`;
    space.style.width = `${currentGraph.layout.width * zoom}px`;
    space.style.height = `${currentGraph.layout.height * zoom}px`;
    zoomText.textContent = `${Math.round(zoom * 100)}%`;
  }
  function fit() {
    const available = Math.max(100, viewport.clientWidth - (window.innerWidth <= 640 ? 24 : 40));
    zoom = Math.max(.25, Math.min(1, available / currentGraph.layout.width)); autoFit = true; updateZoom();
  }
  function zoomBy(amount) { zoom = Math.max(.25, Math.min(2, zoom + amount)); autoFit = false; updateZoom(); }
  function renderGraph() {
    nodeButtons = new Map();
    currentGraph.layout = layout(currentGraph.nodes, currentGraph.edges);
    const geometry = currentGraph.layout;
    graph.style.width = `${geometry.width}px`; graph.style.height = `${geometry.height}px`;
    const svg = svgNode('svg', { class: 'edges', width: geometry.width, height: geometry.height, 'aria-hidden': 'true' });
    const defs = svgNode('defs');
    [['normal', '#89a494'], ['failure', '#bd6567'], ['recovery', '#8a6fb2']].forEach(([kind, color]) => {
      const marker = svgNode('marker', { id: `arrow-${kind}`, markerWidth: 7, markerHeight: 7, refX: 6, refY: 3.5, orient: 'auto', markerUnits: 'strokeWidth' });
      marker.appendChild(svgNode('path', { d: 'M0,0 L7,3.5 L0,7 Z', fill: color })); defs.appendChild(marker);
    }); svg.appendChild(defs);
    currentGraph.edges.forEach((edge, index) => {
      const from = geometry.positions.get(edge.from), to = geometry.positions.get(edge.to); if (!from || !to) return;
      let path, lx, ly;
      if (to.y > from.y && edge.from !== edge.to) {
        const sx = from.x + from.width / 2, sy = from.y + from.height, tx = to.x + to.width / 2, ty = to.y;
        const mid = sy + (ty - sy) / 2 + (index % 3 - 1) * 9;
        path = `M ${sx} ${sy} C ${sx} ${mid}, ${tx} ${mid}, ${tx} ${ty - 5}`; lx = (sx + tx) / 2; ly = mid - 7;
      } else {
        const right = to.x >= from.x;
        const sx = right ? from.x + from.width : from.x, tx = right ? to.x : to.x + to.width;
        const sy = from.y + from.height / 2, ty = to.y + to.height / 2;
        if (edge.from === edge.to) {
          const x = from.x + from.width, y = from.y + 40;
          path = `M ${x} ${y} C ${x + 44} ${y - 42}, ${x + 44} ${y + 80}, ${x + 5} ${y + 65}`; lx = x + 16; ly = y - 18;
        } else if (from.y === to.y) {
          const top = from.y - 22 - index % 3 * 6;
          path = `M ${sx} ${sy} C ${sx + (right ? 28 : -28)} ${top}, ${tx + (right ? -28 : 28)} ${top}, ${tx + (right ? -5 : 5)} ${ty}`; lx = (sx + tx) / 2; ly = top + 10;
        } else {
          const outer = right ? Math.max(from.x + from.width, to.x + to.width) + 25 : Math.min(from.x, to.x) - 25;
          const endX = right ? to.x + to.width : to.x;
          path = `M ${sx} ${sy} C ${outer} ${sy}, ${outer} ${ty}, ${endX + (right ? 5 : -5)} ${ty}`; lx = outer; ly = (sy + ty) / 2 - 8;
        }
      }
      const outcome = Object.hasOwn(outcomeLabels, edge.outcome) ? edge.outcome : 'normal';
      const statusClass = Object.hasOwn(statusLabels, edge.status) ? edge.status : 'unknown';
      svg.appendChild(svgNode('path', { d: path, class: `edge edge-${statusClass} edge-${outcome}`, 'marker-end': `url(#arrow-${outcome})` }));
      const label = edge.label || edge.condition || '';
      if (label) {
        const text = svgNode('text', { x: lx, y: ly, class: `edge-label edge-label-${outcome}`, 'text-anchor': 'middle' }, [...label].length > 22 ? [...label].slice(0, 21).join('') + '…' : label);
        text.appendChild(svgNode('title', {}, label)); svg.appendChild(text);
      }
    });
    graph.appendChild(svg);
    currentGraph.nodes.forEach((item, index) => {
      const isFlow = currentView.kind === 'flow';
      const outcome = Object.hasOwn(outcomeLabels, item.outcome) ? item.outcome : 'normal';
      const node = button('', `node node-${outcome}`, () => select({ type: isFlow ? 'step' : 'element', item }));
      const position = geometry.positions.get(item.id);
      Object.entries({ left: position.x, top: position.y, width: position.width, height: position.height }).forEach(([key, value]) => { node.style[key] = `${value}px`; });
      node.setAttribute('aria-pressed', 'false');
      const itemStatus = isFlow ? item.status || flows.get(currentView.flowId)?.status : item.status;
      node.setAttribute('aria-label', `${item.name}，${isFlow ? '流程步骤' : kindLabels[item.kind] || item.kind}，${statusLabels[itemStatus] || '待确认'}${isFlow && item.outcome ? `，${outcomeLabels[item.outcome]}` : ''}。查看详情`);
      const top = append(dom('div', 'node-top'), dom('span', isFlow ? 'step-number' : 'kind', isFlow ? `STEP ${String(index + 1).padStart(2, '0')}` : kindLabels[item.kind] || item.kind), status(itemStatus));
      append(node, top, dom('div', 'node-title', item.name), dom('div', 'node-description', item.description || (isFlow ? elements.get(item.elementId)?.name : '') || '选择查看设计详情'));
      append(node, append(dom('div', 'node-bottom'), dom('span', 'node-id', isFlow ? item.elementId : item.id), dom('span', 'node-mark', '↗')));
      node.addEventListener('keydown', event => {
        const items = [...nodeButtons.values()]; let next;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = items[(index + 1) % items.length];
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = items[(index + items.length - 1) % items.length];
        if (event.key === 'Home') next = items[0]; if (event.key === 'End') next = items[items.length - 1];
        if (next) { event.preventDefault(); next.focus(); }
        if (event.key === 'Escape') select(null);
      });
      nodeButtons.set(item.id, node); append(graph, node);
    });
    if (!currentGraph.nodes.length) append(graph, dom('p', 'empty', '此视图没有可显示的节点。'));
    requestAnimationFrame(fit);
  }
  function filterNodes() {
    const query = searchInput.value.trim().toLocaleLowerCase(); let count = 0;
    currentGraph.nodes.forEach(item => {
      const matches = !query || [item.id, item.name, item.kind, item.description, ...(item.responsibilities || [])].filter(Boolean).join(' ').toLocaleLowerCase().includes(query);
      nodeButtons.get(item.id)?.classList.toggle('is-dimmed', !matches); if (matches) count++;
    });
    searchResult.textContent = query ? `${count} / ${currentGraph.nodes.length} 个节点匹配。关系仍完整保留。` : '选择节点查看详情 · Tab / 方向键浏览 · Esc 返回视图说明';
  }
  function renderProvenance() {
    const block = dom('details', 'provenance'); append(block, dom('summary', '', '生成信息 / Provenance'));
    const list = dom('dl');
    [['源文件', metadata.sourceName], ['源文件 SHA-256', metadata.sourceSha256], ['资源 SHA-256', metadata.assetsSha256], ['生成时间', metadata.generatedAt], ['渲染器', metadata.rendererVersion], ['设计修订', data.revision]].forEach(([label, value]) => {
      if (value !== undefined) append(list, dom('dt', '', label), dom('dd', '', typeof value === 'object' ? stringify(value) : value));
    }); append(block, list); append(main, block);
  }
  function openView(view) {
    currentView = view; selected = null; previousSelection = null; main.replaceChildren();
    navButtons.forEach((node, id) => { if (id === view.id) node.setAttribute('aria-current', 'page'); else node.removeAttribute('aria-current'); });
    const flow = view.kind === 'flow' ? flows.get(view.flowId) : null;
    const viewElements = array(view.elementIds).map(id => elements.get(id)).filter(Boolean);
    currentGraph = {
      nodes: flow ? array(flow.steps) : viewElements,
      edges: flow ? array(flow.transitions).map(edge => flowState(edge, flow)) : array(view.relationshipIds).map(id => relationships.get(id)).filter(Boolean)
    };
    const headingText = append(dom('div'), dom('h2', '', view.name));
    append(headingText, dom('p', 'view-description', view.description || flow?.description || '构件、职责边界与协作关系。'));
    append(main, append(dom('div', 'view-heading'), headingText, dom('span', 'view-index', `${String(data.views.indexOf(view) + 1).padStart(2, '0')} / ${String(data.views.length).padStart(2, '0')}`)));
    const toolbar = dom('div', 'toolbar'); const search = dom('label', 'search-box');
    append(search, dom('span', 'sr-only', '在当前视图中查找节点'));
    searchInput = dom('input'); searchInput.type = 'search'; searchInput.placeholder = '查找构件、步骤或职责…'; searchInput.addEventListener('input', filterNodes);
    searchInput.addEventListener('keydown', event => { if (event.key === 'Enter') { const first = [...nodeButtons.values()].find(node => !node.classList.contains('is-dimmed')); first?.focus(); } }); append(search, searchInput);
    const controls = dom('div', 'zoom-controls'); controls.setAttribute('aria-label', '图形缩放');
    const minus = button('−', 'control', () => zoomBy(-.1)); minus.setAttribute('aria-label', '缩小图形');
    const plus = button('+', 'control', () => zoomBy(.1)); plus.setAttribute('aria-label', '放大图形');
    zoomText = dom('span', 'zoom-readout'); zoomText.setAttribute('aria-live', 'polite');
    append(controls, minus, zoomText, plus, button('适应宽度', 'control fit-button', fit)); append(toolbar, search, controls); append(main, toolbar);
    const frame = dom('section', 'diagram-frame'); frame.setAttribute('aria-label', `${view.name}架构图`);
    append(frame, append(dom('div', 'diagram-caption'), dom('strong', '', `${viewLabels[view.kind] || '架构视图'} / ${view.kind.toUpperCase()}`), dom('span', '', `${currentGraph.nodes.length} 个节点 · ${currentGraph.edges.length} 条关系`)));
    viewport = dom('div', 'diagram-viewport'); viewport.tabIndex = 0; viewport.setAttribute('aria-label', '可滚动架构图');
    space = dom('div', 'diagram-space'); graph = dom('div', 'diagram');
    append(space, graph); append(viewport, space); append(frame, viewport); append(main, frame);
    const legend = dom('div', 'legend');
    Object.keys(statusLabels).forEach(value => append(legend, status(value)));
    const edgeLegend = (label, className) => append(legend, append(dom('span', 'legend-item'), dom('span', `legend-line ${className}`), dom('span', '', label)));
    edgeLegend('当前关系', ''); edgeLegend('非当前关系', 'dashed');
    if (flow) { edgeLegend('失败', 'failure'); edgeLegend('恢复', 'recovery'); }
    append(main, legend);
    searchResult = dom('p', 'search-result'); searchResult.setAttribute('role', 'status'); append(main, searchResult);
    if (currentGraph.edges.length) {
      const relationBlock = dom('details', 'relations'); append(relationBlock, dom('summary', '', `关系清单 · ${currentGraph.edges.length} 条（可键盘访问）`));
      const list = dom('div', 'relation-list'); const map = flow ? new Map(flow.steps.map(step => [step.id, step])) : elements;
      currentGraph.edges.forEach(edge => detailLink(list, edge.label || edge.condition || '未命名关系', `${map.get(edge.from)?.name || edge.from} → ${map.get(edge.to)?.name || edge.to}`, () => select({ type: flow ? 'transition' : 'relationship', item: edge })));
      append(relationBlock, list); append(main, relationBlock);
    }
    if (data.architecture?.rationale) {
      const note = dom('div', 'architecture-note');
      append(note, dom('span', 'note-icon', '◇'), append(dom('div'), dom('h3', '', `架构决策 · ${data.architecture.style}`), dom('p', '', data.architecture.rationale))); append(main, note);
    }
    const warnings = array(metadata.warnings);
    if (warnings.length) {
      const block = dom('details', 'warnings'); append(block, dom('summary', '', `${warnings.length} 条待核实事项`)); const list = dom('ul');
      warnings.forEach(warning => append(list, dom('li', '', warningText(warning)))); append(block, list); append(main, block);
    }
    renderProvenance(); renderGraph(); filterNodes(); select(null);
  }
  ['overview', 'module', 'flow'].forEach(kind => {
    const views = data.views.filter(view => view.kind === kind); if (!views.length) return;
    const group = dom('div', 'nav-group'); append(group, dom('div', 'nav-label', `${viewLabels[kind]} / ${kind.toUpperCase()}`));
    views.forEach(view => {
      const node = button('', 'nav-button', () => openView(view));
      const count = kind === 'flow' ? array(flows.get(view.flowId)?.steps).length : array(view.elementIds).length;
      append(node, dom('span', 'nav-dot'), dom('span', 'nav-name', view.name), dom('span', 'nav-count', String(count)));
      navButtons.set(view.id, node); append(group, node);
    }); append(nav, group);
  });
  if (!data.views.length) { append(main, dom('p', 'empty', '尚未定义架构视图。')); return; }
  const observer = typeof ResizeObserver === 'function' ? new ResizeObserver(() => { if (autoFit && viewport) fit(); }) : null;
  if (observer) observer.observe(main); else window.addEventListener('resize', () => { if (autoFit && viewport) fit(); });
  openView(data.views.find(view => view.kind === 'overview') || data.views[0]);
})();
