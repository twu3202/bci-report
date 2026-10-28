// The checks of cards 8 to 14 of /topics/new-ssvep-frequencies/ (release ssvep-followups-update-20261028; plan §2.1;
// owner decisions D14, D22, D23, D25, D28), run on a built site:
//
//   node scripts/checks/ssvep-followups.mjs <dist directory>
//
// The page shell and cards 1 to 7 keep their own module (new-ssvep-frequencies.mjs). This one reads both languages,
// their Markdown copies and the served ssvep-followups-update.json, and holds every figure of that file to the field it
// was read from: each prints as <span data-at="<path>" data-fig="<file>|<format>|<raw>">, the raw value must be the
// field's own number and the format the one that field's kind takes (levels pct2; paired differences pp2, pp2eq for two
// equal levels; bounds sgn2, sgn5 for a bound the export flags below two decimals; card 12's gap statistics sig3, its
// win fractions auc3; the CPU component milliseconds sig3; counts count; card 12's family level pct2, card 13's margin
// test pct0 and margin pm1). It then checks the rules the cards live under: a shared level prints its interval on its
// interval_home card only and links that card elsewhere; every contrast prints its own interval beside it; English and
// Chinese print the same figures card by card; the pinned multiplicity sentence; the name key; the intervals, not-run,
// disclosure and not-published lists; the credits; card 11's timings (components, never summed, no host label); the
// thread's bet on card 4 only; "not external replication" once; nothing refused (blocks_cca.REFUSED_TEXT, read from its
// source, so this file adds no literal of what it refuses). Exit code 1 on any failure. No network, no writes.
import { readFileSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = resolve(process.argv[2] ?? fileURLToPath(new URL('../../dist/', import.meta.url)));
const SITE = fileURLToPath(new URL('../../', import.meta.url));
const FILE = 'ssvep-followups-update.json', RELEASED = 'new-ssvep-frequencies-update.json';
const PAGE = 'topics/new-ssvep-frequencies/';
const results = [];
const report = (name, status, detail = '') => results.push({ name, status, detail });
const check = (name, fn) => {
  try { const r = fn(); if (r && r.pending) report(name, 'PENDING', r.pending); else report(name, 'PASS', typeof r === 'string' ? r : ''); }
  catch (e) { report(name, 'FAIL', e.message); }
};
const ok = (cond, msg) => { if (!cond) throw new Error(msg); };
const eq = (a, b, msg) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); };

// --- Inputs ----------------------------------------------------------------------------------------------------
const read = p => readFileSync(join(DIST, p), 'utf8');
const L = ['en', 'zh'], PFX = { en: '', zh: 'zh/' };
for (const l of L) if (!existsSync(join(DIST, PFX[l] + PAGE, 'index.html'))) { console.error(`ssvep-followups: ${PFX[l]}${PAGE}index.html is missing from ${DIST}`); process.exit(1); }
const html = Object.fromEntries(L.map(l => [l, read(PFX[l] + PAGE + 'index.html')]));
const md = Object.fromEntries(L.map(l => [l, existsSync(join(DIST, PFX[l] + PAGE, 'index.md')) ? read(PFX[l] + PAGE + 'index.md') : null]));
const servedText = read('data/' + FILE);
const data = JSON.parse(servedText), S = data.studies, released = JSON.parse(read('data/' + RELEASED));

