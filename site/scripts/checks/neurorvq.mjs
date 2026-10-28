// NeuroRVQ's frozen backbone on three tasks (release neurorvq-update-20261028, owner decisions D14 and D19 of 2026-10-28):
// the separate panel #neurorvq on /topics/pilot-studies/ and the pointers on three protocol pages, checked in a built site.
//
//   node scripts/checks/neurorvq.mjs <build dir>        (or import { checkNeurorvq } and pass the dir)
//
// What it holds, in both languages:
//  1. every figure in the panel is a leaf of neurorvq-update.json under that file's name, printed in its format, and no
//     figure of that file appears anywhere else in the built site;
//  2. English and Chinese print the same figures, and the same typed numbers outside them;
//  3. each figure by field: each block's arms in the export's order with their dimension, balanced accuracy and
//     macro-F1, each paired difference with its bounds in the chart and in its finding, beside its reading sentence;
//  4. collision guards, by field and file: every level, difference and bound prints at two decimals; the panel prints
//     none of its levels at one decimal or as a whole percent (66.34 and 64.82 would read as REVE LoRA's 66.3% and
//     BrainOmni LoRA's 64.8%, the motor-imagery band power's 58.83 as BrainOmni's and CodeBrain's 58.8% on that
//     protocol), and those coincident figures elsewhere cite their own files;
//  5. after #neurolm-eegmat and before #related, marked data-counted="false"; the pilot count, short answer,
//     description, dek and card carry nothing of the panel;
//  6. the caveats from the export's caveat_keys: every limitation id prints exactly once in the panel; the leaderboard
//     statement once on the page, from `separation`; EEGMAT's shared facts once on the page, the NeuroLM panel's (rest
//     recorded before arithmetic, a known development cohort, the dataset's credit and consent), with the EEGMAT block's
//     one line pointing to them (ids eegmat-order and development-cohort) and its EEGMAT credit pointing to the NeuroLM
//     credits with the licence linked;
//  7. the model's identity: the variant, the strict restore of the trained tensors, the authors' wrapper and its missing
//     normalisation tensors, CC BY-NC 4.0 for code and weights, exposure unknown, no weights distributed;
//  8. the cite block names the pilot studies' release and each separate panel's, computed from the page;
//  9. every table has a header row, a table inside <details> has four or more columns; no inline script, style
//     attribute or handler; no private path or host, nothing blocks_cca.REFUSED_TEXT refuses; no ICLR 2027 or OpenReview
//     reference; no version label or update word; no ranking word outside a denial; no Jev; no number typed outside a
//     figure except the export's own sentences, names and licence identifiers;
// 10. the Markdown copy carries the panel's figures in order;
// 11. the pointers: on the three protocol pages the export names, in both languages, once each, with no figure and no
//     digit, linking the panel (Arithmetic & rest in one line with the ten-second panel); on no other protocol page.
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { resolve, join, relative } from 'node:path';
import { strict as assert } from 'node:assert';
import { fileURLToPath, pathToFileURL } from 'node:url';

const FILE = 'neurorvq-update.json';
const ANCHOR = 'neurorvq';
const H2 = { en: 'A separate panel: NeuroRVQ’s frozen backbone on three tasks', zh: '单独一栏：NeuroRVQ 冻结主干，三项任务' };
const SPANS_ZERO = { en: 'the interval spans zero, so neither is shown to be better, and the two are not shown to be equivalent', zh: '区间跨过零，既不能说明哪一方更好，也不能说明两者等效' };
const BELOW_ZERO = { en: 'the interval lies below zero; descriptive, from this one cohort', zh: '区间整个低于零；这是描述性结果，只来自这一个队列' };
const POINTER = { en: 'A frozen NeuroRVQ probe with its own input chain is on the pilot studies page →', zh: '另有一项冻结 NeuroRVQ 的探针，使用自己的输入流程，见试点研究页面 →' };
const POINTER_BOTH = {
  en: 'Frozen-encoder probes with their own preprocessing are on the pilot studies page: NeuroRVQ on three tasks → · EEG-Captioner and AXON on ten-second windows →',
  zh: '另有使用自己预处理流程的冻结编码器探针，见试点研究页面：NeuroRVQ，三项任务 → · EEG-Captioner 与 AXON，十秒时间窗 →',
};
const LEADERBOARD = { en: 'so these scores stay outside every leaderboard', zh: '所以这些分数不进入任何排行榜' };
const DEVELOPMENT = { en: 'known development cohort', zh: '已知开发队列' };
const SHARED = ['eegmat-order', 'development-cohort'];
const SHARED_REF = {
  en: 'EEGMAT’s recording order (rest before arithmetic), the source’s prior ICA cleaning and EEGMAT’s use as a development cohort are stated in the NeuroLM panel above ↑ and bound this block too: it is not an untouched external confirmation.',
  zh: 'EEGMAT 的记录顺序（静息在心算之前）、数据源事先做过的 ICA 清理，以及 EEGMAT 在本站作为开发队列的用途，见上面 NeuroLM 一栏 ↑，同样限定这一块：它不是未经使用的外部确认。',
};
const EEGMAT_CREDIT_REF = { en: 'Credit, ethics and consent: in the NeuroLM panel’s credits above ↑', zh: '署名、伦理与知情同意：见上面 NeuroLM 一栏的署名 ↑' };
const RECORDING_ORDER = { en: /rest is recorded before arithmetic/gi, zh: /静息在心算之前记录/g };
const MODEL_LIMITS = ['variant', 'transfer', 'exposure'], CREDIT_LIMITS = ['rights'];

