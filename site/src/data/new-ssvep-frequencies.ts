/**
 * Route 3's follow-ups on SSVEP frequencies a decoder never trained on (owner decision D1): what
 * /topics/new-ssvep-frequencies/ and its three card components (src/components/ssvep/QueryCards.astro, cards 1–2;
 * PhaseCards.astro, cards 3–4; CcaCards.astro, cards 5–7) read from new-ssvep-frequencies-update.json. Card 8, the
 * cross-spectral card, has no study block in this file: its results are ssvep-followups-update.json's (owner decision
 * D28; src/data/ssvep-followups.ts reads cards 8 to 14), and this file keeps its bytes.
 *
 * Every figure is a leaf of that one file: an `SsvepFig`, printed as <span data-fig="<file>|<format>|<raw>"> and
 * re-read by the page's check (scripts/checks/new-ssvep-frequencies.mjs) and, once wired, by check-workbench.mjs.
 * Formats follow entities.ts formatFig: levels at pct2, paired differences at pp2 with their interval bounds at sgn2,
 * counts at count. One format is added here, pct0: the bet in the public thread prints as "39%", the precision the
 * thread stated, never as pct2 "39.00%" (wording review M5). A second, num1, prints the adapter's protected margin
 * (0.200001) as "0.2" on card 6. formatFig and check-workbench's format table do not know pct0 or num1 yet, so render
 * figures with formatSsvep() and figAttr() (the page shows how), not with Fig.astro, wherever either can occur.
 *
 * What this module adds is words: the card chrome (anchors, eyebrows, titles), the site's names for the export codes
 * in both languages, each study's interval method in words, and the Chinese of the export's English that the pages
 * print (what was not run, what is not published), keyed by the exact English so that a changed export fails the
 * build instead of printing other words. Every map below is checked against the export when this module loads.
 *
 * Rules the cards live under (plan §2.1 and the reviews that supersede its copy): levels at pct2, contrasts at pp2;
 * each card prints its own study's interval and names the bootstrap; every 73.2x value is labelled with its study
 * and task; Wearable values are labelled "Wearable-102"; the bet "held-out accuracy would clear 39%" appears once, on
 * card 4, and the commenter's confidence figure never appears; the thread is linked once, by the page's intro line.
 */
import ssvep from './new-ssvep-frequencies-update.json';
import { formatFig, type Fig, type Fmt } from './entities';
import type { Locale } from './i18n';

// --- The file and its release ----------------------------------------------------------------------------------
export const SSVEP = 'new-ssvep-frequencies-update.json' as const;
/** The served copy, as a page links it (download button, data-source note). */
export const SSVEP_PATH = `/data/${SSVEP}` as const;
export const ssvepRelease = { id: ssvep.release_id, schema: ssvep.schema_version, generated: ssvep.generated_at } as const;
/** The whole export, for blocks the typed accessors below do not cover. Read-only. */
export const SSVEP_DATA = ssvep;

/** A guard: the page refuses to build when the export stops supporting a sentence. */
export const needFor = (where: string) => (ok: unknown, what: string): void => {
  if (!ok) throw new Error(`${where}: the copy says ${what}`);
};
export const need = needFor('new-ssvep-frequencies');

// --- Figures ---------------------------------------------------------------------------------------------------
/**
 * entities.ts formats, plus pct0: a proportion as a whole percent ("39%"), for the thread's bet only; and num1: a
 * plain number at one decimal with a true minus sign, for the adapter's protected margin (0.200001 prints "0.2").
 */
export type SsvepFmt = Fmt | 'pct0' | 'num1';
export interface SsvepFig { raw: number; fmt: SsvepFmt; src: typeof SSVEP }
/** A sentence as the cards write it: words, and figures. */
export type Part = string | SsvepFig;

export function fig(raw: number, fmt: SsvepFmt): SsvepFig {
  need(typeof raw === 'number' && Number.isFinite(raw), `a finite figure (${String(raw)} as ${fmt})`);
  return { raw, fmt, src: SSVEP };
}
/** A level (accuracy, balanced accuracy, chance, a transition share): "86.15%". */
export const pct2 = (raw: number) => fig(raw, 'pct2');
/** A paired difference: "+5.24 pp", "−0.61 pp". */
export const pp2 = (raw: number) => fig(raw, 'pp2');
/** An interval bound of a paired difference: "+3.91", "−0.71". */
export const sgn2 = (raw: number) => fig(raw, 'sgn2');
/** The thread's bet, as the thread stated it: "39%". Nothing else prints at pct0. */
export const pct0 = (raw: number) => fig(raw, 'pct0');
/** A plain number at one decimal: the adapter's protected margin on the CCA-correlation scale, "0.2". */
export const num1 = (raw: number) => fig(raw, 'num1');
/** A count: "11,200". */
export const count = (raw: number) => fig(raw, 'count');

