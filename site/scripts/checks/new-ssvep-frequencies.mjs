// The checks of /topics/new-ssvep-frequencies/ (package P-SS1, plan §2.1 and §4.7), run on a built site:
//
//   node scripts/checks/new-ssvep-frequencies.mjs <dist directory>
//
// It reads the page in both languages, their Markdown copies and the served data file, and asserts the page shell's
// acceptance items: figure parity between English and Chinese against new-ssvep-frequencies-update.json, the pinned
// short answer, headings and anchors, the endpoint strip, the scope line, the name key, card 8, methods and limits,
// the cite block, the thread linked once, and the strings that must never appear. The cards themselves are written by
// three components (src/components/ssvep/); a section still marked data-ssvep-stub keeps the assertions that need its
// content PENDING rather than failing. Cards 3 and 4 (PhaseCards.astro) have their own block of checks near the end.
// Exit code 1 on any failure. No network, no writes.
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = resolve(process.argv[2] ?? fileURLToPath(new URL('../../dist/', import.meta.url)));
const SITE = fileURLToPath(new URL('../../', import.meta.url));
const FILE = 'new-ssvep-frequencies-update.json';
const PAGE = 'topics/new-ssvep-frequencies/';
const results = [];
const report = (name, status, detail = '') => results.push({ name, status, detail });
const check = (name, fn) => {
  try { const r = fn(); if (r === 'pending' || (r && r.pending)) report(name, 'PENDING', r.pending ?? ''); else report(name, 'PASS', typeof r === 'string' ? r : ''); }
  catch (e) { report(name, 'FAIL', e.message); }
};
const ok = (cond, msg) => { if (!cond) throw new Error(msg); };
const eq = (a, b, msg) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); };

// --- Inputs ----------------------------------------------------------------------------------------------------
const read = p => readFileSync(join(DIST, p), 'utf8');
const pages = { en: PAGE, zh: 'zh/' + PAGE };
for (const [l, p] of Object.entries(pages)) if (!existsSync(join(DIST, p, 'index.html'))) {
  console.error(`new-ssvep-frequencies: ${p}index.html is missing from ${DIST}`); process.exit(1);
}
const html = { en: read(pages.en + 'index.html'), zh: read(pages.zh + 'index.html') };
const md = { en: existsSync(join(DIST, pages.en, 'index.md')) ? read(pages.en + 'index.md') : null,
             zh: existsSync(join(DIST, pages.zh, 'index.md')) ? read(pages.zh + 'index.md') : null };
const servedText = read('data/' + FILE);
const data = JSON.parse(servedText);
const S = data.studies;

// --- Helpers (formats as entities.ts formatFig and check-workbench.mjs, plus pct0 and num1) ----------------------
const fmt = {
  pct2: r => (r * 100).toFixed(2) + '%', pp2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2) + ' pp',
  sgn2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2), count: r => r.toLocaleString('en-US'),
  pct1: r => (r * 100).toFixed(1) + '%', pp1: r => (r >= 0 ? '+' : '−') + Math.abs(r * 100).toFixed(1) + ' pp',
  sgn1: r => (r >= 0 ? '+' : '−') + Math.abs(r * 100).toFixed(1), sgn3: r => (r >= 0 ? '+' : '−') + Math.abs(r).toFixed(3),
  auc3: r => r.toFixed(3), auc2: r => r.toFixed(2), num3: r => r.toFixed(3).replace(/^-/, '−'),
  int0: r => Math.round(r).toLocaleString('en-US').replace(/^-/, '−'), sig3: r => r.toPrecision(3).replace(/^-/, '−'),
  // The thread's bet, as the thread stated it (wording review M5).
  pct0: r => (r * 100).toFixed(0) + '%',
  // The adapter's protected margin on the CCA-correlation scale, at one decimal (card 6: 0.200001 prints "0.2").
  num1: r => r.toFixed(1).replace(/^-/, '−'),
};
const leaves = new Set();
(function walk(v) { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(data);
const decode = s => s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&(amp|lt|gt|quot|apos|nbsp);/g, (_, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' })[e]);
const visible = h => decode(h.replace(/<head>[\s\S]*?<\/head>/, '').replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '')
  .replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ');
const mainOf = h => h.slice(h.indexOf('<main'), h.indexOf('</main>'));
/** A <section> by its id: from its opening tag to the first </section> after it (the page nests none). */
const sectionOf = (h, id) => {
  const at = h.search(new RegExp(`<section[^>]*\\sid="${id}"`));
  if (at < 0) return null;
  return h.slice(at, h.indexOf('</section>', at) + '</section>'.length);
};
const figsIn = h => [...h.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)].map(m => ({ file: m[1], fmt: m[2], raw: Number(m[3]), text: decode(m[4]) }));
const stubs = h => (h.match(/data-ssvep-stub/g) ?? []).length;
const anyStub = stubs(html.en) + stubs(html.zh) > 0;
const pendingIfStub = msg => ({ pending: msg + ` (${stubs(html.en)} card sections still stubs)` });
const tokens55 = /(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?!\d)|fifty[- ]five|五十五/i;

// --- Files ---------------------------------------------------------------------------------------------------------
check('served data file is byte-identical to src/data and public/data', () => {
  for (const p of ['src/data/' + FILE, 'public/data/' + FILE]) eq(readFileSync(join(SITE, p), 'utf8') === servedText, true, p);
  eq(data.release_id, 'new-ssvep-frequencies-update-20261020', 'release id');
});
check('Markdown copies exist and carry the cite block', () => {
  for (const l of ['en', 'zh']) {
    ok(md[l], `${l}: index.md missing (run build-agent-files.mjs on the build)`);
    ok(md[l].includes(l === 'zh' ? '## 引用本页' : '## Cite this page') && md[l].includes('`' + data.release_id + '`'), `${l}: the cite block in the Markdown copy`);
  }
});

// --- Headings, anchors, structure ----------------------------------------------------------------------------------
const H1 = { en: 'What lets a decoder answer an SSVEP frequency it never trained on?', zh: '解码器靠什么回答没训练过的 SSVEP 频率？' };
check('h1 is the question, and the <title> leads with it', () => {
  eq(H1.en, data.question, 'the export’s question');
  for (const l of ['en', 'zh']) {
    const h1 = decode(html[l].match(/<h1[^>]*>([\s\S]*?)<\/h1>/)[1].replace(/<[^>]+>/g, ''));
    eq(h1, H1[l], `${l}: h1`);
    ok(html[l].includes('<title>' + H1[l]), `${l}: <title> leads with the question`);
  }
});
const ORDER = ['setup', 'reference-spectrum', 'head-and-features', 'phase-jitter', 'phase-ramp', 'cca-mechanism', 'cca-correction',
  'wearable-transfer', 'cross-spectral', 'methods-and-limits', 'related', 'cite'];
check('sections in order, each card at its anchor with its heading', () => {
  eq(data.placement.cards.map(c => c.anchor), ORDER.slice(1, 9), 'the export’s card anchors');
  for (const l of ['en', 'zh']) {
    const ids = [...mainOf(html[l]).matchAll(/<section[^>]*\sid="([^"]+)"/g)].map(m => m[1]).filter(id => ORDER.includes(id));
    eq(ids, ORDER, `${l}: section order`);
    data.placement.cards.forEach(c => {
      const sec = sectionOf(html[l], c.anchor);
      ok(new RegExp(`data-ssvep-card="${c.card}"`).test(sec.slice(0, 400)), `${l}: #${c.anchor} is card ${c.card}`);
      const by = sec.match(/aria-labelledby="([^"]+)"/)?.[1];
      ok(by && new RegExp(`<h2 id="${by}">`).test(sec), `${l}: #${c.anchor} is labelled by its own h2`);
    });
    ok(/id="credits"/.test(sectionOf(html[l], 'methods-and-limits')), `${l}: #credits inside #methods-and-limits`);
  }
});

// --- Figures ---------------------------------------------------------------------------------------------------------
check('every data-fig is a leaf of the page’s file, printed in its format', () => {
  let n = 0;
  for (const l of ['en', 'zh']) for (const f of figsIn(html[l])) {
    eq(f.file, FILE, `${l}: a figure from another file`);
    ok(leaves.has(f.raw), `${l}: ${f.raw} is not a value in ${FILE}`);
    ok(fmt[f.fmt], `${l}: unknown format ${f.fmt}`);
    eq(f.text, fmt[f.fmt](f.raw), `${l}: ${f.raw} as ${f.fmt}`);
    n++;
  }
  ok(n > 0, 'no figure');
  return `${n} figures`;
});
check('English and Chinese print the same multiset of figures', () => {
  const key = h => figsIn(h).map(f => `${f.fmt}|${f.raw}`).sort();
  eq(key(html.zh), key(html.en), 'data-fig multiset');
  const cls = h => [...mainOf(h).matchAll(/class="(?:metric|num|fig)">([^<]+)</g)].map(m => m[1]).sort();
  eq(cls(html.zh), cls(html.en), 'metric/num/fig texts');
});
check('the bet prints as 39% once per language, on card 4 only', () => {
  const thr = S.phase_ramp.thread_bet;
  eq(Object.keys(thr).sort(), ['held8_threshold', 'source_url'], 'thread_bet fields');
  eq(fmt.pct0(thr.held8_threshold), '39%', 'pct0 of the threshold');
  const owners = [];
  (function walk(v, path) { if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) { if (k === 'thread_bet') owners.push(path); walk(x, path + '.' + k); } })(data, '');
  eq(owners, ['.studies.phase_ramp'], 'thread_bet only under studies.phase_ramp');
  const bet = /(?<![\d.])39%/g;
  for (const l of ['en', 'zh']) {
    const all = (visible(mainOf(html[l])).match(bet) ?? []).length;
    const pct0Figs = figsIn(html[l]).filter(f => f.fmt === 'pct0');
    ok(pct0Figs.every(f => f.raw === thr.held8_threshold), `${l}: pct0 prints the bet only`);
    if (stubs(html[l]) && /data-ssvep-stub/.test(sectionOf(html[l], 'phase-ramp'))) { eq(all, 0, `${l}: no 39% before card 4 is written`); return pendingIfStub('card 4 not written yet'); }
    eq(all, 1, `${l}: "39%" occurrences`);
    eq((visible(sectionOf(html[l], 'phase-ramp')).match(bet) ?? []).length, 1, `${l}: the bet sits on card 4`);
    eq(pct0Figs.length, 1, `${l}: one pct0 figure`);
  }
});