const fmt = {
  pct2: r => (r * 100).toFixed(2) + '%',
  pp2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2) + ' pp',
  sgn2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2),
  count: r => r.toLocaleString('en-US'),
};
const decode = s => s.replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d))).replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const vis = h => decode(h.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
/** The text as it reads, tags removed without a gap (a figure followed by a comma stays "432,"). */
const txt = h => decode(h.replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
const figAttrs = h => [...h.matchAll(/data-fig="([^"]+)"/g)].map(m => m[1]);
const attr = (f, x) => `data-fig="${FILE}|${f}|${x}"`;
const spanEnd = (h, at) => {
  const tag = h.slice(at + 1).match(/^\w+/)[0], re = new RegExp(`<${tag}\\b|</${tag}>`, 'g');
  re.lastIndex = at; let d = 0, m;
  while ((m = re.exec(h))) { d += m[0].startsWith('</') ? -1 : 1; if (!d) return m.index + m[0].length; }
  return h.length;
};
const el = (h, sel, where) => { const a = h.search(sel); assert.ok(a >= 0, `${where}: ${sel} renders`); return h.slice(a, spanEnd(h, a)); };
const all = (h, sel) => { const out = []; const re = new RegExp(sel.source, 'g'); let m; while ((m = re.exec(h))) { out.push(h.slice(m.index, spanEnd(h, m.index))); } return out; };
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const hasFig = (h, f, x) => new RegExp(`${esc(attr(f, x))}[^>]*>${esc(fmt[f](x))}<`).test(h);
const dropEnglish = h => { let out = h, m; const re = /<(\w+)\b[^>]*\slang="en"[^>]*>/g;
  while ((m = re.exec(out))) { const end = spanEnd(out, m.index); out = out.slice(0, m.index) + ' ' + out.slice(end); re.lastIndex = m.index; }
  return out; };
const stripFigs = h => h.replace(/<span data-fig="[^"]*"[^>]*>[^<]*<\/span>/g, ' ').replace(/<div class="ip-row ip-axis"[\s\S]*?<\/div>\s*<div class="ip-value"><\/div>\s*<\/div>/g, ' ')
  .replace(/<code>[\s\S]*?<\/code>/g, ' ').replace(/\s(?:id|href|data-[\w-]+|aria-label)="[^"]*"/g, '');
/** blocks_cca.REFUSED_TEXT, read from its source so no literal of what it refuses is repeated here. */
const refusedText = () => {
  const py = readFileSync(fileURLToPath(new URL('../../../pipeline/publication/ssvep_followups/blocks_cca.py', import.meta.url)), 'utf8');
  const body = py.slice(py.indexOf('REFUSED_TEXT = re.compile('), py.indexOf('re.IGNORECASE)', py.indexOf('REFUSED_TEXT = re.compile(')));
  const parts = [...body.matchAll(/r'((?:[^'\\]|\\.)*)'/g)].map(m => m[1]);
  assert.ok(parts.length >= 2, 'blocks_cca.REFUSED_TEXT read');
  return new RegExp(parts.join(''), 'i');
};
const htmlFiles = dir => readdirSync(dir).flatMap(f => { const p = join(dir, f); return statSync(p).isDirectory() ? htmlFiles(p) : f.endsWith('.html') ? [p] : []; });

export function checkNeurorvq(distDir) {
  const DIST = resolve(distDir);
  const read = rel => readFileSync(join(DIST, rel), 'utf8');
  const X = JSON.parse(read(`data/${FILE}`));
  const src = readFileSync(fileURLToPath(new URL(`../../src/data/${FILE}`, import.meta.url)), 'utf8');
  assert.equal(read(`data/${FILE}`), src, `${FILE}: the served copy is byte-identical to src/data`);
  const PS = JSON.parse(read('data/pilot-studies-update.json'));
  const MVP = JSON.parse(readFileSync(fileURLToPath(new URL('../../src/data/mvp.json', import.meta.url)), 'utf8'));
  const REFUSED = refusedText();
  const leaves = new Set(); const walk = v => { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); }; walk(X);
  const B = X.blocks, L = Object.fromEntries(X.limitations.map(l => [l.id, l.text]));
  assert.deepEqual(B.map(b => b.id), ['eegmat', 'mi-rest', 'p300-target'], 'three blocks');
  assert.equal(X.placement.counted_in_pilots, false, 'the panel is outside the pilot count');
  assert.equal(X.pretraining_exposure.status, 'unknown', 'exposure unknown');
  // The levels, differences and bounds: two decimals in the panel, never one, never a whole percent.
  const levels = B.flatMap(b => b.arms.flatMap(a => [a.balanced_accuracy, a.macro_f1]));
  const diffs = B.flatMap(b => [b.paired_difference.difference, ...b.paired_difference.interval_95]);
  const results = new Set([...levels, ...diffs].map(v => Math.abs(v * 100).toFixed(2)));
  const carries = t => /NeuroRVQ/i.test(t) || [...t.matchAll(/\d+(?:\.\d+)?/g)].some(m => results.has(m[0]));
  const nPilots = PS.pilots.filter(p => p.publication === 'released').length;
  // Where each limitation prints, from the blocks' caveat keys.
  const keys = b => b.caveat_keys, every = id => B.every(b => keys(b).includes(id));
  const place = id => MODEL_LIMITS.includes(id) ? 'model' : CREDIT_LIMITS.includes(id) ? 'credits' : every(id) ? 'panel' : B.find(b => keys(b).includes(id)).id;
  assert.deepEqual([...new Set(B.flatMap(keys))].sort(), X.limitations.map(l => l.id).sort(), 'every limitation is some block’s caveat');
  assert.ok([...MODEL_LIMITS, ...CREDIT_LIMITS].every(every), 'the model’s identity bounds every block');
  // The export's own sentences, names and identifiers: the only places a number may be typed.
  const consent = s => s.slice(0, s.indexOf('. ') + 1);
  const verbatim = [X.question, ...B.flatMap(b => [b.title, b.dataset, ...b.arms.flatMap(a => [a.label, a.definition]), b.paired_difference.label, b.paired_difference.reading, b.audit.boundary]),
    ...X.limitations.map(l => l.text), ...X.protocols_not_run.map(p => p.gate), ...X.not_published.slice(0, 2),
    ...Object.values(X.rights.datasets).flatMap(d => [d.attribution, d.rightsScope, d.license, consent(d.privacyReview)]),
    ...MVP.tracks.map(t => t.title), `arXiv:${X.model.arxiv_id}`, X.rights.code.licence, X.schema_version, FILE, 'SHA-256']
    .sort((a, b) => b.length - a.length);
  let pinned = 0;
  const sections = {};

  for (const [lang, pfx] of [['en', ''], ['zh', 'zh/']]) {
    const zh = lang === 'zh', path = `${pfx}topics/pilot-studies/`, where = `${path}#${ANCHOR}`, html = read(`${path}index.html`);
    const main = html.slice(html.indexOf('<main'), html.indexOf('<section class="cite-page"'));
    const own = main.slice(0, main.indexOf('<nav class="topic-switcher"'));
    const s = el(own, new RegExp(`<section\\b[^>]*\\sid="${ANCHOR}"`), where);
    sections[lang] = s;
    // (5) Placement, the uncounted mark, and the heading.
    const at = own.indexOf(s);
    assert.ok(own.indexOf('id="neurolm-eegmat"') < at && at < own.indexOf('id="related"'), `${where}: the panel follows NeuroLM's and precedes the related questions`);
    assert.match(s.slice(0, s.indexOf('>')), /data-counted="false"/, `${where}: the panel is marked outside the pilot count`);
    assert.match(s.slice(0, s.indexOf('>')), new RegExp(`data-release="${X.release_id}"`), `${where}: the panel names its release`);
    assert.equal(vis(el(s, /<h2\b/, where)), H2[lang], `${where}: the panel's heading`);
    // (1) Every figure in the panel is a leaf of its file, printed in its format.
    const figs = [...s.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)];
    assert.ok(figs.length > 80, `${where}: the panel's figures (${figs.length})`);
    for (const [, file, f, raw, text] of figs) {
      assert.equal(file, FILE, `${where}: a panel figure from ${file}`);
      assert.ok(leaves.has(Number(raw)), `${where}: ${raw} is not a value in ${FILE}`);
      assert.ok(fmt[f], `${where}: format ${f}`);
      assert.equal(decode(text), fmt[f](Number(raw)), `${where}: ${raw} printed as "${text}"`);
      // (4) A level, difference or bound prints at two decimals.
      if ([...levels, ...diffs].includes(Number(raw)) && f === 'count') assert.fail(`${where}: ${raw} printed as a count`);
    }
    assert.ok(!html.replace(s, ' ').includes(`data-fig="${FILE}|`), `${where}: no NeuroRVQ figure outside its panel`);
    // (5) The count, the short answer, the description, the dek and the card carry nothing of the panel.
    const ans = vis(el(own, /<section class="short-answer"/, where));
    assert.ok(!carries(ans), `${where}: the short answer names NeuroRVQ or prints one of its results`);
    const words = zh ? ['', '', '两', '三', '四'] : ['', '', 'two', 'three', 'four'], counts = zh ? ['', '', '', '三', '四', '五'] : ['', '', '', 'Three', 'Four', 'Five'];
    assert.ok(ans.includes(zh ? `${words[nPilots]}项试点、${counts[nPilots + 1]}项结果` : `${counts[nPilots + 1]} findings from ${words[nPilots]} pilots`), `${where}: the short answer counts the export's ${nPilots} pilots`);
    assert.ok(!carries(decode(html.match(/<meta name="description" content="([^"]*)"/)[1])), `${where}: the description`);
    assert.ok(!carries(vis(el(main, /<p class="topic-dek"/, where))), `${where}: the dek`);
    // (8) The cite block names the pilot studies' release and each separate panel's, as the page prints them.
    const panels = [...own.matchAll(/<section\b[^>]*>/g)].map(m => m[0]).filter(t => /data-counted="false"/.test(t)).map(t => t.match(/data-release="([^"]+)"/)[1]);
    assert.ok(panels.includes(X.release_id), `${where}: the panel is one of the page's separate panels`);
    const cite = html.slice(html.indexOf('<section class="cite-page"'));
    assert.deepEqual(cite.match(/data-releases="([^"]+)"/)[1].split(' ').sort(), [PS.release_id, ...panels].sort(), `${where}: the cite block names the pilot studies' release and each panel's`);
    assert.ok(s.includes(`href="/data/${FILE}"`) && vis(el(s, /<p class="citation-note" data-neurorvq-note="data-source"/, where)).includes(X.schema_version), `${where}: the data source names the file and its schema`);
    // (3) The chart: one row per block, its difference and bounds, zero dashed, no curve.
    const plot = el(s, /<figure class="interval-plot" id="neurorvq-paired"/, where);
    const rows = [...plot.matchAll(/<div class="ip-row">([\s\S]*?<div class="ip-value">[\s\S]*?<\/div>)/g)].map(m => m[1]);
    assert.equal(rows.length, B.length, `${where}: the chart draws one paired difference per task`);
    B.forEach((b, i) => {
      const d = b.paired_difference;
      assert.ok(hasFig(rows[i], 'pp2', d.difference) && hasFig(rows[i], 'sgn2', d.interval_95[0]) && hasFig(rows[i], 'pp2', d.interval_95[1]) && rows[i].includes('class="ip-ci"'), `${where}: chart row ${b.id}`); pinned += 3;
    });
    assert.equal((plot.match(/class="ip-ref" x1="75\.00"/g) || []).length, B.length, `${where}: zero dashed on every row (−30 to +10 pp)`);
    assert.ok(!/<path|<polyline|<polygon/.test(plot), `${where}: no curve`);
    // (3) Each block: its cohort, its arms in their cells, its finding with the reading, its own limitations and audit.
    const blocks = all(s, /<div class="neurorvq-block" data-neurorvq-block="/);
    assert.deepEqual(blocks.map(h => h.match(/data-neurorvq-block="([^"]+)"/)[1]), B.map(b => b.id), `${where}: the three blocks, in the export's order`);
    B.forEach((b, i) => {
      const bh = blocks[i], w = `${where} ${b.id}`, C = b.cohort, d = b.paired_difference;
      const co = el(bh, /<p class="roadmap-p" data-neurorvq-cohort=/, w);
      assert.ok([C.people, C.windows, C.channels, C.folds, b.input_chain.source_sampling_hz, b.input_chain.sampling_hz].every(v => hasFig(co, 'count', v))
        && co.includes(`href="/${pfx}protocols/${b.protocol}/"`), `${w}: the cohort, its chain's rates and the protocol linked`); pinned += 6;
      const t = el(bh, new RegExp(`<table data-neurorvq-table="${b.id}"`), w);
      assert.deepEqual([...t.matchAll(/<tr data-neurorvq-row="([^"]+)"/g)].map(m => m[1]), b.arms.map(a => a.id), `${w}: the arms, in the export's order`);
      for (const a of b.arms) {
        const row = el(t, new RegExp(`<tr data-neurorvq-row="${a.id}"`), w);
        assert.ok(hasFig(el(row, /<td data-cell="dimension"/, w), 'count', a.dimension) && hasFig(el(row, /<td data-cell="ba"/, w), 'pct2', a.balanced_accuracy)
          && hasFig(el(row, /<td data-cell="f1"/, w), 'pct2', a.macro_f1) && figAttrs(row).length === 3, `${w}: ${a.id}, its dimension, balanced accuracy and macro-F1 by field, no interval`); pinned += 3;
      }
      assert.equal(vis(el(t, /<th scope="row"/, w)), zh ? 'NeuroRVQ 主干' : 'NeuroRVQ backbone', `${w}: the arm is "NeuroRVQ backbone"`);
      const fd = el(bh, new RegExp(`<div class="finding" data-finding="neurorvq-${b.id}"`), w), fp = el(fd, /<div class="finding-copy"/, w);
      assert.ok(hasFig(el(fd, /<div class="finding-number"/, w), 'pp2', d.difference) && [d.difference, ...d.interval_95].every(v => hasFig(fp, 'sgn2', v)), `${w}: the finding's difference and bounds`); pinned += 4;
      assert.ok(vis(fp).includes((d.interval_includes_zero ? SPANS_ZERO : BELOW_ZERO)[lang]), `${w}: the reading beside its interval`);
      const lis = [...bh.matchAll(/<li data-neurorvq-limit="([^"]+)"/g)].map(m => m[1]), lim = lis.flatMap(x => x.split(' '));
      assert.deepEqual(lim, X.limitations.map(l => l.id).filter(id => place(id) === b.id), `${w}: the limitations only this block names, beside it`);
      for (const id of lis) {
        const li = el(bh, new RegExp(`<li data-neurorvq-limit="${id}"`), w);
        if (id.includes(' ') || SHARED.includes(id)) { assert.ok(id === SHARED.join(' ') && b.id === 'eegmat' && li.includes(`href="/${pfx}topics/pilot-studies/#neurolm-eegmat"`) && txt(li) === SHARED_REF[lang],
          `${w}: one line pointing to the NeuroLM panel's EEGMAT statements (recording order, ICA cleaning, development cohort)`); continue; }
        if (zh) assert.ok(decode(li).includes(`<span class="note-original" lang="en">${L[id]}</span>`), `${w}: ${id}, the English beside the Chinese`);
        else assert.equal(vis(li), L[id], `${w}: ${id} as the export words it`);
      }
      const au = el(bh, /<p class="citation-note" data-neurorvq-audit=/, w);
      assert.ok(zh ? decode(au).includes(b.audit.boundary) : vis(au) === b.audit.boundary, `${w}: the audit boundary`);
    });
    // (6) Every limitation exactly once in the panel; the panel's own in its list, the model's in its list, the rights in the credit.
    const ids = [...s.matchAll(/data-neurorvq-limit="([^"]+)"/g)].flatMap(m => m[1].split(' '));
    assert.deepEqual([...ids].sort(), X.limitations.map(l => l.id).sort(), `${where}: every limitation prints exactly once`);
    for (const [sel, placeId] of [[/<ul class="rd-rules" data-neurorvq-note="limits"/, 'panel'], [/<ul class="rd-rules" data-neurorvq-note="model"/, 'model'], [/<div class="citation-list" id="neurorvq-credits"/, 'credits']])
      assert.deepEqual([...el(s, sel, where).matchAll(/data-neurorvq-limit="([^"]+)"/g)].map(m => m[1]), X.limitations.map(l => l.id).filter(id => place(id) === placeId), `${where}: the ${placeId} limitations`);
    const pageText = vis(own);
    assert.equal(pageText.split(LEADERBOARD[lang]).length - 1, 1, `${where}: the leaderboard statement once on the page`);
    assert.ok(vis(el(s, /<ul class="rd-rules" data-neurorvq-note="limits"/, where)).includes(LEADERBOARD[lang]), `${where}: …from the separation limitation`);
    if (!zh) assert.equal(pageText.split('outside every leaderboard').length - 1, 1, `${where}: "outside every leaderboard" once on the page`);
    assert.equal(pageText.split(DEVELOPMENT[lang]).length - 1, 1, `${where}: EEGMAT's development-cohort statement once on the page`);
    assert.ok(vis(el(own, /<section\b[^>]*\sid="neurolm-eegmat"/, where)).includes(DEVELOPMENT[lang]), `${where}: …in the NeuroLM panel`);
    // EEGMAT's recording order, its credit and its consent: once on the page, in the NeuroLM panel.
    const nl = el(own, /<section\b[^>]*\sid="neurolm-eegmat"/, where), eeg = X.rights.datasets.eegmat;
    assert.equal((pageText.match(RECORDING_ORDER[lang]) || []).length, 1, `${where}: "rest is recorded before arithmetic" once on the page`);
    assert.ok(RECORDING_ORDER[lang].test(vis(nl)), `${where}: …in the NeuroLM panel`); RECORDING_ORDER[lang].lastIndex = 0;
    for (const t of [eeg.attribution, consent(eeg.privacyReview)]) assert.ok(decode(own).split(t).length - 1 === 1 && decode(nl).includes(t), `${where}: EEGMAT's "${t.slice(0, 40)}…" once on the page, in the NeuroLM credits`);
    // (7) The model's identity, the head, the protocols not run and the credits.
    const mo = el(s, /<ul class="rd-rules" data-neurorvq-note="model"/, where), M = X.model, R = X.rights;
    assert.ok(decode(mo).includes(L.variant) && L.variant.includes(`${M.restore.trained_tensors} trained tensors restore strictly`) && /eight normalisation tensors/.test(L.variant)
      && M.authors_wrapper.missing_normalisation_tensors === 8, `${where}: the variant, the strict restore and the wrapper's missing tensors`);
    assert.ok(vis(mo).includes(zh ? '是否出现在预训练数据中，未知' : 'Pretraining exposure is unknown'), `${where}: exposure unknown`);
    const hd = el(s, /<p class="roadmap-p" data-neurorvq-note="head"/, where);
    assert.ok(hasFig(hd, 'count', X.probe.alpha) && B.every(b => hasFig(hd, 'count', b.fits)), `${where}: the head and its fits`); pinned += 4;
    const nr = vis(el(s, /<p class="roadmap-p" data-neurorvq-note="not-run"/, where));
    assert.ok(!/data-fig/.test(el(s, /<p class="roadmap-p" data-neurorvq-note="not-run"/, where)) && X.protocols_not_run.length === 5, `${where}: the protocols not run, in words`);
    if (!zh) for (const p of X.protocols_not_run) assert.ok(nr.includes(`${MVP.tracks.find(t => t.id === p.protocol).title} (${p.gate})`), `${where}: ${p.protocol} with its gate`);
    const cr = el(s, /<div class="citation-list" id="neurorvq-credits"/, where);
    assert.ok(cr.includes(`href="${R.code.url}"`) && cr.includes(`href="${R.weights.url}"`) && (vis(cr).match(/CC BY-NC 4\.0/g) || []).length >= 2 && cr.includes(M.checkpoint.sha256)
      && cr.includes(M.checkpoint.revision) && cr.includes(M.source_revision) && cr.includes(`href="${M.paper}"`), `${where}: the credits, CC BY-NC 4.0 for code and weights, the checkpoint's identity`);
    assert.ok(decode(cr).includes(L.rights) && vis(cr).includes(zh ? '不分发任何权重' : 'no weights are distributed'), `${where}: no weights distributed`);
    for (const b of B) {
      const d = R.datasets[b.id], a = el(cr, new RegExp(`<article data-credit="neurorvq-dataset-${b.id}"`), where);
      if (b.id === 'eegmat') {
        assert.ok(a.includes('data-credit-ref="neurolm-credits"') && a.includes(`href="/${pfx}topics/pilot-studies/#neurolm-credits"`) && vis(a).includes(EEGMAT_CREDIT_REF[lang]) && a.includes(`href="${d.licenseUrl}"`)
          && vis(a).includes(d.license) && a.includes(`href="/${pfx}datasets/eegmat/"`) && !decode(a).includes(d.attribution), `${where}: EEGMAT's credit points to the NeuroLM credits, its licence linked`);
        continue;
      }
      assert.ok(decode(a).includes(d.attribution) && decode(a).includes(consent(d.privacyReview)) && a.includes(`href="${d.source}"`) && a.includes(`href="${d.licenseUrl}"`), `${where}: ${b.dataset}'s credit, licence and consent`);
    }
    // (4) Collisions: none of the panel's levels at one decimal or as a whole percent, outside the export's own sentences.
    // In English, outside the export's own sentences (the Chinese carries the same numbers, by (2) below).
    if (!zh) { let words2 = vis(stripFigs(s));
      for (const v of verbatim) words2 = words2.split(v).join(' ');
      for (const v of levels) for (const t of [`${(v * 100).toFixed(1)}%`, `${Math.round(v * 100)}%`]) assert.ok(!words2.includes(t), `${where}: ${t} printed beside the panel's two-decimal ${fmt.pct2(v)}`); }
    assert.ok(!/\d+\.\d%/.test(vis(s)), `${where}: no one-decimal percent in the panel`);
    // (9) Structure and words.
    for (const t of s.match(/<table\b[\s\S]*?<\/table>/g)) assert.ok(/<thead>/.test(t), `${where}: every table has a header row`);
    for (const d of s.match(/<details\b[\s\S]*?<\/details>/g) || []) for (const t of d.match(/<table\b[\s\S]*?<\/table>/g) || [])
      assert.ok((el(t, /<thead>/, where).match(/<th\b/g) || []).length >= 4, `${where}: a table inside <details> has four or more columns`);
    assert.doesNotMatch(s, /<script\b|\sstyle="|\son[a-z]+=/i, `${where}: no inline script, style attribute or handler`);
    assert.doesNotMatch(s, /\/Users\/|\/home\/|\/Volumes\/|\/mnt\/|\/root\/|\/private\/|trx50|\btrx\b|Gal4|BCI_Arena|\btwu\b/i, `${where}: no private path or host`);
    assert.doesNotMatch(vis(s), REFUSED, `${where}: nothing blocks_cca.REFUSED_TEXT refuses`);
    assert.doesNotMatch(s, /ICLR 2027|openreview|submission/i, `${where}: no conference-submission reference`);
    assert.doesNotMatch(s, /\bJev\b/, `${where}: no Jev`);
    const textNoCode = vis(s.replace(/<code>[\s\S]*?<\/code>/g, ' ')).replace(/https?:\/\/\S+/g, ' ');
    assert.doesNotMatch(textNoCode, zh ? /新增|本次更新|这次更新|最新|新发布|更新于|(?<![\w.\/#-])v\d+\b/ : /\b(?:new|newly|added|updated|this update|this release adds)\b|(?<![\w.\/#-])v\d+\b/i, `${where}: no update wording or version label`);
    const sentences = vis(s.replace(/<div class="citation-list" id="neurorvq-credits">[\s\S]*?<\/article>\s*<\/div>/, ' ').replace(/<\/(?:h[1-6]|p|li|th|td|caption|figcaption|small|div)>/g, ' ¶ '))
      .split(/¶|(?<=[.;:?])\s+|(?<=[。；：？])/).map(t => t.trim()).filter(Boolean);
    const ranking = zh ? /排行榜|排名|最先进|在线|实时|闭环|临床|零样本|合并|总分|最好|最佳|优于|等效|胜过/ : /leaderboard|\brank(?:ing|ed|s)?\b|state[- ]of[- ]the[- ]art|\bSOTA\b|\bonline\b|real[- ]time|closed[- ]loop|clinical|zero[- ]shot|\bpool(?:s|ed|ing)?\b|\bbest\b|outperform|superior|equivalen|\bbeats?\b/i;
    const denial = zh ? /不|没|无|未|非/ : /\b(?:not|no|never|nor|none|nothing|neither|without)\b/i;
    // "Mean-token pooling" names how the backbone's tokens are averaged (the export's variant), not a pooled score.
    for (const t of sentences) if (ranking.test(t.replace(/mean-token pooling/g, ''))) assert.match(t, denial, `${where}: "${t.slice(0, 140)}" reads as a claim it may only deny`);
    // No typed number: outside the figures, the digits are the export's own sentences, names and identifiers.
    if (!zh) {
      let rest = vis(stripFigs(s));
      for (const v of verbatim) rest = rest.split(v).join(' ');
      const typed = [...rest.replace(/[A-Za-z]+\d+/g, ' ').matchAll(/\d[\d,]*(?:\.\d+)?%?/g)].map(m => m[0].replace(/,$/, '')).filter(t => t !== '95%');
      assert.deepEqual(typed, [], `${where}: a number typed outside the export`);
    }
    // (10) The Markdown copy: the heading and every panel figure, in order.
    const md = read(`${path}index.md`);
    let k = md.indexOf(H2[lang]);
    assert.ok(k >= 0, `${path}index.md: the panel's heading`);
    for (const [, , , , t] of figs) { const j = md.indexOf(decode(t), k); assert.ok(j >= 0, `${path}index.md: the figure "${t}" after offset ${k}`); k = j + decode(t).length; }
    // The card on the home page and the Questions hub.
    for (const page of [pfx, `${pfx}topics/`]) {
      const h = read(`${page}index.html`), a = h.search(new RegExp(`<a class="topic-entry-card" href="${pfx ? '/zh' : ''}/topics/pilot-studies/"`));
      assert.ok(a >= 0, `${page || '/'}: the pilot-studies card`);
      assert.ok(!carries(vis(h.slice(a, h.indexOf('</a>', a)))), `${page || '/'}: the pilot-studies card names nothing of the panel`);
    }
  }
  // (2) The same figures in both languages, and the same typed numbers outside them.
  const ms = h => figAttrs(h).sort();
  assert.deepEqual(ms(sections.zh), ms(sections.en), 'pilot-studies #neurorvq: the Chinese panel prints exactly the English panel’s figures');
  const typedAll = h => [...vis(stripFigs(dropEnglish(h))).replace(/(\d+) 年 (\d+) 月 (\d+) 日/g, '$3 $1').replace(/SHA-256/g, ' ').replace(/[A-Za-z]+\d+/g, ' ')
    .matchAll(/\d+(?:[.,]\d+)*/g)].map(m => m[0]).sort();
  assert.deepEqual(typedAll(sections.zh), typedAll(sections.en), 'pilot-studies #neurorvq: the Chinese panel types the same numbers as the English outside its figures');

  // (1, 4) No figure of the file anywhere else in the site; the coincident one-decimal figures cite their own files.
  let scanned = 0;
  for (const f of htmlFiles(DIST)) {
    const rel = relative(DIST, f), h = readFileSync(f, 'utf8');
    if (!h.includes(`data-fig="${FILE}|`)) continue;
    assert.ok(/^(?:zh\/)?topics\/pilot-studies\/index\.html$/.test(rel), `${rel}: a NeuroRVQ figure outside the pilot studies page`);
    scanned++;
  }
  assert.equal(scanned, 2, 'NeuroRVQ figures on the pilot studies page alone, in both languages');
  for (const id of ['mi-rest', 'p300-target', 'arithmetic-rest']) for (const pfx of ['', 'zh/']) {
    const h = read(`${pfx}protocols/${id}/index.html`);
    for (const [, file, f, raw] of h.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"/g))
      if (['pct1', 'pct1raw'].includes(f) && results.has(Math.abs(Number(raw) * (f === 'pct1' ? 100 : 1)).toFixed(2)))
        assert.notEqual(file, FILE, `${pfx}protocols/${id}/: ${raw} cites its own file`);
  }

  // (11) The pointers: the protocol pages the export names, in words, linking the panel.
  const pointed = X.placement.pointers_from.map(p => p.match(/^\/protocols\/([a-z0-9-]+)\/$/)[1]);
  assert.deepEqual([...pointed].sort(), B.map(b => b.protocol).sort(), 'the pointers come from the three blocks’ protocol pages');
  let pointers = 0;
  for (const [lang, pfx] of [['en', ''], ['zh', 'zh/']]) {
    const dir = join(DIST, `${pfx}protocols`);
    for (const id of readdirSync(dir).filter(d => existsSync(join(dir, d, 'index.html')))) {
      const where = `${pfx}protocols/${id}/`, h = read(`${where}index.html`);
      const n = (h.match(/data-neurorvq-pointer="true"/g) || []).length, links = (h.match(/href="(?:\/zh)?\/topics\/pilot-studies\/#neurorvq"/g) || []).length;
      if (!pointed.includes(id)) { assert.equal(n + links, 0, `${where}: no pointer to the NeuroRVQ panel`); continue; }
      assert.equal(n, 1, `${where}: one pointer`); assert.equal(links, 1, `${where}: one link to the panel`);
      const p = el(h, /<p class="citation-note" data-neurorvq-pointer="true"/, where);
      const both = id === 'arithmetic-rest';
      assert.ok(p.includes(`href="/${pfx}topics/pilot-studies/#${ANCHOR}"`) && txt(p) === (both ? POINTER_BOTH : POINTER)[lang], `${where}: the pointer's words and link`);
      assert.equal(/data-eegmat-ten-second-pointer="true"/.test(p), both, `${where}: Arithmetic & rest links both panels in one line`);
      assert.ok(!p.includes('data-fig') && !/\d/.test(vis(p)), `${where}: the pointer carries no figure`);
      assert.ok(h.includes('data-neurolm-pointer="true"') === both, `${where}: the NeuroLM pointer stays on Arithmetic & rest alone`);
      const md = read(`${where}index.md`);
      for (const t of both ? [POINTER_BOTH[lang].split(': ')[0].split('：')[0], 'NeuroRVQ'] : [POINTER[lang]]) assert.ok(md.includes(t), `${where}index.md: the pointer`);
      pointers++;
    }
  }
  assert.equal(pointers, 6, 'the pointer on three protocol pages in both languages');
  return { pinned, figures: figAttrs(sections.en).length };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/neurorvq.mjs <build dir>'); process.exit(2); }
  const { pinned, figures } = checkNeurorvq(dir);
  console.log(`PASS: NeuroRVQ on three tasks — the separate panel #neurorvq on /topics/pilot-studies/ in both languages: ${figures} figures, every one a leaf of ${FILE} at two decimals and none elsewhere in the site, ${pinned} pinned to their cells by field; the same figures and typed numbers in English and Chinese; the three blocks with their arms, paired differences, readings, own limitations and audits; every limitation printed once, the leaderboard statement once and EEGMAT's shared facts once (the NeuroLM panel's: recording order, development cohort, credit and consent), pointed to from the EEGMAT block and credit; the model's identity and CC BY-NC 4.0 terms; the pilot count, short answer, description, dek and card carrying nothing of the panel; the cite block naming each panel's release; the Markdown copy in order; the pointers on /protocols/mi-rest/, /protocols/p300-target/ and /protocols/arithmetic-rest/ alone, in words.`);
}