export const isFig = (p: unknown): p is SsvepFig => typeof p === 'object' && p !== null && 'raw' in p && 'fmt' in p;
/** The printed text of a figure: entities.ts formatFig, pct0 and num1. */
export function formatSsvep(f: SsvepFig): string {
  if (f.fmt === 'pct0') return `${(f.raw * 100).toFixed(0)}%`;
  if (f.fmt === 'num1') return f.raw.toFixed(1).replace(/^-/, '−');
  return formatFig(f as Fig);
}
/** The data-fig attribute: `<span data-fig={figAttr(f)} class=…>{formatSsvep(f)}</span>`. */
export const figAttr = (f: SsvepFig) => `${f.src}|${f.fmt}|${f.raw}`;
/** A figure inside a short answer or description string, marked for answer.ts. */
export const ans = (f: SsvepFig) => `[[${formatSsvep(f)}]]`;
/** Parts as plain text (aria labels, meta descriptions). */
export const plain = (parts: Part[]) => parts.map(p => (typeof p === 'string' ? p : formatSsvep(p))).join('');

// pct0 must print the thread's bet as the thread stated it, and the export must hold it where the plan puts it.
need(formatSsvep(pct0(ssvep.studies.phase_ramp.thread_bet.held8_threshold)) === '39%', 'the bet prints as 39%');

// --- Study blocks ----------------------------------------------------------------------------------------------
type Iv = [number, number];
export interface Level { estimate: number; interval: Iv; unit: string; people: number; seeds: number | string; origin: string }
export interface Contrast {
  role: string; left: string; right: string; estimate: number; interval: Iv; unit: string; people: number;
  seeds: number | string; flags?: Record<string, unknown>;
}
export interface IntervalMethod { method: string; draws: number; seed: number; level: number; conditional_on?: string }
export type StudyId = 'ref' | 'ref2' | 'softmax' | 'phase_jitter' | 'phase_ramp' | 'cca_diagnostics' | 'cca_adapter' | 'wearable_transfer';
export const STUDY_IDS: readonly StudyId[] = ['ref', 'ref2', 'softmax', 'phase_jitter', 'phase_ramp', 'cca_diagnostics', 'cca_adapter', 'wearable_transfer'];
export interface NotRun { item: string; run_in: StudyId | null }
export interface StudyBlock {
  source_sha256: string;
  interval_method: IntervalMethod;
  design?: Record<string, any>;
  levels: Record<string, Level>;
  contrasts: Record<string, Contrast>;
  undefined: Record<string, string>[];
  not_run: NotRun[];
  checks: Record<string, any>;
  limitations_keys: string[];
  display_names: Record<string, string>;
  export_codes: Record<string, unknown>;
  [extra: string]: any;
}
const studies = ssvep.studies as unknown as Record<StudyId, StudyBlock>;
need(Object.keys(ssvep.studies).join() === STUDY_IDS.join(), 'eight study blocks, in card order');

export const study = (id: StudyId): StudyBlock => studies[id];
/**
 * A level by its export key ("RAW-RESIDUAL/u8"). Most levels are proportions; a generalisation cost ("…/cost", u8
 * minus m8) is stored among the levels as a difference of proportions, and levelFig / levelIv print it as one.
 */
