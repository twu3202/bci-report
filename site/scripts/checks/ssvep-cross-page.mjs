// The SSVEP follow-ups on other pages (package P-XP, plan §2.1 "Edits on other pages"; owner decisions D22, D24, D28),
// run on a built site:
//
//   node scripts/checks/ssvep-cross-page.mjs <dist directory>
//
// What it holds, in both languages:
//   - the 'new-ssvep-frequencies' topic card (home page and Questions hub) counts the follow-ups of both releases,
//     new-ssvep-frequencies-update.json and ssvep-followups-update.json, in words computed from the two served files;
//   - the line #unseen-frequency ends with on /topics/questions-in-language/, and the same line under route 3 on
//     /jev-style/, count both releases in words, link the follow-up page and print no digit;
//   - /topics/fewer-electrodes/ carries one figure-free pointer to /topics/new-ssvep-frequencies/#practical-settings;
//   - /datasets/wearable-ssvep-102/ carries one figure-free line to the cards that run on its dry and wet headbands,
//     each link named by its card's heading, and no other dataset page links a follow-up card;
//   - /methods/fbcca/ and /methods/cca/ gain no group from this round;
//   - none of these strings names the thread's commenter, prints the commenter's confidence figure, a date or version
//     label, or a rejected Chinese rendering.
// The counts are re-derived here from the served files, independently of questions-in-language.ts. A target anchor that
// another package has not built yet is PENDING, not FAIL. Exit code 1 on any failure. No network, no writes.
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = resolve(process.argv[2] ?? fileURLToPath(new URL('../../dist/', import.meta.url)));
const results = [];
const report = (name, status, detail = '') => results.push({ name, status, detail });
const check = (name, fn) => {
  try { const r = fn(); if (r && r.pending) report(name, 'PENDING', r.pending); else report(name, 'PASS', typeof r === 'string' ? r : ''); }
  catch (e) { report(name, 'FAIL', e.message); }
};
const ok = (cond, msg) => { if (!cond) throw new Error(msg); };
const eq = (a, b, msg) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); };

