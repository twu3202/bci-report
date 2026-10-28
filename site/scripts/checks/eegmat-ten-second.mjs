// Two frozen encoders on ten-second EEGMAT windows (release eegmat-ten-second-update-20261028, owner decision D14 of
// 2026-10-28): the separate panel #eegmat-ten-second on /topics/pilot-studies/ and its pointer on the Arithmetic & rest
// protocol page, checked in a built site.
//
//   node scripts/checks/eegmat-ten-second.mjs <build dir>        (or import { checkEegmatTenSecond } and pass the dir)
//
// What it holds, in both languages:
//  1. every figure in the panel is a leaf of eegmat-ten-second-update.json under that file's name, printed in its format,
//     and no figure of that file appears anywhere else in the built site;
//  2. English and Chinese print the same figures, and the same typed numbers outside them;
//  3. a cohort block, then EEG-Captioner and AXON in separate subsections, each with its own table beside the same Welch
//     baseline (matched for EEG-Captioner; reused without refitting for AXON), each figure by field; no table or figure
//     sets the two encoders against each other, and the export's reason for that prints once;
//  4. collision guards, by field and file: every level, difference and bound prints at two decimals; EEG-Captioner's
//     65.74% cites this file in its own cell (the same number as LaBraM last-block's per-seed mean in
//     adaptation-update.json), the Welch baseline's 67.59% never prints as 67.6% (core EEGNet on Arithmetic & rest), and
//     the panel prints none of its levels at one decimal;
//  5. beside both scores the source annotation-QC totals; beside AXON's also its own numerical input check, a different
//     check; the QC flag's scope once; the audit boundaries, AXON's failed first audit kept;
//  6. after #neurorvq and before #related, marked data-counted="false"; the pilot count, short answer, description, dek
//     and card carry nothing of the panel; the cite block names each panel's release, computed from the page;
//  7. the licence of each part as the export states it, each licence sentence naming its own model (EEG-Captioner's
//     and AXON's Apache-2.0 terms never read as EEGPT's), each encoder's identity, no weights distributed; EEGMAT's
//     credit and consent once on the page, the NeuroLM panel's, this panel's EEGMAT credit pointing there with the
//     licence linked; the recording-order limitation one line pointing to the NeuroLM panel's statement, keeping what
//     this export adds;
//  8. every table has a header row, a table inside <details> has four or more columns; no inline script, style
//     attribute or handler; no private path or host, nothing blocks_cca.REFUSED_TEXT refuses; no ICLR 2027 or OpenReview
//     reference; no version label or update word; no ranking word outside a denial; no Jev; no number typed outside a
//     figure except the export's own sentences, names and licence identifiers;
//  9. the Markdown copy carries the panel's figures in order;
// 10. the pointer: on the Arithmetic & rest protocol page alone, in both languages, once, in the same line as the NeuroRVQ
//     pointer, with no figure and no digit, linking the panel.
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { resolve, join, relative } from 'node:path';
import { strict as assert } from 'node:assert';
import { fileURLToPath, pathToFileURL } from 'node:url';