export function level(id: StudyId, key: string): Level {
  const x = studies[id].levels[key];
  need(x && (x.unit === 'proportion' || (x.unit === 'difference of proportions' && key.endsWith('/cost'))),
    `${id} has the level ${key}, a proportion (or a cost, a difference of proportions)`);
  return x;
}
const isDiff = (x: Level) => x.unit === 'difference of proportions';
export function contrast(id: StudyId, key: string): Contrast {
  const x = studies[id].contrasts[key];
  need(x && x.unit === 'difference of proportions', `${id} has the contrast ${key}, a difference of proportions`);
  return x;
}
/** A level's point estimate at pct2 (a cost at pp2). */
export const levelFig = (id: StudyId, key: string) => { const x = level(id, key); return isDiff(x) ? pp2(x.estimate) : pct2(x.estimate); };
/** A level's 95% interval at pct2: "82.84%", "–", "89.35%" (a cost's bounds at sgn2). */
export const levelIv = (id: StudyId, key: string, sep = '–'): Part[] => {
  const x = level(id, key);
  return isDiff(x) ? [sgn2(x.interval[0]), sep, sgn2(x.interval[1])] : [pct2(x.interval[0]), sep, pct2(x.interval[1])];
};
/**
 * Why a level or contrast has no value ("cannot_ask_unseen": the question number on held-out frequencies;
 * "not_a_planned_contrast": the adapted head against CCA alone), or undefined when it has one. A table prints an em
 * dash for it, never a zero.
 */
export function undefinedReason(id: StudyId, key: string): string | undefined {
  return studies[id].undefined.find(u => u.level === key || u.contrast === key)?.reason;
}
/** A paired difference at pp2. */
export const contrastFig = (id: StudyId, key: string) => pp2(contrast(id, key).estimate);
/** A paired difference's 95% interval, signed: "+3.91", " to ", "+6.62". */
export const contrastIv = (id: StudyId, key: string, to: string): Part[] => {
  const x = contrast(id, key);
  return [sgn2(x.interval[0]), to, sgn2(x.interval[1])];
};

// --- Cards -----------------------------------------------------------------------------------------------------
export type CardNumber = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
export interface CardPlacement { card: CardNumber; anchor: string; studies: StudyId[]; status_only?: boolean }
export const cards = ssvep.placement.cards as unknown as CardPlacement[];
const ANCHORS = ['reference-spectrum', 'head-and-features', 'phase-jitter', 'phase-ramp', 'cca-mechanism', 'cca-correction',
  'wearable-transfer', 'cross-spectral'];
need(cards.map(c => c.card).join() === '1,2,3,4,5,6,7,8' && cards.map(c => c.anchor).join() === ANCHORS.join(),
  'eight cards, at the anchors the plan fixes');
need(cards.filter(c => !c.status_only).flatMap(c => c.studies).join() === STUDY_IDS.join() && cards[7].status_only === true
  && cards[7].studies.length === 0, 'cards 1 to 7 read the eight study blocks in order; card 8 is a status card with no study');
export const cardOf = (n: CardNumber): CardPlacement => cards[n - 1];
export function cardOfStudy(id: StudyId): CardNumber {
  const c = cards.find(x => x.studies.includes(id));
  need(c, `a card for the ${id} study`);
  return c!.card;
}
/**
 * The card chrome both languages print: the eyebrow names the idea each follow-up tested (the route 3 link line's
 * list: the question, the head, phase, the matching computation, a learned correction to CCA), the title is the
 * plan's §2.1 title (card 3's with the wording review's R1 preposition: the delay acts on the window, not the query).
 */
