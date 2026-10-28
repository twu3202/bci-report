// The open register's model ladder (owner decisions D1 and D4; the newest register file, which since the 20261028 round
// is open-register-20261028.json, owner decisions D14, D19 and D26): /methods/register/ in both languages and the /methods/
// link line, checked in a built site.
//
//   node scripts/checks/model-register.mjs <build dir>        (or import { checkModelRegister } and pass the dir)
//
// What it holds, in both languages:
//  1. the page: its h1 and <title>; #counts, #levels and #models once each; the served register file is the newest
//     open-register-<YYYYMMDD>.json and byte-identical to public/data;
//  2. the table: one server-rendered table (components/RegisterTable.astro, ladder "model") with a <thead> of the five
//     model columns; one <tbody> per group (models with results on this site, then the other models and papers), each
//     opened by a heading row that spans the table; the rows rendered are exactly the file's model rows, each once,
//     anchored by its opaque id, in the page's order (the site's models furthest step first, then the file's order);
//  3. the ladder's own step names: steps 1 to 4 are named apart from the dataset ladder's in both languages; every
//     badge is a model badge by class (rg-l<step>) that names the model ladder, and no dataset badge is on the page;
//     a row's step is the furthest one whose key item (item_definitions `anchor`) is on file with every earlier
//     step's, and its gaps are the items missing at that step or before, as #levels says; step 5 is held by exactly
//     the methods named in a row of a built /protocols/* page;
//  4. each row: its badge, gaps, a status word that is not a step name of either ladder, and one correction mail
//     naming its id alone; its terms by part, code, weights and data in that order, each stated value as code and
//     "not found" printed for every part the file has none for; its kind and signals; a venue only where the file
//     gives one, resting on the venue's proceedings (linked) or the camera-ready paper, with the date it was checked,
//     and never one owner decision D4 keeps off; its holds, one item each; its pretraining exposure where the file
//     gives one; its result pages: NeuroLM-B at step 4 links both of its pilots (#neurolm-eegmat on pilot studies,
//     #iesseeg on clinical groups) and prints exposure "unknown"; ZUNA 1.1 and eeg-fm-masking link their method pages
//     with no venue; the eight held models print their holds; no two links of a name cell share an address;
//  5. links: no Hugging Face link or anchor carries a user name (every Hugging Face link is a search, never for a
//     namespace the register knows); every site link reaches a built page, and every #anchor exists where it points;
//  6. figures: every data-fig is a value of the register file printed as a count, each read from the field the counts
//     strip names, in order (model rows, the rows at each step that has any, the dataset rows, the models and papers
//     read, those merged into a method page's row); a step with no rows is said in words; English and Chinese print
//     the same figures in the same order;
//  7. #levels: the five steps with the file's model names and what each needs, in each language as the file says it;
//     the file's two rules that apply to every row, each once; the dataset ladder's access and re-upload rules are not
//     repeated here and are linked on the dataset register;
//  8. the filter: rendered hidden, with its "no row matches" note inside it, loaded as an external module; no inline
//     script, style attribute or handler; every table has a <thead>; hreflang reciprocal; the cite block names the
//     register's release only; the DataCatalog markup on the English page, one CreativeWork part per row, never a
//     Dataset and never isBasedOn, no "<user>/" prefix in any name, each of this site's methods named as /methods/
//     names it, a description for each;
//  9. words: no private path, nothing owner decision D4 keeps off anywhere on the page or in the file's model rows,
//     no "55%" and not the thread commenter's name, no version label or update date, no ranking word, no ", not"
//     hedge; no rejected Chinese rendering, no spaced 和 between Chinese words, no 序列 for a ladder, no space after a
//     full-width colon;
// 10. the Markdown copy carries the table with every row and every figure;
// 11. /methods/: one link line to the model register with the model row count as a figure, above the first table,
//     whose three columns are unchanged; /datasets/register/ links the model register;
// 12. the population and the sentences that describe it: every model the built /methods/ page names (its methods
//     table, #other-evaluated and #unmeasured) has a row, and each of this site's methods' rows is named as the
//     methods table names it, with no "<user>/" prefix; the count sentence names exactly the parts of /methods/ the
//     rows cover; the terms sentence says what a "—" means for as long as a row carries no terms by part; the group
//     notes claim holds and official records only where every row of the group bears them out;
// 13. the page's weight, reported;
// 14. the 20261028 round's rows: NeuroRVQ, EEG-Captioner and AXON at step 4, each linking its panel on the pilot-studies
//     page (a built anchor), with pretraining exposure unknown, no venue, no method page and no weights copy; AXON with no
//     paper link; FAME, EEG-PRIME, STST-JEPA, BandVQ and USE-FM at step 1, each with its hold and its paper linked, no
//     venue; FAME a model row apart from the L-FAME dataset row; every row's terms values licence codes only (AXON's code:
//     the module's file terms and the project's root licence, in that order, worded by the page in each language).
//
// While the register file says it is provisional (`status: "provisional"`, its site rows placeholders until the
// freeze), an item of 3, 4 or 12 that the placeholders, or a change requested of another package, have not met yet is
// reported as owed, with the rows it concerns; once the file is final, every one of them fails the check.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { strict as assert } from 'node:assert';
import { createHash as hash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const PATH = 'methods/register/';
const H1 = { en: 'Every EEG model and paper we track, and how far we checked it', zh: '我们关注的每个 EEG 模型与论文，以及核验到了哪一步' };
const TITLE = { en: 'Open register · models', zh: '开放登记册 · 模型' };
const COLUMNS = {
  en: ['Model or paper', 'Kind · signal', 'Terms by part (code / weights / data)', 'Checked to', 'What we found'],
  zh: ['模型或论文', '类型 · 信号', '各部分条款（代码 / 权重 / 数据）', '核验到', '核验所见'],
};
const GROUPS = ['site_model', 'model'];
const GROUP_NAMES = {
  en: { site_model: 'Models with results on this site', model: 'Other models and papers we track' },
  zh: { site_model: '在本站有结果的模型', model: '我们关注的其他模型与论文' },
};
const STATUS = {
  en: { published: 'Published', score_held: 'Score held', status_only: 'Status only', planned: 'Planned', listed: 'Listed' },
  zh: { published: '已发布', score_held: '分数暂缓', status_only: '只发状态', planned: '计划中', listed: '已列出' },
};
const PARTS = ['code', 'weights', 'data'];
const PART_NAME = { en: { code: 'Code', weights: 'Weights', data: 'Data' }, zh: { code: '代码', weights: '权重', data: '数据' } };
const PART_STATE = {
  en: { not_found: 'not found', per_source: 'per source', not_applicable: 'not applicable', application_required: 'on application' },
  zh: { not_found: '未找到', per_source: '按各来源', not_applicable: '不适用', application_required: '需申请' },
};
const EXPOSURE = { en: { unknown: 'Pretraining exposure: unknown' }, zh: { unknown: '是否出现在预训练数据中：未知' } };
// The rules that apply to every row; the other three are the dataset ladder's and stay on the dataset register.
const RULES = ['rows_state_facts', 'correction_route'];
// Rows the plan names (§2.7).
const NEUROLM = 'r-model-neurolm-b';
const NEUROLM_CASES = ['/topics/pilot-studies/#neurolm-eegmat', '/topics/clinical-groups/#iesseeg'];
const PAGED_NO_VENUE = { 'r-model-zuna': '/methods/zuna/', 'r-model-eeg-fm-masking': '/methods/eeg-fm-masking/' };
const HELD = ['r-model-diver-1', 'r-model-popt', 'r-model-omnimouse', 'r-model-biox-bridge', 'r-model-poyo-plus', 'r-model-poyo-cap', 'r-model-neuroformer', 'r-model-brainlm'];
// The 20261028 round (owner decisions D14, D19, D26): three models scored on the pilot-studies page, each linking its
// panel; five identified from their papers, each with its hold.
const SCORED = { 'r-model-neurorvq': '/topics/pilot-studies/#neurorvq', 'r-model-eeg-captioner': '/topics/pilot-studies/#eegmat-ten-second',
                 'r-model-axon': '/topics/pilot-studies/#eegmat-ten-second' };
const IDENTIFIED = { 'r-model-fame': 'no_release_found', 'r-model-eeg-prime': 'code_not_reachable', 'r-model-stst-jepa': 'no_release_found',
                     'r-model-bandvq': 'no_release_found', 'r-model-use-fm': 'no_release_found' };
const MAIL = 'contact@bci.report';
// Owner decision D4: what it keeps off the rows and the page, put together here so that this file does not spell it out.
const D4_RE = new RegExp(['IC' + 'LR 20' + '27', 'open' + 'review', 'sub' + 'mission', 'forum\\?id='].join('|'), 'i');
const D4_KEYS = new RegExp(['iclr', 'sub' + 'mission', 'open' + 'review', 'forum', 'venue_status'].join('|'), 'i');
const D4_YEAR = new RegExp('\\b20' + '27\\b');
const D4_PAGE = new RegExp(['IC' + 'LR 20' + '27', 'open' + 'review'].join('|'), 'i');
const D4_OWN = new RegExp(`\\bsub${'mi'}(?:ssion|tted)\\b|${'投' + '稿'}|${'审' + '稿'}`, 'i');
// A venue rests on the venue's proceedings (linked) or on the paper's camera-ready version: the #models sentence.
const VENUE_EVIDENCE = ['official_proceedings', 'camera_ready_pdf'];
const VENUE_SENTENCE = {
  en: 'A paper’s venue appears only where the venue’s proceedings or the paper’s camera-ready version show it accepted, with the date we checked; where the proceedings are online, the venue links them.',
  zh: '只有会议论文集或论文的最终定稿显示论文已被接收时，才写出发表场合，并附核对日期；论文集可在线查阅的，发表场合链接到论文集。',
};
// The terms sentence (methods/register.astro): the "—" clause stands for as long as a row carries no terms by part.
const TERMS_SENTENCE = {
  en: 'Terms are given for the code, the weights and the data separately, each with who states them, and a part whose terms we could not find says “not found”.',
  zh: '条款按代码、权重与数据分别写明，并注明各自的出处；找不到条款的部分写作“未找到”。',
};
const DASH_SENTENCE = { en: 'A row of this site’s models that prints “—” there has no terms by part in the register file.', zh: '本站模型中这一栏写作“—”的行，登记册文件没有按部分给出它的条款。' };
// The count sentence's parts (methods/register.astro `coverage`), in order.
const COVERAGE = {
  en: { paged: 'each model and method with a page on this site', baselines: 'the other baselines measured here', directory: 'the models in the directory', others: 'the other models and papers whose official records we read' },
  zh: { paged: '在本站有页面的每个模型与方法', baselines: '本站测过的其他基线', directory: '模型目录中的模型', others: '我们读过官方记录的其他模型与论文' },
};
const coverageText = (lang, parts) => (lang === 'zh'
  ? (parts.length < 2 ? parts.join('') : `${parts.slice(0, -1).join('、')}，以及${parts.at(-1)}`)
  : (parts.length < 2 ? parts.join('') : `${parts.slice(0, -1).join(', ')}${parts.length > 2 ? ',' : ''} and ${parts.at(-1)}`));
// What a group note may claim only where every row of its group bears it out (open-register.ts `groupNotes`).
const NOTE_CLAIMS = { holds: { en: /with their holds/, zh: /并附暂缓原因/ }, records: { en: /official records reached/, zh: /官方记录所到/ } };
// A name with a Hugging Face user name in front ("<user>/<repo>").
const USER_PREFIX = /(?<![\w.-])[\w.-]+\/[\w.-]/;
const norm = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '');
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const longDate = (iso, lang) => { const [y, m, d] = iso.slice(0, 10).split('-').map(Number); return lang === 'zh' ? `${y} 年 ${m} 月 ${d} 日` : `${d} ${MONTHS[m - 1]} ${y}`; };
const badge = (lang, step, name) => (lang === 'zh' ? `模型核验 · 第 ${step} 步（共 5 步）· ${name}` : `Model ladder · step ${step} of 5 · ${name}`);
const gapText = (lang, step, label) => (lang === 'zh' ? `第 ${step} 步缺：${label}` : `gap at step ${step}: ${label}`);
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
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
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

