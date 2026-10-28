// The release log as an index and an archive (owner decisions D17, D20 and D29, 2026-10-28): /releases/ and
// /releases/archive/ in both languages, the /api/ release links and the feed, checked in a built site.
//
//   node scripts/checks/release-log.mjs <build dir>        (or import { checkReleaseLog } and pass the dir)
//
// The archive is the record: every release's entry as released, so the ids, dates and files it lists are what the
// index is checked against. What it holds, in both languages:
//  (a) the index's #latest has exactly three <article class="release-latest">, one for each of the three newest release
//      dates, each with <h3 id="day-…"><time>, and its <ul class="release-ids"> lists that day's ids in the archive's
//      order, each <li id> linking its archive entry and its files as plain downloads;
//  (b) each day has one to three changes, each with one or two links that land on a built page and anchor, at most 220
//      English or 110 Chinese characters, no date, version label or update word; the figures each change prints are the
//      ones its payloads give (pinned below for the three days this round shows) and English and Chinese print the same;
//  (c) every release id appears once on the index as a visible id (#latest or #earlier, never inside <details>); #earlier
//      lists every older id in the archive's order with its date, its archive link and the pages it added; no open-hold
//      row sits inside <details>, the resolved holds sit in <details class="holds-resolved"> with their row ids and the
//      hold-resolved class, and the open holds come first, newest first; the corrections come before the holds;
//  (d) no hash on the index: no class="hash", no data-file=, no SHA-256 value, no release-entry article;
//  (e) every /releases/#hold-<id> link on any page or Markdown copy names an open hold's row;
//  (f) every other /releases/#<id> link on any page or Markdown copy lands on a visible id of the index;
//  (g) the archive has no holds or corrections table and links both; it lists every served file once, each with the
//      SHA-256 of the served bytes, and each payload's review manifest in its release's entry; the feed's entries keep
//      their /releases/#<id> ids and link their archive entries;
//  (h) every /releases/archive/#<id> link on /api/ lands on an archive entry, /api/ links the archive for the hashes and
//      no longer links /releases/#<id>;
//  and on both pages: a <thead> on every table, four or more columns for a table in <details>, no inline script, style
//  attribute or handler, reciprocal hreflang, the Markdown copy carrying every change and id, and no private path, host
//  label, "55%" or the thread commenter's name (blocks_cca.REFUSED_TEXT, read from its source).
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { strict as assert } from 'node:assert';
import { createHash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const LATEST_DAYS = 3;
const LIMIT = { en: 220, zh: 110 };
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DATE_OR_VERSION = new RegExp(`\\b20\\d\\d\\b|\\b(?:${MONTHS.join('|')})\\b|\\b(?:[Uu]pdated|[Ss]ince|[Nn]ew in|[Aa]dded)\\b|(?<![\\w./#-])[vV]\\d+\\b|\\d+ ?[年月日]|更新|新增于|本次|这次|第[一二三四五六七八九十]+轮`);
const FIGURES = /(?<![A-Za-z0-9.-])[0-9][0-9,.]*(?<![,.])/g;
const WORDS_IN = { en: /\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten)\b/gi, zh: /[零一两二三四五六七八九十]+(?=个|项|名|秒|通道)/g };
const WORDS = { en: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'], zh: ['零', '一', '两', '三', '四', '五', '六', '七', '八', '九', '十'] };
// Glossary renderings the site rejects (check-workbench.mjs `rejected`), the ones this page could reach.
const REJECTED_ZH = ['参与者', '受试者', '读出头', '区块', '暴露', '个百分点', '源数据'];

const decode = s => s.replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d))).replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const vis = h => decode(h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
// Visible text with no space added at tag boundaries (an inline link's text joins the words around it).
const text = h => decode(h.replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
// The element that opens at `at`, through its matching close tag.
const spanEnd = (h, at) => {
  const tag = h.slice(at + 1).match(/^\w+/)[0], re = new RegExp(`<${tag}\\b|</${tag}>`, 'g');
  re.lastIndex = at; let d = 0, m;
  while ((m = re.exec(h))) { d += m[0].startsWith('</') ? -1 : 1; if (!d) return m.index + m[0].length; }
  return h.length;
};
const el = (h, sel, where) => { const a = h.search(sel); assert.ok(a >= 0, `${where}: ${sel} renders`); return h.slice(a, spanEnd(h, a)); };
const all = (h, re) => [...h.matchAll(re)].map(m => h.slice(m.index, spanEnd(h, m.index)));
const spans = (h, re) => [...h.matchAll(re)].map(m => [m.index, spanEnd(h, m.index)]);
const sorted = a => [...a].sort();

// blocks_cca.REFUSED_TEXT, read from its source, so this file adds no literal of what it refuses.
const refusedText = () => {
  const py = readFileSync(fileURLToPath(new URL('../../../pipeline/publication/ssvep_followups/blocks_cca.py', import.meta.url)), 'utf8');
  const at = py.indexOf('REFUSED_TEXT = re.compile(');
  assert.ok(at >= 0, 'blocks_cca.py: REFUSED_TEXT');
  const body = py.slice(at, py.indexOf(', re.IGNORECASE)', at));
  return new RegExp([...body.matchAll(/r'((?:[^'\\]|\\.)*)'/g)].map(m => m[1]).join(''), 'i');
};

export function checkReleaseLog(distDir) {
  const DIST = resolve(distDir);
  assert.ok(existsSync(join(DIST, 'index.html')), `${DIST}: not a built site`);
  const read = p => readFileSync(join(DIST, p), 'utf8');
  const exists = p => existsSync(join(DIST, p));
  const srcJson = f => JSON.parse(readFileSync(fileURLToPath(new URL(`../../src/data/${f}`, import.meta.url)), 'utf8'));
  const REFUSED = refusedText();
  let checks = 0;
  const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };
  const eq = (a, b, msg) => { assert.deepEqual(a, b, msg); checks++; };
  const servedFiles = readdirSync(join(DIST, 'data')).sort();

  // Every page and Markdown copy of the build, for the link checks (e, f).
  const walk = rel => readdirSync(join(DIST, rel), { withFileTypes: true }).flatMap(d => d.isDirectory()
    ? (['_astro', 'data'].includes(d.name) && rel === '' ? [] : walk(rel + d.name + '/')) : [rel + d.name]);
  const pageFiles = walk('').filter(f => /(?:^|\/)index\.(?:html|md)$/.test(f));

  // The pins: the figures each change of this round's three days prints, from the payloads (D29).
  const sc = srcJson('ssvep-followups-update.json'), dc = srcJson('dataset-checks-update.json'), ts = srcJson('eegmat-ten-second-update.json');
  const reg20 = srcJson('open-register-20261020.json'), eegpt = srcJson('eegpt-core-update.json');
  const ch = id => eegpt.protocols.find(p => p.id === id).channels;
  const w = n => ({ en: WORDS.en[n], zh: WORDS.zh[n] });
  const PINS = {
    '2026-10-28': [{ words: [w(sc.placement.cards.length)], digits: [] }, { words: [w(ts.cohort.window_seconds)], digits: [] }, { words: [w(dc.cases.length)], digits: [] }],
    '2026-10-20': [{ words: [], digits: [reg20.counts.rows.total.toLocaleString('en-US')] }, { words: [w(2)], digits: [] }, { words: [], digits: [] }],
    '2026-10-13': [{ words: [], digits: [] }, { words: [w(ch('beta-4ch')), w(ch('sleep-scalp'))], digits: [] }, { words: [], digits: [] }],
  };
  ok(PINS['2026-10-20'][1].words[0].en === 'two', 'the 2026-10-20 questions pin');

  const archives = {}, indexes = {}, changeFigs = {};
  let archiveEntries = null;
  for (const lang of ['en', 'zh']) {
    const pfx = lang === 'zh' ? 'zh/' : '', lp = lang === 'zh' ? '/zh' : '';
    const AW = `/${pfx}releases/archive/`, IW = `/${pfx}releases/`;
    const arch = read(`${pfx}releases/archive/index.html`), idx = read(`${pfx}releases/index.html`);
    archives[lang] = arch; indexes[lang] = idx;
    const amain = el(arch, /<main\b/, AW), imain = el(idx, /<main\b/, IW);

    // The archive: every entry as released.
    const entries = all(amain, /<article class="release-entry" id="/g).map(a => {
      const m = a.match(/^<article class="release-entry" id="([^"]+)">\s*<header><time datetime="([^"]+)">/);
      assert.ok(m, `${AW}: an entry opens with its id and date`);
      return { id: m[1], date: m[2], html: a, files: [...a.matchAll(/data-file="([^"]+)"/g)].map(x => x[1]) };
    });
    ok(entries.length >= 20, `${AW}: every release (${entries.length})`);
    ok(entries.every((e, i) => i === 0 || e.date <= entries[i - 1].date), `${AW}: newest first`);
    ok(new Set(entries.map(e => e.id)).size === entries.length, `${AW}: each id once`);
    if (archiveEntries) eq(entries.map(e => [e.id, e.date, e.files]), archiveEntries.map(e => [e.id, e.date, e.files]), `${AW}: the same entries in both languages`);
    else archiveEntries = entries;
    ok(vis(el(amain, /<h1\b/, AW)) === (lang === 'zh' ? '发布归档' : 'Release archive'), `${AW}: the h1`);

    // (g) The archive: no holds or corrections table, a link to each; every served file once, with its served hash.
    for (const bad of ['id="holds"', 'id="corrections"', '<tr id="hold-', 'hold-open', 'hold-resolved'])
      ok(!amain.includes(bad), `${AW}: no holds or corrections table (${bad})`);
    for (const a of ['holds', 'corrections']) ok(amain.includes(`href="${lp}/releases/#${a}"`), `${AW}: links the ${a}`);
    const listed = [...amain.matchAll(/<code class="hash" data-file="([^"]+)">([0-9a-f]{64})<\/code>/g)];
    eq(sorted(listed.map(m => m[1])), servedFiles, `${AW}: every served file listed once`);
    for (const [, file, sha] of listed)
      ok(sha === createHash('sha256').update(readFileSync(join(DIST, 'data', file))).digest('hex'), `${AW}: ${file}'s hash is the served file's`);
    // Each payload that records its review manifest has it in its own release's entry.
    for (const e of entries) for (const f of e.files.filter(f => f.endsWith('.json'))) {
      const j = JSON.parse(read(`data/${f}`)), man = j?.provenance?.manifest_sha256;
      if (man && (j.release_id ?? j.releaseId) === e.id) ok(e.html.includes(`<code class="hash">${man}</code>`), `${AW}: ${e.id} shows its review manifest`);
    }

    // The days, from the archive.
    const days = [];
    for (const e of entries) { const d = days.at(-1); if (d?.date === e.date) d.ids.push(e.id); else days.push({ date: e.date, ids: [e.id] }); }
    const byId = new Map(entries.map(e => [e.id, e]));

    // (d) No hash on the index.
    ok(!/class="hash"|data-file=|class="release-entry"/.test(idx) && !/\b[0-9a-f]{64}\b/.test(imain), `${IW}: no hash, data-file or release entry`);
    ok(idx.length * 2 < arch.length, `${IW}: the index is shorter than half the archive (${idx.length} against ${arch.length} bytes)`);
    ok(imain.includes(`href="${lp}/releases/archive/"`), `${IW}: the dek links the archive`);

    // (a, b) #latest.
    const latest = el(imain, /<section class="topic-section" id="latest"/, IW);
    const arts = all(latest, /<article class="release-latest"/g);
    eq(arts.length, LATEST_DAYS, `${IW}: three newest days`);
    changeFigs[lang] = [];
    arts.forEach((art, i) => {
      const day = days[i], where = `${IW} ${day.date}`;
      ok(new RegExp(`<h3 id="day-${day.date}"><time datetime="${day.date}">[^<]+</time></h3>`).test(art), `${where}: the day's heading and date`);
      const ids = el(art, /<ul class="release-ids"/, where);
      eq([...ids.matchAll(/<li id="([^"]+)">/g)].map(m => m[1]), day.ids, `${where}: the day's ids, in the archive's order`);
      for (const li of all(ids, /<li id="/g)) {
        const id = li.match(/^<li id="([^"]+)"/)[1];
        ok(li.includes(`<a href="${lp}/releases/archive/#${id}"><code>${id}</code></a>`), `${where}: ${id} links its archive entry`);
        eq([...li.matchAll(/<a href="\/data\/([^"]+)" download>/g)].map(m => m[1]), byId.get(id).files, `${where}: ${id}'s downloads`);
      }
      const changes = all(el(art, /<ul class="release-changes"/, where), /<li\b/g);
      ok(changes.length >= 1 && changes.length <= 3, `${where}: one to three changes (${changes.length})`);
      const pins = PINS[day.date];
      if (pins) eq(changes.length, pins.length, `${where}: the changes the pins expect`);
      changes.forEach((c, k) => {
        const t = text(c), wc = `${where} change ${k + 1}`;
        const links = [...c.matchAll(/<a href="([^"]+)"/g)].map(m => m[1]);
        ok(links.length >= 1 && links.length <= 2, `${wc}: one or two links (${links.length})`);
        ok(t.length <= LIMIT[lang], `${wc}: ${t.length} characters, at most ${LIMIT[lang]}`);
        const label = t.match(DATE_OR_VERSION);
        ok(!label, `${wc}: a date, version or update word (${label?.[0]})`);
        for (const href of links) {
          ok(href.startsWith(`${lp}/`) && !href.startsWith('//'), `${wc}: ${href} is a site link in its language`);
          const [path, frag] = href.split('#'), file = `${path.slice(1)}index.html`;
          ok(exists(file), `${wc}: ${href} leads to a built page`);
          if (frag) ok(read(file).includes(`id="${frag}"`), `${wc}: ${href} names an anchor on its page`);
        }
        const digits = [...t.matchAll(FIGURES)].map(m => m[0]), words = [...t.matchAll(WORDS_IN[lang])].map(m => m[0].toLowerCase());
        if (pins) {
          eq(sorted(digits), sorted(pins[k].digits), `${wc}: the figures its payloads give`);
          eq(sorted(words), sorted(pins[k].words.map(x => x[lang])), `${wc}: the counts its payloads give`);
        }
        changeFigs[lang].push(sorted(digits).join(' '));
        if (lang === 'zh') {
          for (const bad of REJECTED_ZH) ok(!t.includes(bad), `${wc}: "${bad}" is a rejected rendering`);
          ok(!/[一-鿿]\.$/.test(t), `${wc}: no ASCII full stop after Chinese`);
        }
      });
    });

    // (c) Every release id once, visible; #earlier; holds and corrections.
    const details = spans(imain, /<details\b/g), inDetails = at => details.some(([a, b]) => a < at && at < b);
    for (const e of entries) {
      const at = [...imain.matchAll(new RegExp(`\\sid="${e.id}"`, 'g'))];
      ok(at.length === 1 && !inDetails(at[0].index), `${IW}: ${e.id} once, visible`);
      ok(/<li$/.test(imain.slice(Math.max(0, at[0].index - 3), at[0].index)), `${IW}: ${e.id} is a line`);
    }
    const earlier = el(imain, /<section class="topic-section" id="earlier"/, IW);
    const older = days.slice(LATEST_DAYS).flatMap(d => d.ids);
    eq([...earlier.matchAll(/<li id="([^"]+)">/g)].map(m => m[1]), older, `${IW}: #earlier lists every older id in order`);
    for (const li of all(earlier, /<li id="/g)) {
      const id = li.match(/^<li id="([^"]+)"/)[1], e = byId.get(id);
      ok(li.includes(`<time datetime="${e.date}">`) && li.includes(`<a href="${lp}/releases/archive/#${id}"><code>${id}</code></a>`), `${IW}: ${id}'s date and archive link`);
      const pages = [...el(e.html, /<p class="release-meta"><strong>/, AW).matchAll(/<a href="([^"]+)">/g)].map(m => m[1]);
      eq([...li.matchAll(/<a href="([^"]+)">/g)].map(m => m[1]).slice(1), pages, `${IW}: ${id}'s pages, as its archive entry names them`);
    }
    ok(!inDetails(imain.indexOf('id="earlier"')), `${IW}: #earlier is always visible`);
    const corrAt = imain.indexOf('id="corrections"'), holdsAt = imain.indexOf('id="holds"');
    ok(corrAt > 0 && corrAt < holdsAt, `${IW}: the corrections, then the holds`);
    const corr = imain.slice(corrAt, holdsAt);
    ok((corr.match(/<tr><th scope="row"><time /g) || []).length >= 2 && corr.includes(`href="${lp}/releases/archive/"`), `${IW}: the corrections, their lede linking the archive`);
    const holds = imain.slice(holdsAt);
    const rows = [...holds.matchAll(/<tr id="(hold-[^"]+)" class="(hold-open|hold-resolved)">[\s\S]*?<time datetime="([^"]+)">/g)]
      .map(m => ({ id: m[1], cls: m[2], opened: m[3], at: holdsAt + m.index }));
    ok(rows.length >= 10, `${IW}: the holds register (${rows.length})`);
    const open = rows.filter(r => r.cls === 'hold-open'), resolved = rows.filter(r => r.cls === 'hold-resolved');
    ok(open.every(r => !inDetails(r.at)), `${IW}: no open hold inside <details>`);
    ok(open.every((r, i) => i === 0 || r.opened <= open[i - 1].opened), `${IW}: open holds newest first`);
    ok(resolved.length >= 2 && resolved.every(r => inDetails(r.at)), `${IW}: the resolved holds collapsed`);
    ok(rows.findIndex(r => r.cls === 'hold-resolved') > open.length - 1, `${IW}: the open holds first`);
    const rd = el(holds, /<details class="holds-resolved">/, IW);
    ok(resolved.every(r => rd.includes(`<tr id="${r.id}" class="hold-resolved">`)), `${IW}: the resolved rows in <details class="holds-resolved">`);

    // Markup on both pages: <thead>, columns in <details>, CSP, hreflang.
    for (const [page, where, h, path] of [[arch, AW, amain, 'releases/archive/'], [idx, IW, imain, 'releases/']]) {
      for (const t of all(h, /<table\b/g)) ok(/<thead>[\s\S]*?<th\b/.test(t), `${where}: a table without a header row`);
      for (const d of all(h, /<details\b/g)) for (const t of all(d, /<table\b/g))
        ok((el(t, /<thead>/, where).match(/<th\b/g) || []).length >= 4, `${where}: a table inside <details> has four or more columns`);
      ok(!/<script(?![^>]*\bsrc=)(?![^>]*\btype="application\/(?:ld\+)?json")[^>]*>/.test(page) && !/\sstyle="|\son[a-z]+="/.test(page), `${where}: no inline script, style attribute or handler`);
      for (const [hl, p] of [['en', `https://bci.report/${path}`], ['zh-Hans', `https://bci.report/zh/${path}`], ['x-default', `https://bci.report/${path}`]])
        ok(page.includes(`<link rel="alternate" hreflang="${hl}" href="${p}">`), `${where}: hreflang ${hl}`);
      ok(!REFUSED.test(vis(page.replace(/<head>[\s\S]*?<\/head>/, ''))), `${where}: no private path, host label, refused figure or name`);
    }
    // The Markdown copy carries every change and id.
    const md = read(`${pfx}releases/index.md`), mdText = md.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1').replace(/`/g, '').replace(/\s+/g, ' ');
    for (const art of arts) for (const c of all(el(art, /<ul class="release-changes"/, IW), /<li\b/g)) ok(mdText.includes(text(c)), `${IW}index.md: the change “${text(c).slice(0, 40)}…”`);
    for (const e of entries) ok(md.includes(`#${e.id})`), `${IW}index.md: ${e.id}`);
    for (const f of [`${pfx}releases/index.md`, `${pfx}releases/archive/index.md`]) ok(!REFUSED.test(read(f)), `${f}: nothing refused`);
    ok(!/Jev-style|Jev 式/.test(vis(imain)), `${IW}: the index does not name "Jev-style", so it need not define it`);

    // (h) /api/: the release column and the hashes link the archive.
    const api = el(read(`${pfx}api/index.html`), /<main\b/, `/${pfx}api/`);
    const apiLinks = [...api.matchAll(/href="([^"]*\/releases\/[^"]*)"/g)].map(m => m[1]);
    ok(apiLinks.length >= servedFiles.length, `/${pfx}api/: a release link per file (${apiLinks.length})`);
    for (const href of apiLinks) {
      ok(href.startsWith(`${lp}/releases/archive/`), `/${pfx}api/: ${href} links the archive`);
      const id = href.split('#')[1];
      if (id) ok(byId.has(id), `/${pfx}api/: ${href} lands on an archive entry`);
    }
    ok(api.includes(`<a href="${lp}/releases/archive/">`), `/${pfx}api/: the hashes link`);
  }
  // (b) English and Chinese print the same figures in each change.
  eq(changeFigs.zh, changeFigs.en, 'the changes print the same figures in English and Chinese');

  // (e, f) Every link into /releases/ from any page or copy lands on a visible line of the index; a hold link on an open hold.
  const visibleIds = {}, openHolds = {};
  for (const lang of ['en', 'zh']) {
    const imain = el(indexes[lang], /<main\b/, lang), details = spans(imain, /<details\b/g);
    visibleIds[lang] = new Set([...imain.matchAll(/\sid="([^"]+)"/g)].filter(m => !details.some(([a, b]) => a < m.index && m.index < b)).map(m => m[1]));
    openHolds[lang] = new Set([...imain.matchAll(/<tr id="hold-([^"]+)" class="hold-open">/g)].map(m => m[1]));
  }
  let links = 0;
  for (const f of pageFiles) {
    const body = read(f);
    for (const m of body.matchAll(/(?:href="|\]\()(?:https:\/\/bci\.report)?(\/zh)?\/releases\/#([^")\s]+)/g)) {
      const lang = m[1] ? 'zh' : 'en', frag = decode(m[2]);
      if (frag.startsWith('hold-')) ok(openHolds[lang].has(frag.slice(5)), `${f}: ${m[0]} names no open hold`);
      ok(visibleIds[lang].has(frag), `${f}: ${m[0]} lands on no visible line of /releases/`);
      links++;
    }
  }
  ok(links > 200, `links into /releases/ were read (${links})`);

  // (g) The feed: ids unchanged, each entry's page its archive entry.
  const feed = read('releases.xml');
  const fe = [...feed.matchAll(/<entry>\n {4}<title>[^<]*<\/title>\n {4}<id>https:\/\/bci\.report\/releases\/#([^<]+)<\/id>\n {4}<link rel="alternate" type="text\/html" href="https:\/\/bci\.report\/releases\/archive\/#([^"]+)"\/>/g)];
  eq(fe.map(m => m[1]), archiveEntries.map(e => e.id), 'releases.xml: one entry per release, its id unchanged');
  ok(fe.every(m => m[1] === m[2]), 'releases.xml: each entry links its archive entry');
  ok(!REFUSED.test(feed), 'releases.xml: nothing refused');

  return { checks, releases: archiveEntries.length, links };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node scripts/checks/release-log.mjs <build dir>'); process.exit(2); }
  const { checks, releases, links } = checkReleaseLog(dir);
  console.log(`PASS: release log — /releases/ and /releases/archive/ in both languages, ${checks} checks: the three newest days with one to three changes each, their figures from the payloads and the same in English and Chinese, every link landing; all ${releases} release ids once and visible on the index, none in <details>, no hash there; the archive with every entry, file hash and manifest and no holds or corrections table; the open holds first, the resolved ones collapsed with their rows; ${links} links into /releases/ from pages and copies, each landing on a visible line and every hold link on an open hold; /api/ and the feed linking the archive; markup, hreflang, the Markdown copy, and nothing refused.`);
}