const CARD_COPY: Record<CardNumber, Record<Locale, { eyebrow: string; title: string }>> = {
  1: { en: { eyebrow: 'Card 1 · how the question is asked', title: 'Asking with the reference spectrum' },
       zh: { eyebrow: '卡片 1 · 提问方式', title: '用参考谱来提问' } },
  2: { en: { eyebrow: 'Card 2 · head, features and question', title: 'The head, the spectrum or the question' },
       zh: { eyebrow: '卡片 2 · 分类头、特征与提问方式', title: '是分类头、频谱还是提问方式' } },
  3: { en: { eyebrow: 'Card 3 · stimulus phase', title: 'A random delay with the phase-carrying query' },
       zh: { eyebrow: '卡片 3 · 刺激相位', title: '带相位查询下的随机延迟' } },
  4: { en: { eyebrow: 'Card 4 · stimulus phase', title: 'A random phase ramp with magnitude queries' },
       zh: { eyebrow: '卡片 4 · 刺激相位', title: '幅度查询下的随机相位斜坡' } },
  5: { en: { eyebrow: 'Card 5 · the matching computation', title: 'Where CCA’s lead comes from' },
       zh: { eyebrow: '卡片 5 · 匹配计算', title: 'CCA 的领先从哪里来' } },
  6: { en: { eyebrow: 'Card 6 · a learned correction to CCA', title: 'Learning on top of CCA' },
       zh: { eyebrow: '卡片 6 · 对 CCA 的学习修正', title: '在 CCA 之上学习修正' } },
  7: { en: { eyebrow: 'Card 7 · a second dataset', title: 'The same correction on Wearable-102' },
       zh: { eyebrow: '卡片 7 · 第二个数据集', title: '同一修正用于 Wearable-102' } },
  // Card 8's results are read from ssvep-followups-update.json (src/data/ssvep-followups.ts, D28); its chrome stays here.
  8: { en: { eyebrow: 'Card 8 · a shared learned scorer', title: 'A shared scorer on the cross-spectral matrix' },
       zh: { eyebrow: '卡片 8 · 共享的学习型打分器', title: '互谱矩阵上的共享打分器' } },
};
export interface CardChrome {
  card: CardNumber; anchor: string; headingId: string; eyebrow: string; title: string; studies: StudyId[]; statusOnly: boolean;
}
/** What a card's <section> needs: its anchor, the id of its h2, its eyebrow and its title. */
export function cardChrome(n: CardNumber, locale: Locale): CardChrome {
  const c = cardOf(n), t = CARD_COPY[n][locale];
  return { card: n, anchor: c.anchor, headingId: `${c.anchor}-heading`, eyebrow: t.eyebrow, title: t.title, studies: c.studies,
           statusOnly: c.status_only === true };
}

// --- Cohorts, endpoints, the thread ----------------------------------------------------------------------------
export const cohort = ssvep.cohort;
export const wearable = ssvep.wearable;
export const thread = ssvep.thread;
export const rights = ssvep.rights;
export const notPublished = ssvep.not_published;
export interface Endpoint {
  id: 'u8' | 'seen_ba' | 'core_40' | 'wearable_12' | 'id_held_out'; task: string; candidates: number | null; chance: number | null;
  cards: number[]; pages?: string[]; separate_page?: boolean; defined?: boolean; reason?: string;
}
export const endpoints = ssvep.endpoints as unknown as Endpoint[];
export function endpoint(id: Endpoint['id']): Endpoint {
  const e = endpoints.find(x => x.id === id);
  need(e, `the endpoint ${id}`);
  return e!;
}
need(endpoints.map(e => e.id).join() === 'u8,seen_ba,core_40,wearable_12,id_held_out', 'the five endpoints of the strip, in order');
need(endpoints.every(e => e.candidates === null ? e.chance === null : Math.abs(e.chance! - 1 / e.candidates) < 1e-12),
  'each chance level is one over the number of candidates');
need(thread.commenter_named === false && thread.url === ssvep.studies.phase_ramp.thread_bet.source_url
  && /^https:\/\/huggingface\.co\/posts\/[^/]+\/\d+$/.test(thread.url), 'the thread is the public post, its commenter unnamed');
// The BETA cohort every block of cards 1–6 reads: the scope line states it once.
for (const id of cohort.studies as StudyId[]) {
  const d = studies[id].design?.dataset ?? studies[id].design;
  if (!d) continue;
  need((d.people ?? cohort.people) === cohort.people && (d.windows ?? d.trials ?? cohort.windows) === cohort.windows
    && (d.person_folds ?? d.participant_folds ?? cohort.person_folds) === cohort.person_folds
    && (d.frequency_rotations ?? cohort.frequency_rotations) === cohort.frequency_rotations
    && (d.training_seeds ?? cohort.training_seeds) === cohort.training_seeds, `${id} reads the cohort the scope line states`);
}
need(cohort.cards.join() === '1,2,3,4,5,6' && cohort.studies.every(id => cardOfStudy(id as StudyId) <= 6) && wearable.cards.join() === '7'
  && wearable.studies.join() === 'wearable_transfer', 'cards 1 to 6 read the BETA cohort, card 7 Wearable-102');

// --- Names -----------------------------------------------------------------------------------------------------
/**
 * The site's names (the export's name_key and every study's display_names), in Chinese, keyed by the exact English.
 * A name the export adds without a Chinese entry fails the build; each Chinese name carries exactly the digits of its
 * English (as directory-zh.json's entries must).
 */