const read = p => readFileSync(join(DIST, p), 'utf8');
const page = p => { ok(existsSync(join(DIST, p, 'index.html')), `${p}index.html is missing from ${DIST}`); return read(p + 'index.html'); };
const decode = s => s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&(amp|lt|gt|quot|apos|nbsp);/g, (_, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' })[e]);
const vis = h => decode(h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
/** Every element opening with `re`, up to its matching close tag (no nesting of the same tag inside). */
const elements = (h, re, tag) => [...h.matchAll(new RegExp(re.source, 'g'))].map(m => h.slice(m.index, h.indexOf(`</${tag}>`, m.index) + tag.length + 3));
const PFX = { en: '', zh: 'zh/' };
const href = (l, path) => `${l === 'zh' ? '/zh' : ''}${path}`;
/** A page's question, from its h1 (whose <wbr> phrase breaks are not spaces). */
const questionOf = h => vis((h.match(/<h1>([\s\S]*?)<\/h1>/)?.[1] ?? '').replace(/<wbr\s*\/?>/g, ''));

// --- The two served files, and the counts re-derived from them --------------------------------------------------
const first = JSON.parse(read('data/new-ssvep-frequencies-update.json'));
const more = JSON.parse(read('data/ssvep-followups-update.json'));
const runFirst = first.placement.cards.filter(c => !c.status_only).map(c => c.card);
const cardsAll = [...runFirst, ...more.placement.cards.map(c => c.card)];
const ep = (j, id) => j.endpoints.find(e => e.id === id);
const beta = [...first.cohort.cards, ...ep(more, 'u8').cards];
const wear = [...first.wearable.cards, ...ep(more, 'wearable_12').cards];
const wearOnly = wear.filter(k => !beta.includes(k));
const N = { total: cardsAll.length, beta: beta.length, wearable: wear.length, wearableOnly: wearOnly.length };
const WORDS = {
  en: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
       'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty'],
  zh: ['零', '一', '两', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十'],
};
const word = (n, l, cap = false) => { const w = WORDS[l][n]; ok(w, `no word for ${n}`); return cap && l === 'en' ? w[0].toUpperCase() + w.slice(1) : w; };

// The commenter's name, held as hashes so that this file does not print it (new-ssvep-frequencies.mjs).
const COMMENTER = new Set(['6e7f5e4c7a5ed600cb60c4cd7fa0b60724ddd2a89426474c71d7d8d06bb9c4d9', 'f695cdd94ee90fff62b7216da4bcd9283b9514e061f6108043cac331f5f1a65a']);
const namesCommenter = s => (s.toLowerCase().match(/[a-z]+/g) ?? []).some(w => COMMENTER.has(createHash('sha256').update(w).digest('hex')));
const tokens55 = /(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?!\d)|fifty[- ]five|五十五/i;
// The site's date and version-label rules as they reach these strings (check-workbench.mjs), and the glossary's rejects.
const LABELS = /\b[Uu]pdated\b|\b[Nn]ew in\b|\b[Ss]ince (?:20\d\d|\w+ \d)|\b[Aa]dded (?:on )?20\d\d|(?<![\w.\/#-])[vV]\d+\b|更新于|新增于|起暂缓|本次更新|第[一二三四五六七八九十]+轮|ICLR/;
const REJECTED_ZH = ['参与者', '受试者', '区块', '暴露', '源数据', '个百分点', '读出头', '构造器随机', '弃权', '误激活', '提示门控'];
const hygiene = (text, l, where) => {
  ok(!namesCommenter(text), `${where}: names the thread's commenter`);
  const m = text.match(tokens55); ok(!m, `${where}: prints “${m?.[0]}”`);
  const v = text.match(LABELS); ok(!v, `${where}: a date or version label “${v?.[0]}”`);
  if (l === 'zh') for (const r of REJECTED_ZH) ok(!text.includes(r), `${where}: the rejected rendering ${r}`);
};

check('inputs · both releases fit together: the later file reads with the earlier, cards 1 to N once each', () => {
  eq(more.placement.reads_with.file, 'new-ssvep-frequencies-update.json', 'reads_with');
  eq(more.placement.reads_with.cards, runFirst, 'the earlier cards the later file reads with');
  eq(cardsAll, cardsAll.map((_, i) => i + 1), 'cards 1 to N');
  eq(more.placement.cards.filter(c => c.supersedes).map(c => c.card), first.placement.cards.filter(c => c.status_only).map(c => c.card), 'the status entry superseded');
  eq(N.beta + N.wearableOnly, N.total, 'BETA plus Wearable-102 alone');
  eq(wearOnly, first.wearable.cards, 'the one card on Wearable-102 alone');
  return `${N.total} follow-ups: ${N.beta} BETA, ${N.wearable} Wearable-102, ${N.wearableOnly} only there`;
});

// --- The topic card ---------------------------------------------------------------------------------------------
const cardLead = {
  en: `${word(N.total, 'en', true)} follow-ups: ${word(N.beta, 'en')} on route 3’s BETA cohort, `,
  zh: `${word(N.total, 'zh')}项后续检验：${word(N.beta, 'zh')}项在第三条路线所用的 BETA 队列上，`,
};
const cardWear = {
  en: `, ${word(N.wearable, 'en')} on Wearable-102, ${word(N.wearableOnly, 'en')} of them only there.`,
  zh: `，${word(N.wearable, 'zh')}项在 Wearable-102 上，其中${word(N.wearableOnly, 'zh')}项只在那里运行。`,
};
const cardD22 = {
  en: ['filter-bank CCA, untrained too, scored above CCA in every setting tested', 'an untrained harmonic sum came out nearly level with a learned eigenvalue head'],
  zh: ['同样无需训练的滤波器组 CCA 在所测的每种设置下都高于 CCA', '无需训练的谐波求和与学习得到的特征值分类头几乎持平'],
};
for (const [l, p] of [['en', ''], ['zh', 'zh/'], ['en', 'topics/'], ['zh', 'zh/topics/']]) {
  check(`topic card · /${p} counts both releases in words`, () => {
    const h = page(p);
    const at = h.search(new RegExp(`<a class="topic-entry-card" href="${href(l, '/topics/new-ssvep-frequencies/')}"`));
    ok(at >= 0, 'the card');
    const card = h.slice(at, h.indexOf('</a>', at)), summary = vis(card.match(/<p>([\s\S]*?)<\/p>/)?.[1] ?? '');
    ok(summary.startsWith(cardLead[l]), `the summary opens with the counts: “${summary.slice(0, 90)}”`);
    ok(summary.includes(cardWear[l]), 'Wearable-102 counted, one card only there');
    for (const s of cardD22[l]) ok(summary.includes(s), `the later file's sentence “${s.slice(0, 40)}…”`);
    // Its only digits are a name's: route 3, Wearable-102 (the card's detail line carries the payload counts).
    ok(!/\d/.test(summary.replace(/Wearable-102|[Rr]oute 3/g, '')), 'the summary types no digit');
    ok(!summary.includes(l === 'en' ? 'Seven follow-ups' : '七项后续检验'), 'the earlier count is gone');
    ok(summary.length <= (l === 'en' ? 470 : 200), `the summary stays card-sized (${summary.length} characters)`);
    hygiene(vis(card), l, 'card');
  });
}

// --- The follow-up line: questions-in-language #unseen-frequency and /jev-style/ --------------------------------
const lineLead = {
  en: `${word(N.total, 'en', true)} follow-up experiments, ${word(N.beta, 'en')} of them on the same BETA cohort, tested `,
  zh: `${word(N.total, 'zh')}项后续实验（${word(N.beta, 'zh')}项在同一批 BETA 被试上）检验了`,
};
const lineTail = {
  en: `; ${word(N.wearable, 'en')} ran on a second dataset, ${word(N.wearableOnly, 'en')} of them only there:`,
  zh: `；${word(N.wearable, 'zh')}项用到第二个数据集，其中${word(N.wearableOnly, 'zh')}项只在那里运行：`,
};
const lines = { en: {}, zh: {} };
for (const l of ['en', 'zh']) {
  const q = questionOf(page(PFX[l] + 'topics/new-ssvep-frequencies/')).replace(/[?？]$/, '');
  const linkText = l === 'en' ? `${q.charAt(0).toLowerCase()}${q.slice(1)} →` : `${q} →`;
  for (const [where, path, re] of [['questions-in-language', 'topics/questions-in-language/', /<p class="roadmap-p" data-follow-ups="true">/],
                                   ['jev-style', 'jev-style/', /<p class="route-run-note" data-follow-ups="true">/]]) {
    check(`follow-up line · ${l} ${where}: both releases counted in words, no digit, the follow-up page linked`, () => {
      const h = page(PFX[l] + path), ps = elements(h, re, 'p');
      eq(ps.length, 1, 'one line');
      const p = ps[0], t = vis(p);
      ok(t.startsWith(lineLead[l]), `opens with the counts: “${t.slice(0, 90)}”`);
      ok(t.includes(lineTail[l]), 'Wearable-102 counted as a second dataset, one card only there');
      ok(!/\d/.test(t), 'the line types no digit');
      const a = [...p.matchAll(/<a href="([^"]+)">([\s\S]*?)<\/a>/g)];
      eq(a.map(m => [m[1], vis(m[2])]), [[href(l, '/topics/new-ssvep-frequencies/'), linkText]], 'its one link, the follow-up page\'s question');
      ok(!t.includes(l === 'en' ? 'Six follow-up experiments' : '六项后续实验'), 'the earlier count is gone');
      hygiene(t, l, where);
      if (where === 'questions-in-language') {
        const at = h.search(/<section\b[^>]*\sid="unseen-frequency"/), end = h.indexOf('</section>', at);
        ok(at >= 0 && h.indexOf(p) > at && h.indexOf(p) < end, 'the line sits in #unseen-frequency');
      } else {
        const li = elements(h, /<li data-route="questions-in-language"/, 'li')[0] ?? '';
        ok(li.includes(p), 'the line sits under route 3');
        const main = h.slice(h.indexOf('<main'), h.indexOf('</main>'));
        ok(!main.includes('data-fig'), '/jev-style/ prints no figure');
      }
      lines[l][where] = t;
    });
  }
  check(`follow-up line · ${l}: the same words on both pages`, () => {
    ok(lines[l]['questions-in-language'] && lines[l]['jev-style'], 'both lines read');
    eq(lines[l]['jev-style'], lines[l]['questions-in-language'], 'the line');
  });
}

// --- /topics/fewer-electrodes/: one figure-free pointer to card 11 ---------------------------------------------
const pointerLead = {
  en: 'Filter-bank CCA, CCA and learned heads on CCA’s statistics are also compared with fewer of BETA’s posterior electrodes and with shorter windows, on SSVEP frequencies held out of training:',
  zh: '滤波器组 CCA、CCA 以及基于 CCA 统计量的学习分类头，也在 BETA 上用更少的后部电极和更短的时间窗做了比较，所用 SSVEP 频率不参与训练。见「',
};
for (const l of ['en', 'zh']) {
  check(`fewer-electrodes · ${l}: one figure-free pointer to #practical-settings, in its methods and limits`, () => {
    const h = page(PFX[l] + 'topics/fewer-electrodes/'), ps = elements(h, /<p class="citation-note" data-practical-pointer="true">/, 'p');
    eq(ps.length, 1, 'one pointer');
    const p = ps[0], t = vis(p);
    ok(t.startsWith(pointerLead[l]), `its words: “${t.slice(0, 90)}”`);
    ok(!/\d/.test(t) && !p.includes('data-fig'), 'no figure');
    const q = questionOf(page(PFX[l] + 'topics/new-ssvep-frequencies/'));
    const a = [...p.matchAll(/<a href="([^"]+)">([\s\S]*?)<\/a>/g)];
    eq(a.map(m => [m[1], vis(m[2])]), [[href(l, '/topics/new-ssvep-frequencies/#practical-settings'), q]], 'its one link');
    const at = h.search(/<section\b[^>]*\sid="methods-and-limits"/);
    ok(at >= 0 && h.indexOf(p) > at && h.indexOf(p) < h.indexOf('</section>', at), 'inside #methods-and-limits');
    ok(!/fewer electrodes (?:are )?(?:generally )?better|电极越少(?:一般)?越好/.test(t), 'no “fewer is better” claim');
    ok(!/\sstyle="|\son[a-z]+=/.test(p), 'no inline style or handler');
    hygiene(t, l, 'pointer');
    ok(!h.includes('ssvep-followups-update.json'), 'the page cites no figure of the later file');
  });
  check(`fewer-electrodes · ${l}: the pointer's target anchor exists`, () => {
    const s = page(PFX[l] + 'topics/new-ssvep-frequencies/');
    if (!/\sid="practical-settings"/.test(s)) return { pending: 'card 11 (#practical-settings) is not on the SSVEP page yet (package P-SS)' };
  });
  check(`fewer-electrodes · ${l}: the Markdown copy keeps the pointer`, () => {
    const p = PFX[l] + 'topics/fewer-electrodes/index.md';
    if (!existsSync(join(DIST, p))) return { pending: 'no Markdown copy in this build' };
    ok(read(p).includes('/topics/new-ssvep-frequencies/#practical-settings'), 'the link in index.md');
  });
}

// --- /datasets/wearable-ssvep-102/: one figure-free line to the cards that also run on its headbands --------------
// Plan §2.1: Wearable-102's page links the follow-up cards whose endpoints include its dry and wet headbands, by their
// anchors, with no new figure row. Each link's text is the heading its anchor carries on the SSVEP page.
const wearCards = more.placement.cards.filter(c => c.endpoints.includes('dry') && c.endpoints.includes('wet'));
for (const l of ['en', 'zh']) {
  check(`wearable-ssvep-102 · ${l}: one figure-free line linking cards ${wearCards.map(c => c.card).join(' and ')} by their headings`, () => {
    const h = page(PFX[l] + 'datasets/wearable-ssvep-102/'), target = page(PFX[l] + 'topics/new-ssvep-frequencies/');
    ok(wearCards.length > 0, 'the later file places Wearable-102 dry and wet on a card');
    const lines = elements(h, /<p class="citation-note" id="related-follow-ups">/, 'p');
    eq(lines.length, 1, 'one #related-follow-ups line');
    const line = lines[0];
    const appears = h.slice(h.indexOf('id="appears-heading"'), h.indexOf('id="results-heading"'));
    ok(appears.includes(line), 'the line sits under “Where it appears”');
    ok(!/data-fig=/.test(line) && !/\d/.test(vis(line)), 'the line prints no figure or digit');
    const links = [...line.matchAll(/<a href="([^"]+)">([\s\S]*?)<\/a>/g)].map(m => ({ href: m[1], text: vis(m[2]) }));
    eq(links.map(x => x.href), wearCards.map(c => href(l, `/topics/new-ssvep-frequencies/#${c.anchor}`)), 'links to the cards, in order');
    for (const [i, c] of wearCards.entries()) {
      const heading = target.match(new RegExp(`<h2 id="${c.anchor}-heading">([\\s\\S]*?)</h2>`))?.[1];
      ok(heading !== undefined, `#${c.anchor}-heading is on the SSVEP page`);
      eq(links[i].text, vis(heading), `card ${c.card}'s link text is its heading`);
    }
    hygiene(vis(line), l, `${l} wearable-ssvep-102 line`);
    const md = PFX[l] + 'datasets/wearable-ssvep-102/index.md';
    if (existsSync(join(DIST, md))) for (const c of wearCards) ok(read(md).includes(`/topics/new-ssvep-frequencies/#${c.anchor}`), `the Markdown copy keeps card ${c.card}'s link`);
  });
  check(`wearable-ssvep-102 · ${l}: no other dataset page links a follow-up card`, () => {
    const listing = read(PFX[l] + 'datasets/index.html');
    const slugs = [...new Set([...listing.matchAll(new RegExp(`href="${l === 'zh' ? '/zh' : ''}/datasets/([a-z0-9-]+)/"`, 'g'))].map(m => m[1]))]
      .filter(s => s !== 'register' && s !== 'wearable-ssvep-102');
    ok(slugs.length > 10, 'the dataset index lists the dataset pages');
    for (const s of slugs) {
      const h = page(PFX[l] + `datasets/${s}/`);
      for (const c of more.placement.cards) ok(!h.includes(`/topics/new-ssvep-frequencies/#${c.anchor}"`), `/datasets/${s}/ links card ${c.card}`);
    }
  });
}

// --- /methods/fbcca/ and /methods/cca/: no new group --------------------------------------------------------------
for (const l of ['en', 'zh']) for (const m of ['fbcca', 'cca']) {
  check(`methods · ${l} /methods/${m}/ carries no group of this round`, () => {
    const p = PFX[l] + `methods/${m}/`;
    if (!existsSync(join(DIST, p, 'index.html'))) return { pending: `no ${p} in this build` };
    const h = read(p + 'index.html');
    ok(!h.includes('ssvep-followups-update.json'), 'no figure or link of ssvep-followups-update.json');
    for (const c of more.placement.cards) ok(!h.includes(`/topics/new-ssvep-frequencies/#${c.anchor}`), `no link to card ${c.card}`);
    ok(!/id="g-[^"]*(?:ssvep-followups|practical|harmonic-pooling|harmonic-gap|fixed-decay|rising-weights|eigenvalue|cross-spectral)/.test(h), 'no group id of this round');
  });
}

// --- Report --------------------------------------------------------------------------------------------------------
const w = Math.max(...results.map(r => r.name.length));
for (const r of results) console.log(`${r.status.padEnd(7)} ${r.name.padEnd(w)}${r.detail ? '  — ' + r.detail : ''}`);
const fails = results.filter(r => r.status === 'FAIL').length, pend = results.filter(r => r.status === 'PENDING').length;
console.log(`\nssvep-cross-page: ${results.length - fails - pend} passed, ${pend} pending, ${fails} failed (${DIST})`);
process.exit(fails ? 1 : 0);
