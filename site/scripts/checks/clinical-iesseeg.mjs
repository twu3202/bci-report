// IESSEEG on /topics/clinical-groups/ (package P-CL; owner decisions D13 and D7 option A; release
// clinical-iesseeg-update-20261020). Run against a built site:
//
//   node scripts/checks/clinical-iesseeg.mjs <build directory>
//
// What it holds, in both languages: the Parkinson's question, short answer, description and card unchanged and citing
// clinical-update.json only; the dek's one added clause; the #iesseeg section after the Parkinson's comparison, with its
// own h2 question; #iesseeg-controls (six arms) and #iesseeg-neurolm (four arms), each a table with a <thead> and the
// three columns balanced accuracy, AUROC and age ≤2 balanced accuracy, every cell re-read from the served export; no
// F1; the shared caption once; the audit boundary prominent, before the tables; the NeuroLM footnote after its table;
// the medical disclaimer reused; consent and HIPAA authorization stated as waived; attribution from the release card at
// the pinned revision; every figure a data-fig leaf of its file, the same multiset in English and Chinese, and no
// unmarked number in the section's prose; no ranking word, no submission reference, no private path, no version label;
// CSP; the cite block naming both clinical releases; the Markdown copy carrying the section.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = resolve(process.argv[2] ?? '');
assert.ok(process.argv[2] && existsSync(join(DIST, 'index.html')), 'usage: node scripts/checks/clinical-iesseeg.mjs <build directory>');
const SITE = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const read = rel => readFileSync(join(DIST, rel), 'utf8');
const FILE = 'clinical-iesseeg-update.json';
const X = JSON.parse(read('data/' + FILE));
const CL = JSON.parse(read('data/clinical-update.json'));
let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };
const eq = (a, b, msg) => { assert.deepEqual(a, b, msg); checks++; };

// The served export is the reviewed one, byte for byte, in all three places.
{
  const served = readFileSync(join(DIST, 'data', FILE));
  for (const p of ['src/data/', 'public/data/']) ok(served.equals(readFileSync(join(SITE, p, FILE))), `${p}${FILE} is byte-identical to the served file`);
}

// Formatters, as entities.ts formatFig prints them.
const fmt = {
  pct2: r => (r * 100).toFixed(2) + '%', pct1: r => (r * 100).toFixed(1) + '%', auc3: r => r.toFixed(3), auc2: r => r.toFixed(2),
  count: r => r.toLocaleString('en-US'),
};
const leaves = (() => { const s = new Set(); const walk = v => { if (typeof v === 'number') s.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); }; walk(X); return s; })();
const decode = s => s.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
// Inline tags join their text (a figure inside a word stays in it); every other tag separates.
const visible = html => decode(html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<\/?(?:span|strong|em|code|a|wbr|q)\b[^>]*>/g, '').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
const figsOf = html => [...html.matchAll(/data-fig="([^"]+)"/g)].map(m => m[1]);
const sorted = a => [...a].sort();

const page = { en: read('topics/clinical-groups/index.html'), zh: read('zh/topics/clinical-groups/index.html') };
const md = { en: read('topics/clinical-groups/index.md'), zh: read('zh/topics/clinical-groups/index.md') };
const section = html => {
  const a = html.indexOf('<section class="topic-section" id="iesseeg"');
  assert.ok(a > 0, 'the #iesseeg section renders');
  const b = html.indexOf('</section>', a);
  assert.equal(html.slice(a + 8, b).indexOf('<section'), -1, '#iesseeg nests no section');
  return html.slice(a, b + 10);
};
const between = (html, startRe, endTag) => { const m = html.match(startRe); assert.ok(m, `${startRe} renders`); const b = html.indexOf(endTag, m.index); return html.slice(m.index, b + endTag.length); };

// --- What stays the Parkinson's comparison's (D13). ---------------------------------------------------------------
const ds = CL.results.ds004584, byId = Object.fromEntries(ds.models.map(m => [m.id, m]));
const eeg = byId.spectral_logistic, demo = byId.demographics_only;
const iv = ci => `${fmt.pct1(ci[0])}–${fmt.pct1(ci[1])}`;
const answerFigs = [String(ds.cohort.people), fmt.pct1(eeg.mean_balanced_accuracy), iv(eeg.balanced_accuracy_bootstrap_95), fmt.auc2(eeg.auroc),
  `${(ds.chance_level * 100).toFixed(0)}%`, fmt.pct1(demo.mean_balanced_accuracy), iv(demo.balanced_accuracy_bootstrap_95)];