const NAME_ZH: Record<string, string> = {
  'question number': '题号',
  'numeric code': '数值编码',
  'label template': '标签模板',
  'reference spectrum': '参考谱',
  'reference with stimulus phase': '带刺激相位的参考谱',
  'fixed spectrum match (no training)': '固定频谱匹配（无需训练）',
  'plain spectrum': '普通频谱',
  'complex spectrum': '复数频谱',
  'frozen CBraMod features': '冻结的 CBraMod 特征',
  'FiLM head': 'FiLM 分类头',
  'matching head': '匹配分类头',
  'CCA (no training)': 'CCA（无需训练）',
  'Hann-tapered CCA': 'Hann 窗 CCA',
  'cropped-spectrum match (no training)': '裁剪谱匹配（无需训练）',
  'channel-energy average': '通道能量平均',
  'shared ridge scorer': '共享岭回归打分器',
  'energy head': '能量分类头',
  'adapted head': '适配分类头',
  'CCA with learned correction': '加学习修正的 CCA',
  'cropped match with learned correction': '加学习修正的裁剪谱匹配',
  'cropped-spectrum check (Wearable-102)': '裁剪谱检查（Wearable-102）',
  'fundamental-only reference': '仅含基频的参考谱',
  'plain 32-way softmax': '普通的 32 类 softmax',
  'one output per question, softmax training': '每个问题一个输出，softmax 训练',
  'one output per question, one-vs-rest training': '每个问题一个输出，一对其余训练',
  '0–125 ms delay': '0–125 ms 延迟',
  'one-period delay': '一个周期的延迟',
  'matched CCA': '匹配 CCA',
};
export interface NameKeyEntry { site_name: string; export_codes: string; codes: { study: StudyId; code: string }[]; in_page_key: boolean }
export const nameKey = ssvep.name_key as unknown as NameKeyEntry[];
const digitsOf = (s: string) => (s.match(/\d+/g) ?? []).join(',');
for (const [en, zh] of Object.entries(NAME_ZH)) need(digitsOf(en) === digitsOf(zh), `the Chinese name of "${en}" carries its digits`);
for (const n of nameKey) need(n.site_name in NAME_ZH, `a Chinese name for "${n.site_name}"`);
for (const id of STUDY_IDS) for (const v of Object.values(studies[id].display_names)) need(v in NAME_ZH, `a Chinese name for "${v}" (${id})`);
for (const n of nameKey) for (const c of n.codes) need(STUDY_IDS.includes(c.study) && c.code in studies[c.study].display_names
  && studies[c.study].display_names[c.code] === n.site_name, `the name key's ${c.study} ${c.code} is "${n.site_name}" in that study`);
/** A site name in the page's language. */
export function siteName(english: string, locale: Locale): string {
  need(english in NAME_ZH, `a site name "${english}"`);
  return locale === 'zh' ? NAME_ZH[english] : english;
}
/** A study's export code by its site name ("FS" in phase_ramp → "FiLM head" / "FiLM 分类头"). */
export function nameOf(id: StudyId, code: string, locale: Locale): string {
  const en = studies[id].display_names[code];
  need(en, `${id} names the code ${code}`);
  return siteName(en, locale);
}
/** The name key's note where one site name covers codes from different exports. */
const CODES_NOTE: Record<string, Record<Locale, string>> = {
  'SUBSPACE-CROP in the diagnostics export, CCA-CROP in the adapter export: one set of scores': {
    en: 'one set of scores: SUBSPACE-CROP in card 5’s export, CCA-CROP in card 6’s',
    zh: '同一组分数：卡片 5 的导出中为 SUBSPACE-CROP，卡片 6 的导出中为 CCA-CROP',
  },
  'CCA-CROP in the Wearable export': {
    en: 'the code in card 7’s Wearable-102 export',
    zh: '卡片 7 的 Wearable-102 导出中的代码',
  },
};
const PURE_CODES = /^[A-Za-z0-9-]+(?:\/[A-Za-z0-9-]+)?$/;
for (const n of nameKey) need(PURE_CODES.test(n.export_codes) || n.export_codes in CODES_NOTE, `a note for the name key's "${n.export_codes}"`);
need(cardOfStudy('cca_diagnostics') === 5 && cardOfStudy('cca_adapter') === 6 && cardOfStudy('wearable_transfer') === 7, 'the name key notes name cards 5, 6 and 7');
/** The name key's export codes for one site name (unique, in the export's order) and its note, if any. */
export function codesOf(n: NameKeyEntry, locale: Locale): { codes: string[]; note?: string } {
  const codes = [...new Set(n.codes.map(c => c.code))];
  return { codes, note: CODES_NOTE[n.export_codes]?.[locale] };
}
/** The cards a name key entry is used on. */
export const cardsOfName = (n: NameKeyEntry): CardNumber[] => [...new Set(n.codes.map(c => cardOfStudy(c.study)))].sort((a, b) => a - b);