export function checkModelRegister(distDir) {
  const DIST = resolve(distDir);
  assert.ok(existsSync(join(DIST, 'index.html')), `${DIST}: not a built site`);
  const read = p => readFileSync(join(DIST, p), 'utf8');
  const served = readdirSync(join(DIST, 'data')).filter(f => /^open-register-\d{8}\.json$/.test(f)).sort();
  assert.ok(served.length, 'a register file is served');
  const FILE = served.at(-1);
  const text = read(`data/${FILE}`);
  assert.equal(text, readFileSync(fileURLToPath(new URL(`../../public/data/${FILE}`, import.meta.url)), 'utf8'), `${FILE}: the served copy is public/data's`);
  const R = JSON.parse(text);
  // The release that ships the newest file is named by its date.
  const RELEASE = `open-register-update-${FILE.match(/(\d{8})/)[1]}`;
  assert.equal(R.release_id, RELEASE, 'the release');
  const rows = R.entries.filter(e => e.ladder === 'model');
  const byId = new Map(R.entries.map(e => [e.id, e]));
  const N = R.counts.rows, M = R.counts.models;
  const defs = R.level_definitions.model, items = R.item_definitions.model, dsDefs = R.level_definitions.dataset;
  // Every Hugging Face namespace the register names.
  const namespaces = new Set();
  for (const e of R.entries) {
    if (e.hf) namespaces.add(e.hf.repo.split('/')[0].toLowerCase());
    if (e.family) namespaces.add(e.family.uploader.toLowerCase());
    for (const a of e.aliases) if (a.value.includes('/') && ['hf_repo', 'eegdash_mirror', 'official_weights', 'weights_copy'].includes(a.kind)) namespaces.add(a.value.split('/')[0].toLowerCase());
  }

  let checks = 0;
  const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };
  // An item the placeholders, or a change requested of another package, have not met yet: owed while the file is
  // provisional, a failure once it is final. Each is kept by the row or name it concerns.
  const provisional = R.status === 'provisional';
  const owedItems = new Map();
  const owed = (cond, kind, item, msg) => {
    if (cond) { checks++; return; }
    assert.ok(provisional, `${msg} (the register file is final)`);
    if (!owedItems.has(kind)) owedItems.set(kind, new Set());
    owedItems.get(kind).add(item);
  };

  // The file's model rows: the counts add up; nothing owner decision D4 keeps off, as a field, a value or a link.
  ok(rows.length === N.model, `the file: ${rows.length} model rows, and its counts say ${N.model}`);
  ok([1, 2, 3, 4, 5].every(l => rows.filter(e => e.level === l).length === (N.model_by_level[String(l)] ?? 0)), 'the file: the model rows by step');
  ok(M.external_rows - M.merged_into_site_methods === rows.filter(e => e.kind === 'model').length, 'the file: the models and papers read, less those merged into a method page’s row');
  ok(rows.every(e => GROUPS.includes(e.kind)), 'the file: every model row in one of the two groups');
  const keys = new Set(); (function walk(v) { if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) { keys.add(k); walk(x); } })(rows);
  ok(![...keys].some(k => D4_KEYS.test(k)), `the file: a field owner decision D4 keeps off (${[...keys].filter(k => D4_KEYS.test(k))})`);
  ok(!D4_RE.test(JSON.stringify(rows)), 'the file: a model row carries what owner decision D4 keeps off');
  ok(rows.every(e => !e.venue || (!D4_YEAR.test(e.venue.value) && /^\d{4}-\d\d-\d\d$/.test(e.venue.checked))), 'the file: a venue owner decision D4 keeps off, or one with no checked date');
  ok(rows.every(e => !e.venue || (VENUE_EVIDENCE.includes(e.venue.evidence) && (e.venue.evidence !== 'official_proceedings' || /^https:\/\//.test(e.venue.url ?? '')))),
    'the file: a venue resting on evidence the #models sentence does not name, or proceedings with no address');

  // 3. The ladder's own step names: steps 1–4 apart from the dataset ladder's, in both languages.
  for (const s of ['1', '2', '3', '4']) ok(defs[s].en !== dsDefs[s].en && defs[s].zh !== dsDefs[s].zh && !Object.values(dsDefs).some(d => d.en === defs[s].en), `the model ladder's step ${s} has a name of its own (${defs[s].en})`);
  // A row's step is the furthest one whose key item is on file with every earlier step's; its gaps are the items
  // missing at that step or before (the #levels sentence). A step without items stands as its state says.
  const reached = (e, s) => {
    const se = e.step_evidence?.[String(s)];
    if (!se) return false;
    if (!se.items) return se.state === 'pass';
    const keyed = se.items.filter(i => items[i.item]?.anchor);
    return keyed.length > 0 && keyed.every(i => i.state === 'pass');
  };
  for (const e of rows) {
    let lvl = 0; for (const s of [1, 2, 3, 4, 5]) { if (reached(e, s)) lvl = s; }
    ok(lvl === e.level, `the file: ${e.id} is at step ${e.level}, and its key items reach step ${lvl}`);
    const missing = [1, 2, 3, 4, 5].filter(s => s <= e.level).flatMap(s => (e.step_evidence[String(s)].items ?? []).filter(i => i.state === 'gap').map(i => `${s}:${i.item}`)).sort();
    ok(JSON.stringify(missing) === JSON.stringify(e.gaps.map(g => `${g.step}:${g.item}`).sort()), `the file: ${e.id}'s gaps are the items missing at its step or before`);
  }
  const keyedSteps = [1, 2, 3, 4, 5].map(s => ({ s, all: Object.values(items).filter(i => i.step === s) }));
  ok(keyedSteps.every(x => x.all.some(i => i.anchor)), 'the file: every step has a key item');
  const keyedText = lang => keyedSteps.filter(x => x.all.length > 1).map(x => (lang === 'zh'
    ? `第 ${x.s} 步的关键项目是${x.all.filter(i => i.anchor).map(i => i.label_zh).join('、')}`
    : `at step ${x.s}, the ${x.all.filter(i => i.anchor).map(i => i.label_en).join(' and the ')}`));

  // /methods/ as built: its methods table (name by page), #other-evaluated and #unmeasured (name and anchor).
  const methodsEn = el(read('methods/index.html'), /<main\b/, '/methods/');
  const tableNames = new Map([...el(methodsEn, /<table>/, '/methods/').matchAll(/<th scope="row"><a href="(\/methods\/[a-z0-9-]+\/)"[^>]*>([^<]+)<\/a><\/th>/g)].map(m => [m[1], decode(m[2])]));
  ok(tableNames.size > 0, '/methods/: the methods table names its methods');
  const listed = id => [...el(methodsEn, new RegExp(`<section[^>]*aria-labelledby="${id}"`), '/methods/').matchAll(/<li\b([^>]*)>([\s\S]*?)<\/li>/g)]
    .map(m => ({ anchor: (m[1].match(/\sid="([^"]+)"/) ?? [])[1], name: decode((m[2].match(/<(?:a|span)\b[^>]*\slang="en"[^>]*>([^<]+)</) ?? [])[1] ?? '').replace(/\s*↗$/, '').trim() }));
  const baselines = listed('other-evaluated'), directory = listed('unmeasured');
  ok([...baselines, ...directory].every(m => m.name), '/methods/: every listed model has a name');
  const namesOf = e => [e.name, ...e.aliases.filter(a => a.kind === 'name').map(a => a.value)].map(norm);
  const rowNamed = (name, page) => rows.some(e => (page !== undefined && e.links.page === page) || namesOf(e).includes(norm(name)));
  // 12. The population: every model /methods/ names has a row.
  for (const [page, name] of tableNames) ok(rows.some(e => e.kind === 'site_model' && e.links.page === page), `the file: ${name} (${page}) has a row`);
  for (const m of baselines) owed(rowNamed(m.name), 'a row for each model /methods/ names', m.name, `the file: ${m.name}, a measured baseline on /methods/, has no row`);
  for (const m of directory) owed(rowNamed(m.name, m.anchor ? `/methods/#${m.anchor}` : undefined), 'a row for each model /methods/ names', m.name, `the file: ${m.name}, in the directory on /methods/, has no row`);
  const covers = { baselines: baselines.length > 0 && baselines.every(m => rowNamed(m.name)),
                   directory: directory.length > 0 && directory.every(m => rowNamed(m.name, m.anchor ? `/methods/#${m.anchor}` : undefined)) };
  const coverage = lang => coverageText(lang, ['paged', ...(covers.baselines ? ['baselines'] : []), ...(covers.directory ? ['directory'] : []),
                                               ...(rows.some(e => e.kind === 'model') ? ['others'] : [])].map(k => COVERAGE[lang][k]));
  // Each of this site's methods' rows is named as the methods table names it; no row name has a user name in front.
  for (const e of rows) {
    if (e.kind === 'site_model') {
      owed(tableNames.get(e.links.page) === e.name, 'a site row named as /methods/ names it', e.id, `the file: ${e.id} is named “${e.name}”, and /methods/ names it “${tableNames.get(e.links.page)}”`);
      owed(!USER_PREFIX.test(e.name), 'a site row named as /methods/ names it', e.id, `the file: ${e.id} is named with a user name (${e.name})`);
    } else ok(!USER_PREFIX.test(e.name), `the file: ${e.id} is named with a user name (${e.name})`);
    // Terms by part, kind and signal on every row.
    owed(!!e.terms_by_part, 'terms by part on every row', e.id, `the file: ${e.id} has no terms by part`);
    owed(!!e.model_kind && !!e.signal?.length, 'kind and signal on every row', e.id, `the file: ${e.id} has no kind or no signal`);
  }
  // Step 5 is held by exactly the methods in a row of a built protocol page's core-matrix table.
  const protoDir = join(DIST, 'protocols');
  const onProtocols = new Set(readdirSync(protoDir).filter(d => existsSync(join(protoDir, d, 'index.html'))).flatMap(d =>
    [...(read(`protocols/${d}/index.html`).match(/<table class="protocol-results[\s\S]*?<\/table>/g) ?? []).join('').matchAll(/<th scope="row">([\s\S]*?)<\/th>/g)].flatMap(m => [...m[1].matchAll(/href="(\/methods\/[a-z0-9-]+\/)"/g)].map(x => x[1]))));
  // The core matrix's rows without a method page (the ridge baselines), by name.
  const namedOnProtocols = new Set(readdirSync(protoDir).filter(d => existsSync(join(protoDir, d, 'index.html'))).flatMap(d => [...(read(`protocols/${d}/index.html`).match(/<table class="protocol-results[\s\S]*?<\/table>/g) ?? []).join('').matchAll(/<th scope="row">([\s\S]*?)<\/th>/g)].filter(m => !/href="\/methods\//.test(m[1])).map(m => norm(vis(m[1].replace(/<small>[\s\S]*?<\/small>|<sup[\s\S]*?<\/sup>/g, ' '))))));
  ok(onProtocols.size > 0, '/protocols/: rows name methods');
  for (const e of rows) {
    const inMatrix = (!!e.links.page && onProtocols.has(e.links.page)) || (e.kind === 'model' && namedOnProtocols.has(norm(e.name)));
    owed((e.level === 5) === inMatrix, 'step 5 exactly where a protocol page has the method’s row', e.id,
      `the file: ${e.id} is at step ${e.level}, and ${inMatrix ? 'a' : 'no'} protocol page has a row for it`);
  }

  // The rows in the page's order: this site's models furthest step first, then the others in the file's order.
  const expectedOrder = GROUPS.flatMap(g => {
    const m = rows.filter(e => e.kind === g);
    return g === 'site_model' ? [...m].sort((a, b) => b.level - a.level || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)) : m;
  }).map(e => e.id);
  // The counts strip's figures, in order (methods/register.astro): the steps that have rows, then the other ladder and
  // the models and papers read.
  const levels = [1, 2, 3, 4, 5].filter(l => N.model_by_level[String(l)] !== undefined);
  const countsOrder = [N.model, ...levels.map(l => N.model_by_level[String(l)]), N.dataset, M.external_rows, M.merged_into_site_methods];
  const builtPage = p => existsSync(join(DIST, p.replace(/^\//, ''), 'index.html'));
  const idsOf = new Map();
  const pageIds = p => { if (!idsOf.has(p)) idsOf.set(p, new Set([...read(join(p.replace(/^\//, ''), 'index.html')).matchAll(/\sid="([^"]+)"/g)].map(m => m[1]))); return idsOf.get(p); };

  const pages = {}, mains = {};
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}${PATH}`, zh = lang === 'zh';
    const loc = p => `${zh ? '/zh' : ''}${p}`;
    const html = read(`${pfx}${PATH}index.html`); pages[lang] = html;
    const main = el(html, /<main\b/, where); mains[lang] = main;
    const cite = el(main, /<section class="cite-page"/, where);
    const body = main.replace(cite, ' ');

    // 1. The page.
    ok(vis(el(main, /<h1\b/, where)) === H1[lang], `${where}: the h1`);
    ok(html.includes(`<title>${TITLE[lang]} · BCI Report</title>`), `${where}: the <title>`);
    for (const id of ['counts', 'levels', 'models']) ok(count(html, ` id="${id}"`) === 1 && new RegExp(`<section[^>]*\\sid="${id}"`).test(main), `${where}: #${id} once`);
    ok(main.includes(`<a href="${loc('/methods/')}">`), `${where}: the breadcrumb leads back to the methods`);

    // 2. The table.
    ok(count(main, '<table') === 1, `${where}: one table`);
    const table = el(main, /<table class="rg-table" data-register-table="model"/, where);
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
      ok(tb.indexOf(head) < tb.indexOf('<tr id='), `${where}: the ${g} heading comes first`);
      for (const [, id] of tb.matchAll(/<tr id="([^"]+)"/g)) { ok(byId.get(id)?.kind === g && byId.get(id)?.ladder === 'model', `${where}: ${id} sits in the ${g} group`); rendered.push(id); }
    }
    ok(JSON.stringify(rendered) === JSON.stringify(expectedOrder), `${where}: the rows rendered are the file's model rows, each once, in order (${rendered.length} of ${expectedOrder.length})`);
    ok(count(main, ' id="r-') === rendered.length, `${where}: no other row anchor`);

    // 3. Badges: the model ladder's, by class; no dataset badge.
    const badges = [...table.matchAll(/<span class="rg-badge rg-l(\d)">([^<]+)<\/span>/g)];
    ok(badges.length === rendered.length, `${where}: one badge per row`);
    for (const [, s, t] of badges) ok(decode(t) === badge(lang, Number(s), defs[s][zh ? 'zh' : 'en']), `${where}: a model badge naming the ladder (${decode(t)})`);
    ok(!(zh ? /第 \d 步（共 5 步）· (?:已列出|已读取|已追溯|已运行)/ : /Step \d of 5 · (?:Listed|Read|Traced|Run)\b/).test(vis(main)), `${where}: a dataset badge on the model register`);

    // 4. Each row.
    let fullRows = 0;
    for (const m of table.matchAll(/<tr id="(r-[^"]+)" data-g="([^"]+)" data-step="(\d)" data-terms="([01])" data-gap="([01])">([\s\S]*?)<\/tr>/g)) {
      const [, id, g, step, , gap, tr] = m, e = byId.get(id), w = `${where}#${id}`, t = vis(tr);
      fullRows++;
      ok(/^r-model-[a-z0-9-]+$/.test(id), `${w}: an opaque id`);
      ok(e.kind === g && String(e.level) === step && (e.gaps.length > 0 ? '1' : '0') === gap, `${w}: its group, step and gap flags`);
      const cells = [...tr.matchAll(/<(th|td)\b[^>]*>([\s\S]*?)<\/\1>(?=<t[hd]\b|$)/g)];
      ok(cells.length === 5 && /^<th scope="row">/.test(tr), `${w}: five cells, the first its name`);
      ok(tr.includes(esc(e.name)), `${w}: its name`);
      for (const gp of e.gaps) ok(t.includes(gapText(lang, gp.step, zh ? items[gp.item].label_zh : items[gp.item].label_en)), `${w}: its gap at step ${gp.step}`);
      // The status: as the file gives it where printed, and never a step name of either ladder; it may be left out
      // only where it restates the step (listed, published).
      const sw = tr.match(zh ? /<small>状态：([^<]+)<\/small>/ : /<small>Status: ([^<]+)<\/small>/)?.[1];
      if (sw === undefined) ok(['listed', 'published'].includes(e.status), `${w}: its status ${e.status} left out`);
      else {
        if (Object.values(STATUS[lang]).includes(decode(sw))) ok(decode(sw) === STATUS[lang][e.status], `${w}: its status`);
        owed(![...Object.values(dsDefs), ...Object.values(defs)].some(d => d[zh ? 'zh' : 'en'] === decode(sw)), 'a status word that is no step name', `${lang}:${decode(sw)}`,
          `${w}: its status “${decode(sw)}” is a step name`);
      }
      const mails = [...tr.matchAll(/href="(mailto:[^"]*)"/g)].map(x => decode(x[1]));
      ok(mails.length === 1 && mails[0] === `mailto:${MAIL}?subject=Register%20row%20${id}` && mails[0] === e.correction.mailto, `${w}: one correction mail naming its id alone`);
      // Terms by part: code, weights, data, in order; "not found" visible for every part that has none on record.
      const terms = cells[2][2];
      if (e.terms_by_part) {
        const lines = [...terms.matchAll(/<span class="rg-main">([\s\S]*?)<\/span>/g)].map(x => vis(x[1]));
        ok(lines.length === 3, `${w}: three parts in its terms`);
        PARTS.forEach((k, i) => {
          const p = e.terms_by_part[k], head = `${PART_NAME[lang][k]}${zh ? '：' : ': '}`;
          ok(lines[i]?.startsWith(head), `${w}: the ${k} part in its place`);
          if (p.state === 'stated') ok(p.value && terms.includes(`<code>${esc(p.value)}</code>`), `${w}: the ${k} terms as stated (${p.value})`);
          else ok(lines[i].startsWith(`${head}${PART_STATE[lang][p.state]}`), `${w}: the ${k} part says “${PART_STATE[lang][p.state]}”`);
        });
        const nf = PARTS.filter(k => e.terms_by_part[k].state === 'not_found').length;
        ok(count(terms, PART_STATE[lang].not_found) === nf, `${w}: “${PART_STATE[lang].not_found}” for each of its ${nf} parts with no terms`);
      } else {
        // Owed while the file is provisional (above): one of this site's models, linking its page, with "—" for terms.
        ok(e.kind === 'site_model' && e.links.page && vis(terms) === '—', `${w}: no terms by part, and not one of this site's models`);
      }
      ok((vis(cells[1][2]) === '—') === (!e.model_kind && !e.signal?.length), `${w}: its kind and signal, or “—” where the file gives neither`);
      // No two links of the name cell share an address (a venue and a paper link to one record are one link).
      const nameHrefs = [...cells[0][2].matchAll(/href="([^"]+)"/g)].map(x => decode(x[1]));
      owed(new Set(nameHrefs).size === nameHrefs.length, 'one link per address in a name cell', id, `${w}: two links of its name cell share an address`);
      // Its own page, venue, holds, exposure and result pages.
      if (e.links.page) ok(cells[0][2].includes(`href="${loc(e.links.page)}"`), `${w}: links its page ${e.links.page}`);
      // The venue's text, linked (" ↗") where the file gives the record's address.
      const venueAt = zh ? / 论文(?: ↗)? · 状态于 / : / paper(?: ↗)? · status checked /;
      ok(!e.venue === !venueAt.test(t), `${w}: a venue only where the file gives one`);
      if (e.venue) ok(t.includes(zh ? `${e.venue.value} 论文${e.venue.url ? ' ↗' : ''} · 状态于 ${longDate(e.venue.checked, lang)}核对` : `${e.venue.value} paper${e.venue.url ? ' ↗' : ''} · status checked ${longDate(e.venue.checked, lang)}`), `${w}: its venue with the date it was checked`);
      if (e.venue?.url) ok(cells[0][2].includes(`href="${esc(e.venue.url)}"`), `${w}: its venue linked to the official record`);
      const holds = e.findings.filter(f => f.code === 'hold').length;
      const nItems = e.findings.length + (e.exposure ? 1 : 0) + (e.links.cases?.length ? 1 : 0);
      ok(count(tr, '<li>') === nItems, `${w}: ${nItems} items in what we found (${count(tr, '<li>')})`);
      ok(count(t, zh ? '暂缓：' : 'Held: ') === holds, `${w}: its ${holds} holds`);
      if (e.exposure) ok(t.includes(EXPOSURE[lang][e.exposure]), `${w}: its pretraining exposure`);
      for (const c of e.links.cases ?? []) {
        ok(tr.includes(`href="${loc(c)}"`), `${w}: links its result ${c}`);
        const [p, a] = loc(c).split('#');
        ok(builtPage(p) && pageIds(p).has(a), `${w}: ${loc(c)} is a built anchor`);
      }
      ok(figAttrs(tr).length === 0, `${w}: no figure in a model row`);
      // The rows the plan names.
      if (id === NEUROLM) {
        ok(e.level === 4 && JSON.stringify(e.links.cases) === JSON.stringify(NEUROLM_CASES) && e.exposure === 'unknown', `${w}: NeuroLM-B at step 4, linking both pilots, exposure unknown`);
      }
      if (PAGED_NO_VENUE[id]) ok(e.links.page === PAGED_NO_VENUE[id] && !e.venue, `${w}: links ${PAGED_NO_VENUE[id]}, with no venue`);
      if (HELD.includes(id)) ok(holds > 0, `${w}: at its step with its holds`);
      // The 20261028 round's rows.
      if (SCORED[id]) {
        ok(e.level === 4 && e.kind === 'model' && !e.links.page && !e.venue && JSON.stringify(e.links.cases) === JSON.stringify([SCORED[id]]) && e.exposure === 'unknown',
          `${w}: at step 4, linking ${SCORED[id]}, exposure unknown, no method page and no venue`);
        ok(!e.aliases.some(a => a.kind === 'weights_copy') && !t.includes(zh ? '权重副本' : 'Weights copies'), `${w}: the authors' weights only, no copy`);
        ok(t.includes(EXPOSURE[lang].unknown), `${w}: prints its pretraining exposure`);
        if (id === 'r-model-axon') ok(!e.urls.paper && !cells[0][2].includes(zh ? '>论文' : '>Paper'), `${w}: no paper cited until it is checked`);
      }
      // A terms value is licence codes only: words about it come from the page's own vocabulary, in each language.
      ok(!Object.values(e.terms_by_part ?? {}).some(p => /[()]/.test(p.value ?? '')), `${w}: its terms are licence codes, with no words of their own in parentheses`);
      if (IDENTIFIED[id]) {
        ok(e.level === 1 && !e.venue && JSON.stringify(e.findings) === JSON.stringify([{ code: 'hold', params: { reason_code: IDENTIFIED[id] } }]),
          `${w}: at step 1, held (${IDENTIFIED[id]}), no venue`);
        ok(e.urls.paper && cells[0][2].includes(`href="${esc(e.urls.paper)}"`), `${w}: its paper linked`);
        ok(holds === 1, `${w}: its hold printed`);
      }
    }
    ok(fullRows === rendered.length, `${where}: every row parsed (${fullRows})`);
    for (const id of [NEUROLM, ...Object.keys(PAGED_NO_VENUE), ...HELD]) ok(rendered.includes(id), `${where}: the row ${id}`);
    if (R.release_id >= 'open-register-update-20261028') {
      for (const id of [...Object.keys(SCORED), ...Object.keys(IDENTIFIED)]) ok(rendered.includes(id), `${where}: the row ${id}`);
      const fame = byId.get('r-model-fame'), lfame = byId.get('r-site-lfame');
      ok(fame?.ladder === 'model' && lfame?.ladder === 'dataset' && fame.name !== lfame.name, `${where}: FAME, a model row apart from the L-FAME dataset row`);
    }

    // 5. Links and anchors.
    const ids = [...main.matchAll(/\sid="([^"]+)"/g)].map(x => x[1]);
    ok(new Set(ids).size === ids.length, `${where}: every id once`);
    for (const id of ids) ok(/^(?:r-model-[a-z0-9-]+|group-[a-z_]+|[a-z]+(?:-[a-z]+)*-heading|counts|levels|models|register-files|cite|entity-content)$/.test(id), `${where}: the anchor "${id}" is opaque`);
    for (const [, raw] of body.matchAll(/href="([^"]+)"/g)) {
      const href = decode(raw);
      if (/^https?:/.test(href)) {
        const u = new URL(href);
        if (/(^|\.)huggingface\.co$/.test(u.hostname)) {
          ok(/^\/(?:datasets|models)$/.test(u.pathname) && [...u.searchParams.keys()].join() === 'search', `${where}: a Hugging Face link other than a search: ${href}`);
          const q = u.searchParams.get('search').toLowerCase();
          ok(![...namespaces].some(ns => q === ns || q.startsWith(`${ns}/`)), `${where}: a search for a user name: ${href}`);
          ok(!u.pathname.toLowerCase().split('/').some(s => namespaces.has(s)), `${where}: a user name in a link: ${href}`);
        }
        ok(!D4_PAGE.test(u.hostname), `${where}: a link owner decision D4 keeps off: ${href}`);
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

    // 6. Figures: each a value of the register file, read from the field the strip names.
    let figs = 0;
    for (const [, file, f, raw, t] of main.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)) {
      ok(file === FILE && f === 'count', `${where}: a figure from ${file} as ${f}`);
      ok(t === fmtCount(Number(raw)), `${where}: ${raw} printed as "${t}"`);
      figs++;
    }
    const counts = el(main, /<section[^>]*\sid="counts"/, where);
    ok(JSON.stringify(figAttrs(counts).map(a => Number(a.split('|')[2]))) === JSON.stringify(countsOrder), `${where}: the counts strip prints the file's counts in order (${figAttrs(counts).map(a => a.split('|')[2])})`);
    ok(figs === countsOrder.length, `${where}: no figure outside the counts strip (${figs})`);
    const rowsItem = vis(el(counts, /<li data-rg-count="rows">/, where));
    for (const l of [1, 2, 3, 4, 5].filter(l => !levels.includes(l))) ok(rowsItem.includes(zh ? `第 ${l} 步没有` : `none at step ${l}`), `${where}: step ${l}, with no rows, said in words`);
    ok(rowsItem.includes(zh ? `模型登记共 ${fmtCount(N.model)} 行` : `${fmtCount(N.model)} rows on the model ladder`), `${where}: the model rows`);
    // 12. The count sentence names exactly the parts of /methods/ the rows cover.
    ok(rowsItem.includes(zh ? `行：${coverage(lang)}。` : `rows on the model ladder: ${coverage(lang)}.`), `${where}: the rows described as what they cover (${coverage(lang)})`);
    ok(vis(el(counts, /<li data-rg-count="tracked">/, where)).includes(zh ? '已并入该方法的那一行' : 'are merged into that method’s row'), `${where}: the records merged into a method's row`);
    ok(counts.includes(`href="${loc('/datasets/register/')}"`), `${where}: the counts link the dataset register`);
    for (const d of [...new Set(rows.map(e => e.checked))]) ok(rowsItem.includes(longDate(d, lang)), `${where}: the date ${d} the rows were checked`);

    // 7. #levels.
    const lv = el(main, /<section[^>]*\sid="levels"/, where);
    const dts = [...lv.matchAll(/<dt><span class="rg-badge rg-l(\d)">([^<]+)<\/span><\/dt><dd>([^<]+)<\/dd>/g)];
    ok(dts.length === 5, `${where}: five steps`);
    for (const [, s, label, needs] of dts) {
      const d = defs[s];
      ok(decode(label) === (zh ? `第 ${s} 步 · ${d.zh}` : `Step ${s} · ${d.en}`), `${where}: step ${s}'s name`);
      ok(decode(needs) === (zh ? d.needs_zh : d.needs_en), `${where}: what step ${s} needs, as the file says it`);
    }
    const rules = [...el(lv, /<ul class="rg-rules">/, where).matchAll(/<li>([^<]+)<\/li>/g)].map(x => decode(x[1]));
    const want = RULES.map(id => R.rules.find(r => r.id === id)).map(r => (zh ? r.zh : r.en));
    ok(JSON.stringify(rules) === JSON.stringify(want), `${where}: the file's rules for every row`);
    for (const r of R.rules) ok(count(vis(main), zh ? r.zh : r.en) === (RULES.includes(r.id) ? 1 : 0), `${where}: the rule "${r.id}" ${RULES.includes(r.id) ? 'once' : 'left to the dataset register'}`);
    ok(lv.includes(`href="${loc('/datasets/register/')}#levels"`), `${where}: the dataset ladder's rules linked`);
    // The step sentence: the key item, and the gaps at the row's step or before (as the file's rows bear out above).
    const kt = keyedText(lang);
    const stepSentence = zh
      ? `一行所在的步骤，是关键项目已在案的最远一步${kt.length ? `（${kt.join('；')}）` : ''}；该步及之前各步缺少的项目作为缺口，列在步骤标记旁边。`
      : `A row’s step is the furthest one whose key item is on file${kt.length ? ` (${kt.join('; ')})` : ''}; an item still missing at its step or an earlier one is listed beside the badge as a gap.`;
    ok(vis(lv).includes(stepSentence), `${where}: the step sentence (${stepSentence})`);
    ok(vis(lv).includes(zh ? '步骤名称与数据集登记的不同' : 'five steps with names of their own'), `${where}: the steps named apart from the dataset ladder's`);
    // #models: the terms sentence, with what a "—" means while a row carries no terms by part; the venue sentence.
    const intro = vis(el(el(main, /<section[^>]*\sid="models"/, where), /<div class="topic-heading">/, where));
    const partless = rows.filter(e => !e.terms_by_part).length;
    ok(intro.includes(TERMS_SENTENCE[lang]) && intro.includes(DASH_SENTENCE[lang]) === partless > 0, `${where}: the terms sentence, ${partless ? 'with' : 'without'} what “—” means`);
    ok(intro.includes(VENUE_SENTENCE[lang]), `${where}: the venue sentence`);
    // The group notes claim holds, and steps reached through official records, only where every row bears it out.
    for (const g of GROUPS) {
      const note = vis(el(el(table, new RegExp(`<tbody id="group-${g}"`), where), /<small class="rg-note">/, where));
      const members = rows.filter(e => e.kind === g);
      if (NOTE_CLAIMS.holds[lang].test(note)) owed(members.every(e => e.findings.some(f => f.code === 'hold')), 'group notes that every row bears out', `${g}:holds`,
        `${where}: the ${g} note says each row has holds, and ${members.filter(e => !e.findings.some(f => f.code === 'hold')).map(e => e.id)} has none`);
      if (NOTE_CLAIMS.records[lang].test(note)) owed(members.every(e => e.level <= 2), 'group notes that every row bears out', `${g}:records`,
        `${where}: the ${g} note says the rows stop where their official records reached, and ${members.filter(e => e.level > 2).map(e => e.id)} went further`);
    }
    ok(lv.includes('href="/data-use/#register-corrections"'), `${where}: how corrections are handled`);

    // 8. Filter, CSP, tables, hreflang, cite, markup.
    const form = el(main, /<form class="rg-filter" data-register-filter="model" hidden>/, where);
    for (const n of ['g', 'step', 'terms']) ok(form.includes(`<select name="${n}">`), `${where}: the ${n} filter`);
    ok(JSON.stringify([...el(form, /<select name="g">/, where).matchAll(/<option value="([^"]+)">/g)].map(x => x[1])) === JSON.stringify(GROUPS), `${where}: the group filter's choices`);
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
      ok(cat && cat.url === `https://bci.report/${PATH}` && !('dataset' in cat) && cat.hasPart.length === rows.length && cat.hasPart.every(d => d['@type'] === 'CreativeWork'), `${where}: a DataCatalog whose parts are the model rows`);
      ok(!JSON.stringify(ld).includes('isBasedOn') && !JSON.stringify(ld).includes('"Dataset"'), `${where}: never a Dataset, never isBasedOn`);
      cat.hasPart.forEach((d, i) => {
        // No "<user>/" in any name; each of this site's methods named as the methods table names it.
        ok(!USER_PREFIX.test(d.name), `${where}: a user name in the markup (${d.name})`);
        const e = rows[i];
        if (e.kind === 'site_model') ok(d.name === tableNames.get(e.links.page) && d.url === `https://bci.report${e.links.page}`, `${where}: ${e.id} named in the markup as /methods/ names it (${d.name})`);
        ok(typeof d.description === 'string' && d.description.length >= 50 && d.description.length <= 5000, `${where}: ${d.name} has a description`);
        if (d.url && /huggingface\.co/.test(d.url)) { const u = new URL(d.url); ok(/^\/(?:datasets|models)$/.test(u.pathname) && !namespaces.has(u.searchParams.get('search').toLowerCase()), `${where}: the markup links no user name (${d.url})`); }
      });
    }

    // 9. Words.
    const md = existsSync(join(DIST, `${pfx}${PATH}index.md`)) ? read(`${pfx}${PATH}index.md`) : '';
    const all = html + md;
    // A public address may hold such a segment: the paths are looked for outside addresses.
    const noUrls = all.replace(/https?:\/\/[^\s"<>)]+/g, ' ');
    for (const bad of ['/Us' + 'ers/', '/ho' + 'me/', '/Vol' + 'umes/', '/m' + 'nt/', 'tr' + 'x50', 'Ga' + 'l4', 'BCI' + '_Arena'])
      ok(!noUrls.includes(bad), `${where}: "${bad}" never appears`);
    ok(!D4_PAGE.test(all), `${where}: nothing owner decision D4 keeps off`);
    ok(!new RegExp(`\\b${'tw' + 'u'}\\b`).test(all), `${where}: no private user name`);
    ok(!/(?<![\d.])55 ?%|fifty[- ]five per|五十五/.test(vis(all)), `${where}: no 55%`);
    const words = s => (s.toLowerCase().match(/[a-z]+/g) ?? []);
    ok(!words(all).some(x => COMMENTER.has(hash('sha256').update(x).digest('hex'))), `${where}: the thread commenter is not named`);
    // The page's own words: the rows' names and the stated terms are the sources' own.
    const own = vis(body.replace(/<th scope="row">[\s\S]*?<\/th>/g, ' ').replace(/“[^”]*”/g, ' ').replace(/<code>[^<]*<\/code>/g, ' '));
    ok(!D4_OWN.test(own), `${where}: nothing owner decision D4 keeps off, in the page's own words`);
    for (const re of UPDATE_RULES) { const x = vis(main.replace(cite, ' ')).match(re); ok(!x, `${where}: an update date or version label: “${x?.[0]}”`); }
    ok(!(zh ? /最佳|最好|胜出|排名|第一名/ : /\b(?:best|worst|top|winner|leader|outperform\w*|beats?|ranks?|ranked|ranking)\b/i).test(own), `${where}: no ranking word`);
    if (!zh) ok(!/, not\b/.test(own), `${where}: no ", not" hedge`);
    if (zh) {
      const zhText = vis(dropEnglish(body));
      for (const bad of REJECTED_ZH) ok(!zhText.includes(bad), `${where}: "${bad}" is a rejected rendering`);
      ok(!/[一-鿿\d]\.<\/p>/.test(dropEnglish(main)), `${where}: no ASCII full stop after Chinese`);
      const spaced = vis(main).match(/[一-鿿] 和|和 [一-鿿]/); ok(!spaced, `${where}: a spaced 和 between Chinese words (“${spaced?.[0]}”)`);
      const glued = vis(main).match(/和\d|\d和/); ok(!glued, `${where}: 和 glued to a figure or date (“${glued?.[0]}”)`);
      const seq = vis(main).match(/(?:数据集|模型|两个|本)序列/); ok(!seq, `${where}: 序列 for a ladder (“${seq?.[0]}”)`);
      // A full-width colon takes no space after it (the markup is read as written: a tag is not a space).
      const colons = [...main.matchAll(/：(?:[ \u00a0]|&nbsp;)+/g)].length;
      owed(colons === 0, 'no space after a full-width colon', `${lang}: ${colons}`, `${where}: ${colons} full-width colons with a space after them`);
    }

    // 10. The Markdown copy.
    ok(md.length > 0, `${where}index.md: the Markdown copy`);
    const head = `| ${COLUMNS[lang].join(' | ')} |`;
    ok(md.includes(head), `${where}index.md: the table's header`);
    const tableMd = md.slice(md.indexOf(head)).split('\n\n')[0].split('\n').slice(2);
    ok(tableMd.length === rows.length + GROUPS.length, `${where}index.md: every row and group heading (${tableMd.length})`);
    for (const id of rendered) ok(md.includes(`subject=Register%20row%20${id})`), `${where}index.md: the row ${id}`);
    for (const v of numTexts(main)) ok(md.includes(decode(v)), `${where}index.md: figure "${v}"`);
  }
  // English and Chinese print the same figures, in the same order.
  assert.deepEqual(figAttrs(mains.zh), figAttrs(mains.en), 'the same figures in English and Chinese, in order'); checks++;
  assert.deepEqual(numTexts(mains.zh), numTexts(mains.en), 'the same figure texts in English and Chinese'); checks++;

  // 11. /methods/: one link line, its figure the model row count; its first table keeps three columns. The dataset
  // register links the model register.
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', where = `/${pfx}methods/`;
    const main = el(read(`${pfx}methods/index.html`), /<main\b/, where);
    const line = el(main, /<p class="citation-note" id="register-line">/, where);
    ok(count(main, `/${pfx}methods/register/`) === 1 && line.includes(`href="/${pfx}methods/register/"`), `${where}: one link to the model register, in its line`);
    ok(figAttrs(line).join() === `${FILE}|count|${N.model}`, `${where}: the line prints the model row count`);
    ok(vis(line).includes(lang === 'zh' ? '模型登记册' : 'The model register'), `${where}: the line names the model register`);
    ok(main.indexOf(line) < main.indexOf('<table'), `${where}: the line sits above the first table`);
    ok(count(el(el(main, /<table>/, where), /<thead>/, where), '<th scope="col">') === 3, `${where}: the methods table keeps its three columns`);
    const ds = el(read(`${pfx}datasets/register/index.html`), /<main\b/, `/${pfx}datasets/register/`);
    ok(ds.includes(`href="/${pfx}methods/register/"`), `/${pfx}datasets/register/: links the model register`);
  }

  // 12. Weight.
  const weight = Object.fromEntries(['en', 'zh'].map(l => [l, { bytes: Buffer.byteLength(pages[l]), gzip: gzipSync(pages[l]).length }]));
  for (const l of ['en', 'zh']) ok(weight[l].bytes < 300_000 && weight[l].gzip < 60_000, `/${l === 'zh' ? 'zh/' : ''}${PATH}: ${weight[l].bytes} bytes, ${weight[l].gzip} gzipped`);
  const owing = [...owedItems].map(([kind, set]) => ({ kind, items: [...set] }));
  return { checks, rows: rows.length, figures: figAttrs(mains.en).length, file: FILE, weight, provisional, owing };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/model-register.mjs <build dir>'); process.exit(2); }
  const { checks, rows, figures, file, weight, provisional, owing } = checkModelRegister(dir);
  const owed = owing.length
    ? ` Owed while the register file is provisional (each fails once it is final): ${owing.map(o => `${o.kind} (${o.items.length}: ${o.items.join(', ')})`).join('; ')}.`
    : '';
  console.log(`PASS: model register — /methods/register/ in both languages, ${checks} checks: ${rows} model rows of ${file}${provisional ? ' (provisional)' : ''}, each once under its opaque id in two groups with their heading rows; the model ladder's own step names, every badge naming the ladder, every row at the step its key items reach with its gaps; terms by part with "not found" where a part has none on record; venues only from the proceedings or the camera-ready paper, none owner decision D4 keeps off; holds, exposure, and NeuroLM-B linking both pilots; ${figures} figures per page, every one the field it names and the same in English and Chinese; the count, step, terms and venue sentences as the rows bear them out; the steps and the rules for every row once; the filter hidden until its module runs; no Hugging Face user name in any link, anchor or markup name; DataCatalog markup with CreativeWork parts, this site's methods named as /methods/ names them; the Markdown copy with every row; the /methods/ line. Weight: ${weight.en.bytes.toLocaleString('en-US')} bytes (${weight.en.gzip.toLocaleString('en-US')} gzipped) in English, ${weight.zh.bytes.toLocaleString('en-US')} (${weight.zh.gzip.toLocaleString('en-US')}) in Chinese.${owed}`);
}
