// NeuroLM's frozen features on EEGMAT (release neurolm-eegmat-update-20261020, owner decision D1 of 2026-10-19): the
// separate panel #neurolm-eegmat on /topics/pilot-studies/ and the pointer on /protocols/arithmetic-rest/, checked in a
// built site.
//
//   node scripts/checks/neurolm-eegmat.mjs <build dir>        (or import { checkNeurolmEegmat } and pass the dir)
//
// What it holds, in both languages:
//  1. every figure in the panel is a leaf of neurolm-eegmat-update.json under that file's name, printed in its format,
//     and no figure of that file appears anywhere else on the page: the tokenizer arm's 64.49% equals ST-EEGFormer
//     Base's own EEGMAT score by coincidence, so a figure is held to its field and its file;
//  2. English and Chinese print the same figures, and the same typed numbers outside them;
//  3. each figure in its own place: the three arms with their dimensions, balanced accuracy and macro-F1; the three
//     paired differences with their bounds in the chart and the table; the finding with the reused interval sentence;
//     the caveat paragraph with exposure "unknown" and the adapter beside the result;
//  4. the pilot count, short answer, description, dek and card unchanged in substance: none names NeuroLM or prints one
//     of the panel's results, and the answer still counts the pilots the pilot-studies export releases;
//  5. the cite block names the two releases the page prints; the data source names the file;
//  6. every table has a header row, a table inside <details> has four or more columns; no inline script, style
//     attribute or handler; no private path, no ICLR 2027 or OpenReview reference, no version label or update word,
//     no ranking word outside a denial, no Jev; no number typed outside a figure except the export's own sentences;
//  7. the licences per part, the consent statement and the checkpoint's identity in the credits;
//  8. the Markdown copy carries the panel's figures in order;
//  9. the pointer: on the Arithmetic & rest protocol page in both languages, once, with no figure and no digit, linking
//     the panel; on no other protocol page.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { strict as assert } from 'node:assert';
import { fileURLToPath, pathToFileURL } from 'node:url';

const FILE = 'neurolm-eegmat-update.json';
const ANCHOR = 'neurolm-eegmat';
const H2 = { en: 'A separate panel: NeuroLM’s frozen features on arithmetic and rest', zh: '单独一栏：NeuroLM 冻结特征，心算与静息' };
const SPANS_ZERO = { en: 'the interval spans zero, so neither is shown to be better, and the two are not shown to be equivalent', zh: '区间跨过零，既不能说明哪一方更好，也不能说明两者等效' };
const POINTER = { en: 'A frozen NeuroLM pilot with its own preprocessing is on the pilot studies page →', zh: '另有一项冻结 NeuroLM 的试点，使用自己的预处理流程，见试点研究页面 →' };
const LISTED_LIMITS = ['band-power', 'capacity', 'random-initialisation', 'development-cohort', 'ica', 'scope'];