// --- Interval methods, in words --------------------------------------------------------------------------------
/**
 * Each study's interval method as a caption names it (plan §2.1 figure rules; wording review M3 for cards 3 and 4),
 * from interval_method: the draws as a figure, the bootstrap seed as printed in the export.
 */
const METHOD_WORDS: Record<string, Record<Locale, { draws: string; tail: string }>> = {
  'hierarchical paired bootstrap over people and fold-shared seed indices': {
    en: { draws: '95% intervals from ', tail: ' hierarchical paired bootstrap draws over people and fold-shared seed indices' },
    zh: { draws: '95% 区间来自对被试与各折共享的种子编号所做的 ', tail: ' 次分层配对 bootstrap 抽样' },
  },
  'hierarchical paired bootstrap': {
    en: { draws: '95% intervals from ', tail: ' hierarchical paired bootstrap draws over people and training seeds' },
    zh: { draws: '95% 区间来自对被试与训练种子所做的 ', tail: ' 次分层配对 bootstrap 抽样' },
  },
  'paired person bootstrap, percentile interval': {
    en: { draws: '95% percentile intervals from ', tail: ' paired person bootstrap draws' },
    zh: { draws: '95% 百分位区间来自以被试为单位的 ', tail: ' 次配对 bootstrap 抽样' },
  },
};
const CONDITIONAL_WORDS: Record<string, Record<Locale, () => Part[]>> = {
  'fixed person folds and three training seeds; five fixed rotations averaged first': {
    en: () => [', conditional on the fixed person folds and three seeds; the five fixed rotations are averaged first'],
    zh: () => ['，以固定的被试折与三个种子为条件；五个固定的频率轮换先取平均'],
  },
  'the fitted models and the three fixed training seeds': {
    en: () => [', conditional on the fitted models and the three fixed training seeds'],
    zh: () => ['，以拟合好的模型与三个固定的训练种子为条件'],
  },
  'the fixed 105 source models': {
    en: () => [', conditional on the fixed ', count(wearable.source_models), ' source models'],
    zh: () => ['，以固定的 ', count(wearable.source_models), ' 个源模型为条件'],
  },
};
need(wearable.source_models === 105 && studies.wearable_transfer.design?.source_models?.models === wearable.source_models,
  'the 105 source models of the Wearable-102 conditional');
for (const id of STUDY_IDS) {
  const m = studies[id].interval_method;
  need(m.method in METHOD_WORDS && m.level === 0.95 && m.draws === 2000 && (m.conditional_on === undefined || m.conditional_on in CONDITIONAL_WORDS),
    `${id}'s interval method in words, 95%, 2,000 draws`);
  need(m.seed === (cardOfStudy(id) <= 4 ? 20261007 : 20261015), `${id}'s bootstrap seed: 20261007 for cards 1–4, 20261015 for cards 5–7`);
}
need(studies.phase_jitter.interval_method.conditional_on === studies.phase_ramp.interval_method.conditional_on
  && studies.phase_jitter.intervals?.conditional_on === 'Fixed folds and three training seeds; five fixed rotations averaged first.',
  'cards 3 and 4: conditional on the fixed person folds and three seeds');
need(cohort.training_seeds === 3 && cohort.frequency_rotations === 5, 'three seeds and five rotations, as the conditional words say');
/** A study's interval method, as one clause: "95% intervals from 2,000 … draws (seed 20261007), conditional on …". */
export function intervalText(id: StudyId, locale: Locale): Part[] {
  const m = studies[id].interval_method, w = METHOD_WORDS[m.method][locale];
  const seed = locale === 'zh' ? `（种子 ${m.seed}）` : ` (seed ${m.seed})`;
  return [w.draws, count(m.draws), w.tail, seed, ...(m.conditional_on ? CONDITIONAL_WORDS[m.conditional_on][locale]() : [])];
}