const allowedNums = new Set([...answerFigs, '95%']);
const H1 = { en: 'Can resting-state EEG separate Parkinson&#39;s disease from controls?', zh: '静息态 EEG 能把帕金森病患者和对照组区分开吗？' };
const DEK = {
  en: 'Parkinson&#39;s disease against controls, person by person: a spectral model on resting-state EEG, and a comparator given only age and sex; and an infant case-control pilot with age and recording-setting controls.',
  zh: '逐名被试区分帕金森病与对照：一个基于静息态 EEG 的频谱模型，以及一个只用年龄和性别的对照基线；另有一项婴儿病例对照试点，附年龄与采集设置对照。',
};
const IES_WORDS = /IESSEEG|NeuroLM|infant|spasm|婴儿|痉挛/i;
for (const L of ['en', 'zh']) {
  const html = page[L], where = `${L}/clinical-groups`;
  const h1 = (html.match(/<h1>([\s\S]*?)<\/h1>/) || [])[1] ?? '';
  eq(h1.replace(/<wbr>/g, ''), H1[L], `${where}: the h1 stays the Parkinson's question`);
  ok(html.includes(`<title>${H1[L]}`), `${where}: the <title> leads with the Parkinson's question`);
  const sa = between(html, /<section class="short-answer"/, '</section>');
  eq([...sa.matchAll(/class="fig">([^<]+)</g)].map(m => m[1]), answerFigs, `${where}: the short answer prints clinical-update.json's figures, in order`);
  ok(!IES_WORDS.test(visible(sa)) && !sa.includes('data-fig'), `${where}: the short answer names nothing of the IESSEEG section`);
  const metas = [...html.matchAll(/<meta (?:name|property)="(?:description|og:description|twitter:description)" content="([^"]*)"/g)].map(m => decode(m[1]));
  ok(metas.length >= 2, `${where}: description metas render`);
  for (const d of metas) {
    ok(!IES_WORDS.test(d), `${where}: the description names nothing of the IESSEEG section`);
    for (const m of d.matchAll(/\d(?:\d|,(?=\d{3}))*(?:\.\d+)?%?(?:–\d(?:\d|,(?=\d{3}))*(?:\.\d+)?%)?/g)) ok(allowedNums.has(m[0]), `${where}: description figure ${m[0]} is clinical-update.json's`);
  }
  eq((html.match(/<p class="topic-dek">([\s\S]*?)<\/p>/) || [])[1], DEK[L], `${where}: the dek with its one added clause`);
  ok(html.includes('href="/data/clinical-update.json"') && html.includes(`href="/data/${FILE}"`), `${where}: both reviewed downloads are linked`);
  // The earlier batch's pins on this page still hold.
  for (const re of [/71\.7%/, /55\.0%/, /63\.5%–79\.3%/, /46\.9%–63\.6%/, /\+16\.6 pp/, /0\.76/, /IRB 201707828/, /10\.1136\/jnnp-2022-330154/]) ok(re.test(html), `${where}: ${re} (2026-09-23 pin)`);
  ok(!/68\.5|70\.9|68\.53|70\.92/.test(html), `${where}: no per-group age mean`);
  ok(!/−1\.6 pp|77\.9%/.test(html), `${where}: no Alpha Waves figure`);
  ok(!/diagnostic accuracy(?!,| —)|screening tool(?!,)/.test(html) && !/可以诊断|用于诊断|诊断准确率(?!，)/.test(html), `${where}: no diagnostic claim`);
  for (const v of ['0.3540', '0.3849', '0.2303', '0.2655', '0.2319'])
    ok(!html.replace(/ data-fig="(?:shared-representation|later-sessions|questions-in-language)-update\.json\|[^"]*"/g, '').includes(v.slice(0, 5)), `${where}: no withheld L-FAME descriptor (${v})`);
}

// --- The section. -------------------------------------------------------------------------------------------------
const ZH = {
  h2: 'EEG 病例对照结果经得起年龄与采集设置校正吗？',
  caption: '折外点估计；事先没有指定区间或检验。每人一段清醒期记录，取前 60 秒。两组之间年龄与采集设置不同；回归掉年龄是一项敏感性分析。',
  boundary: '分类头与每一个分数都经过独立复现；NeuroLM 特征本身没有用第二套实现重新提取。',
  disclaimer: '公开数据集上的研究结果：不是诊断，不是诊断准确率，也不是医疗器械或医疗建议。',
};
const sec = { en: section(page.en), zh: section(page.zh) };
const arms = { controls: X.controls.arms, neurolm: X.neurolm.arms };
eq(arms.controls.length, 6, 'six CPU arms in the export'); eq(arms.neurolm.length, 4, 'four neural arms in the export');
for (const L of ['en', 'zh']) {
  const html = page[L], s = sec[L], where = `${L}/clinical-groups#iesseeg`, zh = L === 'zh';
  // Placement: after the Parkinson's comparison and its limits, before the topic switcher.
  const at = html.indexOf('id="iesseeg"');
  ok(html.indexOf('id="clinical-coverage"') < at && html.indexOf('id="methods-and-limits"') < at && at < html.indexOf('class="topic-switcher"'), `${where}: after the Parkinson's comparison`);
  eq((s.match(/<h2 id="iesseeg-heading">([^<]*)<\/h2>/) || [])[1], zh ? ZH.h2 : X.question, `${where}: the section's own question`);
  ok(s.includes('aria-labelledby="iesseeg-heading"'), `${where}: the section is labelled by its question`);
  // The two blocks, in order, each with its table.
  const ci = s.indexOf(`id="${X.controls.anchor}"`), ni = s.indexOf(`id="${X.neurolm.anchor}"`);
  ok(ci > 0 && ni > ci, `${where}: #iesseeg-controls, then #iesseeg-neurolm`);
  ok(visible(s.slice(ci, ni)).includes(zh ? '清醒期 EEG 病例对照试点中的年龄与采集设置对照' : X.controls.title), `${where}: the controls block carries the approved title`);
  ok(visible(s.slice(ni)).includes(zh ? '冻结的 EEG 表示经得起年龄校正吗？' : X.neurolm.title), `${where}: the NeuroLM block carries its title`);
  for (const [block, list] of Object.entries(arms)) {
    const t = between(s, new RegExp(`<table data-iesseeg-table="${block}"`), '</table>');
    ok(/<caption>[^<]+<\/caption>/.test(t), `${where}: ${block} table has a caption`);
    const head = between(t, /<thead>/, '</thead>');
    eq((head.match(/<th scope="col"/g) || []).length, 4, `${where}: ${block} table has a <thead> with four columns`);
    const hv = visible(head);
    ok(zh ? /组 平衡准确率，全部 100 人 AUROC，全部 100 人 平衡准确率，≤2 岁 68 人/.test(hv) : /Arm Balanced accuracy, all 100 AUROC, all 100 Balanced accuracy, age ≤2 years 68 people/.test(hv), `${where}: ${block} columns: ${hv}`);
    ok(!/F1/.test(hv), `${where}: no F1 column`);
    eq([...t.matchAll(/data-iesseeg-arm="([^"]+)"/g)].map(m => m[1]), list.map(a => a.id), `${where}: ${block} rows, every arm in the export's order`);
    for (const a of list) {
      const r = between(t, new RegExp(`<tr data-iesseeg-arm="${a.id}"`), '</tr>');
      const cells = [...r.matchAll(/<td data-cell="([^"]+)"><span data-fig="([^|"]+)\|(\w+)\|([^"]+)" class="metric">([^<]+)<\/span><\/td>/g)]
        .map(m => [m[1], m[2], m[3], Number(m[4]), m[5]]);
      const want = [['ba', 'pct2', a.pooled.balanced_accuracy], ['auroc', 'auc3', a.pooled.auroc], ['ba-age', 'pct2', a.age_le_2.balanced_accuracy]]
        .map(([c, f, v]) => [c, FILE, f, v, fmt[f](v)]);
      eq(cells, want, `${where}: ${a.id} cells are the export's balanced accuracy, AUROC and age ≤2 balanced accuracy`);
    }
    if (block === 'controls') {
      const groups = [...t.matchAll(/<tr class="subhead"><th scope="colgroup" colspan="4">([^<]+)<\/th><\/tr>/g)].map(m => m[1]);
      eq(groups, zh ? ['不用 EEG', '使用 EEG'] : ['Without EEG', 'With EEG'], `${where}: the controls table's two groups`);
      const first = t.indexOf('<tr class="subhead"'), noEeg = t.slice(first, t.indexOf('<tr class="subhead"', first + 1));
      ok(list.filter(a => !a.eeg_input).every(a => noEeg.includes(`data-iesseeg-arm="${a.id}"`)) && list.filter(a => a.eeg_input).every(a => !noEeg.includes(`data-iesseeg-arm="${a.id}"`)), `${where}: arms with no EEG input sit under their own heading`);
    }
  }
  const v = visible(s);
  ok(!/\bF1\b/.test(v), `${where}: F1 is not printed`);
  // The shared caption once on the page; the boundary prominent and before the tables; the footnote after its table.
  const cap = zh ? ZH.caption : X.caption;
  eq(visible(html).split(cap).length - 1, 1, `${where}: the shared caption, once`);
  ok(between(s, /data-iesseeg-note="caption"/, '</p>').includes(zh ? '两张表：' : 'Both tables.'), `${where}: the caption is the tables' shared one`);
  const bnd = between(s, /<p class="protocol-note" data-iesseeg-note="audit-boundary">/, '</p>');
  eq(visible(bnd.replace(/^<p[^>]*>/, '')), zh ? ZH.boundary : X.audit_boundary, `${where}: the audit boundary, as released`);
  ok(/^<p class="protocol-note" data-iesseeg-note="audit-boundary"><strong>[^<]+<\/strong><\/p>$/.test(bnd), `${where}: the audit boundary is set in bold`);
  ok(s.indexOf('data-iesseeg-note="audit-boundary"') < s.indexOf('<table'), `${where}: the audit boundary comes before the tables`);
  const ft = s.indexOf('data-iesseeg-note="neurolm-footnote"');
  ok(ft > s.indexOf('<table data-iesseeg-table="neurolm"') && ft > ni, `${where}: the NeuroLM footnote follows its table`);
  const fv = visible(between(s, /<p class="protocol-note" data-iesseeg-note="neurolm-footnote">/, '</p>'));
  ok(zh ? /预处理与频谱流程不同/.test(fv) && /训练阶段/.test(fv) && /未知/.test(fv) : fv === `NeuroLM. ${X.neurolm.footnote}`, `${where}: the NeuroLM footnote: preprocessing differs; stage and exposure unknown`);
  // The medical disclaimer, reused from the clinical release.
  const dis = between(s, /<p class="protocol-note" data-iesseeg-note="disclaimer">/, '</p>');
  ok(zh ? dis.includes(ZH.disclaimer) && dis.includes(`<span lang="en">${CL.medical_disclaimer}</span>`) : visible(dis) === CL.medical_disclaimer, `${where}: the clinical page's medical disclaimer, reused`);
  // Consent: waived, as the release card states; nothing says the participants consented.
  const credits = between(s, /<article data-iesseeg-credits="true">/, '</article>');
  const cv = visible(credits);
  ok(zh ? /豁免了知情同意与 HIPAA 研究授权/.test(cv) : /waivers of informed consent and HIPAA research authorization/.test(cv), `${where}: consent and HIPAA authorization were waived`);
  ok(cv.includes('17-000026'), `${where}: the approval's protocol number`);
  ok(!/gave (?:written )?(?:informed )?consent|consented|provided (?:their )?(?:written )?(?:informed )?consent/i.test(v) && !/签署了[^。]{0,8}知情同意|同意参加/.test(v), `${where}: nothing says the participants consented`);
  // Attribution: the release card at the pinned revision, its requested title, the licence, the prior-reuse declaration.
  ok(cv.includes(X.dataset.requested_citation) && cv.includes('Rajaraman et al. (2024)') && cv.includes(X.dataset.prior_reuse.study_title), `${where}: requested citation and prior-reuse declaration`);
  for (const u of [X.dataset.url, X.dataset.release_card_url, X.dataset.licence_file_url, X.dataset.licence_deed]) ok(credits.includes(`href="${u}"`), `${where}: links ${u}`);
  ok(/>CC BY 4\.0</.test(credits), `${where}: CC BY 4.0`);
  for (const [, u] of s.matchAll(/href="(https:\/\/huggingface\.co\/[^"]+)"/g)) ok(u.includes(X.dataset.revision), `${where}: ${u} is pinned to the revision`);
  ok(s.includes(`href="${X.neurolm.model.source_url}"`) && s.includes(X.neurolm.model.checkpoint_sha256), `${where}: NeuroLM's code revision and checkpoint hash`);
  // The age ≤2 band: its size and its case and control counts, as figures.
  for (const k of ['people', 'cases', 'controls', 'maximum_age_years']) ok(s.includes(`data-fig="${FILE}|count|${X.age_band[k]}"`), `${where}: the age band's ${k}`);
  // Every figure: a leaf of the export, printed in its format; nothing else in the section prints a number.
  for (const [, file, f, raw, text] of s.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)) {
    eq(file, FILE, `${where}: a section figure from ${file}`);
    ok(leaves.has(Number(raw)), `${where}: ${raw} is a value in ${FILE}`);
    eq(text, fmt[f](Number(raw)), `${where}: ${raw} printed as "${text}"`);
  }
  const prose = visible(s.replace(/<span data-fig="[^"]*"[^>]*>[^<]*<\/span>/g, ' ').replace(/<code>[^<]*<\/code>/g, ' ')
    .replace(/<article data-iesseeg-credits="true">[\s\S]*?<\/article>/, ' ').replace(/<p class="citation-note">(?:Data source:|数据来源：)[\s\S]*?<\/p>/g, ' '))
    .replace(/\bL2\b|\blog1p\b|SHA-256/g, ' ');
  ok(!/\d/.test(prose), `${where}: an unmarked number in the section: “…${prose.slice(Math.max(0, prose.search(/\d/) - 40), prose.search(/\d/) + 20)}…”`);
  // No winner, no ranking word, no hedge of the "not ranked" kind, no submission, no update wording.
  ok(!(zh ? /最好|最佳|最高|最低|胜出|排名|名列|领先|优于|胜过|冠军/ : /\b(?:best|winner|wins?|won|outperform\w*|superior|beats?|leads?|leading|top|rank\w*|state[- ]of[- ]the[- ]art|SOTA|highest|lowest)\b/i).test(v), `${where}: no ranking word`);
  ok(!/not ranked|unranked|不排名|未排名/i.test(v), `${where}: no "not ranked" hedge`);
}
// Figure parity: the same data-fig multiset, page and section, in both languages; the classed figures in the same order.
eq(sorted(figsOf(page.zh)), sorted(figsOf(page.en)), 'zh/clinical-groups: every data-fig equals the English page (multiset)');
eq(sorted(figsOf(sec.zh)), sorted(figsOf(sec.en)), 'zh/clinical-groups#iesseeg: every data-fig equals the English section (multiset)');
const classed = html => [...html.matchAll(/class="(?:metric|num|fig)">([^<]+)</g)].map(m => m[1]);
eq(classed(page.zh), classed(page.en), 'zh/clinical-groups: every classed figure equals the English page, in order');
ok(figsOf(sec.en).length >= 30 + 8, `the section prints its figures (${figsOf(sec.en).length})`);

// --- Whole page, both languages: what may never appear, CSP, tables, cite block, Markdown copy. ---------------------
const VERSION_LABEL = /(?<![\w.\/#-])(?<!Figshare(?: record)?(?: \d+)? )v\d+(?![\w.]|-\d)|\brelease v\d|第[一二三四五六七八九十]+轮/;
// Absolute path roots, and the two short host and user tokens the plan names (§4.7), spelled in parts so that this
// file does not itself carry a machine's names.
const PRIVATE = new RegExp(['/Users/', '/home/', '/Volumes/', '/mnt/', 'C:\\\\', `\\b${'tr' + 'x'}`, `\\b${'tw' + 'u'}\\b`].join('|'), 'i');
for (const L of ['en', 'zh']) {
  const html = page[L], where = `${L}/clinical-groups`;
  const body = html.replace(/<head>[\s\S]*?<\/head>/, '');
  for (const text of [html, md[L]]) {
    const noUrls = text.replace(/https?:\/\/[^\s"'<>)]+/g, ' ');
    ok(!/ICLR|OpenReview|openreview|\bsubmission\b|投稿/i.test(noUrls) && !/openreview\.net/.test(text), `${where}: nothing refers to a conference submission`);
    ok(!PRIVATE.test(noUrls), `${where}: no private path`);
  }
  ok(!VERSION_LABEL.test(visible(sec[L])), `${where}: no version label in the section`);
  ok(!/\sstyle="|<style[\s>]|\son[a-z]+=/i.test(body), `${where}: the CSP forbids inline style and handlers`);
  ok(!/<script(?![^>]*\bsrc=)(?![^>]*\btype="application\/(?:ld\+)?json")[^>]*>/.test(html), `${where}: no inline script`);
  for (const t of html.matchAll(/<table\b[\s\S]*?<\/table>/g)) ok(t[0].includes('<thead>'), `${where}: every table has a <thead>`);
  for (const d of html.matchAll(/<details\b[\s\S]*?<\/details>/g)) for (const t of d[0].matchAll(/<table\b[\s\S]*?<\/table>/g))
    ok((between(t[0], /<thead>/, '</thead>').match(/<th\b/g) || []).length >= 4, `${where}: a table inside <details> has at least four columns`);
  const cite = between(html, /<section class="cite-page"/, '</section>');
  eq(sorted(cite.match(/data-releases="([^"]+)"/)[1].split(' ')), sorted([CL.release_id, X.release_id]), `${where}: the cite block names both clinical releases`);
  // Markdown copy: the section's question, its caption, the boundary and every table figure.
  const m = md[L];
  ok(m.includes(L === 'zh' ? ZH.h2 : X.question) && m.includes(L === 'zh' ? ZH.caption : X.caption) && m.includes(L === 'zh' ? ZH.boundary : X.audit_boundary), `${where}: the Markdown copy carries the section`);
  for (const a of [...arms.controls, ...arms.neurolm]) for (const x of [fmt.pct2(a.pooled.balanced_accuracy), fmt.auc3(a.pooled.auroc), fmt.pct2(a.age_le_2.balanced_accuracy)])
    ok(m.includes(x), `${where}: the Markdown copy carries ${a.id} ${x}`);
}
// Chinese: the glossary's rejected renderings and the full-stop rule, outside English-marked text.
{
  const zhText = page.zh.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<(\w+)[^>]*\blang="en"[^>]*>[\s\S]*?<\/\1>/g, '');
  for (const bad of ['参与者', '受试者', '读出头', '暴露', '个百分点', '源数据', '冻结的编码器', '区块', '导 EEG']) ok(!zhText.includes(bad), `zh/clinical-groups: "${bad}" is a rejected rendering`);
  ok(!/[一-鿿\d]\.<\/p>/.test(zhText), 'zh/clinical-groups: no Chinese sentence ends with an ASCII period');
  const zs = visible(sec.zh.replace(/<(\w+)[^>]*\blang="en"[^>]*>[\s\S]*?<\/\1>/g, ''));
  ok(!/\b(?:the|and|with|of|is)\b/.test(zs), 'zh/clinical-groups#iesseeg: no untranslated English prose');
}

console.log(`PASS: clinical-iesseeg — ${checks} checks: the Parkinson's question, short answer, description and card unchanged and citing clinical-update.json only; #iesseeg after the comparison with its own question, six CPU and four neural arms, balanced accuracy, AUROC and age ≤2 balanced accuracy re-read from ${FILE}, no F1; caption once, boundary prominent, footnote beside its table, disclaimer reused, consent waived, attribution from the release card; figure parity in both languages; no ranking, submission, private path or version label; CSP, <thead>, cite block and Markdown copy.`);
