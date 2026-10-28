// What do the files show once a public EEG dataset is checked end to end? (releases data-quality-update-20261020 and
// dataset-checks-update-20261028; owner decisions D1, D2, D15, D16, D18, D21): /topics/data-quality/ and Kim
// beta-range's dataset page in both languages, checked in a built site.
//
//   node scripts/checks/data-quality.mjs <build dir>        (or import { checkDataQuality } and pass the dir)
//
// What it holds, in both languages:
//  1. the page: its question as the h1 and the <title>; its sections in the order the dataset-checks file sets
//     (#shin2022, #kim2025-beta-range, #mind2026, the one-person lead, #eldbeta, #damm, #nebula, #zuco2), then the
//     register rows and #methods-and-limits; Shin2022's, Kim's and MIND's questions as their h2s; the short answer states
//     Shin2022's three figures, which the page shows again below it; the description is one or two sentences;
//  2. every figure is a leaf of data-quality-update.json or dataset-checks-update.json under that file's name, printed in
//     its format, and the page's figures, in order, are the named fields each sentence and table cell reads; English and
//     Chinese print the same figures; the served files are the reviewed ones, byte for byte;
//  3. Shin2022: the three arms in the export's order with mean, interval and pooled value; the duration control
//     labelled retrospective and set apart under its own heading row; the caveat once, beside the table; the coverage
//     chain once, in its table, every link a figure and none of its distinctive counts anywhere else (the short answer
//     and description included); the catalog line; the six checks and seven holds; consent and ethics as the A3 record
//     states them; the attribution ending "Derived analysis by BCI Report; not endorsed by the authors.";
//  4. Kim beta-range: the lede's cohort, mean participant accuracy with its interval and chance; the intake; five checks,
//     the sealing stated as process separation, not blinded labels; each of the eight caveats once; its hold named and
//     linked, and the amplitude hold named once there (the scope check's own repeat is reworded away); its rights,
//     consent and ethics; its dataset page linked while built, and no method page linked;
//  5. MIND: record IDs, never people (a person word only in the record-ID caveat); the primary table with CSP + LDA and
//     both controls; the four contrasts, each the arm less its control, with record-ID resampling ranges named as such
//     and never called confidence intervals; the schedule facts; the secondary panel in a table of its own with no
//     interval; the coverage from the runs in the release to the two panels; the four licence statements side by side
//     with ScienceDB's terms-of-use page stated as unread; no dataset page;
//  6. the one-person sentence once, between MIND and eldBETA, and eldBETA's own repeat gone; eldBETA: counts only
//     (blocks, targets, trials, non-finite values), no score and no percentage, no held figure anywhere; "header
//     calibration", never "units verified"; the holds line; the SingLEM fact line; its hold linked;
//  7. Damm and NeBULA: whole counts only (no percentage, no score format, no comparison word), the design, file and
//     timing facts, the arms run and their holds, each hold named and linked; NeBULA's participant counts exactly as the
//     export states them, and its task line saying what MOABB's catalog lists (the register row prints no task label);
//     the Zenodo id its files name is never linked;
//  8. ZuCo 2.0: its section prints no figure and no digit outside the dataset's name; its hold linked;
//  9. no hold reason of the dataset checks is printed (they are on /releases/#holds);
// 10. the open register: each of the seven cases links its row (/datasets/register/#r-site-…) only while a register file
//     is served and the register page is built, each row a dataset row of the newest served file and an anchor on that
//     page; the catalog line names Shin2022's register row, and the not-published list the register file, if and only if
//     that row carries MOABB's counts; a frozen register without that finding fails;
// 11. every table has a <thead>, a table inside <details> has four or more columns; no inline script, style attribute
//     or handler; hreflang reciprocal; the cite block names exactly the two releases; both files are downloadable;
// 12. no private path or host label, no ICLR 2027, OpenReview or submission reference, no "55%", not the thread
//     commenter's name (blocks_cca.REFUSED_TEXT, read from its source), no version label or update word, no ranking
//     word, no ", not" hedge in the English beyond Kim's sealing sentence; no rejected Chinese rendering, no ASCII full
//     stop after Chinese;
// 13. the Markdown copy carries every figure the page marks;
// 14. Kim beta-range's dataset page: its profile's summary as its subtitle, its names once, its cohort figures and facts,
//     a pointer to its worked case, its ethics
//     and consent, its register row; no method page linked; the cite block names the dataset checks only.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { strict as assert } from 'node:assert';
import { fileURLToPath, pathToFileURL } from 'node:url';

const FILE = 'data-quality-update.json';
const DCF = 'dataset-checks-update.json';
const PATH = 'topics/data-quality/';
const KIM_PATH = 'datasets/kim2025-beta-range/';
const H1 = { en: 'What do the files show once a public EEG dataset is checked end to end?', zh: '把公开 EEG 数据集从头到尾核一遍，文件里能看到什么？' };
const SHIN_H2 = { en: 'What survives a participant-held-out check?', zh: '整名被试留出后，还剩下什么？' };
const ENDORSEMENT = 'Derived analysis by BCI Report; not endorsed by the authors.';
const RETRO = { en: /Retrospective/, zh: /回溯/ };
const SINGLEM = { en: '/methods/singlem/#pretraining-exposure', zh: '/zh/methods/singlem/#pretraining-exposure' };
const CASE_ROWS = ['r-site-shin2022', 'r-site-kim2025-beta-range', 'r-site-mind2026', 'r-site-eldbeta', 'r-site-damm-finger-imagery', 'r-site-nebula', 'r-site-zuco2'];
const REGISTER_NAMED = { en: /open register/, zh: /开放登记册/ };
// The one-person sentence in Chinese (data-quality.ts dqZh), and eldBETA's repeat that the page no longer prints.
const ONE_PERSON_ZH = '只有一个人时，任何分数都是这个人的分数，所以这三个案例只发布计数与文件事实，所有分数暂缓。';
const ELD_REPEAT = { en: 'every score is that person’s, so the accuracy is held', zh: '任何分数都是这个人的分数，所以准确率暂缓' };
const PERSON_CORE = { en: 'every score is that person’s', zh: '任何分数都是这个人的分数' };
// Kim's sealing sentence: process separation, not blinded labels.
const SEALING = { en: 'process separation, not blinded labels', zh: '进程上的隔离，不是对标签设盲' };
// Export sentences the page prints in its own words (data-quality.ts dqReworded): Kim's amplitude hold is said once, by
// its caveat beside the hold line; NeBULA's register row prints no task label, so the line says what MOABB's catalog lists.
const REWORDED = {
  'A separate review admitted the as-stored, scale-invariant CCA arm before any score, and kept amplitude-dependent models held.':
    'A separate review admitted the as-stored, scale-invariant CCA arm before any score.',
  'The source describes executed reaching with an upper-limb exoskeleton; the open register keeps MOABB’s imagery label as MOABB lists it.':
    'The source describes executed reaching with an upper-limb exoskeleton; MOABB’s catalog lists the dataset under motor imagery.',
};
const shown = t => REWORDED[t] ?? t;
// MIND's ranges are never confidence intervals: the phrase appears once, in the sentence that says so.
const CI_WORD = { en: /confidence interval/g, zh: /置信区间/g };
const PERSON_WORD = { en: /\b(?:participants?|people|persons?|subjects?)\b/gi, zh: /被试/g };
// Words that compare or score, which Damm's and NeBULA's sections never use.
const COMPARE = { en: /\b(?:above|below|higher|lower|better|worse|exceeds?|outperform\w*|beats?|than|versus|vs\.?|chance|accura\w*|scored at)\b/i,
                  zh: /高于|低于|优于|劣于|超过|胜过|不如|随机水平|准确率为/ };