// --- What was not run --------------------------------------------------------------------------------------------
/** Each study's not_run items in words, keyed by the export's English. */
const NOT_RUN: Record<string, Record<Locale, string>> = {
  'Synthetic reference waveform through CBraMod': { en: 'a synthetic reference waveform passed through CBraMod', zh: '把合成的参考波形送入 CBraMod' },
  'Matching/bilinear head': { en: 'the matching (bilinear) head', zh: '匹配（双线性）分类头' },
  'Fundamental-only reference ablation': { en: 'a fundamental-only reference', zh: '仅含基频的参考谱' },
  'Hyperparameter search': { en: 'a hyperparameter search', zh: '超参数搜索' },
  'Independent new dataset replication': { en: 'an independent replication on a new dataset', zh: '在新数据集上的独立重复' },
  'Independent-channel delay mechanism control': { en: 'a control with an independent delay on each channel', zh: '每个通道各自独立延迟的机制对照' },
  'Same augmentation on FS-NUM': { en: 'the same delay with the numeric-code query', zh: '以数值编码作查询时的同样延迟' },
  'MATCH head follow-up': { en: 'the matching head', zh: '匹配分类头' },
  'Literal raw-window recropping': { en: 'cutting a new raw window at the delayed onset', zh: '在延迟后的起点重新截取原始时间窗' },
  'Test-time augmentation': { en: 'delays at test time', zh: '测试时的延迟增强' },
  'CCA-derived features or residuals': { en: 'features derived from CCA, or a learned correction to it', zh: '来自 CCA 的特征，或对 CCA 的学习修正' },
  'New dataset transfer': { en: 'transfer to a new dataset', zh: '迁移到新数据集' },
  'Extra label-independent MATCH-REF arm': { en: 'an extra matching-head arm whose delay ignores the label', zh: '延迟与标签无关的额外匹配分类头组' },
  'Augmented no-query softmax': { en: 'a plain softmax trained with the same delay', zh: '用同样延迟训练、不带查询的 softmax' },
  'Test-time phase-ramp invariance diagnostic': { en: 'a test-time check of how far scores change under the ramp', zh: '测试时检查分数随相位斜坡变化多少的诊断' },
  'Literal raw rewindowing': { en: 'cutting a new raw window at the delayed onset', zh: '在延迟后的起点重新截取原始时间窗' },
  'Extra dataset or model': { en: 'another dataset or model', zh: '其他数据集或模型' },
  'Learning-rate/augmentation sweeps': { en: 'sweeps over the learning rate or the delay range', zh: '学习率或延迟范围的扫描' },
  'paired contrast with the earlier complex-spectrum heads': { en: 'a paired contrast with the earlier complex-spectrum heads', zh: '与此前复数频谱分类头的配对对比' },
  'filter-bank CCA': { en: 'filter-bank CCA', zh: '滤波器组 CCA' },
  'supervised spatial templates': { en: 'supervised spatial templates', zh: '有监督的空间模板' },
  'trunk or query ablation': { en: 'removing the trunk or the query', zh: '去掉主干或查询的消融' },
  'simpler learned head on the CCA features': { en: 'a simpler learned head on the CCA features', zh: '在 CCA 特征上更简单的学习型分类头' },
  'equivalence margin': { en: 'an equivalence margin', zh: '等效界值' },
  'one-factor ablations of units, window onset, hardware, people or frequency grid': {
    en: 'changing one factor at a time: units, window onset, hardware, people or the frequency grid',
    zh: '逐一改变单个因素：单位、时间窗起点、硬件、被试或频率网格' },
  'target adaptation or retraining': { en: 'adapting or retraining on the target data', zh: '在目标数据上适配或重新训练' },
};
for (const id of STUDY_IDS) for (const x of studies[id].not_run)
  need(x.item in NOT_RUN && (x.run_in === null || STUDY_IDS.includes(x.run_in)), `words for ${id}'s not-run item "${x.item}"`);
/** A study's not-run items: the words, and the card that ran the item later, if one did. */
export const notRunOf = (id: StudyId, locale: Locale): { text: string; runIn?: CardNumber }[] =>
  studies[id].not_run.map(x => ({ text: NOT_RUN[x.item][locale], runIn: x.run_in ? cardOfStudy(x.run_in) : undefined }));