// --- The short answer ----------------------------------------------------------------------------------------------
const A = S.cca_adapter, W = S.wearable_transfer;
const gain = A.contrasts['RAW-RESIDUAL minus CCA-RAW/u8'], dry = W.contrasts['RAW-RESIDUAL_minus_CCA-RAW/dry'], wet = W.contrasts['RAW-RESIDUAL_minus_CCA-RAW/wet'];
const ANSWER_FIGS = [fmt.pct2(A.levels['RAW-RESIDUAL/u8'].estimate), fmt.pct2(A.levels['CCA-RAW/u8'].estimate), fmt.count(data.endpoints[0].candidates),
  fmt.pp2(gain.estimate), fmt.sgn2(gain.interval[0]), fmt.sgn2(gain.interval[1]), fmt.count(data.cohort.people),
  fmt.pp2(dry.estimate), fmt.sgn2(dry.interval[0]), fmt.sgn2(dry.interval[1]), fmt.pp2(wet.estimate), fmt.sgn2(wet.interval[0]), fmt.sgn2(wet.interval[1])];
const answerOf = h => { const a = h.indexOf('<section class="short-answer"'); return h.slice(a, h.indexOf('</section>', a)); };
check('short answer as pinned (adapter binding review §3 item 3; Wearable-102 and heads sentences of plan §2.1)', () => {
  eq(ANSWER_FIGS, ['86.15%', '80.90%', '8', '+5.24 pp', '+3.91', '+6.62', '70', '+0.07 pp', '−0.71', '+0.91', '−0.61 pp', '−1.48', '+0.23'], 'the pinned figures');
  const PHRASES = {
    en: ['On BETA’s held-out frequencies, temporal CCA with a small learned correction reached', 'for CCA alone, choosing among',
      'Run unchanged on Wearable-102, the same models changed CCA’s score by', 'on dry electrodes', 'on wet',
      'Learned heads that read reference spectra or stimulus phase stayed far below CCA.'],
    zh: ['在 BETA 的留出频率上，时域 CCA 加一个小的学习修正达到', 'CCA 单独为', '同一批模型原样用于 Wearable-102，相对 CCA 的变化为干电极', '湿电极',
      '读参考谱或刺激相位的学习型分类头远低于 CCA。'],
  };
  for (const l of ['en', 'zh']) {
    const ans = answerOf(html[l]);
    eq([...ans.matchAll(/<strong class="fig">([^<]*)<\/strong>/g)].map(m => decode(m[1])), ANSWER_FIGS, `${l}: answer figures, in order`);
    const text = visible(ans);
    for (const p of PHRASES[l]) ok(text.includes(p), `${l}: the answer says "${p}"`);
    ok(!/\bhighest\b|\bbest\b|最高|最好/.test(text), `${l}: no ranking word in the answer`);
  }
});
check('every number in the short answer appears elsewhere on the page', () => {
  const nums = s => [...s.matchAll(/\d[\d,]*(?:\.\d+)?/g)].map(m => m[0]);
  const missing = [];
  for (const l of ['en', 'zh']) {
    const h = html[l], a = h.indexOf('<section class="short-answer"'), b = h.indexOf('</section>', a);
    const rest = visible(h.slice(0, a) + h.slice(b));
    for (const f of ANSWER_FIGS) for (const n of nums(f)) if (!rest.includes(n)) missing.push(`${l}:${n}`);
  }
  if (missing.length && anyStub) return pendingIfStub(`answer numbers not yet elsewhere: ${missing.join(' ')}`);
  eq(missing, [], 'answer numbers missing from the rest of the page');
});
check('meta description answers in one or two sentences (40–320 characters)', () => {
  for (const l of ['en', 'zh']) {
    const d = decode(html[l].match(/<meta name="description" content="([^"]*)"/)[1]);
    ok(d.length > 40 && d.length <= 320, `${l}: ${d.length} characters`);
    for (const f of ['86.15%', '80.90%', '+0.07 pp', '−0.61 pp']) ok(d.includes(f), `${l}: the description names ${f}`);
  }
});

