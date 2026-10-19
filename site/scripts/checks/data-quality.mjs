// What do the files show once a public EEG dataset is checked end to end? (release data-quality-update-20261020, owner
// decisions D1 and D2): /topics/data-quality/ in both languages, checked in a built site.
//
//   node scripts/checks/data-quality.mjs <build dir>        (or import { checkDataQuality } and pass the dir)
//
// What it holds, in both languages:
//  1. the page: its question as the h1 and the <title>, its sections #shin2022, #eldbeta, #zuco2 and #methods-and-limits,
//     Shin2022's question as its h2; the short answer states figures that the page shows again below it;
//  2. every figure is a leaf of data-quality-update.json under that file's name, printed in its format, and the page's
//     figures, in order, are the named fields each sentence and table cell reads (the lede, the arms, the chain, the
//     catalog line, eldBETA's counts, the method and the intervals); English and Chinese print the same figures; the
//     served file is the reviewed one, byte for byte;
//  3. Shin2022: the three arms in the export's order with mean, interval and pooled value; the duration control
//     labelled retrospective and set apart under its own heading row; the caveat once, beside the table; the coverage
//     chain once, in its table, every link a figure and none of its distinctive counts anywhere else (the short answer
//     and description included); the catalog line; the six checks and seven holds; consent and ethics as the A3 record
//     states them; the attribution ending "Derived analysis by BCI Report; not endorsed by the authors.";
//  4. eldBETA: counts only (blocks, targets, trials, non-finite values), no score and no percentage in its section,
//     no held figure anywhere; "header calibration", never "units verified"; the holds line; the SingLEM fact line
//     linking the paper's list (the exposure row's own source) and the existing exposure rows; its hold linked;
//  5. ZuCo 2.0: its section prints no figure and no digit outside the dataset's name; its hold linked;
//  6. the open register: each case links its row (/datasets/register/#r-site-…) only while a register file is served
//     and the register page is built, each row a dataset row of the newest served file and an anchor on that page;
//     otherwise no link to the register. The catalog line names Shin2022's register row, and the not-published list
//     the register file, if and only if that row carries MOABB's counts (catalog_differs_from_files, case shin2022);
//     a frozen register without that finding fails;
//  7. every table has a <thead>, a table inside <details> has four or more columns; no inline script, style attribute
//     or handler; hreflang reciprocal; the cite block names this release only;
//  8. no private path, no ICLR 2027, OpenReview or submission reference, no "55%", no version label or update word, no
//     ranking word, no ", not" hedge in the English; no rejected Chinese rendering, no ASCII full stop after Chinese;
//  9. the Markdown copy carries every figure the page marks.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { strict as assert } from 'node:assert';
import { fileURLToPath, pathToFileURL } from 'node:url';

const FILE = 'data-quality-update.json';
const PATH = 'topics/data-quality/';
const RELEASE = 'data-quality-update-20261020';
const H1 = { en: 'What do the files show once a public EEG dataset is checked end to end?', zh: '把公开 EEG 数据集从头到尾核一遍，文件里能看到什么？' };
const SHIN_H2 = { en: 'What survives a participant-held-out check?', zh: '整名被试留出后，还剩下什么？' };
const ENDORSEMENT = 'Derived analysis by BCI Report; not endorsed by the authors.';
const RETRO = { en: /Retrospective/, zh: /回溯/ };
const SINGLEM = { en: '/methods/singlem/#pretraining-exposure', zh: '/zh/methods/singlem/#pretraining-exposure' };
const CASE_ROWS = ['r-site-shin2022', 'r-site-eldbeta', 'r-site-zuco2'];
const REGISTER_NAMED = { en: /open register/, zh: /开放登记册/ };
// Glossary renderings the site rejects (check-workbench.mjs `rejected`), the ones this page could reach.
const REJECTED_ZH = ['参与者', '受试者', '读出头', '区块', '谱岭回归', '暴露', '个百分点', '源数据'];