const FILE = 'eegmat-ten-second-update.json';
const ANCHOR = 'eegmat-ten-second';
const H2 = { en: 'A separate panel: two frozen encoders on ten-second arithmetic and rest windows', zh: '单独一栏：两个冻结编码器，十秒心算与静息时间窗' };
const SPANS_ZERO = { en: 'the interval spans zero, so neither is shown to be better, and the two are not shown to be equivalent', zh: '区间跨过零，既不能说明哪一方更好，也不能说明两者等效' };
const QC_SCOPE = { en: 'it is not evidence that EEGMAT as a whole is unusable', zh: '也不是 EEGMAT 整体不可用的证据' };
const POINTER_LINK = { en: 'EEG-Captioner and AXON on ten-second windows →', zh: 'EEG-Captioner 与 AXON，十秒时间窗 →' };
const ORDER_REF = {
  en: 'EEGMAT’s recording order (rest before arithmetic), stated in the NeuroLM panel above ↑, holds for these windows too: time and artifacts also move with the label, subject-disjoint folds do not remove this, and neither probe isolates cognitive workload.',
  zh: 'EEGMAT 的记录顺序（静息在心算之前，见上面 NeuroLM 一栏 ↑）同样适用于这些时间窗：时间与伪迹也随标签一起变化，被试不重叠的分折并不能消除这一点，两个探针也都不能单独分离出脑力负荷。',
};
const EEGMAT_CREDIT_REF = { en: 'Credit, ethics and consent: in the NeuroLM panel’s credits above ↑', zh: '署名、伦理与知情同意：见上面 NeuroLM 一栏的署名 ↑' };
const RECORDING_ORDER = { en: /rest is recorded before arithmetic/gi, zh: /静息在心算之前记录/g };

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
const spanEnd = (h, at) => {
  const tag = h.slice(at + 1).match(/^\w+/)[0], re = new RegExp(`<${tag}\\b|</${tag}>`, 'g');
  re.lastIndex = at; let d = 0, m;
  while ((m = re.exec(h))) { d += m[0].startsWith('</') ? -1 : 1; if (!d) return m.index + m[0].length; }
  return h.length;
};
const el = (h, sel, where) => { const a = h.search(sel); assert.ok(a >= 0, `${where}: ${sel} renders`); return h.slice(a, spanEnd(h, a)); };
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const hasFigOf = (file, h, f, x) => new RegExp(`${esc(`data-fig="${file}|${f}|${x}"`)}[^>]*>${esc(fmt[f](x))}<`).test(h);
const hasFig = (h, f, x) => hasFigOf(FILE, h, f, x);
const dropEnglish = h => { let out = h, m; const re = /<(\w+)\b[^>]*\slang="en"[^>]*>/g;
  while ((m = re.exec(out))) { const end = spanEnd(out, m.index); out = out.slice(0, m.index) + ' ' + out.slice(end); re.lastIndex = m.index; }
  return out; };
const stripFigs = h => h.replace(/<span data-fig="[^"]*"[^>]*>[^<]*<\/span>/g, ' ').replace(/<div class="ip-row ip-axis"[\s\S]*?<\/div>\s*<div class="ip-value"><\/div>\s*<\/div>/g, ' ')
  .replace(/<code>[\s\S]*?<\/code>/g, ' ').replace(/\s(?:id|href|data-[\w-]+|aria-label)="[^"]*"/g, '');
const refusedText = () => {
  const py = readFileSync(fileURLToPath(new URL('../../../pipeline/publication/ssvep_followups/blocks_cca.py', import.meta.url)), 'utf8');
  const body = py.slice(py.indexOf('REFUSED_TEXT = re.compile('), py.indexOf('re.IGNORECASE)', py.indexOf('REFUSED_TEXT = re.compile(')));
  const parts = [...body.matchAll(/r'((?:[^'\\]|\\.)*)'/g)].map(m => m[1]);
  assert.ok(parts.length >= 2, 'blocks_cca.REFUSED_TEXT read');
  return new RegExp(parts.join(''), 'i');
};
const htmlFiles = dir => readdirSync(dir).flatMap(f => { const p = join(dir, f); return statSync(p).isDirectory() ? htmlFiles(p) : f.endsWith('.html') ? [p] : []; });

