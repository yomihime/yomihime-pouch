(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  let data = null, tab = 'active', failed = false;
  const staleMs = 7 * 24 * 60 * 60 * 1000;
  const labels = {draft:'草稿', running:'执行中', needs_decision:'等待决策', consulting:'咨询中', blocked:'已阻塞', completed:'已完成'};
  function kind(r) {
    if (r.error) return 'unknown';
    if (r.status === 'completed') return 'archive';
    return Date.now() - Date.parse(r.updated_at) >= staleMs ? 'archive' : 'active';
  }
  function isStale(r) { return !r.error && r.status !== 'completed' && kind(r) === 'archive'; }
  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function render() {
    if (!data) return;
    const runs = data.runs.slice().sort((a,b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
    const active = runs.filter(r => kind(r) === 'active').length, archived = runs.filter(r => kind(r) === 'archive').length, unknown = runs.filter(r => kind(r) === 'unknown').length;
    $('#active-count').textContent = active; $('#archive-count').textContent = archived;
    $('#attention-count').textContent = runs.filter(r => r.error || ['needs_decision','consulting','blocked'].includes(r.status)).length;
    document.querySelectorAll('.tab').forEach(b => { b.classList.toggle('active', b.dataset.tab === tab); b.setAttribute('aria-selected', String(b.dataset.tab === tab)); b.querySelector('small').textContent = b.dataset.tab === 'active' ? active : b.dataset.tab === 'archive' ? archived : b.dataset.tab === 'unknown' ? unknown : runs.length; });
    $('#notice').textContent = (failed ? '本地索引读取失败，显示的是上次成功加载的数据。' : '索引生成于 ' + new Date(data.generated_at).toLocaleString() + '。') + ' 状态来自事件记录，不探测进程；7 天无新事件的未完成运行标为过期。' + (unknown ? ' 有 ' + unknown + ' 条日志读取失败，请查看“读取失败”。' : '');
    const q = $('#search').value.trim().toLocaleLowerCase();
    const rows = runs.filter(r => (tab === 'all' || kind(r) === tab) && [r.title,r.run_id,r.project,r.round,r.path,r.status,r.error].join(' ').toLocaleLowerCase().includes(q));
    const list = $('#list'); list.replaceChildren();
    if (!rows.length) list.append(el('div','empty','没有找到匹配的流水线'));
    for (const r of rows) {
      const row = el('div','row'), name = el('div'), repo = el('div','repo'), status = el('div','status'), updated = el('div','updated muted'), links = el('div','links');
      name.append(el('div','name',r.title || '无法读取的运行'), el('div','sub',r.run_id || r.path));
      if (r.demo) name.append(el('div','sub','合成演示记录'));
      if (r.error) name.append(el('div','sub','事件日志读取失败：' + r.error));
      repo.append(el('div',null,r.project || '项目未记录'), el('div','sub',r.round ? '当前轮次：' + r.round : '无当前轮次'));
      const label = r.error ? '读取失败' : isStale(r) ? '过期 · ' + (labels[r.status] || r.status) : (labels[r.status] || r.status);
      const cls = r.error || r.status === 'blocked' ? ' block' : isStale(r) || ['needs_decision','consulting'].includes(r.status) ? ' wait' : r.status === 'completed' ? ' done' : '';
      status.append(el('span','pill' + cls,label));
      updated.textContent = r.updated_at ? new Date(r.updated_at).toLocaleString() : '未知';
      for (const [href, label] of [[r.observer,'观察页面'],[r.report,'最终报告']]) if (href) { const a = el('a',null,label); a.href = href; links.append(a); }
      row.append(name,repo,status,updated,links); list.append(row);
    }
    $('#count').textContent = `显示 ${rows.length} 条 · 观察页面和报告由各运行的事件记录生成`;
  }
  window.pipelineIndexReceive = value => { if (!value || !Array.isArray(value.runs)) return; data = value; failed = false; render(); };
  function refresh() { const old = document.getElementById('index-data'); if (old) old.remove(); const script = document.createElement('script'); script.id = 'index-data'; script.src = './pipeline-index-data.js?t=' + Date.now(); script.onerror = () => { failed = true; if (data) render(); else $('#notice').textContent = '无法读取本地索引数据。请运行 index 命令重新生成。'; }; document.body.append(script); }
  document.querySelectorAll('.tab').forEach(b => b.addEventListener('click', () => { tab = b.dataset.tab; render(); }));
  $('#search').addEventListener('input', render);
  $('#theme').addEventListener('click', () => { document.body.classList.toggle('dark'); $('#theme').textContent = document.body.classList.contains('dark') ? '☀ 浅色' : '◐ 深色'; });
  refresh(); setInterval(refresh, 5000);
})();