// --- Helpers ---------------------------------------------------------------------------------------------------
const sign = r => (r === 0 ? '' : r > 0 ? '+' : '−');
const minus = s => s.replace(/^-/, '−');
const FMT = {
  pct2: r => (r * 100).toFixed(2) + '%', pct0: r => (r * 100).toFixed(0) + '%',
  pp2: r => sign(r) + Math.abs(r * 100).toFixed(2) + ' pp', sgn2: r => sign(r) + Math.abs(r * 100).toFixed(2),
  pp2eq: r => (Math.abs(r) < 1e-12 ? '0.00 pp' : sign(r) + Math.abs(r * 100).toFixed(2) + ' pp'),
  sgn5: r => sign(r) + Math.abs(r * 100).toFixed(5), pm1: r => '±' + Math.abs(r * 100).toFixed(1) + ' pp',
  sig3: r => minus(r.toPrecision(3)), auc3: r => r.toFixed(3), auc2: r => r.toFixed(2), count: r => r.toLocaleString('en-US'),
  s1: r => minus(r.toFixed(1)) + ' s',
};
const decode = s => s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&(amp|lt|gt|quot|apos|nbsp);/g, (_, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' })[e]);
const visible = h => decode(h.replace(/<head>[\s\S]*?<\/head>/, '').replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '')
  .replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ');
/** Visible text with inline markup dropped in place (no space where a figure or link sat). */
const text = h => decode(h.replace(/<head>[\s\S]*?<\/head>/, '').replace(/<(?!\/?(?:span|a|code|strong|small)\b)[^>]+>/g, ' ').replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ');
const sectionOf = (h, id) => { const at = h.search(new RegExp(`<section[^>]*\\sid="${id}"`)); ok(at >= 0, `#${id} missing`); return h.slice(at, h.indexOf('</section>', at) + 10); };
const figsIn = h => [...h.matchAll(/<span (?:data-at="([^"]*)" )?data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)]
  .map(m => ({ at: m[1] ? decode(m[1]) : null, file: m[2], fmt: m[3], raw: Number(m[4]), text: decode(m[5]), index: m.index }));
const valueAt = path => path.reduce((o, k) => (o === null || o === undefined ? undefined : o[k]), data);
const P = at => at.split('|');
const cards = data.placement.cards;
const cardOfStudy = id => cards.find(c => c.studies.includes(id)).card;
const codeOfKey = key => { const p = key.split('/'); return p[p.length - 2]; };
/** The home card of a level: interval_home of its shared estimate, else the card a reused comparator comes from, else its own. */
const homeOf = (id, key) => {
  const sh = data.shared_estimates.find(e => e.levels.some(x => x.study === id && x.level === key));
  if (sh) return sh.interval_home;
  const lv = S[id].levels[key];
  if (String(lv.origin).startsWith('reused_')) return S[id].reused[codeOfKey(key)].card;
  return cardOfStudy(id);
};
/** The format a field takes, by its path. */
function formatFor(path) {
  const p = path, n = p.length, last = p[n - 1], v = valueAt(p);
  if (p[0] === 'studies') {
    const id = p[1], block = p[2];
    if (block === 'levels') { ok(S[id].levels[p[3]].unit === 'proportion', `${path.join('|')}: a proportion`); return (last === 'estimate' || p[4] === 'interval') ? 'pct2' : 'count'; }
    if (block === 'contrasts') {
      const c = S[id].contrasts[p[3]], fl = c.flags ?? {};
      if (last === 'estimate') return fl.levels_equal ? 'pp2eq' : 'pp2';
      if (p[4] === 'interval') return (fl.bound_below_two_decimals ?? []).includes(last === '0' ? 'lower' : 'upper') ? 'sgn5' : 'sgn2';
      if (last === 'interval_level') return 'pct2';
    }
    if (block === 'descriptive_gaps' && last === 'estimate') return 'pp2';
    if (block === 'gap') return last === 'interval_level' ? 'pct2' : 'sig3';
    if (block === 'win_fractions') return 'auc3';
    if (block === 'allocation') return p[5] === 'interval' ? 'sgn2' : 'pp2';
    if (block === 'transitions') return p[3] === 'edges' ? 'pct2' : 'count';
    if (block === 'cpu_components' && p[3] === 'groups') return 'sig3';
    if (block === 'design' && last === 'window_s') return 's1';
    if (id === 'fixed_decay' && block === 'design' && p[3] === 'rule') return 'auc2';
    if (id === 'fixed_decay' && block === 'equivalence') return p[3] === 'interval' ? 'sgn2' : last === 'interval_level' ? 'pct0' : last === 'margin' ? 'pm1' : null;
  }
  if (p[0] === 'interval_methods') { if (last === 'draws' || last === 'comparisons') return 'count'; if (p[n - 2] === 'family' && last === 'level') return 'pct2';
    if (p[n - 2] === 'equivalence') return last === 'level' ? 'pct0' : 'pm1'; }
  if (p[0] === 'interval_adjustment') return p[2] === '0' ? 'pct2' : 'pct0';
  if (Number.isInteger(v) && v >= 0) return 'count';
  throw new Error(`${path.join('|')}: no format rule for this field`);
}
const cardSections = l => cards.map(c => ({ card: c.card, anchor: c.anchor, sec: sectionOf(html[l], c.anchor) }));

// --- Files and placement ---------------------------------------------------------------------------------------------
check('served file is byte-identical to src/data and public/data; the released file keeps its bytes', () => {
  for (const p of ['src/data/' + FILE, 'public/data/' + FILE]) eq(readFileSync(join(SITE, p), 'utf8') === servedText, true, p);
  eq(data.release_id, 'ssvep-followups-update-20261028', 'release id');
  eq(data.placement.reads_with.release_id, released.release_id, 'reads with the released file');
  eq(data.provenance.released_file.unchanged, true, 'the released file is unchanged (D28)');
  for (const p of ['src/data/' + RELEASED, 'public/data/' + RELEASED]) eq(readFileSync(join(SITE, p), 'utf8') === read('data/' + RELEASED), true, p);
  eq(cards.map(c => `${c.card}:${c.anchor}`), ['8:cross-spectral', '9:eigenvalue-pooling', '10:harmonic-pooling', '11:practical-settings', '12:harmonic-gap', '13:fixed-decay', '14:rising-weights'], 'cards and anchors');
  eq(cards[0].supersedes, { release_id: released.release_id, file: RELEASED, entry: 'status_only' }, 'card 8 replaces the released status entry');
});
check('cards 8 to 14 at their anchors, in order, each with its h2; card 8 a result card', () => {
  for (const l of L) {
    const ids = [...html[l].matchAll(/<section[^>]*\sid="([^"]+)"[^>]*data-ssvep-card="(\d+)"/g)].map(m => `${m[2]}:${m[1]}`);
    eq(ids.slice(7), cards.map(c => `${c.card}:${c.anchor}`), `${l}: card sections 8 to 14`);
    for (const { card, sec } of cardSections(l)) {
      const by = sec.match(/aria-labelledby="([^"]+)"/)?.[1];
      ok(by && new RegExp(`<h2 id="${by}">`).test(sec), `${l}: card ${card} labelled by its own h2`);
      ok(figsIn(sec).length > 10, `${l}: card ${card} carries its figures`);
    }
    const c8 = sectionOf(html[l], 'cross-spectral');
    ok(!/data-status-only|ssvep-status/.test(c8) && !/进行中|in progress|join this page after review/.test(visible(c8)), `${l}: card 8 is no longer a status card`);
  }
});

// --- Every figure, held to its field --------------------------------------------------------------------------------
check('every figure of the file is its field’s own number, in the format of that field’s kind', () => {
  let n = 0;
  for (const l of L) for (const f of figsIn(html[l])) {
    if (f.file !== FILE) { ok(f.at === null, `${l}: data-at on a figure of ${f.file}`); continue; }
    ok(f.at, `${l}: a figure of ${FILE} without its path (${f.raw})`);
    const path = P(f.at), v = valueAt(path);
    ok(typeof v === 'number' && v === f.raw, `${l}: ${f.at} is ${v}, printed raw ${f.raw}`);
    eq(f.fmt, formatFor(path), `${l}: ${f.at} format`);
    eq(f.text, FMT[f.fmt](f.raw), `${l}: ${f.at} text`);
    n++;
  }
  ok(n > 1000, `only ${n} figures`);
  return `${n / 2} figures per language`;
});
check('English and Chinese print the same figures, card by card and in the shell', () => {
  const key = h => figsIn(h).filter(f => f.file === FILE).map(f => `${f.at}|${f.fmt}`).sort();
  const en = cardSections('en'), zh = cardSections('zh');
  en.forEach((c, i) => eq(key(zh[i].sec), key(c.sec), `card ${c.card}`));
  eq(key(html.zh), key(html.en), 'the whole page');
  const cls = h => [...h.matchAll(/class="metric">([^<]+)</g)].map(m => m[1]);
  en.forEach((c, i) => eq(cls(zh[i].sec), cls(c.sec), `card ${c.card}: table figures, in order`));
});
check('a shared level prints its interval on its home card only, and names that card everywhere else', () => {
  let shared = 0;
  for (const l of L) for (const { card, sec } of cardSections(l)) {
    const figs = figsIn(sec).filter(f => f.file === FILE && /^studies\|[^|]+\|levels\|/.test(f.at ?? ''));
    for (const f of figs) {
      const [, id, , key, part] = P(f.at), home = homeOf(id, key);
      if (part === 'interval') eq(home, card, `${l}: ${f.at} prints its interval on card ${card}`);
      if (part === 'estimate' && home !== card) {
        const end = sec.indexOf('</span>', f.index), stop = sec.indexOf('data-fig=', end);
        const next = sec.slice(end, stop > 0 ? stop : undefined);
        ok(next.includes(`data-home="${home}"`), `${l}: ${f.at} on card ${card} names card ${home}, which carries its interval`);
        shared++;
      }
    }
  }
  for (const e of data.shared_estimates) ok(e.levels.every(x => Math.abs(S[x.study].levels[x.level].estimate - S[e.levels[0].study].levels[e.levels[0].level].estimate) < 1e-12),
    `${e.site_name} ${e.endpoint}: one value`);
  return `${shared / 2} levels named by their home card`;
});
check('every contrast prints its own interval beside it', () => {
  let n = 0;
  for (const l of L) {
    // A family member's cell names its 99.44% level between the difference and its bounds.
    const figs = figsIn(html[l]).filter(f => f.file === FILE && !/\|contrasts\|[^|]+\|interval_level$/.test(f.at));
    figs.forEach((f, i) => {
      const p = P(f.at);
      if (p[2] !== 'contrasts' || p[4] !== 'estimate') return;
      const base = p.slice(0, 4).join('|');
      eq([figs[i + 1]?.at, figs[i + 2]?.at], [`${base}|interval|0`, `${base}|interval|1`], `${l}: ${f.at} with its interval`);
      n++;
    });
  }
  return `${n / 2} contrasts per language`;
});
check('two equal levels print 0.00 pp; the flagged lower bound prints −0.00022; card 13’s seen change prints −5.72 pp', () => {
  const eqKey = 'studies|harmonic_pooling_wearable|contrasts|EIG-JOINT minus JOINT-ALLSUM/dry|estimate';
  ok(S.harmonic_pooling_wearable.contrasts['EIG-JOINT minus JOINT-ALLSUM/dry'].flags.levels_equal === true, 'the export flags the equal levels');
  const loKey = 'studies|coherence_eigen|contrasts|EIG-SPEC minus SPEC-HARM-SUM/u8|interval|0';
  for (const l of L) {
    const figs = figsIn(html[l]);
    ok(figs.filter(f => f.at === eqKey).length >= 1 && figs.filter(f => f.at === eqKey).every(f => f.text === '0.00 pp'), `${l}: the equal levels print 0.00 pp`);
    ok(figs.filter(f => f.at === loKey).length >= 1 && figs.filter(f => f.at === loKey).every(f => f.text === '−0.00022'), `${l}: the lower bound prints −0.00022`);
    ok(!/[−-]0\.00(?![\d])/.test(visible(html[l])), `${l}: a −0.00 somewhere`);
    ok(figs.filter(f => f.file === FILE && (f.fmt === 'pp2' || f.fmt === 'sgn2') && f.raw !== 0).every(f => !/^[+−]?0\.00(?: pp)?$/.test(f.text)), `${l}: a non-zero difference printed as zero`);
    ok(figs.some(f => f.at === 'studies|fixed_decay|contrasts|H3-DECAY minus H3-FLAT/seen_ba|estimate' && f.text === '−5.72 pp'), `${l}: card 13’s seen change`);
  }
});

// --- Card by card ------------------------------------------------------------------------------------------------------
const leadFigs = (l, n) => figsIn(sectionOf(html[l], cards.find(c => c.card === n).anchor).match(new RegExp(`data-ssvep-lead="${n}"[\\s\\S]*?</p>`))[0]).map(f => f.text);
check('card 8 lead: the two primary contrasts and the whitened readout’s descriptive gaps', () => {
  for (const l of L) {
    eq(leadFigs(l, 8), ['68.03%', '63.39%', '73.05%', '57.45%', '+10.58 pp', '+9.05', '+12.28', '72.00%', '67.59%', '76.65%', '80.90%', '−8.90 pp', '−11.20', '−6.69'], `${l}: lead figures`);
    const b = visible(sectionOf(html[l], 'cross-spectral').match(/data-ssvep-lead="8b"[\s\S]*?<\/p>/)[0]);
    ok(l === 'en' ? b.includes('−0.91 pp from CCA on held-out frequencies and −3.35 pp on seen ones') && b.includes('no planned contrast and no interval')
      : b.includes('−0.91 pp') && b.includes('−3.35 pp') && b.includes('没有计划内的对比，也没有区间'), `${l}: the descriptive gaps`);
  }
  ok(S.xspec.contrasts['XS-MLP minus CCA-RAW/u8'].flags.prespecified_noninferiority_to_CCA === false, 'the MLP’s non-inferiority test failed');
});
check('card 9 lead: the eigenvalue head against CCA and the harmonic sum; the two negative primaries', () => {
  for (const l of L) eq(leadFigs(l, 9), ['82.97%', '79.09%', '86.82%', '80.90%', '+2.07 pp', '+1.09', '+3.12', '82.90%', '78.90%', '86.93%', '+0.07 pp', '−0.45', '+0.62'], `${l}: lead figures`);
  const t = text(sectionOf(html.en, 'eigenvalue-pooling'));
  for (const s of ['−3.68 pp (−4.92 to −2.46)', '−5.07 pp (−6.61 to −3.59)', 'not a conventional (Welch) coherence estimate', 'given statistics derived from CCA',
    'the raw head’s result does not validate the spectral one', 'Card 6 listed a simpler learned head on the CCA features']) ok(t.includes(s), `en: “${s}”`);
});
check('card 10: the BETA primaries and secondaries, the Wearable-102 block on its own, matched CCA as card 7’s level', () => {
  for (const l of L) {
    const sec = sectionOf(html[l], 'harmonic-pooling');
    eq(leadFigs(l, 10), ['+0.30 pp', '−0.12', '+0.78', '−0.23 pp', '−0.57', '+0.11', '−0.87 pp', '−1.42', '−0.37'], `${l}: BETA primaries`);
    ok(/data-ssvep-scope="card-10-wearable"/.test(sec) && /<table data-ssvep-table="c10-beta">/.test(sec) && /<table data-ssvep-table="c10-wearable">/.test(sec), `${l}: separate BETA and Wearable-102 tables`);
    const row = sec.slice(sec.indexOf('<table data-ssvep-table="c10-wearable">')); const cca = row.slice(row.indexOf('data-arm="CCA-RAW"'), row.indexOf('</tr>', row.indexOf('data-arm="CCA-RAW"')));
    ok(cca.includes('data-home="7"') && !figsIn(cca).some(f => /\|interval\|/.test(f.at ?? '')), `${l}: matched CCA is card 7’s level, no second interval`);
  }
});
check('card 11: scope strip, the recipe named, route 3’s other recipe pointed to, the qualifier on eight electrodes', () => {
  const fb = S.practical_settings.design.fbcca;
  for (const l of L) {
    const sec = sectionOf(html[l], 'practical-settings'), t = visible(sec);
    ok(/data-ssvep-scope="card-11"/.test(sec), `${l}: its own scope strip`);
    ok(t.includes(fb.description[l]), `${l}: the recipe as the export words it`);
    ok(sec.includes(`href="${l === 'zh' ? '/zh' : ''}/topics/questions-in-language/#secondary"`) && t.includes(fb.other_recipe_on_site.code) && t.includes(fb.other_recipe_on_site.filter), `${l}: route 3’s S11 recipe, linked`);
    eq(leadFigs(l, 11).sort(), ['90.21%', '87.65%', '92.62%', '2.0 s', '82.90%', '+7.31 pp', '+5.15', '+9.47', '80.90%', '+9.31 pp', '+6.84', '+11.71'].sort(), `${l}: lead figures`);
    ok(l === 'en' ? t.includes('so eight electrodes do not always help') : t.includes('八个电极并不总是更好'), `${l}: the qualifier`);
    ok(l === 'en' ? t.includes('Card 6 listed filter-bank CCA among the things it did not run') : t.includes('把滤波器组 CCA 列为没有运行的部分'), `${l}: card 6’s not-run item, run here`);
    const held = sec.match(/<table data-ssvep-table="c11-held">[\s\S]*?<\/table>/)[0];
    eq([...held.matchAll(/data-cell="([^"]+)"/g)].map(m => m[1]), S.practical_settings.grid.cells, `${l}: the grid in prospective order`);
    eq((sec.match(/<table data-ssvep-table="c11-contrasts">[\s\S]*?<\/table>/)[0].match(/data-contrast=/g) ?? []).length, Object.keys(S.practical_settings.contrasts).length, `${l}: all contrasts`);
  }
});
check('card 11 timings: warm single-thread component medians of the anchor cell, labelled as the export labels them, never summed, no host label', () => {
  const cpu = S.practical_settings.cpu_components;
  ok(cpu.measurement.summed === false && cpu.measurement.threads === 1 && cpu.measurement.buffers === 'warm' && cpu.checks.whole_method_measurements === 0, 'the export’s measurement');
  for (const l of L) {
    const det = sectionOf(html[l], 'practical-settings').match(/<details[^>]*data-ssvep-details="c11-cpu"[\s\S]*?<\/details>/)?.[0];
    ok(det, `${l}: the timings sit in card 11’s details`);
    const t = visible(det);
    ok(t.includes(cpu.label[l]), `${l}: the label “${cpu.label[l]}”`);
    ok(l === 'en' ? t.includes('never summed') && t.includes('single-thread') && t.includes('Warm') : t.includes('从不相加') && t.includes('单线程') && t.includes('预热'), `${l}: warm, single-thread, never summed`);
    const figs = figsIn(det).filter(f => /\|cpu_components\|groups\|/.test(f.at ?? ''));
    ok(figs.length === cpu.components.length * 2 * 3 + 2 && figs.every(f => P(f.at)[4].startsWith(cpu.anchor_cell + '/')), `${l}: the anchor cell’s medians and ranges, nothing else`);
    ok(!/\b(?:A[M]D|Intel|Ry[z]en|Thread[r]ipper|Xeon|EPYC|GHz|Ubuntu|Linux|macOS)\b|T[R]X|主机/i.test(t), `${l}: a host or processor label`);
    const medians = cpu.components.map(c => cpu.groups[`${cpu.anchor_cell}/1/${c.code}`].wall_ms_per_call.median);
    const sum = medians.reduce((a, b) => a + b, 0);
    ok(!figsIn(html[l]).some(f => Math.abs(f.raw - sum) < 1e-9), `${l}: a summed timing`);
  }
  for (const l of L) ok(!/whole-method|end-to-end latency of|端到端延迟为/.test(visible(html[l])), `${l}: no whole-method latency`);
});
check('card 12: the bridge with its family intervals, the gap in score units, the identity line, decision changes as shares', () => {
  for (const l of L) {
    const sec = sectionOf(html[l], 'harmonic-gap'), t = visible(sec);
    eq(leadFigs(l, 12), ['80.90%', '80.94%', '76.79%', '84.90%', '82.90%', '+0.04 pp', '−0.10', '+0.19', '+1.96 pp', '+1.06', '+2.96', '99.44%'], `${l}: the bridge`);
    ok(l === 'en' ? t.includes('Separate harmonic references are not orthogonal over a finite window, so joint CCA squared is not in general the largest eigenvalue of the summed matrices; the coupling residual R = B − J is reported beside G')
      : t.includes('在有限长的时间窗上，各谐波的参考彼此并不正交'), `${l}: the identity line`);
    const g = figsIn(sec.match(/data-ssvep-lead="12b"[\s\S]*?<\/p>/)[0]);
    eq(g.map(f => f.fmt), Array(9).fill('sig3'), `${l}: the gap in squared-correlation units, never a percentage`);
    eq(g.map(f => f.text), ['0.0617', '0.0519', '0.0732', '0.0232', '0.0186', '0.0286', '0.0435', '0.0355', '0.0525'], `${l}: the gap figures`);
    const tr = sec.match(/<table data-ssvep-table="c12-transitions">[\s\S]*?<\/table>/)[0];
    ok(figsIn(tr).every(f => /\|transitions\|(?:edges\|[^|]+\|(?:wrong_to_right|right_to_wrong|changed|unchanged_right|wrong_both)|decisions)$/.test(f.at) && (f.fmt === 'pct2' || /decisions$/.test(f.at))), `${l}: decision changes as shares of the decisions`);
    ok(!figsIn(sec).some(f => /\|win_fractions\|/.test(f.at ?? '') && f.fmt !== 'auc3'), `${l}: win fractions never as percentages`);
    ok(l === 'en' ? t.includes('8 of 40 BETA candidates') : t.includes('40 个候选中有 8 个'), `${l}: the reference check as counts`);
  }
});
check('card 13: the decay rule, the 90% margin test outside ±0.5 pp, the sub-band gain on card 11’s filter-bank CCA', () => {
  for (const l of L) {
    const f = leadFigs(l, 13);
    eq(f.slice(0, 2), ['1.25', '0.25'], `${l}: the rule’s exponent and offset`);
    for (const x of ['82.90%', '79.91%', '−2.99 pp', '−3.77', '−2.29', '90%', '−3.64', '−2.38', '±0.5 pp', '85.01%', '90.21%', '+5.21 pp', '+4.08', '+6.38']) ok(f.includes(x), `${l}: ${x}`);
    ok(l === 'en' ? visible(sectionOf(html[l], 'fixed-decay')).includes('so the equivalence criterion is not met') : visible(sectionOf(html[l], 'fixed-decay')).includes('不满足等效标准'), `${l}: the criterion not met`);
  }
  ok(S.fixed_decay.equivalence.met === false && S.fixed_decay.equivalence.interval[1] < -S.fixed_decay.equivalence.margin, 'the export: not met, wholly outside');
});
check('card 14: the single prespecified criterion, met; Wearable-102 dry down, wet unresolved', () => {
  for (const l of L) eq(leadFigs(l, 14), ['82.90%', '83.76%', '79.91%', '87.32%', '+0.86 pp', '+0.29', '+1.45'], `${l}: lead figures`);
  ok(S.rising_weights.criterion.met === true && S.rising_weights.criterion.prespecified === true, 'the export: met');
  const t = text(sectionOf(html.en, 'rising-weights'));
  for (const s of ['The single prespecified criterion, a paired 95% interval wholly above zero, is met.', '−1.14 pp (−1.86 to −0.46)', '−0.43 pp (−1.03 to +0.16)',
    'the actual filter passbands are wider than their nominal edges'.replace(/^t/, 'T')]) ok(t.includes(s), `en: “${s}”`);
});
check('learned arms sit beside their untrained controls in every levels table', () => {
  for (const l of L) for (const { card, sec } of cardSections(l)) for (const t of sec.matchAll(/<table data-ssvep-table="(c\d+-(?:levels|beta|wearable))">[\s\S]*?<\/table>/g)) {
    const v = visible(t[0]);
    ok(l === 'en' ? /no training/.test(v) : /无需训练/.test(v), `${l}: ${t[1]} has an untrained control`);
    if (card !== 12 && card !== 13 && card !== 14) ok(l === 'en' ? /ridge fitted|MLP trained|BETA heads/.test(v) : /岭回归|MLP|分类头/.test(v), `${l}: ${t[1]} has a learned arm`);
  }
});

// --- The shell's share of this release ----------------------------------------------------------------------------
check('scope line for cards 8 to 14: the cohorts, and “not external replication” once on the page', () => {
  for (const l of L) {
    const s = html[l].match(/data-ssvep-scope="cards-8-14"[^>]*>([\s\S]*?)<\/p>/);
    ok(s, `${l}: the scope line`);
    eq(figsIn(s[0]).map(f => f.at), ['studies|xspec|design|dataset|people', 'studies|harmonic_pooling_wearable|design|dataset|people'], `${l}: its figures`);
    const phrase = l === 'en' ? 'not external replication' : '不是外部重复验证';
    eq((visible(html[l]).match(new RegExp(phrase, 'g')) ?? []).length, 1, `${l}: “${phrase}” once`);
  }
});
check('the multiplicity sentence: card 12’s Bonferroni family and card 13’s 90% interval, no other adjusted', () => {
  const SENT = { en: 'Card 12’s primary family uses Bonferroni-adjusted 99.44% intervals over nine comparisons, and card 13’s equivalence test a 90% interval; no other interval is adjusted.',
                 zh: '卡片 12 的主要比较族在九个比较上使用 Bonferroni 校正的 99.44% 区间，卡片 13 的等效检验使用 90% 区间；其余区间都没有校正。' };
  for (const l of L) {
    const p = html[l].match(/<p class="roadmap-p" data-ssvep-note="rounding">([\s\S]*?)<\/p>/)[1];
    ok(visible(p).trim().startsWith(SENT[l]), `${l}: “${SENT[l]}”`);
    eq(figsIn(p).map(f => f.at), ['interval_adjustment|adjusted|0|level', 'interval_adjustment|adjusted|1|level'], `${l}: its figures`);
    ok(!/No interval is adjusted for multiple comparisons|没有任何区间做多重比较校正/.test(visible(html[l])), `${l}: the old sentence`);
  }
  ok(data.interval_adjustment.other_intervals_adjusted === false, 'the export');
});
check('intervals card by card, 8 to 14, each with its draws and seeds', () => {
  for (const l of L) {
    const sec = sectionOf(html[l], 'methods-and-limits');
    for (const m of data.interval_methods) {
      const li = sec.match(new RegExp(`<li data-interval-cards="${m.card}">[\\s\\S]*?</li>`))?.[0];
      ok(li, `${l}: card ${m.card}’s interval line`);
      ok(figsIn(li).some(f => f.at === `interval_methods|${data.interval_methods.indexOf(m)}|draws`), `${l}: card ${m.card}’s draws`);
      for (const s of m.seed ? [m.seed] : Object.values(m.seeds)) ok(visible(li).includes(String(s)), `${l}: card ${m.card}’s seed ${s}`);
    }
  }
});
check('engineering disclosures, not run and not published: both files’ lists', () => {
  const NR = { en: ['a learned cell on the raw time series', 'a conventional averaged (Welch) coherence estimator', 'a physical four-electrode headset', 'other exponents, offsets or harmonic counts', 'a pre-stimulus alpha or noise measurement'],
               zh: ['在原始时间序列上的学习单元', '常规的平均（Welch）相干估计', '实体的四电极头戴设备', '其他指数、偏移量或谐波数', '刺激前的 alpha 或噪声测量'] };
  for (const l of L) {
    const sec = sectionOf(html[l], 'methods-and-limits'), t = visible(sec);
    for (const n of [8, 9, 10, 11, 12, 13, 14]) ok(new RegExp(`<li data-not-run-card="${n}">`).test(sec), `${l}: card ${n}’s not-run line`);
    for (const s of NR[l]) ok(t.includes(s), `${l}: not run “${s}”`);
    for (const n of [8, 9]) ok(new RegExp(`<li data-disclosure-card="${n}">`).test(sec), `${l}: card ${n}’s disclosures`);
    ok(figsIn(sec).some(f => f.at === 'engineering_disclosures|3|rerun_tests_passed'), `${l}: the rerun’s test count`);
    const np = sec.match(/data-ssvep-note="not-published-8-14">([\s\S]*?)<\/ul>/)[1];
    eq((np.match(/<li>/g) ?? []).length, data.not_published.length, `${l}: this file’s not-published items`);
    const rp = sec.match(/data-ssvep-note="not-published">([\s\S]*?)<\/ul>/)[1];
    eq((rp.match(/<li>/g) ?? []).length, released.not_published.length - 3, `${l}: the released items still in force`);
    ok(!/in progress at the freeze|冻结时仍在进行|Measured compute: run times|实测的计算量/.test(t), `${l}: the replaced released items are gone`);
    ok(l === 'en' ? t.includes('Run times of whole evaluations and audits') : t.includes('整轮评测与审计的运行时间'), `${l}: the narrowed compute item`);
  }
});
check('name key: the new file’s names join it, “joint CCA” as an alias of the CCA scores', () => {
  for (const l of L) {
    const t = html[l].match(/<table data-ssvep-table="name-key">[\s\S]*?<\/table>/)[0];
    const names = [...t.matchAll(/data-name="([^"]+)"/g)].map(m => decode(m[1]));
    const want = [...released.name_key.filter(n => n.in_page_key).map(n => n.site_name), ...data.name_key.filter(n => n.key === 'new').map(n => n.site_name)];
    eq(names, want, `${l}: names`);
    for (const n of data.name_key.filter(x => x.key !== 'card')) {
      if (!names.includes(n.site_name)) { eq(n.site_name, 'matched CCA', `${l}: ${n.site_name} off the key`); continue; }
      const at = t.indexOf(`data-name="${n.site_name}"`), row = t.slice(at, t.indexOf('</tr>', at));
      for (const c of new Set(n.codes.map(x => x.code))) ok(row.includes(`<code>${c}</code>`), `${l}: ${n.site_name} shows ${c}`);
      for (const c of new Set(n.codes.map(x => cardOfStudy(x.study)))) ok(row.includes(`>${c}</a>`), `${l}: ${n.site_name} names card ${c}`);
    }
    const j = t.slice(t.indexOf('data-name="joint CCA"'), t.indexOf('</tr>', t.indexOf('data-name="joint CCA"')));
    ok(l === 'en' ? visible(j).includes('an alias of CCA (no training) and matched CCA') : visible(j).includes('CCA（无需训练）、匹配 CCA的别名'), `${l}: joint CCA is an alias`);
    for (const n of data.name_key.filter(x => x.key === 'card')) ok(!names.includes(n.site_name), `${l}: ${n.site_name} stays on its card`);
  }
});
check('short answer: D22’s sentence from this file; dek counts both files’ cards', () => {
  const ps = S.practical_settings, ce = S.coherence_eigen;
  const fb = ps.levels['w500-c8/FBCCA-M3-N7-H5/u8'], cca = ps.levels['w500-c8/CCA-RAW-H3/u8'], g = ps.contrasts['w500-c8/FBCCA-M3-N7-H5 minus w500-c8/CCA-RAW-H3/u8'];
  const e = ce.contrasts['EIG-RAW minus RAW-HARM-SUM/u8'];
  const want = [FMT.pct2(fb.estimate), FMT.pct2(cca.estimate), FMT.pp2(g.estimate), FMT.sgn2(g.interval[0]), FMT.sgn2(g.interval[1]), FMT.pp2(e.estimate), FMT.sgn2(e.interval[0]), FMT.sgn2(e.interval[1])];
  eq(want, ['90.21%', '80.90%', '+9.31 pp', '+6.84', '+11.71', '+0.07 pp', '−0.45', '+0.62'], 'the figures');
  const nCards = released.placement.cards.filter(c => !c.status_only).length + cards.length, nWear = released.wearable.cards.length + data.endpoints.find(x => x.id === 'wearable_12').cards.length;
  eq([nCards, nWear], [14, 5], 'fourteen cards, five on Wearable-102');
  const betaCards = [...released.cohort.cards, ...data.endpoints.find(x => x.id === 'u8').cards];
  const wearCards = [...released.wearable.cards, ...data.endpoints.find(x => x.id === 'wearable_12').cards];
  eq([betaCards.length, wearCards.filter(n => !betaCards.includes(n)).length], [13, 1], 'thirteen on BETA, one only on Wearable-102');
  for (const l of L) {
    const a = html[l].slice(html[l].indexOf('<section class="short-answer"'), html[l].indexOf('</section>', html[l].indexOf('<section class="short-answer"')));
    eq([...a.matchAll(/<strong class="fig">([^<]*)<\/strong>/g)].map(m => decode(m[1])).slice(-8), want, `${l}: D22’s figures, last in the answer`);
    ok(l === 'en' ? visible(a).includes('filter-bank CCA, which needs no training, reached') && visible(a).includes('the untrained harmonic sum came out nearly level with the learned eigenvalue head') && !/harmonic sum matched/.test(visible(a))
      : visible(a).includes('不需要训练的滤波器组 CCA 达到') && visible(a).includes('不需要训练的谐波求和与学习得到的特征值分类头几乎持平'), `${l}: D22’s sentence`);
    const dek = visible(html[l].match(/<p class="dek">([\s\S]*?)<\/p>/)?.[1] ?? html[l].match(/class="[^"]*dek[^"]*">([\s\S]*?)<\/p>/)?.[1] ?? '');
    ok(l === 'en' ? dek.startsWith('Fourteen follow-ups') && dek.includes('Thirteen run on its BETA cohort and five on Wearable-102, one of them only there.')
      : dek.includes('十四项后续检验') && dek.includes('其中十三项在它的 BETA 队列上运行，五项在 Wearable-102 上运行，有一项只在 Wearable-102 上运行。'), `${l}: the dek’s counts, as the topic card counts them “${dek.slice(0, 60)}”`);
  }
});
check('credits: FBCCA (Chen et al. 2015) with its method page and paper; BETA and Wearable-102 name their cards', () => {
  const fb = data.rights.credits.fbcca;
  for (const l of L) {
    const sec = sectionOf(html[l], 'methods-and-limits'), art = sec.match(/<article data-credit="fbcca">[\s\S]*?<\/article>/)?.[0];
    ok(art, `${l}: the FBCCA credit`);
    ok(art.includes(`href="${l === 'zh' ? '/zh' : ''}${fb.method_page}"`) && art.includes(`href="${fb.reference_url}"`) && decode(art).includes(fb.reference) && decode(art).includes(fb.short), `${l}: its page, paper and reference`);
    const beta = visible(sec.match(/<article data-credit="beta">[\s\S]*?<\/article>/)[0]), wear = visible(sec.match(/<article data-credit="wearable-ssvep-102">[\s\S]*?<\/article>/)[0]);
    ok(l === 'en' ? beta.includes('Cards 1 to 6 and 8 to 14') && wear.includes('Cards 7, 10, 12, 13 and 14.') : beta.includes('卡片 1 至 6 与 8 至 14') && wear.includes('卡片 7、10、12、13、14。'), `${l}: the cards each dataset serves`);
    ok(sec.includes(`href="/data/${FILE}" download`) && sec.includes(`href="/data/${RELEASED}" download`), `${l}: both data files`);
  }
});
check('cite block names both releases, newest first', () => {
  for (const l of L) eq(html[l].match(/<section class="cite-page"[^>]*data-releases="([^"]+)"/)?.[1], `${data.release_id} ${released.release_id}`, `${l}: cite releases`);
});

// --- The F3 review's fixes (2026-10-28) ----------------------------------------------------------------------------
check('review: the name key collapsed (D31); card 11 points to route 3’s recipe with no figure of it (D32); the copy fixes hold', () => {
  for (const l of L) {
    // D31: the name key, one row per set of scores across both files, sits in a collapsed panel in the setup section.
    const setup = sectionOf(html[l], 'setup'), det = setup.match(/<details class="rd-panel" data-ssvep-details="name-key">[\s\S]*?<\/details>/)?.[0];
    ok(det && det.includes('<table data-ssvep-table="name-key">') && !/data-ssvep-details="name-key" open/.test(setup), `${l}: the name key is a collapsed panel`);
    // D32: card 11 names S11 and links route 3's page, and prints nothing from that page's export.
    const c11 = sectionOf(html[l], 'practical-settings'), rec = c11.match(/data-ssvep-note="recipe"[\s\S]*?<\/p>/)[0];
    ok(!figsIn(c11).some(f => f.file === 'questions-in-language-update.json') && !/90\.4/.test(visible(c11)), `${l}: card 11 prints a figure of route 3’s recipe`);
    ok(text(rec).includes(l === 'en' ? 'Route 3’s page reports another filter-bank recipe on the same task, S11, with five Butterworth sub-bands.'
      : '第三条路线的页面报告了同一任务上的另一种滤波器组方案 S11，用五个巴特沃斯（Butterworth）子带。'), `${l}: card 11’s pointer to route 3’s recipe`);
    // Card 10's Wearable-102 caption types no figure (the scope line above prints the candidates).
    const cap = visible(sectionOf(html[l], 'harmonic-pooling').match(/<table data-ssvep-table="c10-wearable">\s*<caption>([\s\S]*?)<\/caption>/)[1]);
    ok(!/\d/.test(cap.replace(/Wearable-102|Card 10|card 7|卡片 10|卡片 7/g, '')), `${l}: a typed figure in card 10’s Wearable-102 caption “${cap}”`);
    // Card 11's sentences say the electrode count in words, as the card's lead does.
    for (const k of ['11b', '11']) ok(!/\d electrodes|\d 个电极/.test(text(c11.match(new RegExp(`data-ssvep-lead="${k}"[\\s\\S]*?<\\/p>`))[0])), `${l}: card 11 lead ${k} prints an electrode count as a digit`);
    // Card 12's reference check says what it measures; card 9 names its two margins; card 14 says where its weights come from.
    const c12 = visible(sectionOf(html[l], 'harmonic-gap')), c9 = visible(sectionOf(html[l], 'eigenvalue-pooling')), c14 = visible(sectionOf(html[l], 'rising-weights'));
    ok(l === 'en' ? c12.includes('the cross-block norm between the harmonic reference blocks falls at or below the threshold, so those blocks are orthogonal to numerical precision')
      : c12.includes('各谐波参考块之间的跨块范数不超过阈值，即这些候选的参考块在数值精度内正交'), `${l}: card 12’s reference check`);
    ok(l === 'en' ? c9.includes('inside the equivalence and non-inferiority margins the protocol set in advance') : c9.includes('落在协议事先设定的等效界值与非劣效界值之内'), `${l}: card 9’s two margins`);
    ok(l === 'en' ? c14.includes('The rising weights follow a coverage heuristic: filter-bank CCA’s sub-bands share one upper edge, so a higher harmonic falls in more of them.')
      : c14.includes('递增权重依据一种覆盖度的经验估计：滤波器组 CCA 的各子带共用同一个上边界，所以越高的谐波落入的子带越多。'), `${l}: card 14’s coverage heuristic`);
    ok(S.rising_weights.limitations_keys.includes('coverage_heuristic') && S.practical_settings.design.fbcca.pass_band_low_edges_hz.length === S.practical_settings.design.fbcca.sub_bands
      && typeof S.practical_settings.design.fbcca.pass_band_high_edge_hz === 'number', 'the export: the coverage heuristic and one upper edge');
  }
  // Chinese typography on cards 8 to 14: no space after a full-width closing parenthesis, no nested full-width parentheses.
  for (const { card, sec } of cardSections('zh')) {
    for (const p of sec.matchAll(/<p class="(?:roadmap-p|protocol-note)[^"]*"[^>]*>[\s\S]*?<\/p>/g)) ok(!/）\s+[一-鿿]/.test(text(p[0])), `zh: card ${card} has a space after “）”: “${text(p[0]).slice(0, 60)}”`);
    for (const p of sec.matchAll(/<p class="roadmap-p"[^>]*>[\s\S]*?<\/p>/g)) {
      let d = 0, mx = 0; for (const ch of text(p[0])) { if (ch === '（') mx = Math.max(mx, ++d); else if (ch === '）') d--; }
      ok(mx <= 1, `zh: card ${card} nests full-width parentheses: “${text(p[0]).slice(0, 60)}”`);
    }
  }
});

// --- What must never appear ------------------------------------------------------------------------------------------
// blocks_cca.REFUSED_TEXT, read from its source, so this file adds no literal of what it refuses.
const REFUSED = (() => {
  const py = readFileSync(fileURLToPath(new URL('../../../pipeline/publication/ssvep_followups/blocks_cca.py', import.meta.url)), 'utf8');
  const at = py.indexOf('REFUSED_TEXT = re.compile(');
  ok(at >= 0, 'blocks_cca.py: REFUSED_TEXT');
  return new RegExp([...py.slice(at, py.indexOf(', re.IGNORECASE)', at)).matchAll(/r'((?:[^'\\]|\\.)*)'/g)].map(m => m[1]).join(''), 'i');
})();
// A printed figure is a field of a served file (held to it above and in new-ssvep-frequencies.mjs), and neither file
// holds the thread's figure (walked below); a figure's own digits can read like it ("30.55%", card 10's "+0.55" pp), so
// the words are read with every figure set aside, and a figure itself must not print as the thread's percentage.
const figTexts = () => [...new Set(L.flatMap(l => figsIn(html[l]).map(f => f.text)))].sort((a, b) => b.length - a.length);
check('nothing refused: no private path, host, the thread’s figure or its commenter; no pending or superseded wording', () => {
  const ft = figTexts().filter(x => REFUSED.test(x)), strip = s => ft.reduce((t, x) => t.split(x).join(' '), s);
  const noFigs = h => h.replace(/<span (?:data-at="[^"]*" )?data-fig="[^"]*"[^>]*>[^<]*<\/span>/g, ' ');
  for (const l of L) {
    for (const f of figsIn(html[l])) ok(!/^[+−]?55(?:\.0+)?%$|^0\.55$/.test(f.text), `${l}: the figure ${f.text} (${f.at ?? f.file})`);
    const v = visible(noFigs(html[l])), m = v.match(REFUSED);
    ok(!m, `${l}: page text “${m && v.slice(Math.max(0, m.index - 50), m.index + 30)}”`);
    const attrs = [...html[l].matchAll(/\s(?:aria-label|title|alt|content)="([^"]*)"/g)].map(x => decode(x[1])).join(' ¶ ').match(REFUSED);
    ok(!attrs, `${l}: attribute “${attrs?.[0]}”`);
    if (md[l]) { const k = strip(md[l]).match(REFUSED); ok(!k, `${l}: Markdown “${k?.[0]}”`); }
  }
  const walk = (v, p) => { if (typeof v === 'string') ok(!REFUSED.test(v), `served file ${p}`); else if (typeof v === 'number') ok(v !== 0.55, `served file ${p}`);
    else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) walk(x, `${p}.${k}`); };
  walk(data, '');
  const rw = (v, p) => { if (typeof v === 'number') ok(v !== 0.55 && v !== 55, `released file ${p}`); else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) rw(x, `${p}.${k}`); };
  rw(released, '');
});
check('the thread’s prediction stays on card 4: no 39% and no thread link on cards 8 to 14', () => {
  for (const l of L) for (const { card, sec } of cardSections(l)) {
    ok(!/(?<![\d.])39%/.test(visible(sec)), `${l}: 39% on card ${card}`);
    ok(!/huggingface\.co\/posts\//.test(sec), `${l}: the thread linked from card ${card}`);
    ok(!/\b(?:bet|forecast|predicted)\b|赌注|预测/.test(visible(sec)), `${l}: a thread prediction on card ${card}`);
  }
});
check('no BETA-against-Wearable ranking; no version label or update date on cards 8 to 14', () => {
  const RANK = { en: /\b(?:best|winner|outperform\w*|beats?|state of the art|SOTA|ranks?|ranked|ranking|superior|significan\w*)\b|\bmore accurate than BETA|\bharder than BETA/i, zh: /最佳|最好|胜出|排名|最先进|第一名|显著/ };
  const LABELS = /\b[Uu]pdated\b|\b[Nn]ew in\b|\b[Ss]ince (?:20\d\d|\w+ \d)|(?<![\w.\/#-])[vV]\d+\b|更新于|新增于|本次更新/;
  for (const l of L) for (const { card, sec } of cardSections(l)) {
    const v = visible(sec), r = v.match(RANK[l]), d = v.match(LABELS);
    ok(!r, `${l}: card ${card} “${r?.[0]}”`); ok(!d, `${l}: card ${card} “${d?.[0]}”`);
  }
});
check('markup: plain tables with a header row, four or more columns inside <details>, no inline style or handler, Chinese periods', () => {
  for (const l of L) for (const { card, sec } of cardSections(l)) {
    for (const t of sec.matchAll(/<table\b[\s\S]*?<\/table>/g)) ok(/<thead><tr>/.test(t[0]), `${l}: card ${card} table without a header row`);
    for (const d of sec.matchAll(/<details\b[\s\S]*?<\/details>/g)) for (const t of d[0].matchAll(/<table\b[\s\S]*?<\/table>/g))
      ok(((t[0].match(/<thead>[\s\S]*?<\/thead>/)?.[0] ?? '').match(/<th\b/g) ?? []).length >= 4, `${l}: card ${card} details table columns`);
    ok(!/\sstyle="|<script|\son[a-z]+=/.test(sec) && !/data-astro-cid/.test(sec), `${l}: card ${card} inline style, script or handler`);
  }
  for (const { card, sec } of cardSections('zh')) {
    const zhOnly = sec.replace(/<(p|span|h3|li)\b[^>]*\slang="en"[^>]*>[\s\S]*?<\/\1>/g, '');
    ok(!/[一-鿿\d]\.<\/(?:p|li|caption)>/.test(zhOnly), `zh: card ${card} ends a Chinese sentence with an ASCII period`);
    ok(!/卡片 \d+[一-鿿]/.test(visible(sec)), `zh: card ${card} runs a card number into Chinese`);
  }
});
check('every table figure survives into the Markdown copy', () => {
  for (const l of L) { ok(md[l], `${l}: no Markdown copy`);
    for (const { card, sec } of cardSections(l)) for (const [, v] of sec.matchAll(/class="metric">([^<]+)</g)) ok(md[l].includes(decode(v)), `${l}: card ${card} ${v}`); }
});

// --- Report --------------------------------------------------------------------------------------------------------
const w = Math.max(...results.map(r => r.name.length));
for (const r of results) console.log(`${r.status.padEnd(7)} ${r.name.padEnd(w)}${r.detail ? '  — ' + r.detail : ''}`);
const fails = results.filter(r => r.status === 'FAIL').length, pend = results.filter(r => r.status === 'PENDING').length;
console.log(`\nssvep-followups: ${results.length - fails - pend} passed, ${pend} pending, ${fails} failed (${DIST})`);
process.exit(fails ? 1 : 0);