export function checkEegmatTenSecond(distDir) {
  const DIST = resolve(distDir);
  const read = rel => readFileSync(join(DIST, rel), 'utf8');
  const X = JSON.parse(read(`data/${FILE}`));
  const src = readFileSync(fileURLToPath(new URL(`../../src/data/${FILE}`, import.meta.url)), 'utf8');
  assert.equal(read(`data/${FILE}`), src, `${FILE}: the served copy is byte-identical to src/data`);
  const PS = JSON.parse(read('data/pilot-studies-update.json'));
  const AD = JSON.parse(read('data/adaptation-update.json'));
  const REFUSED = refusedText();
  const leaves = new Set(); const walk = v => { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); }; walk(X);
  const C = X.cohort, Q = X.source_annotation_qc, CAP = X.eeg_captioner, AX = X.axon, NIC = AX.numerical_input_check, ENC = [CAP, AX];
  assert.equal(X.placement.counted_in_pilots, false, 'the panel is outside the pilot count');
  assert.equal(X.encoder_contrast.published, false, 'no encoder contrast');
  const arm = (e, role) => e.arms.find(a => a.role === role);
  const levels = ENC.flatMap(e => e.arms.map(a => a.balanced_accuracy)), diffs = ENC.flatMap(e => [e.paired_difference.difference, ...e.paired_difference.interval_95]);
  const results = new Set([...levels, ...diffs].map(v => Math.abs(v * 100).toFixed(2)));
  const carries = t => /EEG-Captioner|\bAXON\b/i.test(t) || [...t.matchAll(/\d+(?:\.\d+)?/g)].some(m => results.has(m[0]));
  // The collision the plan names: EEG-Captioner's level is LaBraM last-block's per-seed mean at two decimals.
  const adLeaves = []; const walkAd = v => { if (typeof v === 'number') adLeaves.push(v); else if (v && typeof v === 'object') Object.values(v).forEach(walkAd); }; walkAd(AD);
  assert.ok(adLeaves.some(v => (v * 100).toFixed(2) === fmt.pct2(arm(CAP, 'encoder').balanced_accuracy).slice(0, -1)), 'the adaptation file carries the coincident 65.74 the guard is for');
  const nPilots = PS.pilots.filter(p => p.publication === 'released').length;
  const consent = s => s.slice(0, s.indexOf('. ') + 1);
  const R = X.rights;
  const verbatim = [X.question, X.title, C.preprocessing.text, X.interval.text, X.interval.scope, Q.source, Q.rule_text, Q.scope,
    ...ENC.flatMap(e => [e.title, e.input.text, e.representation.definition, e.scope, e.baseline.definition, e.audit.text, e.paired_difference.label, e.paired_difference.reading,
      ...e.arms.flatMap(a => [a.label, a.note]), ...(e.limitations || []).map(l => l.text)]),
    NIC.rule, X.encoder_contrast.text, X.separate_from_two_second_results.text, ...X.limitations.map(l => l.text), X.not_published[0],
    R.dataset.attribution, R.dataset.rightsScope, R.dataset.license, consent(R.dataset.privacyReview),
    CAP.rights.weights.as_stated_by, AX.rights.checkpoint.as_stated_by, AX.rights.module.scope, AX.rights.project.scope,
    'Apache-2.0', 'BSD-3-Clause', X.schema_version, FILE, 'SHA-256'].filter(Boolean).sort((a, b) => b.length - a.length);
  let pinned = 0;
  const sections = {};

  for (const [lang, pfx] of [['en', ''], ['zh', 'zh/']]) {
    const zh = lang === 'zh', path = `${pfx}topics/pilot-studies/`, where = `${path}#${ANCHOR}`, html = read(`${path}index.html`);
    const main = html.slice(html.indexOf('<main'), html.indexOf('<section class="cite-page"'));
    const own = main.slice(0, main.indexOf('<nav class="topic-switcher"'));
    const s = el(own, new RegExp(`<section\\b[^>]*\\sid="${ANCHOR}"`), where);
    sections[lang] = s;
    // (6) Placement, the uncounted mark, the heading.
    const at = own.indexOf(s);
    assert.ok(own.indexOf('id="neurorvq"') < at && at < own.indexOf('id="related"'), `${where}: the panel follows NeuroRVQ's and precedes the related questions`);
    assert.match(s.slice(0, s.indexOf('>')), /data-counted="false"/, `${where}: the panel is marked outside the pilot count`);
    assert.match(s.slice(0, s.indexOf('>')), new RegExp(`data-release="${X.release_id}"`), `${where}: the panel names its release`);
    assert.equal(vis(el(s, /<h2\b/, where)), H2[lang], `${where}: the panel's heading`);
    // (1) Every figure is a leaf of its file, printed in its format; none outside the panel.
    const figs = [...s.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)];
    assert.ok(figs.length > 40, `${where}: the panel's figures (${figs.length})`);
    for (const [, file, f, raw, text] of figs) {
      assert.equal(file, FILE, `${where}: a panel figure from ${file}`);
      assert.ok(leaves.has(Number(raw)), `${where}: ${raw} is not a value in ${FILE}`);
      assert.ok(fmt[f], `${where}: format ${f}`);
      assert.equal(decode(text), fmt[f](Number(raw)), `${where}: ${raw} printed as "${text}"`);
      if ([...levels, ...diffs].includes(Number(raw)) && f === 'count') assert.fail(`${where}: ${raw} printed as a count`);
    }
    assert.ok(!html.replace(s, ' ').includes(`data-fig="${FILE}|`), `${where}: no ten-second figure outside its panel`);
    // (6) The count, the short answer, the description, the dek and the card carry nothing of the panel; the cite block.
    const ans = vis(el(own, /<section class="short-answer"/, where));
    assert.ok(!carries(ans), `${where}: the short answer names either encoder or prints one of the panel's results`);
    const words = zh ? ['', '', '两', '三', '四'] : ['', '', 'two', 'three', 'four'], counts = zh ? ['', '', '', '三', '四', '五'] : ['', '', '', 'Three', 'Four', 'Five'];
    assert.ok(ans.includes(zh ? `${words[nPilots]}项试点、${counts[nPilots + 1]}项结果` : `${counts[nPilots + 1]} findings from ${words[nPilots]} pilots`), `${where}: the short answer counts the export's ${nPilots} pilots`);
    assert.ok(!carries(decode(html.match(/<meta name="description" content="([^"]*)"/)[1])), `${where}: the description`);
    assert.ok(!carries(vis(el(main, /<p class="topic-dek"/, where))), `${where}: the dek`);
    const panels = [...own.matchAll(/<section\b[^>]*>/g)].map(m => m[0]).filter(t => /data-counted="false"/.test(t)).map(t => t.match(/data-release="([^"]+)"/)[1]);
    const cite = html.slice(html.indexOf('<section class="cite-page"'));
    assert.ok(panels.includes(X.release_id), `${where}: the panel is one of the page's separate panels`);
    assert.deepEqual(cite.match(/data-releases="([^"]+)"/)[1].split(' ').sort(), [PS.release_id, ...panels].sort(), `${where}: the cite block names the pilot studies' release and each panel's`);
    assert.ok(s.includes(`href="/data/${FILE}"`) && vis(el(s, /<p class="citation-note" data-ts-note="data-source"/, where)).includes(X.schema_version), `${where}: the data source names the file and its schema`);
    // (3) The cohort block, then one subsection per encoder, in the export's order.
    const cb = el(s, /<div data-ts-block="cohort"/, where);
    assert.ok([C.people, C.recordings, C.windows, C.channels, C.sampling_hz, C.folds].every(v => hasFig(el(cb, /<p class="roadmap-p" data-ts-note="cohort"/, where), 'count', v)), `${where}: the cohort`); pinned += 6;
    assert.ok(hasFig(el(cb, /<p class="roadmap-p" data-ts-note="probe"/, where), 'count', X.probe.alpha) && hasFig(el(cb, /<p class="roadmap-p" data-ts-note="probe"/, where), 'count', X.probe.fits_per_representation), `${where}: the shared head`); pinned += 2;
    const qr = el(cb, /<p class="protocol-note" data-ts-note="qc-rule"/, where);
    assert.ok(zh ? decode(qr).includes(Q.rule_text) && decode(qr).includes(Q.scope) : vis(qr).includes(Q.rule_text) && vis(qr).includes(Q.scope), `${where}: the QC rule and its scope as the export words them`);
    assert.equal(vis(own).split(QC_SCOPE[lang]).length - 1, 1, `${where}: the QC flag's scope once on the page`);
    const subs = [...s.matchAll(/<div data-ts-encoder="([^"]+)"/g)].map(m => m[1]);
    assert.deepEqual(subs, ['eeg-captioner', 'axon'], `${where}: two subsections, EEG-Captioner's then AXON's`);
    assert.equal((s.match(/<table\b/g) || []).length, 2, `${where}: one table per encoder, no shared table`);
    for (const e of ENC) {
      const w = `${where} ${e.id}`, sub = el(s, new RegExp(`<div data-ts-encoder="${e.id}"`), w), enc = arm(e, 'encoder'), base = arm(e, 'baseline'), d = e.paired_difference;
      assert.equal(vis(el(sub, /<h3\b/, w)), zh ? vis(el(sub, /<h3\b/, w)) : e.title, `${w}: the subsection names its encoder`);
      const t = el(sub, new RegExp(`<table data-ts-table="${e.id}"`), w);
      assert.deepEqual([...t.matchAll(/<tr data-ts-row="([^"]+)"/g)].map(m => m[1]), [enc.id, base.id], `${w}: the encoder, then the Welch baseline`);
      for (const a of [enc, base]) {
        const row = el(t, new RegExp(`<tr data-ts-row="${a.id}"`), w);
        assert.ok(hasFig(el(row, /<td data-cell="dimension"/, w), 'count', a.dimension) && hasFig(el(row, /<td data-cell="ba"/, w), 'pct2', a.balanced_accuracy) && figAttrs(row).length === 2,
          `${w}: ${a.id}, its dimension and balanced accuracy by field`); pinned += 2;
      }
      // (3) The baseline's note: matched for EEG-Captioner; reused without refitting, not matched, for AXON.
      const note = vis(el(el(t, new RegExp(`<tr data-ts-row="${base.id}"`), w), /<td data-cell="role"/, w));
      assert.ok(note.includes(zh ? (e.baseline.matched ? '在这次运行中作为匹配的对照拟合' : '没有重新拟合') : base.note), `${w}: the baseline's note`);
      // The other encoder's figures never appear here.
      const other = ENC.find(x => x !== e);
      assert.ok(!sub.includes(`|${arm(other, 'encoder').balanced_accuracy}"`) && !sub.includes(`|${other.paired_difference.difference}"`), `${w}: nothing of the other encoder`);
      const fd = el(sub, new RegExp(`<div class="finding" data-finding="eegmat-ten-second-${e.id}"`), w), fp = el(fd, /<div class="finding-copy"/, w);
      assert.ok(hasFig(el(fd, /<div class="finding-number"/, w), 'pp2', d.difference) && hasFig(fp, 'pct2', enc.balanced_accuracy) && hasFig(fp, 'pct2', base.balanced_accuracy)
        && [d.difference, ...d.interval_95].every(v => hasFig(fp, 'sgn2', v)), `${w}: the finding's levels, difference and bounds`); pinned += 6;
      assert.ok(vis(fp).includes(SPANS_ZERO[lang]), `${w}: the reading beside the interval`);
      // (5) Beside the score: the QC totals; for AXON also its own input check.
      const qc = el(fp, new RegExp(`<p data-ts-qc="${e.id}"`), w);
      assert.ok([Q.windows_meeting_rules, Q.windows, Q.recordings_flagged, Q.recordings].every(v => hasFig(qc, 'count', v)) && (zh || txt(qc) === Q.beside_every_score), `${w}: the QC totals beside the score`); pinned += 4;
      if (e === AX) {
        const ic = el(fp, /<p data-ts-input-check="axon"/, w);
        assert.ok(hasFig(ic, 'count', NIC.windows_passed) && (zh || txt(ic).startsWith(`${NIC.beside_score}.`)) && decode(ic).includes(NIC.rule), `${w}: AXON's own input check, a different check`); pinned += 1;
        assert.deepEqual([...sub.matchAll(/<li data-ts-limit="([^"]+)"/g)].map(m => m[1]), [...AX.limitations.map(l => l.id), 'axon-inputs'], `${w}: AXON's limits beside its result`);
      } else assert.ok(!fp.includes('data-ts-input-check'), `${w}: the input check is AXON's alone`);
      const au = el(sub, new RegExp(`<p class="citation-note" data-ts-audit="${e.id}"`), w);
      assert.ok(zh ? decode(au).includes(e.audit.text) : vis(au) === e.audit.text, `${w}: the audit boundary`);
    }
    assert.ok(vis(el(s, /<p class="citation-note" data-ts-audit="axon"/, where)).includes(zh ? '第一次独立审计没有通过特征容差' : 'first independent audit failed its feature tolerance and is kept'), `${where}: AXON's failed first audit, kept`);
    // (3) No contrast between the encoders: the export's reason, once.
    assert.ok(decode(el(s, /<p class="protocol-note" data-ts-note="contrast"/, where)).includes(X.encoder_contrast.text), `${where}: why no encoder contrast is computed`);
    assert.equal((vis(s).match(zh ? /不计算 EEG-Captioner 与 AXON 之间的差值/g : /No EEG-Captioner against AXON difference is computed/g) || []).length, 1, `${where}: said once`);
    const sep = el(s, /<p class="protocol-note" data-ts-note="separation"/, where);
    assert.ok(decode(sep).includes(X.separate_from_two_second_results.text) && sep.includes(`href="/${pfx}protocols/arithmetic-rest/"`), `${where}: not ranked against the two-second results, the core matrix linked`);
    assert.deepEqual([...el(s, /<ul class="rd-rules" data-ts-note="limits"/, where).matchAll(/<li data-ts-limit="([^"]+)"/g)].map(m => m[1]),
      X.limitations.map(l => l.id).filter(id => id !== 'axon-inputs'), `${where}: the panel's other limitations`);
    // The recording order: the NeuroLM panel's statement, pointed to, with what this export adds; once on the page.
    const ro = el(s, /<li data-ts-limit="recording-order"/, where), nl = el(own, /<section\b[^>]*\sid="neurolm-eegmat"/, where);
    assert.ok(ro.includes(`href="/${pfx}topics/pilot-studies/#neurolm-eegmat"`) && txt(ro) === ORDER_REF[lang], `${where}: the recording order points to the NeuroLM panel's statement`);
    assert.ok((vis(own).match(RECORDING_ORDER[lang]) || []).length === 1 && (vis(nl).match(RECORDING_ORDER[lang]) || []).length === 1, `${where}: "rest is recorded before arithmetic" once on the page, in the NeuroLM panel`);
    // (7) Credits: licences per part, consent, each encoder's identity, no weights distributed.
    const cr = el(s, /<div class="citation-list" id="eegmat-ten-second-credits"/, where), CI = CAP.identity, AI = AX.identity;
    const ec = el(cr, /<article data-credit="eegmat-ten-second-dataset"/, where);
    assert.ok(ec.includes('data-credit-ref="neurolm-credits"') && ec.includes(`href="/${pfx}topics/pilot-studies/#neurolm-credits"`) && vis(ec).includes(EEGMAT_CREDIT_REF[lang])
      && ec.includes(`href="${R.dataset.licenseUrl}"`) && vis(ec).includes(R.dataset.license) && ec.includes(`href="/${pfx}datasets/eegmat/"`) && !decode(cr).includes(R.dataset.attribution),
      `${where}: EEGMAT's credit points to the NeuroLM credits, its licence linked`);
    for (const t of [R.dataset.attribution, consent(R.dataset.privacyReview)]) assert.ok(decode(own).split(t).length - 1 === 1 && decode(nl).includes(t), `${where}: EEGMAT's "${t.slice(0, 40)}…" once on the page, in the NeuroLM credits`);
    const cc = el(cr, /<article data-credit="eeg-captioner"/, where), ac = el(cr, /<article data-credit="axon"/, where);
    assert.ok([CI.hf_revision, CI.source_revision, CI.encoder_sha256].every(x => cc.includes(x)) && cc.includes(`href="${CI.hf_repository}"`) && cc.includes(`href="${CI.source_repository}"`)
      && vis(cc).includes('MIT') && vis(cc).includes('Apache-2.0'), `${where}: EEG-Captioner's identity, code MIT and weights Apache-2.0`);
    // Each sentence that names Apache-2.0 names its own model, and none names EEGPT.
    for (const [a, name] of [[cc, 'EEG-Captioner'], [ac, 'AXON']]) {
      const lic = vis(el(a, /<p data-ts-licence=/, where)), apache = lic.split(/(?<=\.)\s+|(?<=。)/).filter(t => /Apache/.test(t));
      assert.ok(apache.length >= 1 && apache.every(t => t.includes(name) && !/EEGPT/.test(t)), `${where}: each Apache-2.0 sentence names ${name}`);
    }
    assert.ok(!/EEGPT[^.。;；]{0,60}Apache|Apache[^.。;；]{0,60}EEGPT/.test(vis(s)), `${where}: no sentence sets EEGPT beside Apache-2.0`);
    assert.ok([AI.hf_revision, AI.source_revision, AI.checkpoint_sha256, AI.module, AI.checkpoint_file].every(x => ac.includes(x)) && vis(ac).includes('Apache-2.0') && vis(ac).includes('BSD-3-Clause'),
      `${where}: AXON's identity, checkpoint and module Apache-2.0 within a BSD-3-Clause project`);
    assert.ok(!/arxiv/i.test(ac), `${where}: AXON's paper reference is not cited until checked`);
    assert.ok(vis(el(s, /<p class="citation-note" data-ts-note="weights"/, where)).includes(zh ? '不分发任何权重' : 'No weights are distributed'), `${where}: no weights distributed`);
    // (4) Collisions: two decimals only; EEG-Captioner's 65.74% and the baseline's 67.59% by field, never at one decimal.
    assert.ok(hasFig(el(el(s, /<table data-ts-table="eeg-captioner"/, where), /<tr data-ts-row="eeg-captioner"/, where), 'pct2', arm(CAP, 'encoder').balanced_accuracy), `${where}: EEG-Captioner's level, this file's field`);
    assert.ok(!s.includes('data-fig="adaptation-update.json|'), `${where}: no adaptation figure in the panel`);
    let words2 = vis(stripFigs(s));
    if (!zh) { for (const v of verbatim) words2 = words2.split(v).join(' ');
      for (const v of levels) for (const t of [`${(v * 100).toFixed(1)}%`, `${Math.round(v * 100)}%`]) assert.ok(!words2.includes(t), `${where}: ${t} printed beside the panel's two-decimal ${fmt.pct2(v)}`); }
    assert.ok(!/\d+\.\d%/.test(vis(s)), `${where}: no one-decimal percent in the panel`);
    // (8) Structure and words.
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
    const sentences = vis(s.replace(/<div class="citation-list" id="eegmat-ten-second-credits">[\s\S]*?<\/article>\s*<\/div>/, ' ').replace(/<\/(?:h[1-6]|p|li|th|td|caption|figcaption|small|div)>/g, ' ¶ '))
      .split(/¶|(?<=[.;:?])\s+|(?<=[。；：？])/).map(t => t.trim()).filter(Boolean);
    const ranking = zh ? /排行榜|排名|最先进|在线|实时|闭环|临床|零样本|合并|总分|最好|最佳|优于|等效|胜过/ : /leaderboard|\brank(?:ing|ed|s)?\b|state[- ]of[- ]the[- ]art|\bSOTA\b|\bonline\b|real[- ]time|closed[- ]loop|clinical|zero[- ]shot|\bpool(?:s|ed|ing)?\b|\bbest\b|outperform|superior|equivalen|\bbeats?\b/i;
    const denial = zh ? /不|没|无|未|非/ : /\b(?:not|no|never|nor|none|nothing|neither|without)\b/i;
    // "Mean-token pooling" names how the backbone's tokens are averaged (the export's variant), not a pooled score.
    for (const t of sentences) if (ranking.test(t.replace(/mean-token pooling/g, ''))) assert.match(t, denial, `${where}: "${t.slice(0, 140)}" reads as a claim it may only deny`);
    if (!zh) {
      let rest = vis(stripFigs(s));
      for (const v of verbatim) rest = rest.split(v).join(' ');
      const typed = [...rest.replace(/[A-Za-z]+\d+/g, ' ').matchAll(/\d[\d,]*(?:\.\d+)?%?/g)].map(m => m[0].replace(/,$/, '')).filter(t => t !== '95%');
      assert.deepEqual(typed, [], `${where}: a number typed outside the export`);
    }
    // (9) The Markdown copy: the heading and every panel figure, in order.
    const md = read(`${path}index.md`);
    let k = md.indexOf(H2[lang]);
    assert.ok(k >= 0, `${path}index.md: the panel's heading`);
    for (const [, , , , t] of figs) { const j = md.indexOf(decode(t), k); assert.ok(j >= 0, `${path}index.md: the figure "${t}" after offset ${k}`); k = j + decode(t).length; }
    for (const page of [pfx, `${pfx}topics/`]) {
      const h = read(`${page}index.html`), a = h.search(new RegExp(`<a class="topic-entry-card" href="${pfx ? '/zh' : ''}/topics/pilot-studies/"`));
      assert.ok(a >= 0, `${page || '/'}: the pilot-studies card`);
      assert.ok(!carries(vis(h.slice(a, h.indexOf('</a>', a)))), `${page || '/'}: the pilot-studies card names nothing of the panel`);
    }
  }
  // (2) The same figures in both languages, and the same typed numbers outside them.
  const ms = h => figAttrs(h).sort();
  assert.deepEqual(ms(sections.zh), ms(sections.en), 'pilot-studies #eegmat-ten-second: the Chinese panel prints exactly the English panel’s figures');
  const typedAll = h => [...vis(stripFigs(dropEnglish(h))).replace(/(\d+) 年 (\d+) 月 (\d+) 日/g, '$3 $1').replace(/SHA-256/g, ' ').replace(/[A-Za-z]+\d+/g, ' ')
    .matchAll(/\d+(?:[.,]\d+)*/g)].map(m => m[0]).sort();
  assert.deepEqual(typedAll(sections.zh), typedAll(sections.en), 'pilot-studies #eegmat-ten-second: the Chinese panel types the same numbers as the English outside its figures');

  // (1, 4) No figure of the file anywhere else; the coincident figures elsewhere cite their own files.
  let found = 0;
  for (const f of htmlFiles(DIST)) {
    const rel = relative(DIST, f), h = readFileSync(f, 'utf8');
    if (h.includes(`data-fig="${FILE}|`)) { assert.ok(/^(?:zh\/)?topics\/pilot-studies\/index\.html$/.test(rel), `${rel}: a ten-second figure outside the pilot studies page`); found++; }
  }
  assert.equal(found, 2, 'ten-second figures on the pilot studies page alone, in both languages');
  for (const pfx of ['', 'zh/']) {
    const h = read(`${pfx}protocols/arithmetic-rest/index.html`);
    for (const [, file, f, raw] of h.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"/g))
      if (['pct1', 'pct1raw'].includes(f) && results.has(Math.abs(Number(raw) * (f === 'pct1' ? 100 : 1)).toFixed(2)))
        assert.notEqual(file, FILE, `${pfx}protocols/arithmetic-rest/: ${raw} cites its own file`);
  }

  // (10) The pointer: Arithmetic & rest alone, in the NeuroRVQ line, in words.
  const pointedFrom = X.placement.pointer_from.match(/^\/protocols\/([a-z0-9-]+)\/$/)[1];
  let pointers = 0;
  for (const [lang, pfx] of [['en', ''], ['zh', 'zh/']]) {
    const dir = join(DIST, `${pfx}protocols`);
    for (const id of readdirSync(dir).filter(d => existsSync(join(dir, d, 'index.html')))) {
      const where = `${pfx}protocols/${id}/`, h = read(`${where}index.html`);
      const n = (h.match(/data-eegmat-ten-second-pointer="true"/g) || []).length, links = (h.match(/href="(?:\/zh)?\/topics\/pilot-studies\/#eegmat-ten-second"/g) || []).length;
      if (id !== pointedFrom) { assert.equal(n + links, 0, `${where}: no pointer to the ten-second panel`); continue; }
      assert.equal(n, 1, `${where}: one pointer`); assert.equal(links, 1, `${where}: one link to the panel`);
      const p = el(h, /<p class="citation-note" data-neurorvq-pointer="true" data-eegmat-ten-second-pointer="true"/, where);
      const a = el(p, /<a href="[^"]*#eegmat-ten-second"/, where);
      assert.ok(a.includes(`href="/${pfx}topics/pilot-studies/#${ANCHOR}"`) && vis(a) === POINTER_LINK[lang], `${where}: the pointer's words and link`);
      assert.ok(!p.includes('data-fig') && !/\d/.test(vis(p)), `${where}: the pointer carries no figure`);
      assert.ok(read(`${where}index.md`).includes(POINTER_LINK[lang]), `${where}index.md: the pointer`);
      pointers++;
    }
  }
  assert.equal(pointers, 2, 'the pointer on the Arithmetic & rest page in both languages');
  return { pinned, figures: figAttrs(sections.en).length };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/eegmat-ten-second.mjs <build dir>'); process.exit(2); }
  const { pinned, figures } = checkEegmatTenSecond(dir);
  console.log(`PASS: ten-second EEGMAT — the separate panel #eegmat-ten-second on /topics/pilot-studies/ in both languages: ${figures} figures, every one a leaf of ${FILE} at two decimals and none elsewhere in the site, ${pinned} pinned to their cells by field; the same figures and typed numbers in English and Chinese; the cohort block, then EEG-Captioner and AXON in separate subsections beside the same Welch baseline, no encoder contrast; the QC totals beside both scores and AXON's own input check beside its own; the audit boundaries, AXON's failed first audit kept; licences per part, each Apache-2.0 sentence naming its model, and identities; EEGMAT's recording order, credit and consent once on the page (the NeuroLM panel's), pointed to; the pilot count, short answer, description, dek and card carrying nothing of the panel; the cite block naming each panel's release; the Markdown copy in order; the pointer on /protocols/arithmetic-rest/ alone, in words.`);
}