// Glossary renderings the site rejects (check-workbench.mjs `rejected`), the ones this page could reach.
const REJECTED_ZH = ['参与者', '受试者', '读出头', '区块', '谱岭回归', '暴露', '个百分点', '源数据'];

const fmt = {
  pct2: r => (r * 100).toFixed(2) + '%',
  pct1raw: r => r.toFixed(1) + '%',
  pct2raw: r => r.toFixed(2) + '%',
  pp2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2) + ' pp',
  sgn2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2),
  count: r => r.toLocaleString('en-US'),
};
const decode = s => s.replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d))).replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const vis = h => decode(h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
// Visible text with no space added at tag boundaries (a figure joins the words around it).
const text = h => decode(h.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
const figAttrs = h => [...h.matchAll(/data-fig="([^"]+)"/g)].map(m => m[1]);
const attr = (f, x, file = FILE) => `data-fig="${file}|${f}|${x}"`;
// The element that opens at `at`, through its matching close tag.
const spanEnd = (h, at) => {
  const tag = h.slice(at + 1).match(/^\w+/)[0], re = new RegExp(`<${tag}\\b|</${tag}>`, 'g');
  re.lastIndex = at; let d = 0, m;
  while ((m = re.exec(h))) { d += m[0].startsWith('</') ? -1 : 1; if (!d) return m.index + m[0].length; }
  return h.length;
};
const el = (h, sel, where) => { const a = h.search(sel); assert.ok(a >= 0, `${where}: ${sel} renders`); return h.slice(a, spanEnd(h, a)); };
const count = (h, s) => h.split(s).length - 1;
// Elements in English inside a Chinese page (attributions, originals beside the Chinese, titles).
const dropEnglish = h => { let out = h, m; const re = /<(\w+)\b[^>]*\slang="en"[^>]*>/g;
  while ((m = re.exec(out))) { const end = spanEnd(out, m.index); out = out.slice(0, m.index) + ' ' + out.slice(end); re.lastIndex = m.index; }
  return out; };
const curly = s => s.replace(/(\w)'(?=\w)/g, '$1’');
const sorted = a => [...a].sort();
// A page and its Markdown copy with every printed figure set aside (the data-fig elements, and their text in the copy).
const unfig = (s, page) => [...page.matchAll(/data-fig="[^"]+"[^>]*>([^<]*)</g)].map(m => decode(m[1])).filter(Boolean)
  .sort((a, b) => b.length - a.length).reduce((t, f) => t.split(f).join(' '), s.replace(/<span data-fig="[^"]+"[^>]*>[^<]*<\/span>/g, ' '));

// blocks_cca.REFUSED_TEXT, read from its source, so this file adds no literal of what it refuses.
const refusedText = () => {
  const py = readFileSync(fileURLToPath(new URL('../../../pipeline/publication/ssvep_followups/blocks_cca.py', import.meta.url)), 'utf8');
  const at = py.indexOf('REFUSED_TEXT = re.compile(');
  assert.ok(at >= 0, 'blocks_cca.py: REFUSED_TEXT');
  const body = py.slice(at, py.indexOf(', re.IGNORECASE)', at));
  return new RegExp([...body.matchAll(/r'((?:[^'\\]|\\.)*)'/g)].map(m => m[1]).join(''), 'i');
};

export function checkDataQuality(distDir) {
  const DIST = resolve(distDir);
  assert.ok(existsSync(join(DIST, 'index.html')), `${DIST}: not a built site`);
  const read = p => readFileSync(join(DIST, p), 'utf8');
  const srcOf = f => readFileSync(fileURLToPath(new URL(`../../src/data/${f}`, import.meta.url)), 'utf8');
  const src = srcOf(FILE), dcSrc = srcOf(DCF);
  assert.equal(read(`data/${FILE}`), src, `${FILE}: the served copy is the reviewed one`);
  assert.equal(read(`data/${DCF}`), dcSrc, `${DCF}: the served copy is the reviewed one`);
  const D = JSON.parse(src), S = D.shin2022, E = D.eldbeta, Z = D.zuco2;
  const DC = JSON.parse(dcSrc), K = DC['kim2025-beta-range'], M = DC.mind2026, DM = DC.damm, NB = DC.nebula;
  const RELEASES = [D.release_id, DC.release_id];
  assert.equal(D.release_id, 'data-quality-update-20261020', 'the earlier release');
  assert.equal(DC.release_id, 'dataset-checks-update-20261028', 'the dataset checks’ release');
  const leavesOf = j => { const s = new Set(); (function walk(v) { if (typeof v === 'number') s.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(j); return s; };
  const leaves = { [FILE]: leavesOf(D), [DCF]: leavesOf(DC) };
  const arms = Object.fromEntries(S.arms.map(a => [a.arm, a]));
  const chain = Object.fromEntries(S.coverage_chain.map(c => [c.id, c]));
  // Chain counts that no other figure on the page shares: each may print once, in the chain table.
  const distinctive = [...new Set([...S.coverage_chain.map(c => c.count), chain.distinct_runs.closed_windows].filter(x => x >= 100 && x !== chain.recorded_runs.count && x !== E.counts.published_participants))];
  assert.ok(distinctive.length >= 6, 'the chain has its distinctive counts');
  // The page's sections, in order: the dataset-checks file's page order, the one-person lead before its first case.
  const ORDER = DC.placement.page_order.flatMap(s => s === DC.placement.one_person_lead_before ? ['one-person', s] : [s]);
  assert.deepEqual(DC.one_person.cases, ['eldbeta', 'damm', 'nebula'], 'the one-person cases');
  const refused = refusedText();

  // The newest served register file, if any (open-register-<YYYYMMDD>.json), and whether Shin2022's row carries MOABB's
  // catalog counts as its finding.
  const served = readdirSync(join(DIST, 'data')).filter(f => /^open-register-\d{8}\.json$/.test(f)).sort();
  const register = served.length ? JSON.parse(read(`data/${served.at(-1)}`)) : null;
  const catalogFinding = !!register?.entries.find(e => e.id === 'r-site-shin2022')?.findings
    ?.some(f => f.code === 'catalog_differs_from_files' && f.params?.case === 'shin2022');
  if (register?.status === 'frozen') assert.ok(catalogFinding, `${served.at(-1)} is frozen, and r-site-shin2022 carries no catalog_differs_from_files finding`);
  // The paper SingLEM's exposure row on BETA links: the list eldBETA is in.
  const FM = JSON.parse(srcOf('foundation-models-update.json'));
  const singlemCell = FM.results['foundation-models-v9'].pretraining_exposure.cells.find(c => c.model === E.related.model && c.dataset === E.related.dataset);
  assert.ok(singlemCell?.urls?.[0], 'SingLEM’s exposure row on BETA links its source');
  const kimBuilt = existsSync(join(DIST, KIM_PATH, 'index.html'));

  // The page's figures, field by field and in order: what each sentence and cell reads.
  const A = (f, x, file = FILE) => `${file}|${f}|${x}`, N = x => A('count', x), P = x => A('pct2', x);
  const CN = x => A('count', x, DCF), CP = x => A('pct2', x, DCF);
  const withInterval = a => [P(a.participant_mean_balanced_accuracy), P(a.participant_bootstrap_percentile_95[0]), P(a.participant_bootstrap_percentile_95[1])];
  const chainFigs = c => [N(c.count),
    ...(c.by_target ? [N(c.by_target['1']), N(c.by_target['2'])] : c.windows_per_run_by_target ? [N(c.windows_per_run_by_target['1']), N(c.windows_per_run_by_target['2'])] : []),
    ...({ distinct_runs: [N(c.closed_windows)], complete_runs: [N(c.participants)],
          signal_invalid: [N(c.flat_on_all_channels), N(c.flat_on_some_channels), N(c.non_finite_input_windows)],
          signal_valid: [A('pct1raw', c.percent_of_closed_windows), A('pct2raw', c.percent_of_duration_eligible), N(c.participants_with_both_targets)] }[c.id] ?? [])];
  const KR = K.result, MP = M.primary, MS = M.secondary, MPR = M.processing, ND = NB.design;
  const mindPair = p => [CP(p.csp_lda), CP(p.ordinal_lookup), CP(p.majority)];
  const byField = [
    ['the Shin2022 lede', [N(S.scope.participants), N(S.method.training_participants_each_fold), ...withInterval(arms.normalized_spectral_ridge),
      ...withInterval(arms.retrospective_duration_ridge), P(arms.training_prior.participant_mean_balanced_accuracy)]],
    ['the arms caption', [N(S.scope.participants)]],
    ...S.arms.map(a => [`the ${a.arm} row`, [...withInterval(a), P(a.pooled_balanced_accuracy_secondary)]]),
    ...S.coverage_chain.map(c => [`the ${c.id} step`, chainFigs(c)]),
    ['the catalog line', [N(S.catalog.catalog_trial_seconds), N(S.catalog.headers_read)]],
    ['the Kim lede', [CN(K.cohort.participants), CN(K.cohort.blocks), CN(K.cohort.trials), CP(KR.mean_participant_accuracy),
      CP(KR.accuracy_interval_95[0]), CP(KR.accuracy_interval_95[1]), CP(KR.chance)]],
    ['the MIND lede', [CN(MP.record_ids), CN(MP.runs), CN(MP.trials)]],
    ...MP.pairs.map(p => [`the MIND primary ${p.pair} row`, mindPair(p)]),
    ...M.contrasts.map(x => [`the MIND ${x.pair} ${x.control} contrast`, [A('pp2', x.mean_difference, DCF), A('sgn2', x.resampling_range[0], DCF), A('pp2', x.resampling_range[1], DCF)]]),
    ['the MIND secondary lede', [CN(MS.record_ids), CN(MS.runs), CN(MS.trials)]],
    ...MS.pairs.map(p => [`the MIND secondary ${p.pair} row`, mindPair(p)]),
    ...M.coverage.map(s => [`the MIND ${s.id} step`, [CN(s.count), ...(s.record_ids !== undefined ? [CN(s.record_ids)] : []), ...(s.trials !== undefined ? [CN(s.trials)] : [])]]),
    ['the eldBETA lede', [N(E.counts.blocks), N(E.counts.targets), N(E.counts.trials), N(E.counts.non_finite_values_outside_analysed_windows)]],
    ['the eldBETA holds', [N(E.counts.published_participants)]],
    ['the Damm lede', [CN(DM.design.delivered_cues), CN(DM.design.trials_per_held_out_run), CN(DM.variant_directions_audited)]],
    ['the Damm holds', [CN(DM.design.published_participants)]],
    ['the NeBULA lede', [CN(ND.trials), ...ND.assistance_conditions.map(a => CN(ND.trials_by_condition[a])), CN(NB.eeg.channels), CN(NB.eeg.sampling_hz),
      CN(NB.arms.eeg_fits), CN(NB.arms.emg_and_fusion_fits)]],
    ['the method', [N(S.method.folds), N(S.method.training_participants_each_fold), N(S.method.window_samples), N(S.scope.sampling_hz)]],
    ['the Kim method', [CN(K.method.channels), CN(K.method.window_samples), CN(K.method.sampling_hz), CN(K.method.band_hz[0]), CN(K.method.band_hz[1])]],
    ['the MIND method', [CN(MPR.channels), CN(MPR.sampling_hz), CN(MPR.band_hz[0]), CN(MPR.band_hz[1]), CN(MPR.resampled_hz), CN(MPR.window_samples), CN(MPR.csp_components)]],
    ['the intervals', [N(S.scope.participants), N(S.interval.resamples)]],
    ['the Kim interval', [CN(K.cohort.participants), CN(K.interval.resamples)]],
  ];

  let checks = 0;
  const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };
  const pages = {};
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}${PATH}`;
    const html = read(`${pfx}${PATH}index.html`); pages[lang] = html;
    const main = el(html, /<main\b/, where);
    const sec = id => el(main, new RegExp(`<section[^>]*\\sid="${id}"`), where);

    // 1. The page.
    // A Chinese heading carries <wbr> between its phrases (questionPhrases), so spaces are compared away.
    ok(vis(el(main, /<h1\b/, where)).replace(/\s+/g, '') === H1[lang].replace(/\s+/g, ''), `${where}: the h1 is the question`);
    ok(html.includes(`<title>${H1[lang]}`), `${where}: the <title> leads with the question`);
    const ids = [...main.matchAll(/<section[^>]*\sid="([^"]+)"/g)].map(m => m[1]);
    ok(JSON.stringify(ids.filter(i => ORDER.includes(i))) === JSON.stringify(ORDER), `${where}: the sections in the dataset-checks file's order (${ids.join(', ')})`);
    ok(ids.indexOf('methods-and-limits') > ids.indexOf('zuco2'), `${where}: #methods-and-limits after the cases`);
    const shin = sec('shin2022'), kim = sec('kim2025-beta-range'), mind = sec('mind2026'), lead = sec('one-person'), eld = sec('eldbeta');
    const damm = sec('damm'), neb = sec('nebula'), zuco = sec('zuco2'), methods = sec('methods-and-limits');
    ok(vis(el(shin, /<h2\b/, where)) === SHIN_H2[lang], `${where}: Shin2022's question`);
    const answer = el(main, /<section class="short-answer"/, where);
    const answerFigs = [...answer.matchAll(/class="fig">([^<]+)</g)].map(m => m[1]);
    ok(answerFigs.length === 3, `${where}: the short answer states the three arms`);
    const rest = vis(main.replace(answer, ' '));
    for (const f of answerFigs) ok(rest.includes(f), `${where}: "${f}" of the short answer appears below it`);
    const desc = decode(html.match(/<meta name="description" content="([^"]*)"/)[1]);
    ok(desc.length > 40 && desc.length <= 320, `${where}: a one- or two-sentence description (${desc.length})`);
    ok(desc.includes(fmt.pct2(KR.mean_participant_accuracy)) && desc.includes(fmt.pct2(KR.chance)), `${where}: the description gives Kim beta-range's figure and chance`);
    for (const f of [FILE, DCF]) ok(main.includes(`href="/data/${f}"`), `${where}: ${f} is downloadable`);

    // 2. Every figure: a leaf of its export, in its format.
    let figs = 0;
    for (const [, file, f, raw, t] of main.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)) {
      ok(file === FILE || file === DCF, `${where}: a figure from ${file}`);
      ok(leaves[file]?.has(Number(raw)), `${where}: ${raw} is not a value in ${file}`);
      ok(fmt[f] && t === fmt[f](Number(raw)), `${where}: ${raw} printed as "${t}" (${f})`);
      figs++;
    }
    ok(figs >= 120, `${where}: the figures carry data-fig (${figs})`);
    {
      const got = figAttrs(main), want = byField.flatMap(([, l]) => l);
      let at = 0;
      for (const [what, l] of byField) {
        const part = got.slice(at, at + l.length);
        ok(JSON.stringify(part) === JSON.stringify(l), `${where}: ${what} prints ${JSON.stringify(l)}, found ${JSON.stringify(part)} (figure ${at + 1})`);
        at += l.length;
      }
      ok(got.length === want.length, `${where}: ${got.length} figures, ${want.length} named by field`);
    }

    // 3. Shin2022: the arms, the retrospective control set apart, the caveat once.
    const armsTable = el(shin, /<table data-dq-table="arms"/, where);
    ok(/<thead>/.test(armsTable), `${where}: the arms table has a header row`);
    ok(JSON.stringify([...armsTable.matchAll(/data-dq-arm="([^"]+)"/g)].map(m => m[1])) === JSON.stringify(S.arms.map(a => a.arm)), `${where}: the arms in the export's order`);
    for (const a of S.arms) {
      const row = el(armsTable, new RegExp(`<tr data-dq-arm="${a.arm}"`), where);
      for (const x of [a.participant_mean_balanced_accuracy, ...a.participant_bootstrap_percentile_95, a.pooled_balanced_accuracy_secondary])
        ok(row.includes(attr('pct2', x)), `${where}: ${a.arm} prints ${x}`);
    }
    const group = el(armsTable, /<tr class="subhead" data-dq-group="retrospective"/, where);
    ok(RETRO[lang].test(vis(group)) && armsTable.indexOf(group) < armsTable.indexOf('data-dq-arm="retrospective_duration_ridge"')
      && armsTable.indexOf(group) > armsTable.indexOf('data-dq-arm="normalized_spectral_ridge"'), `${where}: the duration control set apart under a retrospective heading`);
    ok(RETRO[lang].test(vis(el(armsTable, /<tr data-dq-arm="retrospective_duration_ridge"/, where))), `${where}: the duration control is labelled retrospective`);
    const caveat = el(shin, /<p class="protocol-note" data-dq-note="shin-caveat"/, where);
    ok(shin.indexOf(caveat) > shin.indexOf(armsTable), `${where}: the caveat beside the arms table`);
    if (lang === 'en') ok(count(vis(main), curly(S.caveat)) === 1, `${where}: the caveat once`);
    else ok(count(vis(main), '分数只覆盖信号有效的时间窗') === 1, `${where}: the caveat once`);
    // That the duration is known only after the trial ends is said once, in the caveat.
    ok(count(vis(main), lang === 'en' ? 'known only after the trial ends' : '要到试次结束后才知道') === 1 && vis(caveat).includes(lang === 'en' ? 'known only after the trial ends' : '要到试次结束后才知道'),
      `${where}: "known only after the trial ends" once, in the caveat`);
    // The coverage chain: once, in its table.
    ok(count(main, 'data-dq-table="chain"') === 1, `${where}: one coverage chain`);
    const chainTable = el(shin, /<table data-dq-table="chain"/, where);
    ok(/<thead>/.test(chainTable), `${where}: the chain table has a header row`);
    ok(JSON.stringify([...chainTable.matchAll(/data-dq-step="([^"]+)"/g)].map(m => m[1])) === JSON.stringify(S.coverage_chain.map(c => c.id)), `${where}: every link of the chain, in order`);
    for (const c of S.coverage_chain) {
      const row = el(chainTable, new RegExp(`<tr data-dq-step="${c.id}"`), where);
      ok(row.includes(attr('count', c.count)), `${where}: ${c.id} prints ${c.count}`);
      if (c.by_target) ok(row.includes(attr('count', c.by_target['1'])) && row.includes(attr('count', c.by_target['2'])), `${where}: ${c.id} by target`);
    }
    ok(chainTable.includes(attr('pct1raw', chain.signal_valid.percent_of_closed_windows)) && chainTable.includes(attr('pct2raw', chain.signal_valid.percent_of_duration_eligible)),
      `${where}: the signal-valid shares`);
    for (const x of distinctive) {
      ok(count(main, `|count|${x}"`) === 1 && count(chainTable, `|count|${x}"`) === 1, `${where}: ${x} prints once, in the chain`);
      ok(!vis(answer).includes(fmt.count(x)) && !desc.includes(fmt.count(x)), `${where}: ${x} stays out of the short answer and description`);
    }
    const catalog = el(shin, /<p class="roadmap-p" data-dq-note="catalog"/, where);
    ok(catalog.includes(attr('count', S.catalog.catalog_trial_seconds)) && catalog.includes(attr('count', S.catalog.headers_read)) && catalog.includes('MaxFeedbackDuration'),
      `${where}: the catalog's trial length is the feedback cap`);
    ok(count(el(shin, /<ol class="rd-rules" data-dq-list="how-checked"/, where), '<li') === S.how_checked.length, `${where}: how it was checked`);
    ok(count(el(shin, /<ul class="rd-rules" data-dq-list="shin-holds"/, where), '<li') === S.holds.length, `${where}: Shin2022's holds`);
    // Consent, ethics and attribution, as the export (A3) states them.
    const credit = el(shin, /<div class="citation-list" data-dq-credit="shin2022"/, where);
    const attribution = el(credit, /<p lang="en" data-dq-attribution="shin2022"/, where);
    ok(decode(vis(attribution)) === S.rights.attribution && S.rights.attribution.endsWith(ENDORSEMENT), `${where}: Shin2022's attribution, ending with the site's sentence`);
    const consent = vis(el(credit, /<article data-dq-consent="shin2022"/, where));
    ok(consent.includes(S.consent_and_ethics.ethics_approval.statement) && consent.includes(S.consent_and_ethics.informed_consent.statement),
      `${where}: Shin2022's ethics and consent statements (originals beside the Chinese)`);
    ok(credit.includes(`href="${S.rights.licenseUrl}"`) && credit.includes(`href="${S.rights.source}"`) && credit.includes(`href="${S.consent_and_ethics.read_from}"`),
      `${where}: licence, record and the statement's source linked`);

    // 4. Kim beta-range: a worked case.
    ok(vis(el(kim, /<h2\b/, where)) === (lang === 'en' ? K.question : '不需要训练的 CCA，在 beta 频段的 40 个频率上能做到多少？'), `${where}: Kim beta-range's question`);
    const kimLede = el(kim, /<p data-dq-note="kim-lede"/, where);
    for (const x of [K.cohort.participants, K.cohort.blocks, K.cohort.trials]) ok(kimLede.includes(attr('count', x, DCF)), `${where}: the Kim lede prints ${x}`);
    for (const x of [KR.mean_participant_accuracy, ...KR.accuracy_interval_95, KR.chance]) ok(kimLede.includes(attr('pct2', x, DCF)), `${where}: the Kim lede prints ${x}`);
    if (lang === 'en') {
      ok(text(kimLede).includes(K.task) && text(kimLede).includes(`Chance is ${fmt.pct2(KR.chance)}, ${K.result.chance_basis}.`), `${where}: the Kim task and its chance level`);
      ok(vis(el(kim, /<p class="roadmap-p" data-dq-note="kim-intake"/, where)) === curly(K.intake.text), `${where}: the Kim intake`);
      for (const c of K.caveats) ok(count(vis(main), curly(c.text)) === 1, `${where}: the Kim caveat ${c.id} once`);
      for (const h of K.how_checked) ok(vis(kim).includes(curly(shown(h.text))), `${where}: the Kim check ${h.id}`);
      ok(count(vis(kim), 'amplitude-dependent models') === 1, `${where}: Kim's amplitude hold named once in its section, on the hold line`);
    }
    ok(count(el(kim, /<ol class="rd-rules" data-dq-list="kim-how-checked"/, where), '<li data-state="pass"') === K.how_checked.length, `${where}: Kim's five checks, each passed`);
    ok(count(el(kim, /<ul class="rd-rules" data-dq-list="kim-caveats"/, where), '<li') === K.caveats.length, `${where}: Kim's eight caveats`);
    ok(count(vis(main), SEALING[lang]) === 1 && vis(kim).includes(SEALING[lang]), `${where}: Kim's sealing is process separation, not blinded labels`);
    ok(kim.includes(`href="/${pfx}releases/#hold-${K.hold.id}"`), `${where}: Kim's hold linked`);
    const kimCredit = el(kim, /<div class="citation-list" data-dq-credit="kim2025-beta-range"/, where);
    ok(decode(vis(el(kimCredit, /<p lang="en" data-dq-attribution="kim2025-beta-range"/, where))) === K.rights.attribution && K.rights.attribution.endsWith(ENDORSEMENT), `${where}: Kim's attribution`);
    ok(kimCredit.includes(`href="${K.rights.source}"`) && kimCredit.includes(`href="${K.rights.licenseUrl}"`) && kimCredit.includes(`href="${K.consent_and_ethics.read_from}"`), `${where}: Kim's record, licence and descriptor linked`);
    const kimConsent = decode(vis(el(kimCredit, /<article data-dq-consent="kim2025-beta-range"/, where)));
    for (const q of [K.consent_and_ethics.ethics_approval.quote, K.consent_and_ethics.informed_consent.quote, K.consent_and_ethics.informed_consent.data_sharing_quote])
      ok(kimConsent.includes(`“${q}”`), `${where}: Kim's statement "${q.slice(0, 40)}" quoted`);
    ok(kim.includes(`href="/${pfx}datasets/kim2025-beta-range/"`) === kimBuilt, `${where}: Kim's dataset page linked while it is built`);
    ok(!/href="(?:\/zh)?\/methods\//.test(kim), `${where}: Kim's case links no method page`);

    // 5. MIND: record IDs, never people.
    ok(vis(el(mind, /<h2\b/, where)) === (lang === 'en' ? M.question : '在一份运动想象数据的发布中，存储的标记能支撑什么？'), `${where}: MIND's question`);
    const primary = el(mind, /<table data-dq-table="mind-primary"/, where), contrasts = el(mind, /<table data-dq-table="mind-contrasts"/, where);
    const secondary = el(mind, /<table data-dq-table="mind-secondary"/, where), coverage = el(mind, /<table data-dq-table="mind-coverage"/, where);
    const licences = el(mind, /<table data-dq-table="mind-licences"/, where);
    for (const t of [primary, contrasts, secondary, coverage, licences]) ok(/<thead>/.test(t) && count(el(t, /<thead>/, where), '<th') >= 3, `${where}: a MIND table with a header row`);
    ok(JSON.stringify([...primary.matchAll(/data-dq-pair="([^"]+)"/g)].map(m => m[1])) === JSON.stringify(MP.pairs.map(p => p.pair)), `${where}: MIND's two stored-code pairs`);
    for (const [t, panel] of [[primary, MP], [secondary, MS]]) for (const p of panel.pairs) {
      const row = el(t, new RegExp(`<tr data-dq-pair="${p.pair}"`), where);
      ok(['csp_lda', 'ordinal_lookup', 'majority'].every(k => row.includes(attr('pct2', p[k], DCF))), `${where}: MIND ${p.pair} prints its arm and both controls`);
    }
    ok(JSON.stringify([...contrasts.matchAll(/data-dq-contrast="([^"]+)"/g)].map(m => m[1])) === JSON.stringify(M.contrasts.map(x => `${x.pair}:${x.control}`)), `${where}: MIND's four contrasts`);
    for (const x of M.contrasts) {
      const p = MP.pairs.find(q => q.pair === x.pair);
      ok(Math.abs(x.mean_difference - (p.csp_lda - p[x.control])) < 1e-12 && x.resampling_range[0] <= x.mean_difference && x.mean_difference <= x.resampling_range[1],
        `${where}: MIND ${x.pair} ${x.control}: the arm less its control, inside its range`);
    }
    const caption = vis(el(contrasts, /<caption\b/, where));
    if (lang === 'en') ok(caption === M.resampling.text && /record-ID resampling range/i.test(vis(el(contrasts, /<thead>/, where))), `${where}: the ranges named as record-ID resampling ranges`);
    else ok(/记录编号重抽样/.test(caption) && /记录编号重抽样范围/.test(vis(el(contrasts, /<thead>/, where))), `${where}: the ranges named as record-ID resampling ranges`);
    ok((vis(mind).match(CI_WORD[lang]) ?? []).length === 1 && (caption.match(CI_WORD[lang]) ?? []).length === 1, `${where}: "confidence interval" only where the ranges are said not to be ones`);
    ok(!/95%/.test(vis(mind)) && !vis(mind).includes(lang === 'en' ? 'bootstrap' : 'bootstrap'), `${where}: no MIND figure is called a 95% or bootstrap interval`);
    ok(!/区间|interval/i.test(vis(secondary)) && figAttrs(secondary).length === MS.pairs.length * 3, `${where}: the secondary panel apart, with no interval`);
    ok(mind.indexOf(secondary) > mind.indexOf(contrasts), `${where}: the secondary panel after the primary panel's contrasts`);
    ok(JSON.stringify([...coverage.matchAll(/data-dq-step="([^"]+)"/g)].map(m => m[1])) === JSON.stringify(M.coverage.map(s => s.id)), `${where}: MIND's coverage, every step`);
    const schedule = vis(el(mind, /<p class="protocol-note" data-dq-note="mind-schedule"/, where));
    if (lang === 'en') ok(schedule === M.schedule.text, `${where}: MIND's schedule facts`);
    for (const s of M.schedule.pairs) ok(schedule.includes(String(s.primary_ids_repeating_one_schedule)) && schedule.includes(String(s.trials_per_schedule)), `${where}: MIND's schedule counts`);
    // A person word only in the record-ID caveat (and the attribution's names, which say nothing of people).
    const recordCaveat = el(mind, /<li data-caveat="record-ids"/, where);
    const mindWords = vis(dropEnglish(mind.replace(recordCaveat, ' ').replace(el(mind, /<div class="citation-list" data-dq-credit="mind2026"/, where), ' ')));
    ok(!PERSON_WORD[lang].test(mindWords), `${where}: MIND speaks of record IDs, not people`);
    PERSON_WORD[lang].lastIndex = 0;
    ok(JSON.stringify([...licences.matchAll(/data-dq-licence="([^"]+)"/g)].map(m => m[1])) === JSON.stringify(M.rights.terms.statements.map(s => s.source)), `${where}: MIND's four licence statements, side by side`);
    for (const s of M.rights.terms.statements) ok(vis(el(licences, new RegExp(`<tr data-dq-licence="${s.source}"`), where)).includes(s.value), `${where}: MIND ${s.source} states ${s.value}`);
    ok(licences.includes(`href="${M.rights.terms.statements[3].url}"`), `${where}: the ScienceDB record page's licence linked`);
    ok(vis(el(mind, /<p class="protocol-note" data-dq-note="mind-terms"/, where)) === (lang === 'en' ? 'ScienceDB’s terms-of-use page was not read. Aggregate values only; no data are redistributed.' : 'ScienceDB 的使用条款页面没有读取。只发布聚合数值，不转发任何数据。'),
      `${where}: ScienceDB's terms-of-use page stated as unread`);
    const mindCredit = el(mind, /<div class="citation-list" data-dq-credit="mind2026"/, where);
    ok(decode(vis(el(mindCredit, /<p lang="en" data-dq-attribution="mind2026"/, where))) === M.rights.attribution, `${where}: MIND's attribution`);
    for (const q of [M.consent_and_ethics.ethics_approval.quote, M.consent_and_ethics.informed_consent.quote]) ok(decode(vis(mindCredit)).includes(`“${q}”`), `${where}: MIND's statement quoted`);
    ok(!/href="[^"]*\/datasets\/mind/.test(main), `${where}: MIND has no dataset page`);
    ok(count(el(mind, /<ul class="rd-rules" data-dq-list="mind-caveats"/, where), '<li') === M.caveats.length - 2, `${where}: MIND's caveats, the terms and ethics ones in its source block`);

    // 6. The one-person sentence once, before eldBETA; eldBETA: counts only.
    const sentence = lang === 'en' ? DC.one_person.sentence : ONE_PERSON_ZH;
    ok(count(vis(main), sentence) === 1 && vis(lead).includes(sentence), `${where}: the one-person sentence once, in its lead`);
    ok(count(vis(main), PERSON_CORE[lang]) === 1 && !vis(main).includes(ELD_REPEAT[lang]), `${where}: eldBETA's own repeat of the one-person sentence is gone`);
    ok(main.indexOf(lead) > main.indexOf(mind) && main.indexOf(lead) < main.indexOf(eld), `${where}: the lead between MIND and eldBETA`);
    for (const x of [E.counts.blocks, E.counts.targets, E.counts.trials, E.counts.non_finite_values_outside_analysed_windows, E.counts.published_participants])
      ok(eld.includes(attr('count', x)), `${where}: eldBETA prints ${x}`);
    ok(!/\|pct\w*\|/.test(eld), `${where}: no percentage in the eldBETA section`);
    for (const held of ['26/63', '7/63', '41.27', '41.3%', '0.4127', '11.11', '11.1%']) ok(!vis(main).includes(held), `${where}: no held eldBETA figure (${held})`);
    ok(!/units? (?:were |are |is )?verified|verified units|单位已核实|单位经过核实/i.test(vis(main)), `${where}: units are never called verified`);
    if (lang === 'en') ok(/header calibration applied/.test(vis(eld)) && /MATLAB epochs were not used/.test(vis(eld)), `${where}: the holds line`);
    else ok(/文件头中的定标/.test(vis(eld)) && /MATLAB 分段/.test(vis(eld)), `${where}: the holds line`);
    const fact = el(eld, /<p class="roadmap-p" data-dq-note="singlem"/, where);
    ok(fact.includes(`href="${SINGLEM[lang]}"`) && /SingLEM/.test(vis(fact)), `${where}: the SingLEM fact line links the exposure rows`);
    ok(fact.includes(`href="${singlemCell.urls[0]}"`) && (lang === 'en' ? /Table I\b/ : /表 I/).test(vis(fact)), `${where}: the SingLEM fact line links the paper's list, Table I`);
    ok(eld.includes(`href="/${pfx}releases/#hold-eldbeta-one-participant-score"`), `${where}: the eldBETA hold linked`);
    ok(decode(vis(el(eld, /<p lang="en" data-dq-attribution="eldbeta"/, where))) === E.rights.attribution && E.rights.attribution.endsWith(ENDORSEMENT), `${where}: eldBETA's attribution`);

    // 7. Damm and NeBULA: whole counts, no score, no comparison.
    for (const [name, s, x] of [['Damm', damm, DM], ['NeBULA', neb, NB]]) {
      const fs = [...s.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"/g)];
      ok(fs.length > 0 && fs.every(([, file, f, raw]) => file === DCF && f === 'count' && Number.isInteger(Number(raw))), `${where}: ${name} prints whole counts only`);
      const words = vis(dropEnglish(s));
      ok(!/%/.test(words) && !COMPARE[lang].test(words), `${where}: ${name} carries no score and no comparison (${(words.match(COMPARE[lang]) ?? [''])[0]})`);
      ok(s.includes(`href="/${pfx}releases/#hold-${x.held.id}"`), `${where}: ${name}'s hold linked`);
      ok(decode(vis(el(s, new RegExp(`<p lang="en" data-dq-attribution="${x.id}"`), where))) === x.rights.attribution && x.rights.attribution.endsWith(ENDORSEMENT), `${where}: ${name}'s attribution`);
      ok(s.includes(`href="${x.rights.source}"`) && s.includes(`href="${x.consent_and_ethics.read_from}"`), `${where}: ${name}'s record and the statement's source linked`);
    }
    const dammLede = el(damm, /<p data-dq-note="damm-lede"/, where);
    for (const v of [DM.design.delivered_cues, DM.design.trials_per_held_out_run, DM.variant_directions_audited]) ok(dammLede.includes(attr('count', v, DCF)), `${where}: the Damm lede prints ${v}`);
    ok(count(el(damm, /<ul class="rd-rules" data-dq-list="damm-variants"/, where), '<li') === DM.variants.length, `${where}: Damm's eight variants and controls`);
    ok(count(el(damm, /<ul class="rd-rules" data-dq-list="damm-holds"/, where), '<li') === DM.holds.length && damm.includes(attr('count', DM.design.published_participants, DCF)), `${where}: Damm's holds`);
    if (lang === 'en') {
      ok(vis(el(damm, /<p class="roadmap-p" data-dq-note="damm-files"/, where)) === curly(DM.files.text), `${where}: Damm's file and timing facts`);
      ok(vis(damm).includes(DM.rights.terms.license_file_note) && vis(damm).includes(DM.consent_and_ethics.gaps[0].note), `${where}: Damm's LICENSE gap and consent gap`);
    }
    ok(vis(damm).includes(DM.consent_and_ethics.ethics_approval.approval_number), `${where}: Damm's ethics approval number`);
    const nebLede = el(neb, /<p data-dq-note="nebula-lede"/, where);
    for (const v of [ND.trials, NB.eeg.channels, NB.eeg.sampling_hz]) ok(nebLede.includes(attr('count', v, DCF)), `${where}: the NeBULA lede prints ${v}`);
    const counts = vis(el(neb, /<p class="roadmap-p" data-dq-note="nebula-counts"/, where));
    if (lang === 'en') ok(counts.startsWith(ND.participant_counts.text), `${where}: NeBULA's participant counts as the export states them`);
    else ok(counts.startsWith('论文与 Figshare 记录的说明写的是 40 名被试；记录中的文件有 39 个被试压缩包，MOABB 列出的是 39 名。'), `${where}: NeBULA's participant counts as the export states them`);
    if (lang === 'en') ok(counts.endsWith(shown(ND.task_line)) && !/open register keeps/.test(vis(main)), `${where}: NeBULA's task line says what MOABB's catalog lists, not what the register row does not print`);
    else ok(counts.endsWith('MOABB 的目录把这个数据集列在运动想象之下。'), `${where}: NeBULA's task line in Chinese`);
    const pc = ND.participant_counts;
    ok([pc.paper_and_record_description, pc.participant_archives_in_record, pc.moabb_catalog].join() === [...counts.matchAll(/\d+/g)].slice(0, 3).map(m => Number(m[0])).join(), `${where}: NeBULA's three participant counts, in the export's order`);
    ok(count(el(neb, /<ul class="rd-rules" data-dq-list="nebula-eeg-arms"/, where), '<li') === NB.arms.eeg.length
      && count(el(neb, /<ul class="rd-rules" data-dq-list="nebula-emg-arms"/, where), '<li') === NB.arms.emg_and_fusion.length, `${where}: NeBULA's arms run`);
    ok(count(el(neb, /<ul class="rd-rules" data-dq-list="nebula-files"/, where), '<li') === NB.file_facts.text.length
      && count(el(neb, /<ul class="rd-rules" data-dq-list="nebula-holds"/, where), '<li') === NB.holds.length, `${where}: NeBULA's file facts and holds`);
    if (lang === 'en') for (const t of [...NB.file_facts.text, ...NB.holds, NB.rights.terms.zenodo_13627307.text]) ok(vis(neb).includes(curly(t)), `${where}: NeBULA: "${t.slice(0, 40)}"`);
    ok(!/href="[^"]*13627307/.test(html) && !/href="[^"]*zenodo\.org\/records?\/13627307/.test(html), `${where}: the Zenodo id NeBULA's files name is never linked`);

    // 8. ZuCo 2.0: no figure, no digit outside the dataset's name.
    ok(!zuco.includes('data-fig'), `${where}: no figure in the ZuCo 2.0 case`);
    ok(!/\d/.test(vis(zuco).split('ZuCo 2.0').join(' ')), `${where}: no digit in the ZuCo 2.0 case outside its name`);
    ok(zuco.includes(`href="/${pfx}releases/#hold-zuco2-converted-run-timing"`) && zuco.includes(`href="/${pfx}${PATH}#zuco2-source"`), `${where}: the ZuCo 2.0 hold and its source linked`);
    ok(methods.includes('id="zuco2-source"') && vis(methods).includes(Z.source.licence_as_stated) && vis(methods).includes(Z.source.accession),
      `${where}: ZuCo 2.0's stated licence and record, outside its case`);

    // 9. The hold reasons stay on /releases/#holds.
    for (const h of DC.holds) ok(!vis(main).includes(curly(h.reason)) && !vis(main).includes(h.reason), `${where}: the reason of ${h.id} is not printed`);
    if (lang === 'en') ok(!/one-person rule|owner’s decision/.test(vis(main.replace(answer, ' '))), `${where}: the one-person rule is not cited as a reason`);

    // 10. The open register, guarded on its file being served and its page built; MOABB's counts named on Shin2022's row
    // only while that row carries them.
    const regLinks = [...main.matchAll(/href="([^"]*\/datasets\/register\/[^"]*)"/g)].map(m => m[1]);
    const regPagePath = `${pfx}datasets/register/index.html`, regPage = existsSync(join(DIST, regPagePath)) ? read(regPagePath) : null;
    if (register && regPage) {
      const listed = [...el(main, /<ul class="rd-rules" data-dq-list="register"/, where).matchAll(/data-dq-row="([^"]+)"/g)].map(m => m[1]);
      ok(JSON.stringify(listed) === JSON.stringify(CASE_ROWS), `${where}: every case's register row, in page order`);
      for (const id of CASE_ROWS) {
        ok(regLinks.includes(`/${pfx}datasets/register/#${id}`), `${where}: links its register row ${id}`);
        const row = register.entries.find(e => e.id === id);
        ok(row && row.ladder === 'dataset', `${served.at(-1)}: ${id} is a dataset row`);
        ok(new RegExp(`\\sid="${id}"`).test(regPage), `/${regPagePath}: the anchor #${id} exists`);
        ok(main.includes(`id="${row.links.case.split('#')[1]}"`), `${where}: ${id}'s case link lands on a section here`);
      }
      ok(regLinks.every(h => /^\/(?:zh\/)?datasets\/register\/(?:#r-[a-z0-9-]+)?$/.test(h)), `${where}: register links by opaque id only`);
    } else ok(regLinks.length === 0, `${where}: no register link while ${register ? 'the register page is not built' : 'no register file is served'}`);
    const catalogClause = el(shin, /<p class="roadmap-p" data-dq-note="catalog"/, where).includes('data-dq-part="catalog-register"');
    ok(catalogClause === (catalogFinding && !!register && !!regPage),
      `${where}: the catalog line names Shin2022's register row if and only if the row carries MOABB's counts (${catalogFinding ? 'it does' : 'it does not'}) and the register page is built (${regPage ? 'it is' : 'it is not'})`);
    const listItems = sel => [...el(methods, sel, where).matchAll(/<li>([\s\S]*?)<\/li>/g)].map(m => vis(m[1]));
    const notPub = listItems(/<ul class="rd-rules" data-dq-list="not-published"/), dcNotPub = listItems(/<ul class="rd-rules" data-dq-list="dc-not-published"/);
    ok(notPub.length === D.not_published.length && dcNotPub.length === DC.not_published.length, `${where}: every item of what is not published, from both files`);
    ok(![...notPub, ...dcNotPub].some(x => (lang === 'en' ? /owner|one-person/ : /所有者|单人/).test(x)), `${where}: the held scores' reason stays with the lead line`);
    const moabb = notPub.filter(x => x.startsWith('MOABB'));
    ok(moabb.length === 1 && REGISTER_NAMED[lang].test(moabb[0]) === catalogFinding,
      `${where}: the not-published MOABB line names the register file if and only if Shin2022's row carries the counts`);
    ok(/href="(?:\/zh)?\/data-use\/#sources-dataset-checks"/.test(main), `${where}: the dataset checks' sources on /data-use/ linked`);

    // 11. Tables, CSP, hreflang, the cite block.
    for (const [, t] of main.matchAll(/(<table\b[\s\S]*?<\/table>)/g)) ok(/<thead>/.test(t), `${where}: every table has a <thead>`);
    for (const [, d] of main.matchAll(/(<details\b[\s\S]*?<\/details>)/g))
      for (const [, t] of d.matchAll(/(<table\b[\s\S]*?<\/table>)/g)) ok(count(el(t, /<thead>/, where), '<th') >= 4, `${where}: a table in <details> has four or more columns`);
    ok(!/<script(?![^>]*\bsrc=)(?![^>]*\btype="application\/(?:ld\+)?json")[^>]*>/.test(html), `${where}: no inline script`);
    ok(!/\sstyle="|<style[\s>]|\son[a-z]+=/i.test(html), `${where}: no inline style or handler`);
    ok(html.includes(`hreflang="zh-Hans" href="https://bci.report/zh/${PATH}"`) && html.includes(`hreflang="en" href="https://bci.report/${PATH}"`), `${where}: reciprocal hreflang`);
    const named = el(main, /<section class="cite-page"/, where).match(/data-releases="([^"]+)"/)[1].split(' ');
    ok(JSON.stringify(sorted(named)) === JSON.stringify(sorted(RELEASES)) && named[0] === DC.release_id, `${where}: the cite block names the two releases, the newest first (${named.join(' ')})`);

    // 12. Words.
    const md = `${pfx}${PATH}index.md`;
    const all = html + (existsSync(join(DIST, md)) ? read(md) : '');
    // The private names are spelled in pieces, so this file carries none of them whole.
    for (const bad of ['/Us' + 'ers/', '/ho' + 'me/', '/Vol' + 'umes/', '/m' + 'nt/', '/ro' + 'ot/', '/pri' + 'vate/', 'tr' + 'x50', 'Ga' + 'l4', 'BCI' + '_Arena', 'ICLR 2027', 'OpenReview'])
      ok(!all.includes(bad), `${where}: "${bad}" never appears`);
    ok(!/\btr[x]\d*\b/i.test(vis(all)), `${where}: no host label`);
    ok(!/(?<![\d.])55 ?%/.test(vis(all)), `${where}: no 55%`);
    // REFUSED_TEXT also refuses a bare 55%, which a printed figure's decimals (52.55%) would match: the figures, each a
    // leaf held to its field above, are set aside first.
    ok(!refused.test(unfig(all, main)), `${where}: nothing blocks_cca.REFUSED_TEXT refuses`);
    ok(!new RegExp(`\\b${'tw' + 'u'}\\b`).test(all), `${where}: no private user name`);
    // The page's own words: the other questions' cards in the switcher are theirs.
    const own = main.replace(el(main, /<nav class="topic-switcher"/, where), ' ');
    const words = vis(own);
    ok(!/\bsubmission\b|投稿/i.test(words), `${where}: no submission reference`);
    ok(!/(?<![\w.\/#-])(?<!Figshare(?: record)?(?: \d+)? )v\d+(?![\w.]|-\d)|\brelease v\d/.test(words), `${where}: no version label`);
    ok(!(lang === 'zh' ? /新增|本次更新|这次更新|本次发布|最新发布|更新于/ : /\b(?:new|newly|added|updated|this update|this release)\b/i).test(words), `${where}: no update wording`);
    // Kim's file checks include a matrix rank check, the export's own words.
    ok(!(lang === 'zh' ? /最佳|最好|胜出|排名|第一名/ : /\b(?:best|worst|top|winner|leader|outperform\w*|beats?|ranks?|ranked|ranking)\b/i).test(words.split('finite-value and rank checks').join(' ')), `${where}: no ranking word`);
    // Kim's sealing sentence is the export's own and keeps its ", not"; no other.
    if (lang === 'en') ok(!/, not\b/.test(words.split(SEALING.en).join(' ')), `${where}: no ", not" hedge beyond Kim's sealing sentence`);
    if (lang === 'zh') {
      const zhText = vis(dropEnglish(own));
      for (const bad of REJECTED_ZH) ok(!zhText.includes(bad), `${where}: "${bad}" is a rejected rendering`);
      ok(!/[一-鿿\d]\.<\/p>/.test(dropEnglish(main)), `${where}: no ASCII full stop after Chinese`);
    }

    // 13. The Markdown copy.
    if (existsSync(join(DIST, md))) {
      const copy = read(md);
      for (const [, v] of main.matchAll(/class="(?:metric|num|fig)">([^<]+)</g)) ok(copy.includes(decode(v)), `${md}: figure "${v}"`);
      for (const f of figAttrs(main)) { const [file, k, raw] = f.split('|'); ok(copy.includes(fmt[k](Number(raw))), `${md}: ${file} ${raw}`); }
    }
  }
  // English and Chinese print the same figures.
  const main = lang => el(pages[lang], /<main\b/, lang);
  assert.deepEqual(figAttrs(main('zh')), figAttrs(main('en')), 'the same figures in English and Chinese, in the same order'); checks++;
  const answerFigs = lang => [...el(main(lang), /<section class="short-answer"/, lang).matchAll(/class="fig">([^<]+)</g)].map(m => m[1]);
  assert.deepEqual(answerFigs('zh'), answerFigs('en'), 'the same short-answer figures in English and Chinese'); checks++;

  // 14. Kim beta-range's dataset page.
  let kimFigs = 0;
  if (kimBuilt) {
    const kimPages = {};
    for (const lang of ['en', 'zh']) {
      const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}${KIM_PATH}`;
      const html = read(`${pfx}${KIM_PATH}index.html`), page = el(html, /<main\b/, where); kimPages[lang] = page;
      // Its subtitle is its own profile's summary (entity-profiles.json), never the datasets index's generic line.
      const profile = JSON.parse(readFileSync(fileURLToPath(new URL('../../src/data/entity-profiles.json', import.meta.url)), 'utf8')).datasets['kim2025-beta-range'];
      const dek = html.match(/<p class="topic-dek">([\s\S]*?)<\/p>/)?.[1] ?? '';
      ok(profile && decode(vis(dek)) === profile[lang === 'zh' ? 'summary_zh' : 'summary_en'], `${where}: its subtitle is its profile's summary`);
      ok(count(page, '<section class="entity-profile"') === 1, `${where}: one block of names and sources`);
      const facts = el(page, /<section class="entity-profile"[^>]*data-dataset-facts="kim2025-beta-range"/, where);
      ok(K.aliases.every(a => vis(facts).includes(a)), `${where}: its three names`);
      ok(JSON.stringify(figAttrs(facts)) === JSON.stringify([K.cohort.participants, K.cohort.blocks, K.cohort.trials].map(CN)), `${where}: its cohort, from the export`);
      if (lang === 'en') ok(vis(facts).includes(K.rights.task) && vis(facts).includes(curly(K.intake.text)), `${where}: its task and intake facts`);
      const pointer = el(page, /<p class="citation-note" id="cca-baseline"/, where);
      ok(pointer.includes(`href="/${pfx}${PATH}#kim2025-beta-range"`) && figAttrs(pointer).length === 0, `${where}: a figure-free pointer to its worked case`);
      ok(!/href="(?:\/zh)?\/methods\/[^"#]+\//.test(page), `${where}: no method page linked`);
      const rights = el(page, /<article data-rights-note="kim2025-beta-range"/, where);
      for (const q of [K.consent_and_ethics.ethics_approval.quote, K.consent_and_ethics.informed_consent.quote, K.consent_and_ethics.informed_consent.data_sharing_quote])
        ok(decode(vis(rights)).includes(`“${q}”`), `${where}: "${q.slice(0, 40)}" quoted`);
      ok(rights.includes(`href="${K.consent_and_ethics.read_from}"`) && page.includes(`href="${K.rights.licenseUrl}"`) && page.includes(`href="${K.rights.source}"`), `${where}: descriptor, licence and record linked`);
      if (register) ok(page.includes(`href="/${pfx}datasets/register/#r-site-kim2025-beta-range"`), `${where}: its register row linked`);
      for (const [, file, f, raw, t] of page.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)) {
        ok(file === DCF && leaves[DCF].has(Number(raw)) && fmt[f] && t === fmt[f](Number(raw)), `${where}: ${file} ${raw} printed as "${t}"`);
        kimFigs++;
      }
      ok(page.includes(attr('pct2', KR.mean_participant_accuracy, DCF)), `${where}: the CCA baseline's figure`);
      ok(el(page, /<section class="cite-page"/, where).match(/data-releases="([^"]+)"/)[1] === DC.release_id, `${where}: the cite block names the dataset checks only`);
      const all = html + (existsSync(join(DIST, `${pfx}${KIM_PATH}index.md`)) ? read(`${pfx}${KIM_PATH}index.md`) : '');
      for (const bad of ['/Us' + 'ers/', '/ho' + 'me/', '/m' + 'nt/', 'tr' + 'x50', 'ICLR 2027']) ok(!all.includes(bad), `${where}: "${bad}" never appears`);
      ok(!refused.test(unfig(all, page)) && !/(?<![\d.])55 ?%/.test(vis(all)), `${where}: nothing blocks_cca.REFUSED_TEXT refuses, no 55%`);
      if (lang === 'zh') {
        const zhText = vis(dropEnglish(page));
        for (const bad of REJECTED_ZH) ok(!zhText.includes(bad), `${where}: "${bad}" is a rejected rendering`);
      }
    }
    assert.deepEqual(figAttrs(kimPages.zh), figAttrs(kimPages.en), `/${KIM_PATH}: the same figures in English and Chinese`); checks++;
  }
  const regPageBuilt = existsSync(join(DIST, 'datasets/register/index.html'));
  return { checks, figures: figAttrs(main('en')).length, kimFigs, kimBuilt, register: register ? { file: served.at(-1), page: regPageBuilt, finding: catalogFinding } : null };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/data-quality.mjs <build dir>'); process.exit(2); }
  const { checks, figures, kimFigs, kimBuilt, register } = checkDataQuality(dir);
  console.log(`PASS: data quality — /topics/data-quality/ in both languages, ${checks} checks: ${figures} figures per page, every one a leaf of ${FILE} or ${DCF} in its format, held to its field and the same in English and Chinese; the seven sections in the dataset-checks file's order; Shin2022's three arms with the duration control set apart as retrospective, the caveat once beside them, the coverage chain once in its table, the catalog line, the checks, holds, consent and ethics; Kim beta-range's CCA baseline with its intake, five checks (sealing as process separation), eight caveats once, its hold and rights; MIND on record IDs with both controls, four contrasts with record-ID resampling ranges named as such, the schedule facts, the secondary panel apart with no interval, its coverage and four licence statements side by side; the one-person sentence once, before eldBETA, Damm and NeBULA, which carry whole counts, file facts and linked holds and no score; NeBULA's participant counts as stated, its Zenodo id never linked; ZuCo 2.0 with no figure; no hold reason printed; ${!register ? 'no register link (no register file served)' : register.page ? `each case linked to its row in ${register.file}` : `no register link (${register.file} served, the register page not built)`}; ${register?.finding ? 'MOABB’s counts named as findings on Shin2022’s register row, which carries them' : 'MOABB’s counts not said to be on Shin2022’s register row, which does not carry them'}; ${kimBuilt ? `/datasets/kim2025-beta-range/ with its names, cohort, pointer, ethics and consent and register row, no method link (${kimFigs} figures in both languages)` : 'Kim beta-range’s page not built'}; <thead> everywhere, CSP, hreflang, the cite block naming both releases, the Markdown copy, and no private path, commenter, submission reference, version label, update or ranking word.`);
}