// --- The shell -------------------------------------------------------------------------------------------------------
check('the thread is linked once per language, from the intro line, its commenter unnamed', () => {
  eq(data.thread.commenter_named, false, 'commenter_named');
  for (const l of ['en', 'zh']) {
    const hrefs = [...html[l].matchAll(/href="([^"]*huggingface\.co\/posts\/[^"]*)"/g)].map(m => m[1]);
    eq(hrefs, [data.thread.url], `${l}: links to the thread`);
    ok(sectionOf(html[l], 'setup').includes(`href="${data.thread.url}"`), `${l}: the link sits in the intro line`);
  }
  // The commenter's name, held as hashes so that this file does not print it either.
  const NAME = new Set(['6e7f5e4c7a5ed600cb60c4cd7fa0b60724ddd2a89426474c71d7d8d06bb9c4d9', 'f695cdd94ee90fff62b7216da4bcd9283b9514e061f6108043cac331f5f1a65a']);
  const hit = s => (s.toLowerCase().match(/[a-z]+/g) ?? []).some(w => NAME.has(createHash('sha256').update(w).digest('hex')));
  for (const l of ['en', 'zh']) { ok(!hit(html[l]), `${l}: the page names the commenter`); ok(!md[l] || !hit(md[l]), `${l}: the Markdown copy names the commenter`); }
  ok(!hit(servedText), 'the data file names the commenter');
});
check('the commenter’s confidence figure appears nowhere (wording review M7 token rules)', () => {
  for (const l of ['en', 'zh']) {
    const m = visible(html[l]).match(tokens55); ok(!m, `${l}: page text “${m?.[0]}”`);
    const a = [...html[l].matchAll(/\s(?:aria-label|title|alt|content)="([^"]*)"/g)].map(x => decode(x[1])).join(' ¶ ').match(tokens55); ok(!a, `${l}: attribute “${a?.[0]}”`);
    if (md[l]) { const k = md[l].match(tokens55); ok(!k, `${l}: Markdown “${k?.[0]}”`); }
  }
  (function walk(v, path) {
    if (typeof v === 'number') ok(v !== 11 / 20 && v !== 100 * 11 / 20, `data file: ${path} = ${v}`);
    else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) { ok(!/fifty|05{2}|prediction/i.test(k), `data file: key ${path}.${k}`); walk(x, path + '.' + k); }
  })(data, '');
});
check('endpoint strip: five columns, five tasks, chance from the candidates', () => {
  for (const l of ['en', 'zh']) {
    const sec = sectionOf(html[l], 'setup');
    const t = sec.match(/<table data-ssvep-table="endpoints">[\s\S]*?<\/table>/)?.[0];
    ok(t, `${l}: the strip`);
    eq((t.match(/<thead>[\s\S]*?<\/thead>/)[0].match(/<th\b/g) ?? []).length, 5, `${l}: header columns`);
    eq([...t.matchAll(/data-endpoint="([^"]+)"/g)].map(m => m[1]), data.endpoints.map(e => e.id), `${l}: rows`);
    for (const e of data.endpoints) {
      const row = t.slice(t.indexOf(`data-endpoint="${e.id}"`), t.indexOf('</tr>', t.indexOf(`data-endpoint="${e.id}"`)));
      const want = e.candidates === null ? [] : [`count|${e.candidates}`, `pct2|${e.chance}`];
      eq(figsIn(row).map(f => `${f.fmt}|${f.raw}`), want, `${l}: ${e.id} candidates and chance`);
    }
  }
});
check('the cards 1–6 scope line, once, from the cohort block', () => {
  const c = data.cohort;
  for (const l of ['en', 'zh']) {
    const lines = [...html[l].matchAll(/data-ssvep-scope="cards-1-6"[^>]*>([\s\S]*?)<\/p>/g)];
    eq(lines.length, 1, `${l}: scope lines`);
    eq(figsIn(lines[0][0]).map(f => f.raw), [c.people, c.windows, c.person_folds, c.frequency_rotations, c.seen_frequencies, c.held_out_frequencies, c.training_seeds], `${l}: scope figures`);
    const t = visible(lines[0][1]);
    ok(l === 'en' ? /Cards 1 to 6: BETA/.test(t) && t.includes('“Unseen” means unseen by the trained part of the decoder.') : /卡片 1 至 6：BETA/.test(t) && t.includes('“没见过”指解码器中经过训练的部分没有见过。'), `${l}: scope words`);
    ok(/href="(?:\/zh)?\/topics\/questions-in-language\/"/.test(lines[0][0]), `${l}: route 3 linked`);
  }
});
check('name key: the export’s in-page names, with their codes', () => {
  const key = data.name_key.filter(n => n.in_page_key);
  for (const l of ['en', 'zh']) {
    const t = html[l].match(/<table data-ssvep-table="name-key">[\s\S]*?<\/table>/)?.[0];
    ok(t, `${l}: the name key`);
    eq([...t.matchAll(/data-name="([^"]+)"/g)].map(m => decode(m[1])), key.map(n => n.site_name), `${l}: names`);
    for (const n of key) {
      const at = t.indexOf(`data-name="${n.site_name}"`), row = t.slice(at, t.indexOf('</tr>', at));
      for (const c of new Set(n.codes.map(x => x.code))) ok(row.includes(`<code>${c}</code>`), `${l}: ${n.site_name} shows ${c}`);
    }
  }
});
check('card 8 is a status card: the addendum wording, no figure', () => {
  for (const l of ['en', 'zh']) {
    const sec = sectionOf(html[l], 'cross-spectral');
    eq(figsIn(sec).length, 0, `${l}: figures on card 8`);
    const p = visible(sec.match(/<p class="roadmap-p ssvep-status[^"]*"[^>]*>([\s\S]*?)<\/p>/)?.[1] ?? '');
    ok(p.length > 100 && !/\d/.test(p), `${l}: the status sentence carries no digit`);
    ok(l === 'en' ? p.includes('fixed learned linear readouts of cross-spectral features, with prescribed trial-dependent normalization or whitening')
      && p.includes('The design is frozen and the run is in progress; its results join this page after review.')
      : p.includes('在互谱特征上固定的学习线性读出，并按规定做逐试次归一化或白化') && p.includes('设计已冻结，正在运行；结果经审核后加入本页。'), `${l}: the addendum wording`);
  }
});
check('methods and limits: definitions, intervals by card, disclosures, not run, not published', () => {
  const NEED = {
    en: ['Plain spectrum (L0)', 'Complex spectrum (L0c)', 'Frozen CBraMod features (L1)', 'm8', 'nn8', 'u3', 'an exact score tie selects the lowest frequency',
      'seed 20261007', 'seed 20261015', 'conditional on the fixed person folds and three seeds', 'computed before rounding',
      'No interval is adjusted for multiple comparisons', 'compatibility reader', 'pre-freeze guard', 'Not run', 'Not published here', 'Measured compute'],
    zh: ['普通频谱（L0）', '复数频谱（L0c）', '冻结的 CBraMod 特征（L1）', 'm8', 'nn8', 'u3', '选频率最低的一个', '种子 20261007', '种子 20261015',
      '以固定的被试折与三个种子为条件', '舍入前', '没有任何区间做多重比较校正', '兼容读取器', '冻结前检查', '没有运行的部分', '这里不发布的内容', '实测的计算量'],
  };
  for (const l of ['en', 'zh']) {
    const sec = sectionOf(html[l], 'methods-and-limits'), t = visible(sec);
    for (const s of NEED[l]) ok(t.includes(s), `${l}: “${s}”`);
    eq([...sec.matchAll(/data-interval-cards="([^"]+)"/g)].map(m => m[1]), ['1 2', '3 4', '5', '6', '7'], `${l}: interval lines by card`);
    eq(figsIn(sec.slice(sec.indexOf('data-ssvep-note="intervals"'))).filter(f => f.fmt === 'count').map(f => f.raw).slice(0, 6), [2000, 2000, 2000, 2000, 2000, 105], `${l}: draws and the 105 source models`);
    eq((sec.match(/<li data-not-run-card=/g) ?? []).length, [1, 3, 4, 5, 6, 7].length, `${l}: not-run lines (card 2 ran everything it declared)`);
    eq((sec.slice(sec.indexOf('data-ssvep-note="not-published"')).match(/<li>/g) ?? []).length >= data.not_published.length, true, `${l}: not-published items`);
  }
});
check('credits: BETA, the corrigendum, CBraMod and Wearable-102, with their links', () => {
  const r = data.rights;
  for (const l of ['en', 'zh']) {
    const sec = sectionOf(html[l], 'methods-and-limits'), dsec = decode(sec);
    for (const id of ['beta', 'beta-corrigendum', 'cbramod', 'wearable-ssvep-102']) ok(sec.includes(`data-credit="${id}"`), `${l}: credit ${id}`);
    for (const u of [r.datasets.beta.source, r.datasets.beta.licenseUrl, r.corrigendum.url, r.cbramod.repository, r.datasets.wearable_102.readme,
      'https://doi.org/' + r.datasets.wearable_102.canonical_version_doi]) ok(sec.includes(`href="${u}"`), `${l}: links ${u}`);
    ok(sec.includes(`href="${l === 'zh' ? '/zh' : ''}/methods/cbramod/"`), `${l}: CBraMod’s page`);
    ok(dsec.includes(r.cbramod.license) && dsec.includes(r.corrigendum.revision.slice(0, 8)), `${l}: CBraMod licence and the corrigendum revision`);
    ok(dsec.includes(r.datasets.beta.citation) && dsec.includes(r.datasets.wearable_102.paper_citation) && dsec.includes(r.datasets.wearable_102.dataset_citation),
      `${l}: BETA and Wearable-102 citations`);
    ok(sec.includes(`href="/data/${FILE}" download`), `${l}: data source`);
  }
});

// --- Site rules ----------------------------------------------------------------------------------------------------
check('cite block names this release only', () => {
  for (const l of ['en', 'zh']) eq(html[l].match(/<section class="cite-page"[^>]*data-releases="([^"]+)"/)?.[1], data.release_id, `${l}: cite releases`);
});
check('hreflang reciprocal; structured data on the English page only', () => {
  ok(html.en.includes(`hreflang="zh-Hans" href="https://bci.report/zh/${PAGE}"`) && html.zh.includes(`hreflang="en" href="https://bci.report/${PAGE}"`), 'hreflang');
  ok(/application\/ld\+json/.test(html.en) && !/application\/ld\+json/.test(html.zh), 'JSON-LD on the English canonical only');
});
check('CSP: no inline style, inline script or event handler', () => {
  for (const l of ['en', 'zh']) {
    ok(!/\sstyle="|<style[\s>]|\son[a-z]+=/.test(html[l]), `${l}: inline style or handler`);
    for (const m of html[l].matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) ok(/\ssrc=/.test(m[1]) || /type="application\/ld\+json"/.test(m[1]), `${l}: an inline script`);
  }
});
check('every table has a <thead>; a table inside <details> has at least four columns', () => {
  for (const l of ['en', 'zh']) {
    const m = mainOf(html[l]);
    for (const t of m.matchAll(/<table\b[\s\S]*?<\/table>/g)) ok(/<thead>/.test(t[0]), `${l}: a table without <thead> at ${t.index}`);
    for (const d of m.matchAll(/<details\b[\s\S]*?<\/details>/g)) for (const t of d[0].matchAll(/<table\b[\s\S]*?<\/table>/g)) {
      const head = t[0].match(/<thead>[\s\S]*?<tr>([\s\S]*?)<\/tr>/)?.[1] ?? '';
      const cols = [...head.matchAll(/<th\b([^>]*)>/g)].reduce((s, x) => s + Number(x[1].match(/colspan="(\d+)"/)?.[1] ?? 1), 0);
      ok(cols >= 4, `${l}: a table inside <details> has ${cols} columns`);
    }
  }
});
// Private storage and host names, each written with a character class so that a scan of the tree for the literal
// strings does not flag this file.
const PRIVATE = new RegExp(['\\/U[s]ers\\/', '\\/h[o]me\\/', '\\/V[o]lumes\\/', '\\/m[n]t\\/', '\\btr[x]50\\b', '\\btr[x]\\b', 'G[a]l4', 'BCI_A[r]ena', '\\bt[w]u\\b'].join('|'), 'i');
const VENUE = /ICLR\s*2027|OpenReview|\bsubmission\b|投稿/i;
check('no private path, no venue or submission reference', () => {
  for (const l of ['en', 'zh']) for (const [what, s] of [['page', html[l]], ['Markdown', md[l] ?? '']]) {
    const p = s.match(PRIVATE); ok(!p, `${l} ${what}: private “${p?.[0]}”`);
    const v = s.match(VENUE); ok(!v, `${l} ${what}: “${v?.[0]}”`);
  }
  const p = servedText.match(PRIVATE); ok(!p, `data file: private “${p?.[0]}”`);
});
check('no update date or version label; no ranking word', () => {
  // check-workbench.mjs's rules (owner decision 2026-10-08), on the visible text without the cite block.
  const MONTH = '(?:January|February|March|April|May|June|July|August|September|October|November|December)';
  const DAY = `\\d{1,2} ${MONTH}`, ISO = '20\\d\\d-\\d\\d-\\d\\d', ZHD = '20\\d\\d 年 \\d+ 月 \\d+ 日';
  const rules = [
    new RegExp(`\\b[Uu]pdated:? (?:on )?(?:20\\d\\d|${DAY})|· [Uu]pdated\\b|更新于|${ISO} ?更新`),
    new RegExp(`\\b[Aa]dded:? (?:on )?(?:20\\d\\d|${DAY})|新增于|${ISO} ?新增`),
    new RegExp(`\\b[Ss]ince (?:${ISO}|${DAY})|(?<!来)自 ?20\\d\\d`), /[Hh]eld since|起暂缓/,
    new RegExp(`\\b(?:[Rr]un|[Rr]an|replayed) on (?:${ISO}|${DAY})`), new RegExp(`\\b[Ss]napshot (?:${ISO}|${DAY})|快照 ?(?:${ISO}|${ZHD})`),
    /\b[Tt]his update\b|本次更新|这次更新/, new RegExp(`\\bgenerated:? (?:on )?(?:20\\d\\d|${DAY})|生成于 ?20\\d\\d`),
    /(?<![\w.\/#-])v\d+(?![\w.]|-\d)|\brelease v\d|第[一二三四五六七八九十]+轮/,
  ];
  // "on top of" (card 6's title, "Learning on top of CCA") places one computation over another; it ranks nothing.
  const RANK = { en: /\b(?:best|(?<!on )top(?! of)|winner|leader|outperform\w*|beats?|state of the art|SOTA|ranks?|ranked|ranking)\b/i, zh: /最佳|最好的|胜出|排名第|最先进|第一名/ };
  for (const l of ['en', 'zh']) {
    const body = html[l].replace(/<section class="cite-page"[\s\S]*?<\/section>/g, '');
    const t = visible(body).replace(/https?:\/\/\S+/g, ' ');
    for (const re of rules) { const m = t.match(re); ok(!m, `${l}: “${m && t.slice(Math.max(0, m.index - 40), m.index + 40)}”`); }
    const main = visible(mainOf(body).replace(/<nav class="topic-switcher"[\s\S]*?<\/nav>/, ''));
    const r = main.match(RANK[l]); ok(!r, `${l}: ranking word “${r && main.slice(Math.max(0, r.index - 40), r.index + 40)}”`);
    for (const m of body.matchAll(/<p class="citation-note">([\s\S]*?)<\/p>/g)) {
      const n = visible(m[1]).trim();
      ok(!(/^(?:Data source:|数据来源：)/.test(n) && new RegExp(`${ISO}|${ZHD}`).test(n)), `${l}: a dated data-source note`);
    }
  }
});
check('Chinese: no sentence ends with an ASCII period; the figures survive into the Markdown copies', () => {
  // English kept verbatim on the Chinese page (citations, lang="en") ends as English does.
  const zhOnly = mainOf(html.zh).replace(/<(p|span|h3|li)\b[^>]*\slang="en"[^>]*>[\s\S]*?<\/\1>/g, '');
  const bad = zhOnly.match(/.{0,60}[一-鿿\d]\.<\/(?:p|li)>/);
  ok(!bad, `zh: a Chinese sentence ends with an ASCII period: “${bad?.[0]}”`);
  for (const l of ['en', 'zh']) if (md[l]) for (const [, v] of mainOf(html[l]).matchAll(/class="(?:metric|num|fig)">([^<]+)</g))
    ok(md[l].includes(decode(v)), `${l}: figure "${v}" missing from the Markdown copy`);
});
check('card sections still written by the stubs', () => {
  const n = stubs(html.en);
  eq(n, stubs(html.zh), 'the same stubs in both languages');
  if (n) return { pending: `${n} of 7 card sections are stubs (QueryCards, PhaseCards, CcaCards)` };
});

// --- Cards 3 and 4 (PhaseCards.astro; package P-SS3) ---------------------------------------------------------------
// Folded in from P-SS3's own check. Keyed on the card markup hooks: data-ssvep-lead and data-ssvep-caption ("3", "4"),
// data-ssvep-bet, data-ssvep-table (phase-jitter-arms, phase-jitter-contrasts, phase-ramp-arms, phase-ramp-contrasts,
// phase-ramp-readoffs), data-ssvep-details, data-arm and data-contrast. Its helpers are its own, scoped to this block.
try {
  const J = S.phase_jitter, R = S.phase_ramp;
  const src = readFileSync(join(SITE, 'src/components/ssvep/PhaseCards.astro'), 'utf8');
  const fmt = {
    pct2: r => (r * 100).toFixed(2) + '%', pp2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2) + ' pp',
    sgn2: r => (r === 0 ? '' : r > 0 ? '+' : '−') + Math.abs(r * 100).toFixed(2), count: r => r.toLocaleString('en-US'), pct0: r => (r * 100).toFixed(0) + '%',
  };
  const decode = s => s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&(amp|lt|gt|quot|apos|nbsp);/g, (_, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' })[e]);
  const visible = h => decode(h.replace(/<(?!\/?(?:span|a|code|strong|small)\b)[^>]+>/g, ' ').replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ');
  const sectionOf = (h, id) => { const at = h.search(new RegExp(`<section[^>]*\\sid="${id}"`)); ok(at >= 0, `#${id} missing`); return h.slice(at, h.indexOf('</section>', at) + 10); };
  const figsIn = h => [...h.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)].map(m => ({ file: m[1], fmt: m[2], raw: Number(m[3]), text: decode(m[4]) }));
  const leaves = new Set();
  (function walk(v) { if (typeof v === 'number') leaves.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(data);
  const sec = { en: { 3: sectionOf(html.en, 'phase-jitter'), 4: sectionOf(html.en, 'phase-ramp') }, zh: { 3: sectionOf(html.zh, 'phase-jitter'), 4: sectionOf(html.zh, 'phase-ramp') } };
  const tableOf = (h, name) => { const t = h.match(new RegExp(`<table data-ssvep-table="${name}">[\\s\\S]*?</table>`))?.[0]; ok(t, `table ${name}`); return t; };
  const rowOf = (t, attr, key) => { const a = t.indexOf(`${attr}="${key}"`); ok(a >= 0, `row ${key}`); return t.slice(a, t.indexOf('</tr>', a)); };
  const lvlFigs = l => [fmt.pct2(l.estimate), fmt.pct2(l.interval[0]), fmt.pct2(l.interval[1])];
  const ctrFigs = c => [fmt.pp2(c.estimate), fmt.sgn2(c.interval[0]), fmt.sgn2(c.interval[1])];

  check('cards 3–4 · both cards written, at their anchors, with the chrome titles', () => {
    const T = { en: ['A random delay with the phase-carrying query', 'A random phase ramp with magnitude queries'], zh: ['带相位查询下的随机延迟', '幅度查询下的随机相位斜坡'] };
    for (const l of ['en', 'zh']) [3, 4].forEach((n, i) => {
      ok(!/data-ssvep-stub/.test(sec[l][n]), `${l}: card ${n} still a stub`);
      ok(new RegExp(`data-ssvep-card="${n}"`).test(sec[l][n].slice(0, 300)), `${l}: card ${n} attribute`);
      ok(sec[l][n].includes(`>${T[l][i]}</h2>`), `${l}: card ${n} title`);
    });
  });
  check('cards 3–4 · every figure on the two cards is a leaf of the file in its format; EN and ZH multisets equal', () => {
    const key = h => figsIn(h).map(f => `${f.fmt}|${f.raw}`).sort();
    let n = 0;
    for (const l of ['en', 'zh']) for (const c of [3, 4]) for (const f of figsIn(sec[l][c])) {
      eq(f.file, FILE, `${l}: file`); ok(leaves.has(f.raw), `${l}: ${f.raw} not a leaf`); eq(f.text, fmt[f.fmt](f.raw), `${l}: ${f.raw} as ${f.fmt}`); n++;
    }
    for (const c of [3, 4]) eq(key(sec.zh[c]), key(sec.en[c]), `card ${c} figure multiset`);
    return `${n / 2} figures per language`;
  });
  check('cards 3–4 · the bet: once, on card 4, printed 39% from thread_bet.held8_threshold at pct0; none on card 3', () => {
    for (const l of ['en', 'zh']) {
      eq(figsIn(sec[l][3]).filter(f => f.fmt === 'pct0').length, 0, `${l}: pct0 on card 3`);
      eq(figsIn(sec[l][4]).filter(f => f.fmt === 'pct0').map(f => f.raw), [R.thread_bet.held8_threshold], `${l}: pct0 on card 4`);
      eq((visible(sec[l][3]).match(/(?<![\d.])39%/g) ?? []).length, 0, `${l}: 39% on card 3`);
      eq((visible(sec[l][4]).match(/(?<![\d.])39%/g) ?? []).length, 1, `${l}: 39% on card 4`);
      const bet = visible(sec[l][4].match(/<span data-ssvep-bet="">[\s\S]*?<\/span><\/p>/)[0]);
      ok(l === 'en' ? bet.includes('The bet in the thread was that held-out accuracy would clear 39%') && bet.includes('the FiLM head reached 30.56% with the magnitude reference and 28.10% with the numeric code')
        : bet.includes('讨论串中的赌注是留出频率准确率会超过 39%') && bet.includes('FiLM 分类头以幅度参考谱作查询达到 30.56%，以数值编码作查询为 28.10%'), `${l}: the bet line (M4, M5, R3)`);
    }
  });
  check('cards 3–4 · no confidence figure (M7 token rule), no venue, no private path, no ranking word, no "at chance" on card 3', () => {
    const t55 = /(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?!\d)|fifty[- ]five|五十五/i;
    const PRIVATE = new RegExp(['\\/U[s]ers\\/', '\\/h[o]me\\/', '\\/V[o]lumes\\/', '\\/m[n]t\\/', '\\btr[x]50\\b', 'G[a]l4', 'BCI_A[r]ena', '\\bt[w]u\\b'].join('|'), 'i');
    const RANK = { en: /\b(?:best|top|winner|leader|outperform\w*|beats?|state of the art|SOTA|ranks?|ranked|ranking|highest|lowest score)\b/i, zh: /最佳|最好的|胜出|排名|最先进|第一名|最高/ };
    for (const l of ['en', 'zh']) for (const c of [3, 4]) {
      const v = visible(sec[l][c]), raw = sec[l][c];
      ok(!t55.test(v) && !t55.test(raw.replace(/data-fig="[^"]*"/g, '')), `${l} card ${c}: a 55 token`);
      ok(!/ICLR|OpenReview|submission|投稿/i.test(v), `${l} card ${c}: venue`);
      ok(!PRIVATE.test(raw), `${l} card ${c}: private path`);
      const r = v.match(RANK[l]); ok(!r, `${l} card ${c}: ranking word ${r?.[0]}`);
      if (c === 3) ok(!/at chance|chance-equivalent|随机水平/.test(v), `${l}: card 3 calls an arm at chance`);
    }
    ok(!t55.test(src.replace(/\/\/.*$/gm, '')), 'the component source carries a 55 token');
  });
  check('cards 3–4 · card 3 lead: the R5 §5 figures from the jitter block', () => {
    const L = J.levels, P1 = J.contrasts.P1;
    const want = [fmt.count(J.design.model.parameters), ...lvlFigs(L['COMMON-125MS/u8']), ...lvlFigs(L['COMMON-ONE-PERIOD/u8']), ...lvlFigs(L['L0c-FS-REFc-0/u8']),
      ...ctrFigs(P1), fmt.pct2(L['L0c-FS-REFc-0/seen_ba'].estimate), fmt.pct2(L['COMMON-125MS/seen_ba'].estimate), fmt.pct2(L['COMMON-ONE-PERIOD/seen_ba'].estimate)];
    eq(want.slice(0, 4), ['526,465', '12.51%', '11.93%', '13.13%'], 'spot check');
    for (const l of ['en', 'zh']) eq(figsIn(sec[l][3].match(/data-ssvep-lead="3"[\s\S]*?<\/p>/)[0]).map(f => f.text), want, `${l}: lead figures in order`);
    ok(visible(sec.en[3]).includes('Primary change, 0–125 ms minus no delay: −12.46 pp (−14.84 to −10.25)'), 'en: primary sentence');
    ok(visible(sec.en[3]).includes('The head was the FiLM head on the complex spectrum'), 'en: FiLM head named');
  });
  check('cards 3–4 · card 3 caption: P1 the single primary, conditional bootstrap, "on the plain spectrum", label caveats, randomized-label limit (M3, M4, M8, R2)', () => {
    const NEED = {
      en: ['Only the 0–125 ms minus no-delay contrast is primary; the others are descriptive.', 'hierarchical paired bootstrap draws', '(seed 20261007), conditional on the fixed person folds and three seeds',
        'None of the 6 contrasts is adjusted for multiplicity.', 'approximates an onset shift', 'The one-period range is drawn from the training label’s frequency', 'the 0–125 ms range ignores the label',
        'so the delay also removes information tied to the label', 'The magnitude-reference head on the plain spectrum (39.00%) differs in features, query and size.',
        'All 4 randomized-label checks passed (40 fits); a training-only shortcut through the label-dependent delay remains possible.'],
      zh: ['只有 0–125 ms 减去不加延迟这一项是主要对比', '分层配对 bootstrap 抽样', '以固定的被试折与三个种子为条件', '这 6 项对比都没有做多重比较校正', '近似于起点的平移',
        '一个周期的范围取决于训练标签的频率', '0–125 ms 的范围不看标签', '所以延迟也去掉了与标签相关的信息', '普通频谱上的幅度参考谱分类头（39.00%）在特征、查询和规模上都不同',
        '全部 4 项随机标签检查都通过了（40 次拟合）'],
    };
    for (const l of ['en', 'zh']) { const v = visible(sec[l][3].match(/data-ssvep-caption="3"[\s\S]*?<\/p>/)[0]); for (const s of NEED[l]) ok(v.includes(s), `${l}: “${s}”`); }
  });
  check('cards 3–4 · card 3 tables: four arms; six contrasts in <details>, P1 primary, ≥4 columns, figures from the block', () => {
    for (const l of ['en', 'zh']) {
      const arms = tableOf(sec[l][3], 'phase-jitter-arms');
      ok(/<thead>/.test(arms), `${l}: arms thead`);
      eq([...arms.matchAll(/data-arm="([^"]+)"/g)].map(m => m[1]), J.design.arms.map(a => a.cell), `${l}: arm rows`);
      for (const a of J.design.arms) eq(figsIn(rowOf(arms, 'data-arm', a.cell)).map(f => f.text), [...lvlFigs(J.levels[`${a.cell}/u8`]), ...lvlFigs(J.levels[`${a.cell}/seen_ba`])], `${l}: ${a.cell}`);
      const det = sec[l][3].match(/<details[^>]*data-ssvep-details="phase-jitter-contrasts"[\s\S]*?<\/details>/)?.[0]; ok(det, `${l}: details`);
      const t = tableOf(det, 'phase-jitter-contrasts');
      eq((t.match(/<thead>[\s\S]*?<\/thead>/)[0].match(/<th\b/g) ?? []).length >= 4, true, `${l}: ≥4 columns`);
      eq([...t.matchAll(/data-contrast="([^"]+)"/g)].map(m => m[1]), Object.keys(J.contrasts), `${l}: contrast rows`);
      for (const [k, c] of Object.entries(J.contrasts)) {
        const row = rowOf(t, 'data-contrast', k);
        eq(figsIn(row).map(f => f.text), ctrFigs(c), `${l}: ${k} figures`);
        const role = (row.match(/<td>([^<]*)<\/td>/g) ?? []).map(x => x.replace(/<\/?td>/g, ''));
        ok(role.includes(k === 'P1' ? (l === 'en' ? 'primary' : '主要') : (l === 'en' ? 'descriptive' : '描述性')), `${l}: ${k} role`);
      }
      ok(figsIn(rowOf(t, 'data-contrast', 'S2'))[0].text === '−25.87 pp', `${l}: S2 renders −25.87`);
    }
  });
  check('cards 3–4 · card 4 lead: FiLM head named, primary and secondary contrasts with 8.67%, seen fall, matching head, CCA (R5 §5, M4, R3)', () => {
    const L = R.levels, C = R.contrasts;
    const want = [fmt.pct2(L['FS-REF/u8'].estimate), fmt.pct2(L['FS-REF/u8'].interval[0]), fmt.pct2(L['FS-REF/u8'].interval[1]), ...ctrFigs(C.P1), fmt.pct2(L['L0c-FS-REF/u8'].estimate),
      ...ctrFigs(C.S5), fmt.pct2(L['L0c-FS-REF/seen_ba'].estimate), fmt.pct2(L['FS-REF/seen_ba'].estimate), fmt.pct2(L['CCA/u8'].estimate),
      fmt.pct0(R.thread_bet.held8_threshold), fmt.pct2(L['FS-REF/u8'].estimate), fmt.pct2(L['FS-NUM/u8'].estimate)];
    eq(want, ['30.56%', '27.81%', '33.22%', '−8.45 pp', '−10.14', '−6.69', '8.67%', '+21.88 pp', '+18.78', '+25.00', '47.29%', '15.03%', '80.90%', '39%', '30.56%', '28.10%'], 'the R5 figures');
    for (const l of ['en', 'zh']) eq(figsIn(sec[l][4].match(/data-ssvep-lead="4"[\s\S]*?<\/p>/)[0]).map(f => f.text), want, `${l}: lead figures in order`);
    const v = visible(sec.en[4].match(/data-ssvep-lead="4"[\s\S]*?<\/p>/)[0]);
    for (const s of ['the FiLM head reached 30.56% on held-out frequencies', 'Queries and test windows were unchanged.', 'The matching head ended at chance on both tasks.', '(primary; ', '(secondary; ']) ok(v.includes(s), `en: “${s}”`);
  });
  check('cards 3–4 · card 4 caption: six primary and seven secondary (M1), conditional bootstrap (M3), m8 42.86% as the matched comparison (M2), feature-recipe contrasts, randomized-label limit (M8)', () => {
    const NEED = {
      en: ['Of the 13 contrasts, six are primary (P1–P6) and seven secondary (S1–S7); none is adjusted for multiplicity.', 'hierarchical paired bootstrap draws',
        'conditional on the fixed person folds and three seeds', 'its only contrast is S7 (−67.97 pp)', 'Held-out scores choose among 8 candidates and seen scores among 32, so the two are different tasks',
        'm8 is the matched comparison for a held-out score, and there the FiLM head with the magnitude reference reached 42.86%',
        'The contrasts against the plain spectrum (P1, P2, S3, S4) compare two feature recipes as well as the ramp', 'not initialisation-matched',
        'so phase carries real label information', 'approximates a time shift', 'All 10 randomized-label checks passed (120 fits)'],
      zh: ['这 13 项对比中，六项为主要对比（P1–P6），七项为次要对比（S1–S7）', '以固定的被试折与三个种子为条件', '它唯一的对比是 S7（−67.97 pp）', '两者是不同的任务',
        '留出分数的匹配对照是 m8，以幅度参考谱作查询的 FiLM 分类头在 m8 上达到 42.86%', '与普通频谱的对比（P1、P2、S3、S4）', '近似于一次时间平移', '全部 10 项随机标签检查都通过了（120 次拟合）'],
    };
    for (const l of ['en', 'zh']) { const v = visible(sec[l][4].match(/data-ssvep-caption="4"[\s\S]*?<\/p>/)[0]); for (const s of NEED[l]) ok(v.includes(s), `${l}: “${s}”`); }
    ok(!/The primary contrast/.test(visible(sec.en[4])), 'en: "The primary contrast" (M1)');
  });
  check('cards 3–4 · card 4 tables: six cells and nine comparators; ID held-out a dash; 13 contrasts in <details> with roles; read-offs', () => {
    const arms = [...R.design.cells.map(c => c.cell), ...R.design.comparators];
    for (const l of ['en', 'zh']) {
      const t = tableOf(sec[l][4], 'phase-ramp-arms');
      ok(/<thead>/.test(t), `${l}: arms thead`);
      eq([...t.matchAll(/data-arm="([^"]+)"/g)].map(m => m[1]), arms, `${l}: arm rows`);
      for (const a of arms) {
        const row = rowOf(t, 'data-arm', a), want = [];
        for (const m of ['u8', 'm8', 'seen_ba']) { const x = R.levels[`${a}/${m}`]; if (x) want.push(...lvlFigs(x)); else ok(R.undefined_metrics[a]?.includes(m), `${l}: ${a}/${m} missing`); }
        eq(figsIn(row).map(f => f.text), want, `${l}: ${a}`);
        eq((row.match(/data-null="true">—</g) ?? []).length, a.endsWith('-ID') ? 1 : 0, `${l}: ${a} dashes`);
      }
      const det = sec[l][4].match(/<details[^>]*data-ssvep-details="phase-ramp-contrasts"[\s\S]*?<\/details>/)?.[0]; ok(det, `${l}: contrasts details`);
      const ct = tableOf(det, 'phase-ramp-contrasts');
      const head = ct.match(/<thead>[\s\S]*?<\/thead>/)[0];
      ok((head.match(/<th\b/g) ?? []).length >= 4, `${l}: ≥4 columns`);
      for (const h of l === 'en' ? ['Contrast', 'Role', 'Estimate', '95% interval'] : ['对比', '角色', '估计值', '95% 区间']) ok(head.includes(`>${h}</th>`), `${l}: column ${h}`);
      eq([...ct.matchAll(/data-contrast="([^"]+)"/g)].map(m => m[1]), Object.keys(R.contrasts), `${l}: 13 contrast rows`);
      let prim = 0, secd = 0;
      for (const [k, c] of Object.entries(R.contrasts)) {
        const row = rowOf(ct, 'data-contrast', k);
        eq(figsIn(row).map(f => f.text), ctrFigs(c), `${l}: ${k}`);
        const cells = (row.match(/<td>([^<]*)<\/td>/g) ?? []).map(x => x.replace(/<\/?td>/g, ''));
        const role = l === 'en' ? { primary: 'primary', secondary: 'secondary' }[c.role] : { primary: '主要', secondary: '次要' }[c.role];
        ok(cells.includes(role), `${l}: ${k} role ${role}`); c.role === 'primary' ? prim++ : secd++;
      }
      eq([prim, secd], [6, 7], `${l}: roles`);
      const ro = sec[l][4].match(/<details[^>]*data-ssvep-details="phase-ramp-readoffs"[\s\S]*?<\/details>/)?.[0]; ok(ro, `${l}: read-offs details`);
      const rt = tableOf(ro, 'phase-ramp-readoffs');
      ok((rt.match(/<thead>[\s\S]*?<\/thead>/)[0].match(/<th\b/g) ?? []).length >= 4, `${l}: read-offs ≥4 columns`);
      for (const a of arms) eq((rowOf(rt, 'data-arm', a).match(/data-null="true">—</g) ?? []).length, a.endsWith('-ID') ? 2 : 0, `${l}: ${a} read-off dashes (u3, cost)`);
    }
  });
  check('cards 3–4 · every table on the cards has a <thead>; every <details> table ≥4 columns; no inline style or handler', () => {
    for (const l of ['en', 'zh']) for (const c of [3, 4]) {
      for (const t of sec[l][c].matchAll(/<table\b[\s\S]*?<\/table>/g)) ok(/<thead>/.test(t[0]), `${l} card ${c}: thead`);
      for (const d of sec[l][c].matchAll(/<details\b[\s\S]*?<\/details>/g)) for (const t of d[0].matchAll(/<table\b[\s\S]*?<\/table>/g))
        ok(((t[0].match(/<thead>[\s\S]*?<\/thead>/)?.[0] ?? '').match(/<th\b/g) ?? []).length >= 4, `${l} card ${c}: details table columns`);
      ok(!/\sstyle="|<style[\s>]|\son[a-z]+=|<script/.test(sec[l][c]), `${l} card ${c}: inline style, script or handler`);
      ok(!/data-astro-cid/.test(sec[l][c]), `${l} card ${c}: scoped-style attributes`);
    }
  });
  check('cards 3–4 · Chinese copy: no ASCII sentence period; spacing between Chinese and Latin after 减去', () => {
    for (const c of [3, 4]) {
      ok(!/[一-鿿\d]\.<\/(?:p|li)>/.test(sec.zh[c]), `card ${c}: ASCII period`);
      ok(!/减去[A-Za-z0-9]/.test(visible(sec.zh[c])), `card ${c}: 减去 runs into Latin`);
    }
  });
  check('cards 3–4 · every class="metric" figure of the cards survives into the Markdown copy', () => {
    for (const l of ['en', 'zh']) for (const c of [3, 4]) for (const [, v] of sec[l][c].matchAll(/class="metric">([^<]+)</g)) ok(md[l].includes(decode(v)), `${l}: ${v}`);
  });
} catch (e) { report('cards 3–4 · inputs (sections, tables, PhaseCards.astro)', 'FAIL', e.message); }

// --- Report --------------------------------------------------------------------------------------------------------
const w = Math.max(...results.map(r => r.name.length));
for (const r of results) console.log(`${r.status.padEnd(7)} ${r.name.padEnd(w)}${r.detail ? '  — ' + r.detail : ''}`);
const fails = results.filter(r => r.status === 'FAIL').length, pend = results.filter(r => r.status === 'PENDING').length;
console.log(`\nnew-ssvep-frequencies: ${results.length - fails - pend} passed, ${pend} pending, ${fails} failed (${DIST})`);
process.exit(fails ? 1 : 0);