const fmt = {
  pct2: r => (r * 100).toFixed(2) + '%',
  pp2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2) + ' pp',
  sgn2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2),
  count: r => r.toLocaleString('en-US'),
};
const decode = s => s.replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d))).replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const vis = h => decode(h.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
const figAttrs = h => [...h.matchAll(/data-fig="([^"]+)"/g)].map(m => m[1]);
const attr = (f, x) => `data-fig="${FILE}|${f}|${x}"`;
// The element that opens at `at`, through its matching close tag.
const spanEnd = (h, at) => {
  const tag = h.slice(at + 1).match(/^\w+/)[0], re = new RegExp(`<${tag}\\b|</${tag}>`, 'g');
  re.lastIndex = at; let d = 0, m;
  while ((m = re.exec(h))) { d += m[0].startsWith('</') ? -1 : 1; if (!d) return m.index + m[0].length; }
  return h.length;
};
const el = (h, sel, where) => { const a = h.search(sel); assert.ok(a >= 0, `${where}: ${sel} renders`); return h.slice(a, spanEnd(h, a)); };
const hasFig = (h, f, x) => new RegExp(`${attr(f, x).replace(/[.+|-]/g, '\\$&')}[^>]*>${fmt[f](x).replace(/[.+]/g, '\\$&')}<`).test(h);
// Elements in English inside a page (attributions, originals beside the Chinese, titles), removed before counting typed numbers.
const dropEnglish = h => { let out = h, m; const re = /<(\w+)\b[^>]*\slang="en"[^>]*>/g;
  while ((m = re.exec(out))) { const end = spanEnd(out, m.index); out = out.slice(0, m.index) + ' ' + out.slice(end); re.lastIndex = m.index; }
  return out; };

export function checkNeurolmEegmat(distDir) {
  const DIST = resolve(distDir);
  const read = rel => readFileSync(join(DIST, rel), 'utf8');
  const X = JSON.parse(read(`data/${FILE}`));
  const src = readFileSync(fileURLToPath(new URL(`../../src/data/${FILE}`, import.meta.url)), 'utf8');
  assert.equal(read(`data/${FILE}`), src, `${FILE}: the served copy is byte-identical to src/data`);
  const PS = JSON.parse(read('data/pilot-studies-update.json'));
  const leaves = new Set(); const walk = v => { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); }; walk(X);
  const ARM = Object.fromEntries(X.arms.map(a => [a.id, a])), CON = Object.fromEntries(X.paired_contrasts.map(c => [c.id, c]));
  const results = new Set([...X.arms.flatMap(a => [a.balanced_accuracy, a.macro_f1]),
    ...X.paired_contrasts.flatMap(c => [c.balanced_accuracy, c.macro_f1]).flatMap(d => [d.difference, ...d.interval_95])].map(v => Math.abs(v * 100).toFixed(2)));
  const carries = t => /NeuroLM|EEGMAT/i.test(t) || [...t.matchAll(/\d+(?:\.\d+)?/g)].some(m => results.has(m[0]));
  assert.equal(X.placement.counted_in_pilots, false, 'the panel is outside the pilot count');
  assert.equal(X.pretraining_exposure.status, 'unknown', 'exposure unknown');
  const nPilots = PS.pilots.filter(p => p.publication === 'released').length;
  let pinned = 0;
  const sections = {};
  const verbatim = [...X.arms.map(a => a.definition), ...X.limitations.map(l => l.text), ...X.not_published.slice(0, 3), X.audits.boundary, X.rights.summary,
    X.rights.dataset.attribution, X.rights.dataset.rightsScope, X.model.paper_title, 'Paper reports Bioethics Commission approval (15 August 2018) and written consent from every participant.',
    X.rights.dataset.license, X.model.repository.replace('https://github.com/', ''), 'CC BY 4.0', 'SHA-256'];

  for (const [lang, pfx] of [['en', ''], ['zh', 'zh/']]) {
    const zh = lang === 'zh', path = `${pfx}topics/pilot-studies/`, where = path, html = read(`${path}index.html`);
    const main = html.slice(html.indexOf('<main'), html.indexOf('<section class="cite-page"'));
    const own = main.slice(0, main.indexOf('<nav class="topic-switcher"'));
    const s = el(own, new RegExp(`<section\\b[^>]*\\sid="${ANCHOR}"`), where);
    sections[lang] = s;
    // Placement: after the pilots' methods and limits, before the related questions; marked uncounted.
    const at = own.indexOf(s);
    assert.ok(own.indexOf('id="methods-and-limits"') < at && at < own.indexOf('id="related"'), `${where}: the panel follows the pilots' methods and limits`);
    assert.match(s.slice(0, s.indexOf('>')), /data-counted="false"/, `${where}: the panel is marked outside the pilot count`);
    assert.equal(vis(el(s, /<h2\b/, where)), H2[lang], `${where}: the panel's heading`);
    // (1) Every figure in the panel is a leaf of the file it names, printed in its format; none outside it.
    const figs = [...s.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)];
    assert.ok(figs.length > 60, `${where}: the panel's figures (${figs.length})`);
    for (const [, file, f, raw, text] of figs) {
      assert.equal(file, FILE, `${where}: a panel figure from ${file}`);
      assert.ok(leaves.has(Number(raw)), `${where}: ${raw} is not a value in ${FILE}`);
      assert.ok(fmt[f], `${where}: format ${f}`);
      assert.equal(decode(text), fmt[f](Number(raw)), `${where}: ${raw} printed as "${text}"`);
    }
    const outside = html.replace(s, ' ');
    assert.ok(!outside.includes(`data-fig="${FILE}|`), `${where}: no NeuroLM figure outside its panel`);
    // (4) The count, the short answer, the description, the dek and the card carry nothing of the panel.
    const ans = vis(el(own, /<section class="short-answer"/, where));
    assert.ok(!carries(ans), `${where}: the short answer names NeuroLM or prints one of its results`);
    const words = zh ? ['', '', '两', '三', '四'] : ['', '', 'two', 'three', 'four'], counts = zh ? ['', '', '', '三', '四', '五'] : ['', '', '', 'Three', 'Four', 'Five'];
    assert.ok(ans.includes(zh ? `${words[nPilots]}项试点、${counts[nPilots + 1]}项结果` : `${counts[nPilots + 1]} findings from ${words[nPilots]} pilots`), `${where}: the short answer counts the export's ${nPilots} pilots`);
    const desc = decode(html.match(/<meta name="description" content="([^"]*)"/)[1]);
    assert.ok(!carries(desc), `${where}: the description`);
    assert.ok(!carries(vis(el(main, /<p class="topic-dek"/, where))), `${where}: the dek`);
    // (5) The cite block names the page's two releases; the panel names its file.
    const cite = html.slice(html.indexOf('<section class="cite-page"'));
    assert.deepEqual(cite.match(/data-releases="([^"]+)"/)[1].split(' ').sort(), [PS.release_id, X.release_id].sort(), `${where}: the cite block names the pilot studies' release and the panel's`);
    assert.ok(s.includes(`href="/data/${FILE}"`) && vis(el(s, /<p class="citation-note" data-neurolm-note="data-source"/, where)).includes(X.schema_version), `${where}: the data source names the file and its schema`);
    // (3) The arms table.
    const at1 = el(s, /<table data-neurolm-table="arms"/, where);
    assert.deepEqual([...at1.matchAll(/<tr data-neurolm-row="([^"]+)"/g)].map(m => m[1]), X.arms.map(a => a.id), `${where}: the three representations, in the export's order`);
    for (const a of X.arms) {
      const row = el(at1, new RegExp(`<tr data-neurolm-row="${a.id}"`), where);
      assert.ok(hasFig(row, 'count', a.dimension) && hasFig(el(row, /<td data-cell="ba"/, where), 'pct2', a.balanced_accuracy) && hasFig(el(row, /<td data-cell="f1"/, where), 'pct2', a.macro_f1)
        && figAttrs(row).length === 3, `${where}: ${a.id}, its dimension, balanced accuracy and macro-F1, and no interval`); pinned += 3;
    }
    assert.ok(vis(el(at1, /<th scope="row"/, where)).toLowerCase() === (zh ? '分词器特征' : 'tokenizer features'), `${where}: the arm is "tokenizer features"`);
    // The paired chart: three rows, each difference with its interval drawn, zero dashed, no curve.
    const plot = el(s, /<figure class="interval-plot" id="neurolm-eegmat-paired"/, where);
    const rows = [...plot.matchAll(/<div class="ip-row">([\s\S]*?<div class="ip-value">[\s\S]*?<\/div>)/g)].map(m => m[1]);
    assert.equal(rows.length, 3, `${where}: the chart draws the three paired differences`);
    X.paired_contrasts.forEach((c, i) => {
      const d = c.balanced_accuracy;
      assert.ok(hasFig(rows[i], 'pp2', d.difference) && hasFig(rows[i], 'sgn2', d.interval_95[0]) && hasFig(rows[i], 'pp2', d.interval_95[1]) && rows[i].includes('class="ip-ci"'), `${where}: chart row ${c.id}`); pinned += 3;
    });
    assert.equal((plot.match(/class="ip-ref" x1="50\.00"/g) || []).length, 3, `${where}: zero dashed on every row`);
    assert.ok(!/<path|<polyline|<polygon/.test(plot), `${where}: no curve`);
    // The paired table: both metrics, each with its bounds.
    const pt = el(s, /<table data-neurolm-table="paired"/, where);
    assert.deepEqual([...pt.matchAll(/<tr data-neurolm-row="([^"]+)"/g)].map(m => m[1]), X.paired_contrasts.map(c => c.id), `${where}: the three paired differences, in the export's order`);
    for (const c of X.paired_contrasts) {
      const row = el(pt, new RegExp(`<tr data-neurolm-row="${c.id}"`), where);
      for (const [cell, m] of [['ba', 'balanced_accuracy'], ['f1', 'macro_f1']]) {
        const td = el(row, new RegExp(`<td data-cell="${cell}"`), where), d = c[m];
        assert.ok(hasFig(td, 'pp2', d.difference) && hasFig(td, 'sgn2', d.interval_95[0]) && hasFig(td, 'pp2', d.interval_95[1]), `${where}: ${c.id} ${m}`); pinned += 3;
        assert.ok(vis(td).includes(d.interval_includes_zero ? (zh ? '跨过零' : 'spans zero') : (zh ? '整个低于零' : 'below zero')), `${where}: ${c.id} ${m} says where its interval lies`);
      }
      assert.ok(vis(el(row, /<td data-cell="role"/, where)) === (c.role === 'question' ? (zh ? '这一栏要回答的问题' : 'the panel’s question') : (zh ? '描述性' : 'descriptive')), `${where}: ${c.id}'s role`);
    }
    // The finding: the question's difference, its bounds and the reused interval sentence beside it.
    const tb = CON['tokenizer-minus-band-power'].balanced_accuracy, gt = CON['gpt-minus-tokenizer'].balanced_accuracy;
    const fd = el(s, /<div class="finding" data-finding="neurolm-eegmat"/, where), fp = el(fd, /<div class="finding-copy"/, where);
    assert.ok(hasFig(el(fd, /<div class="finding-number"/, where), 'pp2', tb.difference), `${where}: the finding's number`);
    assert.ok(['tokenizer_mean', 'log_bandpower', 'gpt_mean'].every(k => hasFig(fp, 'pct2', ARM[k].balanced_accuracy) && hasFig(fp, 'pct2', ARM[k].macro_f1))
      && [tb.difference, ...tb.interval_95, gt.difference, ...gt.interval_95].every(v => hasFig(fp, 'sgn2', v)), `${where}: the finding's levels and the two differences with their bounds`); pinned += 12;
    const fpt = vis(fp);
    assert.ok(fpt.includes(`${SPANS_ZERO[lang]}`), `${where}: the reused interval sentence`);
    assert.ok(fpt.includes(zh ? '这是描述性结果，只来自这一个队列' : 'descriptive, from this one cohort'), `${where}: GPT minus tokenizer is descriptive`);
    // The caveat paragraph, beside the result: exposure unknown, the adapter, recording order, the intervals.
    const cv = el(s, /<p class="protocol-note" data-neurolm-note="caveats"/, where), cvt = vis(cv), A = X.adapter;
    assert.ok(cvt.includes(zh ? '是否出现在预训练数据中，未知' : 'pretraining exposure is unknown') && cvt.includes(zh ? '静息在心算之前记录' : 'Rest is recorded before arithmetic')
      && cvt.includes(zh ? '所以这些分数单独成栏' : 'so these scores have their own panel') && cvt.includes(zh ? '不做陷波滤波' : 'with no notch filter'), `${where}: the caveats beside the result`);
    assert.ok([A.band_pass_hz[0], A.band_pass_hz[1], A.sampling_hz, ...A.official_notch_hz, X.separate_from_core.core_sampling_hz, X.interval.resamples, X.probe.fits,
      X.pretraining_exposure.published_pretraining_list.datasets].every(v => hasFig(cv, 'count', v)) && cv.includes(`href="/${pfx}protocols/arithmetic-rest/"`), `${where}: the adapter and interval figures, and the core matrix linked`); pinned += 9;
    // The listed limitations: the export's sentences, the English beside the Chinese.
    const lim = el(s, /<ul class="rd-rules" data-neurolm-note="limits"/, where);
    assert.deepEqual([...lim.matchAll(/<li data-neurolm-limit="([^"]+)"/g)].map(m => m[1]), LISTED_LIMITS, `${where}: the listed limitations`);
    for (const id of LISTED_LIMITS) {
      const t = X.limitations.find(l => l.id === id).text, li = el(lim, new RegExp(`<li data-neurolm-limit="${id}"`), where);
      if (zh) assert.ok(decode(li).includes(`<span class="note-original" lang="en">${t}</span>`), `${where}: ${id}, with the English beside the Chinese`);
      else assert.equal(vis(li), t, `${where}: ${id} as the export words it`);
    }
    // (7) Credits: the licence of each part, consent, the checkpoint's identity; the paper through arXiv.
    const cr = el(s, /<div class="citation-list" id="neurolm-credits"/, where), M = X.model, R = X.rights;
    assert.ok(cr.includes(`href="${R.code.url}"`) && vis(cr).includes('MIT') && vis(cr).includes('CC BY 4.0') && cr.includes(`href="${R.dataset.licenseUrl}"`) && vis(cr).includes(R.dataset.license)
      && cr.includes(`href="${M.paper_arxiv}"`) && cr.includes(M.checkpoint.sha256) && cr.includes(M.checkpoint.revision) && cr.includes(M.source_revision)
      && cr.includes(`href="/${pfx}datasets/eegmat/"`), `${where}: the credits, licences per part and the checkpoint's identity`);
    assert.ok(decode(cr).includes(R.dataset.attribution) && decode(cr).includes('Paper reports Bioethics Commission approval (15 August 2018) and written consent from every participant.'), `${where}: EEGMAT's attribution and its consent statement`);
    assert.ok(vis(s).includes(zh ? '不分发任何权重' : 'No weights are distributed') || vis(s).includes('no weights distributed'), `${where}: no weights distributed`);
    // (6) Structure and words.
    for (const t of s.match(/<table\b[\s\S]*?<\/table>/g)) assert.ok(/<thead>/.test(t), `${where}: every table has a header row`);
    for (const d of s.match(/<details\b[\s\S]*?<\/details>/g) || []) for (const t of d.match(/<table\b[\s\S]*?<\/table>/g) || [])
      assert.ok((el(t, /<thead>/, where).match(/<th\b/g) || []).length >= 4, `${where}: a table inside <details> has four or more columns`);
    assert.doesNotMatch(s, /<script\b|\sstyle="|\son[a-z]+=/i, `${where}: no inline script, style attribute or handler`);
    const text = vis(s), textNoCode = vis(s.replace(/<code>[\s\S]*?<\/code>/g, ' ')).replace(/https?:\/\/\S+/g, ' ');
    assert.doesNotMatch(s, /\/Users\/|\/home\/|\/Volumes\/|\/mnt\/|trx50|\btrx\b|Gal4|BCI_Arena|\btwu\b/i, `${where}: no private path or host`);
    assert.doesNotMatch(s, /ICLR 2027|openreview|submission/i, `${where}: no conference-submission reference`);
    assert.doesNotMatch(s, /\bJev\b/, `${where}: no Jev`);
    assert.doesNotMatch(textNoCode, zh ? /新增|本次更新|这次更新|最新|新发布|更新于|(?<![\w.\/#-])v\d+\b/ : /\b(?:new|newly|added|updated|this update|this release adds)\b|(?<![\w.\/#-])v\d+\b/i, `${where}: no update wording or version label`);
    const sentences = vis(s.replace(/<\/(?:h[1-6]|p|li|th|td|caption|figcaption|small|div)>/g, ' ¶ ')).split(/¶|(?<=[.;:?])\s+|(?<=[。；：？])/).map(t => t.trim()).filter(Boolean);
    const ranking = zh ? /排行榜|排名|最先进|在线|实时|临床|零样本|合并|总分|最好|最佳|优于|等效|胜过/ : /leaderboard|\brank(?:ing|ed|s)?\b|state[- ]of[- ]the[- ]art|\bSOTA\b|\bonline\b|real[- ]time|clinical|zero[- ]shot|\bpool(?:s|ed|ing)?\b|\bbest\b|outperform|superior|equivalen|\bbeats?\b/i;
    const denial = zh ? /不|没|无|未|非/ : /\b(?:not|no|never|nor|none|nothing|neither|without)\b/i;
    for (const t of sentences) if (ranking.test(t)) assert.match(t, denial, `${where}: "${t.slice(0, 140)}" reads as a claim it may only deny`);
    // No typed number: outside the figures, the digits are the export's own sentences, licence names and identifiers.
    let rest = vis(s.replace(/<span data-fig="[^"]*"[^>]*>[^<]*<\/span>/g, ' ').replace(/<div class="ip-row ip-axis"[\s\S]*?<\/div>\s*<div class="ip-value"><\/div>\s*<\/div>/g, ' ')
      .replace(/<code>[\s\S]*?<\/code>/g, ' ').replace(/\s(?:id|href|data-[\w-]+|aria-label)="[^"]*"/g, ''));
    if (!zh) {
      for (const v of verbatim) rest = rest.split(v).join(' ');
      const typed = [...rest.replace(/[A-Za-z]+\d+/g, ' ').matchAll(/\d[\d,]*(?:\.\d+)?%?/g)].map(m => m[0].replace(/,$/, '')).filter(t => t !== '95%');
      assert.deepEqual(typed, [], `${where}: a number typed outside the export`);
    }
    // (8) The Markdown copy: the heading and every panel figure, in order.
    const md = read(`${path}index.md`);
    assert.ok(md.includes(H2[lang]), `${where}index.md: the panel's heading`);
    let k = md.indexOf(H2[lang]);
    for (const [, , , , t] of figs) { const j = md.indexOf(decode(t), k); assert.ok(j >= 0, `${where}index.md: the figure "${t}" after offset ${k}`); k = j + decode(t).length; }
    // The card on the home page and the Questions hub.
    for (const page of [pfx, `${pfx}topics/`]) {
      const h = read(`${page}index.html`), a = h.search(new RegExp(`<a class="topic-entry-card" href="${pfx ? '/zh' : ''}/topics/pilot-studies/"`));
      assert.ok(a >= 0, `${page || '/'}: the pilot-studies card`);
      assert.ok(!carries(vis(h.slice(a, h.indexOf('</a>', a)))), `${page || '/'}: the pilot-studies card names nothing of the panel`);
    }
  }
  // (2) The same figures in both languages, and the same typed numbers outside them.
  const ms = h => figAttrs(h).sort();
  assert.deepEqual(ms(sections.zh), ms(sections.en), 'pilot-studies #neurolm-eegmat: the Chinese panel prints exactly the English panel’s figures');
  const typedAll = h => [...vis(dropEnglish(h).replace(/<span data-fig="[^"]*"[^>]*>[^<]*<\/span>/g, ' ').replace(/<code>[\s\S]*?<\/code>/g, ' ')
    .replace(/<div class="ip-row ip-axis"[\s\S]*?<\/div>\s*<div class="ip-value"><\/div>\s*<\/div>/g, ' ').replace(/\s(?:id|href|data-[\w-]+|aria-label)="[^"]*"/g, ''))
    .replace(/(\d+) 年 (\d+) 月 (\d+) 日/g, '$3 $1').replace(/SHA-256/g, ' ').replace(/[A-Za-z]+\d+/g, ' ').matchAll(/\d+(?:[.,]\d+)*/g)].map(m => m[0]).sort();
  assert.deepEqual(typedAll(sections.zh), typedAll(sections.en), 'pilot-studies #neurolm-eegmat: the Chinese panel types the same numbers as the English outside its figures');

  // (9) The pointer: the Arithmetic & rest protocol page alone, in words, linking the panel.
  let pointers = 0;
  for (const [lang, pfx] of [['en', ''], ['zh', 'zh/']]) {
    const dir = join(DIST, `${pfx}protocols`);
    for (const id of readdirSync(dir).filter(d => existsSync(join(dir, d, 'index.html')))) {
      const where = `${pfx}protocols/${id}/`, h = read(`${where}index.html`);
      const n = (h.match(/data-neurolm-pointer="true"/g) || []).length, links = (h.match(/href="(?:\/zh)?\/topics\/pilot-studies\/#neurolm-eegmat"/g) || []).length;
      if (id !== 'arithmetic-rest') { assert.equal(n + links, 0, `${where}: no pointer to the NeuroLM panel`); continue; }
      assert.equal(n, 1, `${where}: one pointer`); assert.equal(links, 1, `${where}: one link to the panel`);
      const p = el(h, /<p class="citation-note" data-neurolm-pointer="true"/, where);
      assert.ok(p.includes(`href="/${pfx}topics/pilot-studies/#${ANCHOR}"`) && vis(p) === POINTER[lang], `${where}: the pointer's words and link`);
      assert.ok(!p.includes('data-fig') && !/\d/.test(vis(p)), `${where}: the pointer carries no figure`);
      assert.ok(!h.includes(`data-fig="${FILE}|`), `${where}: no NeuroLM figure on the protocol page`);
      assert.ok(read(`${where}index.md`).includes(POINTER[lang]), `${where}index.md: the pointer`);
      pointers++;
    }
  }
  assert.equal(pointers, 2, 'the pointer on the Arithmetic & rest page in both languages');
  return { pinned, figures: figAttrs(sections.en).length };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/neurolm-eegmat.mjs <build dir>'); process.exit(2); }
  const { pinned, figures } = checkNeurolmEegmat(dir);
  console.log(`PASS: NeuroLM on EEGMAT — the separate panel #neurolm-eegmat on /topics/pilot-studies/ in both languages: ${figures} figures, every one a leaf of ${FILE} and none outside the panel, ${pinned} pinned to their cells; the same figures and typed numbers in English and Chinese; the three arms with no per-arm interval, the three paired differences with their bounds, the reused interval sentence, exposure unknown and the adapter beside the result; the pilot count, short answer, description, dek and card carrying nothing of the panel; the cite block naming both releases; licences per part, consent and the checkpoint's identity; the Markdown copy in order; the pointer on /protocols/arithmetic-rest/ alone, in words.`);
}
