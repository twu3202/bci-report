// The open register's dataset ladder (release open-register-update-20261020, owner decisions D3, D5 and D11):
// /datasets/register/ in both languages and the /datasets/ link line, checked in a built site.
//
//   node scripts/checks/open-register.mjs <build dir>        (or import { checkOpenRegister } and pass the dir)
//
// What it holds, in both languages:
//  1. the page: its h1 and <title>; #counts, #levels and #datasets once each; the served register file is the newest
//     open-register-<YYYYMMDD>.json and byte-identical to public/data;
//  2. the table: one server-rendered table with a <thead> of the five columns; one <tbody> per group in the plan's
//     order (Hugging Face, EEGDash, this site, MOABB, corpora), each opened by a heading row that spans the table and
//     prints the group's row count from the file; the rows rendered are exactly the file's dataset rows, each once,
//     anchored by its opaque id, in the file's order (this site's rows furthest step first);
//  3. each row: its badge by class (rg-l<step>) with the ladder's words, its gaps (the share above chance as "not
//     computed", owner decision D12), its status and any rule that keeps it at step 1; on the Chinese page, this site's
//     own rights-record sentences in Chinese; one correction mail whose subject names the row's id and nothing else; its findings, one list item
//     per finding (a source's metadata match and its terms together), each comparison naming its captured source and
//     the capture's date, each derived_from linking a row on the page; its figures (files, bytes, MOABB's fields,
//     family counts) as values of the file;
//  4. links: no link or anchor carries a Hugging Face user name (every Hugging Face link is a search, never for a
//     namespace the register knows); every site link reaches a built page, and every #anchor exists where it points;
//  5. figures: every data-fig is a value of the register file printed as a count; the counts strip prints, in order,
//     the file's counts the plan names, with the snapshot's date and time, the Hugging Face group's figure as rows;
//     English and Chinese print the same figures in the same order;
//  6. #levels: the five steps with the file's names and what each needs, in each language as the file says it, the
//     rules as the file states them;
//  7. the filter: rendered hidden, with its "no row matches" note inside it, loaded as an external module; no inline
//     script, style attribute or handler; every table has a <thead>; hreflang reciprocal; the cite block names the
//     register's release only; the DataCatalog markup on the English page, one dataset per row, never isBasedOn, no
//     Hugging Face user name in any name, a description for each;
//  8. words: no private path, no ICLR 2027, OpenReview or submission reference, no "55%" and not the thread
//     commenter's name, no version label or update date, no ranking word; no rejected Chinese rendering, no spaced 和
//     between Chinese words, no 序列 for a ladder; "1 of N members"; the Hugging Face note as narrowed;
//  9. the Markdown copy carries the table with every row and every figure;
// 10. /datasets/: one link line to the register with the dataset row count as a figure; its results table keeps its
//     five columns;
// 11. the page's weight, reported.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { strict as assert } from 'node:assert';
import { createHash as hash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const PATH = 'datasets/register/';
const RELEASE = 'open-register-update-20261020';
const H1 = { en: 'Every EEG dataset we know of, and how far we checked it', zh: '我们知道的每个 EEG 数据集，以及核验到了哪一步' };
const TITLE = { en: 'Open register · datasets', zh: '开放登记册 · 数据集' };
const COLUMNS = { en: ['Dataset', 'Signal · task', 'Terms as stated', 'Checked to', 'What we found'], zh: ['数据集', '信号 · 任务', '所述条款', '核验到', '核验所见'] };
const GROUPS = ['hf', 'eegdash', 'site', 'moabb', 'corpus'];
const GROUP_NAMES = {
  en: { hf: 'Hugging Face uploads', eegdash: 'OpenNeuro via EEGDash', site: 'This site’s datasets', moabb: 'MOABB catalog', corpus: 'Corpora that require an agreement or request' },
  zh: { hf: 'Hugging Face 上的上传', eegdash: '经 EEGDash 镜像的 OpenNeuro 数据', site: '本站的数据集', moabb: 'MOABB 目录', corpus: '需要签署协议或提出申请的语料' },
};
const STATUS = {
  en: { published: 'Published', score_held: 'Score held', status_only: 'Status only', planned: 'Planned', listed: 'Listed' },
  zh: { published: '已发布', score_held: '分数暂缓', status_only: '只发状态', planned: '计划中', listed: '已列出' },
};
const MAIL = 'contact@bci.report';
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const longDate = (iso, lang) => { const [y, m, d] = iso.slice(0, 10).split('-').map(Number); return lang === 'zh' ? `${y} 年 ${m} 月 ${d} 日` : `${d} ${MONTHS[m - 1]} ${y}`; };
const badge = (lang, step, name) => (lang === 'zh' ? `第 ${step} 步（共 5 步）· ${name}` : `Step ${step} of 5 · ${name}`);
const gapText = (lang, step, label) => (lang === 'zh' ? `第 ${step} 步缺：${label}` : `gap at step ${step}: ${label}`);
// Owner decision D12: the share of participants above chance is a value nobody has computed yet, said as such.
const NOT_COMPUTED = 'share_above_chance';
const notComputed = (lang, label) => (lang === 'zh' ? `${label}：尚未计算` : `${label}: not computed`);
// A licence named by its identifier or its full name (open-register.ts LICENCE_ID).
const LICENCE_ID = /^(?:CC[- ]?BY(?:[- ](?:NC|ND|SA))*(?:[- ]\d\.\d)?|CC0(?:[- ]1\.0)?|MIT|GPL-\d\.\d|ODC-BY(?:-\d\.\d)?|Open Data Commons Attribution License \d\.\d|Creative Commons Attribution(?:[- ][A-Za-z]+)* \d\.\d(?: Generic| International)?)$/i;
// Glossary renderings the site rejects (check-workbench.mjs `rejected`), the ones this page could reach.
const REJECTED_ZH = ['参与者', '受试者', '区块', '暴露', '源数据', '个百分点', '读出头'];
// The thread commenter's name, held as hashes so that this file does not print it (new-ssvep-frequencies.mjs).
const COMMENTER = new Set(['6e7f5e4c7a5ed600cb60c4cd7fa0b60724ddd2a89426474c71d7d8d06bb9c4d9', 'f695cdd94ee90fff62b7216da4bcd9283b9514e061f6108043cac331f5f1a65a']);
// check-workbench.mjs's update-date and version-label rules, as they apply to a page outside the release log.
const DAY = `\\d{1,2} (?:${MONTHS.join('|')})`, ISO = '20\\d\\d-\\d\\d-\\d\\d', ZHD = '20\\d\\d 年 \\d+ 月 \\d+ 日';
const UPDATE_RULES = [
  new RegExp(`\\b[Uu]pdated:? (?:on )?(?:20\\d\\d|${DAY})|· [Uu]pdated\\b|更新于|${ISO} ?更新|\\d+ 月 \\d+ 日更新`),
  new RegExp(`\\b[Aa]dded:? (?:on )?(?:20\\d\\d|${DAY})|新增于|${ISO} ?新增|${ZHD}(?:新增|加入)`),
  new RegExp(`\\b[Ss]ince (?:${ISO}|${DAY})|(?<!来)自 ?20\\d\\d|\\d+ 月 \\d+ 日起[，,：:]`),
  /[Hh]eld since|起暂缓/,
  new RegExp(`\\b(?:[Rr]un|[Rr]an|replayed) on (?:${ISO}|${DAY})|于 ${ZHD}运行|\\d+ 月 \\d+ 日已?运行`),
  new RegExp(`· [Rr]eviewed (?:on )?(?:${ISO}|${DAY})|· ${ZHD}审核`),
  new RegExp(`\\b[Ss]napshot (?:${ISO}|${DAY})|快照 ?(?:${ISO}|${ZHD})`),
  /\b[Tt]his update\b|本次更新|这次更新/,
  new RegExp(`\\bgenerated:? (?:on )?(?:20\\d\\d|${DAY})|生成于 ?20\\d\\d`),
  /(?<![\w.\/#-])(?<!Figshare(?: record)?(?: \d+)? )v\d+(?![\w.]|-\d)|\brelease v\d|第[一二三四五六七八九十]+轮/,
];

const decode = s => s.replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d))).replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&');
const vis = h => decode(h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
const figAttrs = h => [...h.matchAll(/data-fig="([^"]+)"/g)].map(m => m[1]);
const numTexts = h => [...h.matchAll(/class="(?:metric|num|fig)">([^<]+)</g)].map(m => m[1]);
// The element that opens at `at`, through its matching close tag.
const spanEnd = (h, at) => {
  const tag = h.slice(at + 1).match(/^\w+/)[0], re = new RegExp(`<${tag}\\b|</${tag}>`, 'g');
  re.lastIndex = at; let d = 0, m;
  while ((m = re.exec(h))) { d += m[0].startsWith('</') ? -1 : 1; if (!d) return m.index + m[0].length; }
  return h.length;
};
const el = (h, sel, where) => { const a = h.search(sel); assert.ok(a >= 0, `${where}: ${sel} renders`); return h.slice(a, spanEnd(h, a)); };
const count = (h, s) => h.split(s).length - 1;
const dropEnglish = h => { let out = h, m; const re = /<(\w+)\b[^>]*\slang="en"[^>]*>/g;
  while ((m = re.exec(out))) { const end = spanEnd(out, m.index); out = out.slice(0, m.index) + ' ' + out.slice(end); re.lastIndex = m.index; }
  return out; };
const fmtCount = r => r.toLocaleString('en-US');

export function checkOpenRegister(distDir) {
  const DIST = resolve(distDir);
  assert.ok(existsSync(join(DIST, 'index.html')), `${DIST}: not a built site`);
  const read = p => readFileSync(join(DIST, p), 'utf8');
  const served = readdirSync(join(DIST, 'data')).filter(f => /^open-register-\d{8}\.json$/.test(f)).sort();
  assert.ok(served.length, 'a register file is served');
  const FILE = served.at(-1);
  const text = read(`data/${FILE}`);
  assert.equal(text, readFileSync(fileURLToPath(new URL(`../../public/data/${FILE}`, import.meta.url)), 'utf8'), `${FILE}: the served copy is public/data's`);
  const R = JSON.parse(text);
  assert.equal(R.release_id, RELEASE, 'the release');
  const leaves = new Set(); (function walk(v) { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(R);
  const rows = R.entries.filter(e => e.ladder === 'dataset');
  const byId = new Map(R.entries.map(e => [e.id, e]));
  const captures = new Map(R.sources.access_terms.map(c => [c.capture_id, c]));
  const families = new Map(R.families.map(f => [f.id, f]));
  const C = R.counts, H = C.hf, S = H.snapshot;
  // Every Hugging Face namespace the register names.
  const namespaces = new Set();
  for (const e of R.entries) {
    if (e.hf) namespaces.add(e.hf.repo.split('/')[0].toLowerCase());
    if (e.family) namespaces.add(e.family.uploader.toLowerCase());
    for (const a of e.aliases) if (a.value.includes('/') && ['hf_repo', 'eegdash_mirror', 'official_weights', 'weights_copy'].includes(a.kind)) namespaces.add(a.value.split('/')[0].toLowerCase());
  }
  // The rows in the page's order: the groups in the plan's order, this site's rows furthest step first.
  const expectedOrder = GROUPS.flatMap(g => {
    const m = rows.filter(e => e.group === g);
    return g === 'site' ? [...m].sort((a, b) => b.level - a.level || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)) : m;
  }).map(e => e.id);
  assert.equal(expectedOrder.length, C.rows.dataset, 'the file: its dataset rows are its counted rows');
  // The counts strip's figures, in order (register.astro).
  const at = l => C.rows.dataset_by_level[String(l)] ?? 0;
  const countsOrder = [C.rows.dataset, ...GROUPS.map(g => C.rows.dataset_by_group[g]), at(1), at(2), at(3), at(4), at(5), C.rows.model,
    S.search_terms, S.tag_filters, S.listings, S.eegdash_mirrors, S.other_uploads, S.prefilter_dropped, S.classified, H.classifier_in_scope,
    H.recheck_out_emg_rule, H.recheck_out_simulated, H.recheck_out_undetermined, H.in_scope, H.single_rows, H.family_members, H.family_rows,
    H.merged_into_site_rows, H.merged_into_moabb_rows, H.held_for_review, H.no_licence_tag, H.gated_manual, H.gated_auto,
    C.eegdash.mirrors, C.eegdash.openneuro, C.eegdash.nemar, C.eegdash.other, C.eegdash.site_rows_with_mirror, C.eegdash.moabb_rows_with_mirror,
    C.moabb.loaders, C.moabb.record_groups, C.moabb.merged_into_site_rows, C.corpus.families, C.corpus.captured];
  const builtPage = p => existsSync(join(DIST, p.replace(/^\//, ''), 'index.html'));
  const idsOf = new Map();
  const pageIds = p => { if (!idsOf.has(p)) idsOf.set(p, new Set([...read(join(p.replace(/^\//, ''), 'index.html')).matchAll(/\sid="([^"]+)"/g)].map(m => m[1]))); return idsOf.get(p); };

  let checks = 0;
  const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };
  const pages = {}, mains = {};
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}${PATH}`, zh = lang === 'zh';
    const html = read(`${pfx}${PATH}index.html`); pages[lang] = html;
    const main = el(html, /<main\b/, where); mains[lang] = main;
    const cite = el(main, /<section class="cite-page"/, where);
    const body = main.replace(cite, ' ');

    // 1. The page.
    ok(vis(el(main, /<h1\b/, where)) === H1[lang], `${where}: the h1`);
    ok(html.includes(`<title>${TITLE[lang]} · BCI Report</title>`), `${where}: the <title>`);
    for (const id of ['counts', 'levels', 'datasets']) ok(count(html, ` id="${id}"`) === 1 && new RegExp(`<section[^>]*\\sid="${id}"`).test(main), `${where}: #${id} once`);

    // 2. The table.
    ok(count(main, '<table') === 1, `${where}: one table`);
    const table = el(main, /<table class="rg-table" data-register-table="dataset"/, where);
    const thead = el(table, /<thead>/, where);
    ok(JSON.stringify([...thead.matchAll(/<th scope="col">([^<]*)<\/th>/g)].map(m => decode(m[1]))) === JSON.stringify(COLUMNS[lang]), `${where}: the five columns under a <thead>`);
    const bodies = [...table.matchAll(/<tbody id="group-([a-z_]+)" data-rg-group="\1">/g)].map(m => m[1]);
    ok(JSON.stringify(bodies) === JSON.stringify(GROUPS), `${where}: the groups in order (${bodies})`);
    const rendered = [];
    for (const g of GROUPS) {
      const tb = el(table, new RegExp(`<tbody id="group-${g}"`), where);
      const head = el(tb, /<tr class="rg-group">/, where);
      ok(/^<tr class="rg-group"><th colspan="5" scope="rowgroup">/.test(head), `${where}: the ${g} group opens with a heading row across the table`);
      ok(vis(head).startsWith(GROUP_NAMES[lang][g]), `${where}: the ${g} group's name`);
      ok(figAttrs(head).join() === `${FILE}|count|${C.rows.dataset_by_group[g]}`, `${where}: the ${g} group's row count`);
      ok(tb.indexOf(head) < tb.indexOf('<tr id='), `${where}: the ${g} heading comes first`);
      for (const [, id] of tb.matchAll(/<tr id="([^"]+)"/g)) { ok(byId.get(id)?.group === g, `${where}: ${id} sits in the ${g} group`); rendered.push(id); }
    }
    ok(JSON.stringify(rendered) === JSON.stringify(expectedOrder), `${where}: the rows rendered are the file's dataset rows, each once, in order (${rendered.length} of ${expectedOrder.length})`);
    ok(count(main, ' id="r-') === rendered.length, `${where}: no other row anchor`);

    // 3. Each row.
    const defs = R.level_definitions.dataset, items = R.item_definitions.dataset;
    let fullRows = 0;
    for (const m of table.matchAll(/<tr id="(r-[^"]+)" data-g="([^"]+)" data-step="(\d)" data-terms="([01])" data-gap="([01])">([\s\S]*?)<\/tr>/g)) {
      const [, id, g, step, terms, gap, tr] = m, e = byId.get(id), w = `${where}#${id}`;
      fullRows++;
      ok(/^r-(?:hf-\d{4}|moabb-\d{4}|corpus-[a-z0-9-]+|site-[a-z0-9-]+)$/.test(id), `${w}: an opaque id`);
      ok(e.group === g && String(e.level) === step && (e.gaps.length > 0 ? '1' : '0') === gap, `${w}: its group, step and gap flags`);
      if (e.findings.some(f => f.code === 'licence_tag_absent')) ok(terms === '0', `${w}: no licence tag, so no terms stated`);
      const cells = [...tr.matchAll(/<(th|td)\b[^>]*>([\s\S]*?)<\/\1>(?=<t[hd]\b|$)/g)];
      ok(cells.length === 5 && /^<th scope="row">/.test(tr), `${w}: five cells, the first its name`);
      const name = defs[String(e.level)][lang === 'zh' ? 'zh' : 'en'];
      ok(tr.includes(`<span class="rg-badge rg-l${e.level}">${badge(lang, e.level, name)}</span>`), `${w}: its badge, by class`);
      for (const gp of e.gaps) {
        const label = zh ? items[gp.item].label_zh : items[gp.item].label_en;
        if (gp.item === NOT_COMPUTED) ok(vis(tr).includes(notComputed(lang, label)) && !vis(tr).includes(gapText(lang, gp.step, label)), `${w}: ${gp.item}, not computed (D12)`);
        else ok(vis(tr).includes(gapText(lang, gp.step, label)), `${w}: its gap at step ${gp.step}`);
      }
      // This site's own rights-record sentences: Chinese on the Chinese page, unless the terms are a licence's name.
      if (zh && e.terms_as_stated.by === 'site_release' && e.terms_as_stated.value && !e.terms_as_stated.value.split(', ').every(t => LICENCE_ID.test(t))) {
        const main = cells[2][2].split(/<small>/)[0];
        ok(/[一-鿿]/.test(vis(dropEnglish(main))), `${w}: its terms in Chinese (${vis(main)})`);
      }
      ok(vis(tr).includes(`${zh ? '状态：' : 'Status: '}${STATUS[lang][e.status]}`), `${w}: its status`);
      ok(!e.level_cap === !tr.includes('<a href="#levels">'), `${w}: the rule that keeps it at step 1, linked to the rules`);
      const mails = [...tr.matchAll(/href="(mailto:[^"]*)"/g)].map(x => decode(x[1]));
      ok(mails.length === 1 && mails[0] === `mailto:${MAIL}?subject=Register%20row%20${id}` && mails[0] === e.correction.mailto, `${w}: one correction mail naming its id alone`);
      ok(tr.includes(e.name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')), `${w}: its name`);
      // Findings: one item each, a source's comparisons together.
      const comparisons = e.findings.filter(f => ['matches_metadata_of', 'terms_differ'].includes(f.code));
      const nItems = e.findings.length - comparisons.length + new Set(comparisons.map(f => f.params.capture_id)).size;
      ok(count(tr, '<li>') === nItems, `${w}: ${nItems} finding items (${count(tr, '<li>')})`);
      for (const f of comparisons) {
        const c = captures.get(f.params.capture_id);
        ok(c, `${w}: ${f.params.capture_id} is a listed capture`);
        // The source is named once per capture: by its register row where any finding on that capture gives one.
        const row = comparisons.find(x => x.params.capture_id === f.params.capture_id && x.params.row)?.params.row;
        const named = row ? tr.includes(`href="#${row}"`) : vis(tr).includes(c.family);
        ok(named, `${w}: names the source of ${f.code}`);
        ok(vis(tr).includes(zh ? `条款页面于 ${longDate(c.captured_at, lang)}存档` : `terms page captured ${longDate(c.captured_at, lang)}`), `${w}: cites the capture of ${c.family_slug}`);
        if (f.code === 'terms_differ') for (const t of String(f.params.declared).split('+')) if (t !== 'none') ok(tr.includes(`<code>${t}</code>`), `${w}: the declared ${t}`);
        if (f.code === 'terms_differ' && !['signed_agreement', 'request_based', 'registration'].includes(f.params.original)) ok(tr.includes(`<code>${f.params.original}</code>`), `${w}: the original ${f.params.original}`);
      }
      for (const f of e.findings.filter(f => f.code === 'derived_from')) ok(tr.includes(`href="#${f.params.row}"`), `${w}: derived_from links ${f.params.row}`);
      // Its figures.
      const figs = figAttrs(tr).map(a => Number(a.split('|')[2]));
      const want = [];
      if (e.hf) { if (e.hf.files !== null) want.push(e.hf.files); if (e.hf.size_bytes !== null) want.push(e.hf.size_bytes); }
      if (e.moabb) for (const fl of e.moabb.fields_as_listed) for (const k of ['people', 'channels', 'sampling_rate_hz']) if (fl[k] !== null) want.push(fl[k]);
      for (const f of e.findings) for (const k of ['n', 'of', 'recordings_source', 'recordings_evaluated', 'catalog_trials', 'catalog_runs']) if (typeof f.params[k] === 'number') want.push(f.params[k]);
      const fam = families.get(id);
      if (fam) { if (e.kind === 'hf_family') want.push(fam.size_bytes); want.push(...Object.values(fam.licence_tag_counts)); }
      const left = [...figs];
      for (const x of want) { const i = left.indexOf(x); ok(i >= 0, `${w}: prints ${x}`); left.splice(i, 1); }
      ok(left.length === 0, `${w}: no figure beyond its own (${left})`);
    }
    ok(fullRows === rendered.length, `${where}: every row parsed (${fullRows})`);

    // 4. Links and anchors.
    const ids = [...main.matchAll(/\sid="([^"]+)"/g)].map(x => x[1]);
    ok(new Set(ids).size === ids.length, `${where}: every id once`);
    for (const id of ids) ok(/^(?:r-[a-z0-9-]+|group-[a-z_]+|[a-z]+(?:-[a-z]+)*-heading|counts|levels|datasets|register-files|cite|entity-content)$/.test(id), `${where}: the anchor "${id}" is opaque`);
    for (const [, raw] of body.matchAll(/href="([^"]+)"/g)) {
      const href = decode(raw);
      if (/^https?:/.test(href)) {
        const u = new URL(href);
        if (/(^|\.)huggingface\.co$/.test(u.hostname)) {
          ok(/^\/(?:datasets|models)$/.test(u.pathname) && [...u.searchParams.keys()].join() === 'search', `${where}: a Hugging Face link other than a search: ${href}`);
          const q = u.searchParams.get('search').toLowerCase();
          ok(![...namespaces].some(ns => q === ns || q.startsWith(`${ns}/`)), `${where}: a search for a user name: ${href}`);
        }
        const segs = u.pathname.toLowerCase().split('/');
        if (/(^|\.)huggingface\.co$/.test(u.hostname)) ok(!segs.some(s => namespaces.has(s)), `${where}: a user name in a link: ${href}`);
      } else if (href.startsWith('#')) {
        ok(ids.includes(href.slice(1)), `${where}: ${href} is an anchor on the page`);
      } else if (href.startsWith('/')) {
        const [p, anchor] = href.split('#');
        if (p.startsWith('/data/')) ok(existsSync(join(DIST, p)), `${where}: ${p} is served`);
        else {
          ok(builtPage(p), `${where}: ${p} is a built page`);
          if (anchor && builtPage(p)) ok(pageIds(p).has(anchor), `${where}: ${href} names an anchor on that page`);
        }
      } else ok(href.startsWith('mailto:'), `${where}: an unexpected link ${href}`);
    }

    // 5. Figures.
    let figs = 0;
    for (const [, file, f, raw, t] of main.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)) {
      ok(file === FILE && f === 'count', `${where}: a figure from ${file} as ${f}`);
      ok(leaves.has(Number(raw)), `${where}: ${raw} is not a value in ${FILE}`);
      ok(t === fmtCount(Number(raw)), `${where}: ${raw} printed as "${t}"`);
      figs++;
    }
    ok(figs > 1000, `${where}: the figures carry data-fig (${figs})`);
    const counts = el(main, /<section[^>]*\sid="counts"/, where);
    ok(JSON.stringify(figAttrs(counts).map(a => Number(a.split('|')[2]))) === JSON.stringify(countsOrder), `${where}: the counts strip prints the file's counts in order`);
    const snapshot = zh ? `${longDate(S.retrieved_at, lang)} ${S.retrieved_at.slice(11, 16)}（UTC）` : `${longDate(S.retrieved_at, lang)} at ${S.retrieved_at.slice(11, 16)} UTC`;
    ok(vis(counts).includes(snapshot), `${where}: the snapshot's date and time`);
    ok(vis(counts).includes(longDate(R.sources.moabb.catalog_checked, lang)) && vis(counts).includes(C.moabb.release), `${where}: MOABB's release and the catalog's date`);
    for (const t of R.sources.hf.search_terms) ok(counts.includes(`<code>${t}</code>`), `${where}: the search term ${t}`);
    // The strip counts rows: the Hugging Face group's figure is a number of rows, never of uploads.
    const rowsItem = vis(el(counts, /<li data-rg-count="rows">/, where));
    const hfRows = fmtCount(C.rows.dataset_by_group.hf);
    ok(zh ? rowsItem.includes(`Hugging Face 上的上传 ${hfRows} 行`) : rowsItem.includes(`${fmtCount(C.rows.dataset)} rows on the dataset ladder: ${hfRows} for uploads on Hugging Face`), `${where}: the Hugging Face figure counts rows`);
    ok(!new RegExp(`\\b${hfRows} uploads\\b`).test(rowsItem), `${where}: "${hfRows} uploads" in the rows item`);

    // 6. #levels.
    const levels = el(main, /<section[^>]*\sid="levels"/, where);
    const dts = [...levels.matchAll(/<dt><span class="rg-badge rg-l(\d)">([^<]+)<\/span><\/dt><dd>([^<]+)<\/dd>/g)];
    ok(dts.length === 5, `${where}: five steps`);
    for (const [, s, label, needs] of dts) {
      const d = defs[s];
      ok(decode(label) === (zh ? `第 ${s} 步 · ${d.zh}` : `Step ${s} · ${d.en}`), `${where}: step ${s}'s name`);
      ok(decode(needs) === (zh ? d.needs_zh : d.needs_en), `${where}: what step ${s} needs, as the file says it`);
    }
    const rules = [...el(levels, /<ul class="rg-rules">/, where).matchAll(/<li>([^<]+)<\/li>/g)].map(x => decode(x[1]));
    ok(JSON.stringify(rules) === JSON.stringify(R.rules.map(r => (zh ? r.zh : r.en))), `${where}: the file's rules, stated once`);
    for (const r of R.rules) ok(count(vis(main), zh ? r.zh : r.en) === 1, `${where}: the rule "${r.id}" once`);

    // 7. Filter, CSP, tables, hreflang, cite, markup.
    const form = el(main, /<form class="rg-filter" data-register-filter="dataset" hidden>/, where);
    for (const n of ['g', 'step', 'terms']) ok(form.includes(`<select name="${n}">`), `${where}: the ${n} filter`);
    ok(form.includes('<input type="checkbox" name="gap" value="1">') && /<p class="rg-empty" data-register-empty hidden>/.test(form), `${where}: the gap filter and the empty note, inside the form`);
    ok(/<script type="module" src="\/_astro\/RegisterTable[^"]*\.js"><\/script>/.test(html), `${where}: the filter, an external module`);
    ok(!/<script(?![^>]*\bsrc=)(?![^>]*\btype="application\/(?:ld\+)?json")[^>]*>/.test(html), `${where}: no inline script`);
    ok(!/\sstyle="|<style[\s>]|\son[a-z]+=/i.test(html), `${where}: no inline style or handler`);
    for (const [, t] of main.matchAll(/(<table\b[\s\S]*?<\/table>)/g)) ok(/<thead>/.test(t), `${where}: every table has a <thead>`);
    for (const [, d] of main.matchAll(/(<details\b[\s\S]*?<\/details>)/g)) for (const [, t] of d.matchAll(/(<table\b[\s\S]*?<\/table>)/g)) ok(count(el(t, /<thead>/, where), '<th') >= 4, `${where}: a table in <details> has four or more columns`);
    ok(html.includes(`hreflang="zh-Hans" href="https://bci.report/zh/${PATH}"`) && html.includes(`hreflang="en" href="https://bci.report/${PATH}"`), `${where}: reciprocal hreflang`);
    ok(cite.includes(`data-releases="${RELEASE}"`), `${where}: the cite block names this release only`);
    const ld = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(x => JSON.parse(x[1]));
    if (zh) ok(ld.length === 0, `${where}: structured data on the English page only`);
    else {
      const cat = ld.find(x => x['@type'] === 'DataCatalog');
      ok(cat && cat.url === `https://bci.report/${PATH}` && cat.dataset.length === rows.length && cat.dataset.every(d => d['@type'] === 'Dataset'), `${where}: a DataCatalog of the dataset rows`);
      ok(!JSON.stringify(ld).includes('isBasedOn'), `${where}: never isBasedOn`);
      // No user name in the markup (repository ids stay in the rows' text), and every Dataset described (Google requires it).
      for (const d of cat.dataset) {
        const n = d.name.toLowerCase();
        ok(![...namespaces].some(u => n.startsWith(`${u}/`) || n.includes(` ${u}/`) || n.includes(`(${u}/`)), `${where}: a user name in the markup (${d.name})`);
        ok(typeof d.description === 'string' && d.description.length >= 50 && d.description.length <= 5000, `${where}: ${d.name} has a description`);
      }
      for (const d of cat.dataset) if (d.url && /huggingface\.co/.test(d.url)) {
        const u = new URL(d.url);
        ok(/^\/(?:datasets|models)$/.test(u.pathname) && ![...namespaces].includes(u.searchParams.get('search').toLowerCase()), `${where}: the markup links no user name (${d.url})`);
      }
    }

    // 8. Words.
    const md = existsSync(join(DIST, `${pfx}${PATH}index.md`)) ? read(`${pfx}${PATH}index.md`) : '';
    const all = html + md;
    // A public address may hold such a segment (bcmi.sjtu.edu.cn/home/seed/): the paths are looked for outside addresses.
    const noUrls = all.replace(/https?:\/\/[^\s"<>)]+/g, ' ');
    for (const bad of ['/Us' + 'ers/', '/ho' + 'me/', '/Vol' + 'umes/', '/m' + 'nt/', 'tr' + 'x50', 'Ga' + 'l4', 'BCI' + '_Arena', 'ICLR 2027', 'OpenReview', 'openreview'])
      ok(!noUrls.includes(bad), `${where}: "${bad}" never appears`);
    ok(!new RegExp(`\\b${'tw' + 'u'}\\b`).test(all), `${where}: no private user name`);
    ok(!/(?<![\d.])55 ?%|fifty[- ]five per|五十五/.test(vis(all)), `${where}: no 55%`);
    const words = s => (s.toLowerCase().match(/[a-z]+/g) ?? []);
    ok(!words(all).some(x => COMMENTER.has(hash('sha256').update(x).digest('hex'))), `${where}: the thread commenter is not named`);
    // The page's own words: the rows' names and quoted terms are the sources' own.
    const own = vis(body.replace(/<th scope="row">[\s\S]*?<\/th>/g, ' ').replace(/“[^”]*”/g, ' ').replace(/<code>[^<]*<\/code>/g, ' '));
    ok(!/\bsubmission\b|投稿/i.test(own), `${where}: no submission reference`);
    for (const re of UPDATE_RULES) { const x = vis(main.replace(cite, ' ')).match(re); ok(!x, `${where}: an update date or version label: “${x?.[0]}”`); }
    ok(!(zh ? /最佳|最好|胜出|排名|第一名/ : /\b(?:best|worst|top|winner|leader|outperform\w*|beats?|ranks?|ranked|ranking)\b/i).test(own), `${where}: no ranking word`);
    if (!zh) ok(!/, not\b/.test(own), `${where}: no ", not" hedge`);
    // After "of N" the noun is plural ("1 of 737 members carries").
    if (!zh) { const x = vis(main).match(/\bof (?!1 )[\d,]+ member\b/); ok(!x, `${where}: “${x?.[0]}”`); }
    // The Hugging Face group's note narrows what the cards' review withholds to what is left blank.
    ok(vis(el(table, /<tbody id="group-hf"/, where)).includes(zh ? '数据卡片关于信号、任务与被试的说法仍在核查' : 'What the cards state about signal, task and participants is still being reviewed'), `${where}: the Hugging Face note`);
    if (zh) {
      const zhText = vis(dropEnglish(body));
      for (const bad of REJECTED_ZH) ok(!zhText.includes(bad), `${where}: "${bad}" is a rejected rendering`);
      ok(!/[一-鿿\d]\.<\/p>/.test(dropEnglish(main)), `${where}: no ASCII full stop after Chinese`);
      // 和 between Chinese words takes no space; the ladders are 登记 or 核验, never 序列.
      const spaced = vis(main).match(/[一-鿿] 和|和 [一-鿿]/); ok(!spaced, `${where}: a spaced 和 between Chinese words (“${spaced?.[0]}”)`);
      const seq = vis(main).match(/(?:数据集|模型|两个|本)序列/); ok(!seq, `${where}: 序列 for a ladder (“${seq?.[0]}”)`);
    }

    // 9. The Markdown copy.
    if (md) {
      const head = `| ${COLUMNS[lang].join(' | ')} |`;
      ok(md.includes(head), `${where}index.md: the table's header`);
      const tableMd = md.slice(md.indexOf(head)).split('\n\n')[0].split('\n').slice(2);
      ok(tableMd.length === rows.length + GROUPS.length, `${where}index.md: every row and group heading (${tableMd.length})`);
      for (const id of rendered) ok(md.includes(`subject=Register%20row%20${id})`), `${where}index.md: the row ${id}`);
      for (const v of numTexts(main)) ok(md.includes(decode(v)), `${where}index.md: figure "${v}"`);
    }
  }
  // English and Chinese print the same figures, in the same order.
  assert.deepEqual(figAttrs(mains.zh), figAttrs(mains.en), 'the same figures in English and Chinese, in order'); checks++;
  assert.deepEqual(numTexts(mains.zh), numTexts(mains.en), 'the same figure texts in English and Chinese'); checks++;

  // 10. /datasets/: one link line, its figure the dataset row count; the results table keeps five columns.
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}datasets/`;
    const main = el(read(`${pfx}datasets/index.html`), /<main\b/, where);
    const line = el(main, /<p class="citation-note" id="register-line">/, where);
    ok(count(main, `/${pfx}datasets/register/`) === 1 && line.includes(`href="/${pfx}datasets/register/"`), `${where}: one link to the register, in its line`);
    ok(figAttrs(line).join() === `${FILE}|count|${C.rows.dataset}`, `${where}: the line prints the dataset row count`);
    ok(main.indexOf(line) < main.indexOf('<table'), `${where}: the line sits above the results table`);
    ok(count(el(el(main, /<table>/, where), /<thead>/, where), '<th scope="col">') === 5, `${where}: the results table keeps its five columns`);
  }

  // 11. Weight.
  const weight = Object.fromEntries(['en', 'zh'].map(l => [l, { bytes: Buffer.byteLength(pages[l]), gzip: gzipSync(pages[l]).length }]));
  for (const l of ['en', 'zh']) ok(weight[l].bytes < 900_000 && weight[l].gzip < 120_000, `/${l === 'zh' ? 'zh/' : ''}${PATH}: ${weight[l].bytes} bytes, ${weight[l].gzip} gzipped`);
  return { checks, rows: rows.length, figures: figAttrs(mains.en).length, file: FILE, weight };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/open-register.mjs <build dir>'); process.exit(2); }
  const { checks, rows, figures, file, weight } = checkOpenRegister(dir);
  console.log(`PASS: open register — /datasets/register/ in both languages, ${checks} checks: ${rows} dataset rows of ${file}, each once under its opaque id in five groups with their heading rows, badge by class, gaps, status and one correction mail naming its id; findings from codes with each comparison's captured source and date; ${figures} figures per page, every one a value of the file and the same in English and Chinese; the counts strip, the steps and rules once, the filter hidden until its module runs; no Hugging Face user name in any link or anchor; DataCatalog markup; the Markdown copy with every row; the /datasets/ line. Weight: ${weight.en.bytes.toLocaleString('en-US')} bytes (${weight.en.gzip.toLocaleString('en-US')} gzipped) in English, ${weight.zh.bytes.toLocaleString('en-US')} (${weight.zh.gzip.toLocaleString('en-US')}) in Chinese.`);
}