const fmt = {
  pct2: r => (r * 100).toFixed(2) + '%',
  pct1raw: r => r.toFixed(1) + '%',
  pct2raw: r => r.toFixed(2) + '%',
  count: r => r.toLocaleString('en-US'),
};
const decode = s => s.replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d))).replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const vis = h => decode(h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
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
const count = (h, s) => h.split(s).length - 1;
// Elements in English inside a Chinese page (attributions, originals beside the Chinese, titles).
const dropEnglish = h => { let out = h, m; const re = /<(\w+)\b[^>]*\slang="en"[^>]*>/g;
  while ((m = re.exec(out))) { const end = spanEnd(out, m.index); out = out.slice(0, m.index) + ' ' + out.slice(end); re.lastIndex = m.index; }
  return out; };
const curly = s => s.replace(/(\w)'(?=\w)/g, '$1’');

export function checkDataQuality(distDir) {
  const DIST = resolve(distDir);
  assert.ok(existsSync(join(DIST, 'index.html')), `${DIST}: not a built site`);
  const read = p => readFileSync(join(DIST, p), 'utf8');
  const src = readFileSync(fileURLToPath(new URL(`../../src/data/${FILE}`, import.meta.url)), 'utf8');
  assert.equal(read(`data/${FILE}`), src, `${FILE}: the served copy is the reviewed one`);
  const D = JSON.parse(src), S = D.shin2022, E = D.eldbeta, Z = D.zuco2;
  assert.equal(D.release_id, RELEASE, 'the release');
  const leaves = new Set(); (function walk(v) { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(D);
  const arms = Object.fromEntries(S.arms.map(a => [a.arm, a]));
  const chain = Object.fromEntries(S.coverage_chain.map(c => [c.id, c]));
  // Chain counts that no other figure on the page shares: each may print once, in the chain table.
  const distinctive = [...new Set([...S.coverage_chain.map(c => c.count), chain.distinct_runs.closed_windows].filter(x => x >= 100 && x !== chain.recorded_runs.count && x !== E.counts.published_participants))];
  assert.ok(distinctive.length >= 6, 'the chain has its distinctive counts');

  // The newest served register file, if any (open-register-<YYYYMMDD>.json), and whether Shin2022's row carries MOABB's
  // catalog counts as its finding.
  const served = readdirSync(join(DIST, 'data')).filter(f => /^open-register-\d{8}\.json$/.test(f)).sort();
  const register = served.length ? JSON.parse(read(`data/${served.at(-1)}`)) : null;
  const catalogFinding = !!register?.entries.find(e => e.id === 'r-site-shin2022')?.findings
    ?.some(f => f.code === 'catalog_differs_from_files' && f.params?.case === 'shin2022');
  if (register?.status === 'frozen') assert.ok(catalogFinding, `${served.at(-1)} is frozen, and r-site-shin2022 carries no catalog_differs_from_files finding`);
  // The paper SingLEM's exposure row on BETA links: the list eldBETA is in.
  const FM = JSON.parse(readFileSync(fileURLToPath(new URL('../../src/data/foundation-models-update.json', import.meta.url)), 'utf8'));
  const singlemCell = FM.results['foundation-models-v9'].pretraining_exposure.cells.find(c => c.model === E.related.model && c.dataset === E.related.dataset);
  assert.ok(singlemCell?.urls?.[0], 'SingLEM’s exposure row on BETA links its source');

  // The page's figures, field by field and in order: what each sentence and cell reads.
  const A = (f, x) => `${FILE}|${f}|${x}`, N = x => A('count', x), P = x => A('pct2', x);
  const withInterval = a => [P(a.participant_mean_balanced_accuracy), P(a.participant_bootstrap_percentile_95[0]), P(a.participant_bootstrap_percentile_95[1])];
  const chainFigs = c => [N(c.count),
    ...(c.by_target ? [N(c.by_target['1']), N(c.by_target['2'])] : c.windows_per_run_by_target ? [N(c.windows_per_run_by_target['1']), N(c.windows_per_run_by_target['2'])] : []),
    ...({ distinct_runs: [N(c.closed_windows)], complete_runs: [N(c.participants)],
          signal_invalid: [N(c.flat_on_all_channels), N(c.flat_on_some_channels), N(c.non_finite_input_windows)],
          signal_valid: [A('pct1raw', c.percent_of_closed_windows), A('pct2raw', c.percent_of_duration_eligible), N(c.participants_with_both_targets)] }[c.id] ?? [])];
  const byField = [
    ['the Shin2022 lede', [N(S.scope.participants), N(S.method.training_participants_each_fold), ...withInterval(arms.normalized_spectral_ridge),
      ...withInterval(arms.retrospective_duration_ridge), P(arms.training_prior.participant_mean_balanced_accuracy)]],
    ['the arms caption', [N(S.scope.participants)]],
    ...S.arms.map(a => [`the ${a.arm} row`, [...withInterval(a), P(a.pooled_balanced_accuracy_secondary)]]),
    ...S.coverage_chain.map(c => [`the ${c.id} step`, chainFigs(c)]),
    ['the catalog line', [N(S.catalog.catalog_trial_seconds), N(S.catalog.headers_read)]],
    ['the eldBETA lede', [N(E.counts.blocks), N(E.counts.targets), N(E.counts.trials), N(E.counts.non_finite_values_outside_analysed_windows)]],
    ['the eldBETA holds', [N(E.counts.published_participants)]],
    ['the method', [N(S.method.folds), N(S.method.training_participants_each_fold), N(S.method.window_samples), N(S.scope.sampling_hz)]],
    ['the intervals', [N(S.scope.participants), N(S.interval.resamples)]],
  ];

  let checks = 0;
  const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };
  const pages = {};
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}${PATH}`;
    const html = read(`${pfx}${PATH}index.html`); pages[lang] = html;
    const main = el(html, /<main\b/, where);

    // 1. The page.
    // A Chinese heading carries <wbr> between its phrases (questionPhrases), so spaces are compared away.
    ok(vis(el(main, /<h1\b/, where)).replace(/\s+/g, '') === H1[lang].replace(/\s+/g, ''), `${where}: the h1 is the question`);
    ok(html.includes(`<title>${H1[lang]}`), `${where}: the <title> leads with the question`);
    for (const id of ['shin2022', 'eldbeta', 'zuco2', 'methods-and-limits'])
      ok(new RegExp(`<section[^>]*\\sid="${id}"`).test(main), `${where}: #${id}`);
    const shin = el(main, /<section[^>]*\sid="shin2022"/, where), eld = el(main, /<section[^>]*\sid="eldbeta"/, where);
    const zuco = el(main, /<section[^>]*\sid="zuco2"/, where), methods = el(main, /<section[^>]*\sid="methods-and-limits"/, where);
    ok(vis(el(shin, /<h2\b/, where)) === SHIN_H2[lang], `${where}: Shin2022's question`);
    const answer = el(main, /<section class="short-answer"/, where);
    const answerFigs = [...answer.matchAll(/class="fig">([^<]+)</g)].map(m => m[1]);
    ok(answerFigs.length === 3, `${where}: the short answer states the three arms`);
    const rest = vis(main.replace(answer, ' '));
    for (const f of answerFigs) ok(rest.includes(f), `${where}: "${f}" of the short answer appears below it`);
    const desc = decode(html.match(/<meta name="description" content="([^"]*)"/)[1]);
    ok(desc.length > 40 && desc.length <= 320, `${where}: a one- or two-sentence description (${desc.length})`);

    // 2. Every figure: a leaf of the export, in its format.
    let figs = 0;
    for (const [, file, f, raw, text] of main.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)) {
      ok(file === FILE, `${where}: a figure from ${file}`);
      ok(leaves.has(Number(raw)), `${where}: ${raw} is not a value in ${FILE}`);
      ok(fmt[f] && text === fmt[f](Number(raw)), `${where}: ${raw} printed as "${text}" (${f})`);
      figs++;
    }
    ok(figs >= 60, `${where}: the figures carry data-fig (${figs})`);
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

    // 4. eldBETA: counts only.
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

    // 5. ZuCo 2.0: no figure, no digit outside the dataset's name.
    ok(!zuco.includes('data-fig'), `${where}: no figure in the ZuCo 2.0 case`);
    ok(!/\d/.test(vis(zuco).split('ZuCo 2.0').join(' ')), `${where}: no digit in the ZuCo 2.0 case outside its name`);
    ok(zuco.includes(`href="/${pfx}releases/#hold-zuco2-converted-run-timing"`) && zuco.includes(`href="/${pfx}${PATH}#zuco2-source"`), `${where}: the ZuCo 2.0 hold and its source linked`);
    ok(methods.includes('id="zuco2-source"') && vis(methods).includes(Z.source.licence_as_stated) && vis(methods).includes(Z.source.accession),
      `${where}: ZuCo 2.0's stated licence and record, outside its case`);

    // 6. The open register, guarded on its file being served and its page built; MOABB's counts named on Shin2022's row
    // only while that row carries them.
    const regLinks = [...main.matchAll(/href="([^"]*\/datasets\/register\/[^"]*)"/g)].map(m => m[1]);
    const regPagePath = `${pfx}datasets/register/index.html`, regPage = existsSync(join(DIST, regPagePath)) ? read(regPagePath) : null;
    if (register && regPage) {
      for (const id of CASE_ROWS) {
        ok(regLinks.includes(`/${pfx}datasets/register/#${id}`), `${where}: links its register row ${id}`);
        const row = register.entries.find(e => e.id === id);
        ok(row && row.ladder === 'dataset', `${served.at(-1)}: ${id} is a dataset row`);
        ok(new RegExp(`\\sid="${id}"`).test(regPage), `/${regPagePath}: the anchor #${id} exists`);
      }
      ok(regLinks.every(h => /^\/(?:zh\/)?datasets\/register\/(?:#r-[a-z0-9-]+)?$/.test(h)), `${where}: register links by opaque id only`);
    } else ok(regLinks.length === 0, `${where}: no register link while ${register ? 'the register page is not built' : 'no register file is served'}`);
    const catalogClause = el(shin, /<p class="roadmap-p" data-dq-note="catalog"/, where).includes('data-dq-part="catalog-register"');
    ok(catalogClause === (catalogFinding && !!register && !!regPage),
      `${where}: the catalog line names Shin2022's register row if and only if the row carries MOABB's counts (${catalogFinding ? 'it does' : 'it does not'}) and the register page is built (${regPage ? 'it is' : 'it is not'})`);
    const notPub = [...el(methods, /<ul class="rd-rules" data-dq-list="not-published"/, where).matchAll(/<li>([\s\S]*?)<\/li>/g)].map(m => vis(m[1]));
    ok(notPub.length === D.not_published.length, `${where}: every item of what is not published`);
    ok(!notPub.some(x => (lang === 'en' ? /owner|one-person/ : /所有者|单人/).test(x)), `${where}: the eldBETA hold's reason stays with the holds line`);
    const moabb = notPub.filter(x => x.startsWith('MOABB'));
    ok(moabb.length === 1 && REGISTER_NAMED[lang].test(moabb[0]) === catalogFinding,
      `${where}: the not-published MOABB line names the register file if and only if Shin2022's row carries the counts`);

    // 7. Tables, CSP, hreflang, the cite block.
    for (const [, t] of main.matchAll(/(<table\b[\s\S]*?<\/table>)/g)) ok(/<thead>/.test(t), `${where}: every table has a <thead>`);
    for (const [, d] of main.matchAll(/(<details\b[\s\S]*?<\/details>)/g))
      for (const [, t] of d.matchAll(/(<table\b[\s\S]*?<\/table>)/g)) ok(count(el(t, /<thead>/, where), '<th') >= 4, `${where}: a table in <details> has four or more columns`);
    ok(!/<script(?![^>]*\bsrc=)(?![^>]*\btype="application\/(?:ld\+)?json")[^>]*>/.test(html), `${where}: no inline script`);
    ok(!/\sstyle="|<style[\s>]|\son[a-z]+=/i.test(html), `${where}: no inline style or handler`);
    ok(html.includes(`hreflang="zh-Hans" href="https://bci.report/zh/${PATH}"`) && html.includes(`hreflang="en" href="https://bci.report/${PATH}"`), `${where}: reciprocal hreflang`);
    ok(el(main, /<section class="cite-page"/, where).includes(`data-releases="${RELEASE}"`), `${where}: the cite block names this release only`);

    // 8. Words.
    const all = html + (existsSync(join(DIST, `${pfx}${PATH}index.md`)) ? read(`${pfx}${PATH}index.md`) : '');
    // The private names are spelled in pieces, so this file carries none of them whole.
    for (const bad of ['/Us' + 'ers/', '/ho' + 'me/', '/Vol' + 'umes/', '/m' + 'nt/', 'tr' + 'x50', 'Ga' + 'l4', 'BCI' + '_Arena', 'ICLR 2027', 'OpenReview'])
      ok(!all.includes(bad), `${where}: "${bad}" never appears`);
    ok(!/(?<![\d.])55 ?%/.test(vis(all)), `${where}: no 55%`);
    ok(!new RegExp(`\\b${'tw' + 'u'}\\b`).test(all), `${where}: no private user name`);
    // The page's own words: the other questions' cards in the switcher are theirs.
    const own = main.replace(el(main, /<nav class="topic-switcher"/, where), ' ');
    const words = vis(own);
    ok(!/\bsubmission\b|投稿/i.test(words), `${where}: no submission reference`);
    ok(!/(?<![\w.\/#-])(?<!Figshare(?: record)?(?: \d+)? )v\d+(?![\w.]|-\d)|\brelease v\d/.test(words), `${where}: no version label`);
    ok(!(lang === 'zh' ? /新增|本次更新|这次更新|本次发布|最新发布|更新于/ : /\b(?:new|newly|added|updated|this update|this release)\b/i).test(words), `${where}: no update wording`);
    ok(!(lang === 'zh' ? /最佳|最好|胜出|排名|第一名/ : /\b(?:best|worst|top|winner|leader|outperform\w*|beats?|ranks?|ranked|ranking)\b/i).test(words), `${where}: no ranking word`);
    if (lang === 'en') ok(!/, not\b/.test(words), `${where}: no ", not" hedge`);
    if (lang === 'zh') {
      const zhText = vis(dropEnglish(own));
      for (const bad of REJECTED_ZH) ok(!zhText.includes(bad), `${where}: "${bad}" is a rejected rendering`);
      ok(!/[一-鿿\d]\.<\/p>/.test(dropEnglish(main)), `${where}: no ASCII full stop after Chinese`);
    }

    // 9. The Markdown copy.
    const md = `${pfx}${PATH}index.md`;
    if (existsSync(join(DIST, md))) {
      const copy = read(md);
      for (const [, v] of main.matchAll(/class="(?:metric|num|fig)">([^<]+)</g)) ok(copy.includes(decode(v)), `${md}: figure "${v}"`);
    }
  }
  // English and Chinese print the same figures.
  const main = lang => el(pages[lang], /<main\b/, lang);
  assert.deepEqual(figAttrs(main('zh')).sort(), figAttrs(main('en')).sort(), 'the same figures in English and Chinese'); checks++;
  const answerFigs = lang => [...el(main(lang), /<section class="short-answer"/, lang).matchAll(/class="fig">([^<]+)</g)].map(m => m[1]);
  assert.deepEqual(answerFigs('zh'), answerFigs('en'), 'the same short-answer figures in English and Chinese'); checks++;
  const regPageBuilt = existsSync(join(DIST, 'datasets/register/index.html'));
  return { checks, figures: figAttrs(main('en')).length, register: register ? { file: served.at(-1), page: regPageBuilt, finding: catalogFinding } : null };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/data-quality.mjs <build dir>'); process.exit(2); }
  const { checks, figures, register } = checkDataQuality(dir);
  console.log(`PASS: data quality — /topics/data-quality/ in both languages, ${checks} checks: ${figures} figures per page, every one a leaf of ${FILE} in its format and the same in English and Chinese; Shin2022's three arms with the duration control set apart as retrospective, the caveat once beside them, the coverage chain once in its table, the catalog line, the checks, holds, consent and ethics, and the attribution ending with the site's sentence; eldBETA counts and holds with no score, the SingLEM fact line and its hold; ZuCo 2.0 with no figure; ${!register ? 'no register link (no register file served)' : register.page ? `each case linked to its row in ${register.file}` : `no register link (${register.file} served, the register page not built)`}; ${register?.finding ? 'MOABB’s counts named as findings on Shin2022’s register row, which carries them' : 'MOABB’s counts not said to be on Shin2022’s register row, which does not carry them'}; <thead> everywhere, CSP, hreflang, the cite block, the Markdown copy, and no private path, submission reference, version label, update or ranking word.`);
}
