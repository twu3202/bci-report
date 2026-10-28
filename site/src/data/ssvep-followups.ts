/**
 * Cards 8 to 14 of /topics/new-ssvep-frequencies/ (release ssvep-followups-update-20261028, owner decisions D14, D22,
 * D23, D25 and D28): what the page and its two card components (src/components/ssvep/MechanismCards.astro, cards 8, 9
 * and 12; PracticalCards.astro, cards 10, 11, 13 and 14) read from ssvep-followups-update.json. The released file,
 * new-ssvep-frequencies-update.json, keeps its bytes (D28); this file's card 8 takes the place of that file's status
 * entry, and new-ssvep-frequencies.ts keeps reading cards 1 to 7.
 *
 * Every figure is made from a path into this one file (figAt): the raw value is the field's own double, and the page
 * prints it as <span data-at="<path>" data-fig="<file>|<format>|<raw>">, so scripts/checks/ssvep-followups.mjs can hold
 * each printed figure to its field and to the format that field's kind takes:
 *   levels at pct2; paired differences at pp2 with their bounds at sgn2; a difference of two equal levels at pp2eq
 *   ("0.00 pp", never "−0.00 pp"); a bound the export flags as below two decimals at sgn5 ("−0.00022"); card 12's gap
 *   statistics (squared-correlation units, never percentages) and the CPU component milliseconds at sig3; pairwise win
 *   fractions (not accuracies) at auc3; counts at count; card 12's family level at pct2 and card 13's margin-test level
 *   at pct0; card 13's margin at pm1 ("±0.5 pp"); card 13's weight rule's exponent and offset at auc2; card 11's
 *   window lengths at s1. formatSc prints pct0, sgn5, pp2eq and pm1 itself and the rest through formatFig (entities.ts);
 *   check-workbench.mjs's format table does not know sgn5, pp2eq or pm1 yet (reported to the integration package).
 *
 * The words are keyed by the export's English (names, not-run items, interval conditions, disclosures, not-published
 * items, limitation keys), so a changed export fails the build instead of printing other words. Rules: a level shared
 * by several cards prints its interval on its interval_home card only and names that card elsewhere (homeOf); every
 * contrast prints its own interval; thread predictions stay on card 4 (D23): no figure here comes from the thread.
 */
import sc from './ssvep-followups-update.json';
import released from './new-ssvep-frequencies-update.json';
import { formatFig, type Fig, type Fmt } from './entities';
import { hrefFor, type Locale } from './i18n';
import { needFor, cards as releasedCards, cardChrome as releasedChrome, siteName as releasedName, endpoints as releasedEndpoints,
  formatSsvep, figAttr as releasedAttr, isFig as isReleasedFig, type SsvepFig } from './new-ssvep-frequencies';

// --- The file and its release ----------------------------------------------------------------------------------
export const SC = 'ssvep-followups-update.json' as const;
export const SC_PATH = `/data/${SC}` as const;
export const scRelease = { id: sc.release_id, schema: sc.schema_version, generated: sc.generated_at } as const;
/** The whole export, read-only, for blocks the accessors below do not cover. */
export const SC_DATA = sc as any;
export const need = needFor('ssvep-followups');

need(sc.release_id === 'ssvep-followups-update-20261028' && sc.placement.reads_with.release_id === released.release_id
  && sc.placement.reads_with.file === 'new-ssvep-frequencies-update.json' && sc.provenance.released_file.unchanged === true
  && sc.provenance.released_file.release_id === released.release_id, 'this file reads with the released file, which keeps its bytes (D28)');
need(sc.placement.leaderboard === false && sc.placement.new_page_count === 0 && sc.placement.new_dataset_count === 0
  && sc.placement.new_model_count === 0 && sc.placement.page === '/topics/new-ssvep-frequencies/', 'cards on the same page, outside every leaderboard');

// --- Figures ---------------------------------------------------------------------------------------------------
export type ScFmt = Fmt | 'pct0' | 'sgn5' | 'pp2eq' | 'pm1';
export interface ScFig { raw: number; fmt: ScFmt; src: typeof SC; at: string }
export interface Link { href: string; text: string; home?: number }
/** A sentence as the cards write it: words, figures, links. */
export type Bit = string | ScFig | Link;
export type Path = (string | number)[];

const valueAt = (path: Path): unknown => path.reduce((o: any, k) => (o === null || o === undefined ? undefined : o[k]), sc as any);
const sign = (r: number) => (r === 0 ? '' : r > 0 ? '+' : '−');
/** The printed text of a figure. */
export function formatSc(f: ScFig): string {
  switch (f.fmt) {
    case 'pct0': return `${(f.raw * 100).toFixed(0)}%`;
    // A bound the export flags below two decimals: five decimals of a percentage point, never rounded to 0.00.
    case 'sgn5': return `${sign(f.raw)}${Math.abs(f.raw * 100).toFixed(5)}`;
    // A difference of two equal levels (floating-point residue): 0.00 pp, never −0.00 pp.
    case 'pp2eq': return Math.abs(f.raw) < 1e-12 ? '0.00 pp' : `${sign(f.raw)}${Math.abs(f.raw * 100).toFixed(2)} pp`;
    // A symmetric margin in percentage points.
    case 'pm1': return `±${Math.abs(f.raw * 100).toFixed(1)} pp`;
    default: return formatFig(f as unknown as Fig);
  }
}
/** A figure from a path into the file: the raw value is the field's own number. */
export function figAt(path: Path, fmt: ScFmt): ScFig {
  const raw = valueAt(path);
  need(typeof raw === 'number' && Number.isFinite(raw), `a finite figure at ${path.join('/')} (${String(raw)})`);
  const f: ScFig = { raw: raw as number, fmt, src: SC, at: path.join('|') };
  // A non-zero difference never prints as zero: pp2eq and sgn5 exist for the two cases the export flags.
  if ((fmt === 'pp2' || fmt === 'sgn2') && raw !== 0) need(!/^[+−]?0\.00(?: pp)?$/.test(formatSc(f)), `${f.at} prints as zero at ${fmt}`);
  return f;
}
export const isFig = (b: unknown): b is ScFig => typeof b === 'object' && b !== null && 'raw' in b && 'at' in b;
export const isLink = (b: unknown): b is Link => typeof b === 'object' && b !== null && 'href' in b;
/** The data-fig attribute. */
export const figAttr = (f: ScFig) => `${f.src}|${f.fmt}|${f.raw}`;
/** A figure inside a short-answer string, marked for answer.ts. */
export const ans = (f: ScFig) => `[[${formatSc(f)}]]`;
/** Bits as plain text. */
export const plain = (bits: Bit[]) => bits.map(b => (typeof b === 'string' ? b : isFig(b) ? formatSc(b) : b.text)).join('');
const S = ['studies'];

// --- Markup -------------------------------------------------------------------------------------------------------
/**
 * Bits as HTML, for set:html: words escaped; a figure of this file as <span data-at data-fig>, with class="metric" when
 * asked; a figure of the released file as <span data-fig>; a link that names the card carrying a shared level's
 * interval with data-home. One string per element keeps Astro from adding whitespace between parts.
 */
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
export type AnyBit = Bit | SsvepFig | { code: string } | { strong: string };
export function figHtml(f: ScFig, cls?: string): string {
  return `<span data-at="${esc(f.at)}" data-fig="${esc(figAttr(f))}"${cls ? ` class="${cls}"` : ''}>${esc(formatSc(f))}</span>`;
}
export function toHtml(bits: AnyBit[]): string {
  return bits.map(b => typeof b === 'string' ? esc(b)
    : isFig(b) ? figHtml(b)
    : isLink(b) ? `<a href="${esc(b.href)}"${b.home ? ` data-home="${b.home}"` : ''}>${esc(b.text)}</a>`
    : isReleasedFig(b) ? `<span data-fig="${esc(releasedAttr(b))}">${esc(formatSsvep(b))}</span>`
    : 'code' in b ? `<code>${esc(b.code)}</code>`
    : 'strong' in b ? `<strong>${esc(b.strong)}</strong>` : '').join('')
    // Chinese: no space after a full-width closing parenthesis before the next character ("（卡片 9）降到", not "（卡片 9） 降到").
    .replace(/）\s+(?=[㐀-鿿])/g, '）');
}
/** A count at a path. */
export const countAt = (...path: Path) => figAt(path, 'count');

// --- Studies and cards -------------------------------------------------------------------------------------------
export type ScStudy = 'xspec' | 'coherence_eigen' | 'harmonic_pooling' | 'harmonic_pooling_wearable' | 'practical_settings'
  | 'harmonic_gap' | 'fixed_decay' | 'rising_weights';
export const SC_STUDIES: readonly ScStudy[] = ['xspec', 'coherence_eigen', 'harmonic_pooling', 'harmonic_pooling_wearable',
  'practical_settings', 'harmonic_gap', 'fixed_decay', 'rising_weights'];
need(Object.keys(sc.studies).join() === SC_STUDIES.join(), 'eight study blocks, in card order');
const studies = sc.studies as unknown as Record<ScStudy, any>;
export const st = (id: ScStudy): any => studies[id];

export type NewCard = 8 | 9 | 10 | 11 | 12 | 13 | 14;
export const NEW_CARDS: readonly NewCard[] = [8, 9, 10, 11, 12, 13, 14];
interface Placement { card: NewCard; anchor: string; studies: ScStudy[]; endpoints: string[]; supersedes?: { release_id: string; file: string; entry: string } }
export const placements = sc.placement.cards as unknown as Placement[];
const ANCHORS = ['cross-spectral', 'eigenvalue-pooling', 'harmonic-pooling', 'practical-settings', 'harmonic-gap', 'fixed-decay', 'rising-weights'];
need(placements.map(c => c.card).join() === NEW_CARDS.join() && placements.map(c => c.anchor).join() === ANCHORS.join(),
  'cards 8 to 14 at the anchors the plan fixes');
need(placements.flatMap(c => c.studies).join() === SC_STUDIES.join(), 'the cards read the eight study blocks in order');
// Card 8 keeps its number and anchor and takes the place of the released status entry (D28).
const released8 = releasedCards[7];
need(released8.card === 8 && released8.status_only === true && released8.anchor === placements[0].anchor
  && placements[0].supersedes?.release_id === released.release_id && placements[0].supersedes?.entry === 'status_only',
  'card 8 keeps its anchor; this file supersedes the released status entry');
need(sc.placement.reads_with.cards.join() === '1,2,3,4,5,6,7' && releasedCards.slice(0, 7).every((c, i) => c.card === i + 1 && !c.status_only),
  'the released file carries the results of cards 1 to 7');
need(placements.every(p => p.studies.every(id => studies[id].card === undefined || (studies[id].card === p.card && studies[id].anchor === p.anchor))),
  'each study block names its own card and anchor');
export const cardOfStudy = (id: ScStudy): NewCard => placements.find(p => p.studies.includes(id))!.card;
export const placementOf = (n: NewCard) => placements[n - 8];
/** Every card on the page with results, in order: the released file's seven and this file's seven. */
export const ALL_CARDS: number[] = [...releasedCards.filter(c => !c.status_only).map(c => c.card), ...placements.map(c => c.card)];
need(ALL_CARDS.join() === '1,2,3,4,5,6,7,8,9,10,11,12,13,14', 'fourteen cards with results');
/** The anchor of any card, 1 to 14. */
export const anchorOf = (n: number): string => (n <= 7 ? releasedCards[n - 1].anchor : placementOf(n as NewCard).anchor);
/** A link to a card, by the page's path (the Markdown copy drops bare in-page jump links with their text). */
export const cardHref = (n: number, locale: Locale) => hrefFor(`/topics/new-ssvep-frequencies/#${anchorOf(n)}`, locale);
export const cardWord = (n: number, locale: Locale, cap = false) => (locale === 'zh' ? `卡片 ${n}` : `${cap ? 'Card' : 'card'} ${n}`);
export const cardLink = (n: number, locale: Locale, home = false, cap = false): Link => ({ href: cardHref(n, locale), text: cardWord(n, locale, cap), ...(home ? { home: n } : {}) });

/** The card chrome: card 8 keeps the released module's title; 9 to 14 are the plan's §2.1 titles. */
const CARD_COPY: Record<Exclude<NewCard, 8>, Record<Locale, { eyebrow: string; title: string }>> = {
  9: { en: { eyebrow: 'Card 9 · eigenvalue pooling', title: 'Eigenvalues of the harmonic matrices, learned or summed' },
       zh: { eyebrow: '卡片 9 · 特征值汇总', title: '谐波矩阵的特征值：学习的还是直接求和的' } },
  10: { en: { eyebrow: 'Card 10 · harmonic pooling', title: 'Pooling CCA’s per-harmonic statistics' },
        zh: { eyebrow: '卡片 10 · 谐波汇总', title: '汇总 CCA 的逐谐波统计量' } },
  11: { en: { eyebrow: 'Card 11 · practical settings', title: 'Filter-bank CCA, shorter windows and fewer electrodes' },
        zh: { eyebrow: '卡片 11 · 实际使用条件', title: '滤波器组 CCA、更短的时间窗与更少的电极' } },
  12: { en: { eyebrow: 'Card 12 · the harmonic sum’s gain', title: 'Where the harmonic sum’s gain over joint CCA comes from' },
        zh: { eyebrow: '卡片 12 · 谐波求和的增益', title: '谐波求和相对联合 CCA 的增益从哪里来' } },
  13: { en: { eyebrow: 'Card 13 · weights on the harmonics', title: 'One decay rule on harmonics and on filter-bank bands' },
        zh: { eyebrow: '卡片 13 · 谐波的权重', title: '同一衰减规则用于谐波和滤波器组子带' } },
  14: { en: { eyebrow: 'Card 14 · weights on the harmonics', title: 'A rising weight on the harmonics' },
        zh: { eyebrow: '卡片 14 · 谐波的权重', title: '逐级升高的谐波权重' } },
};
export interface ScChrome { card: NewCard; anchor: string; headingId: string; eyebrow: string; title: string; studies: ScStudy[] }
export function scChrome(n: NewCard, locale: Locale): ScChrome {
  const p = placementOf(n);
  const t = n === 8 ? (({ eyebrow, title }) => ({ eyebrow, title }))(releasedChrome(8, locale)) : CARD_COPY[n][locale];
  return { card: n, anchor: p.anchor, headingId: `${p.anchor}-heading`, eyebrow: t.eyebrow, title: t.title, studies: p.studies };
}
need(releasedChrome(8, 'en').title === 'A shared scorer on the cross-spectral matrix' && !/progress/.test(releasedChrome(8, 'en').eyebrow)
  && !/进行中/.test(releasedChrome(8, 'zh').eyebrow), 'card 8 keeps its title; its eyebrow no longer says it is in progress');

// --- Endpoints --------------------------------------------------------------------------------------------------
export interface ScEndpoint { id: 'u8' | 'seen_ba' | 'wearable_12'; task: string; candidates: number; chance: number; cards: NewCard[]; sensors?: string[] }
export const scEndpoints = sc.endpoints as unknown as ScEndpoint[];
need(scEndpoints.map(e => e.id).join() === 'u8,seen_ba,wearable_12' && scEndpoints.every(e => Math.abs(e.chance - 1 / e.candidates) < 1e-12),
  'three endpoints, each chance level one over its candidates');
need(scEndpoints.every(e => { const r = releasedEndpoints.find(x => x.id === e.id); return r && r.candidates === e.candidates && r.chance === e.chance; }),
  'the same three tasks as the released strip');
need(scEndpoints.every(e => e.cards.every(n => placementOf(n).endpoints.some(x => x === e.id || (e.id === 'wearable_12' && (x === 'dry' || x === 'wet'))))),
  'each endpoint lists the cards whose placements report it');
/** The cards of this file that report an endpoint of the released strip. */
export const newCardsOf = (id: string): NewCard[] => scEndpoints.find(e => e.id === id)?.cards ?? [];

// --- Levels, contrasts, homes -----------------------------------------------------------------------------------
interface Shared { site_name: string; endpoint: string; levels: { study: ScStudy; level: string }[]; interval_home: number; aliases?: string[]; released_level?: { release_id: string; study: string; level: string } }
export const shared = sc.shared_estimates as unknown as Shared[];
const codeOfKey = (key: string) => { const p = key.split('/'); return p[p.length - 2]; };
/**
 * The card that prints a level's interval: the shared estimate's interval_home, else the card a reused comparator
 * comes from, else the level's own card.
 */
export function homeOf(id: ScStudy, key: string): number {
  const sh = shared.find(e => e.levels.some(l => l.study === id && l.level === key));
  if (sh) return sh.interval_home;
  const lv = studies[id].levels[key];
  if (typeof lv.origin === 'string' && lv.origin.startsWith('reused_')) {
    const r = studies[id].reused?.[codeOfKey(key)];
    need(r && typeof r.card === 'number', `${id} names the card its reused ${key} comes from`);
    return r.card;
  }
  return cardOfStudy(id);
}
// Each shared estimate's levels carry one value; its home card prints its interval (or, for card 5 or 7, the released file does).
for (const e of shared) {
  const vals = e.levels.map(l => studies[l.study].levels[l.level]?.estimate);
  need(vals.every(v => typeof v === 'number' && Math.abs(v - vals[0]) < 1e-12), `${e.site_name} ${e.endpoint}: one value across its cards`);
  if (e.interval_home <= 7) {
    const r = e.released_level!;
    const rl = (released.studies as any)[r.study]?.levels?.[r.level];
    need(r.release_id === released.release_id && rl && Math.abs(rl.estimate - vals[0]) < 1e-12 && Array.isArray(rl.interval)
      && releasedCards[e.interval_home - 1].studies.includes(r.study as never), `${e.site_name} ${e.endpoint}: card ${e.interval_home}’s released level`);
  } else {
    need(e.levels.some(l => cardOfStudy(l.study) === e.interval_home && Array.isArray(studies[l.study].levels[l.level].interval)),
      `${e.site_name} ${e.endpoint}: an interval on its home card ${e.interval_home}`);
  }
}
// A reused comparator has the value of the card it comes from (cards 5 and 7 in the released file, 8 and 9 in this one).
for (const id of SC_STUDIES) for (const [key, lv] of Object.entries(studies[id].levels as Record<string, any>)) {
  if (!String(lv.origin).startsWith('reused_')) continue;
  const from = String(lv.origin).slice('reused_'.length), home = homeOf(id, key);
  const src = home <= 7 ? (released.studies as any)[from]?.levels?.[key.split('/').slice(-2).join('/')] : studies[from as ScStudy]?.levels?.[key];
  need(src && Math.abs(src.estimate - lv.estimate) < 1e-12, `${id} ${key}: the value of card ${home}`);
}
export interface LevelFigs { est: ScFig; iv: [ScFig, ScFig] | null; home: number; key: string; study: ScStudy }
/** A level (a proportion) at pct2, with its interval only on its home card. */
export function level(id: ScStudy, key: string): LevelFigs {
  const lv = studies[id].levels[key];
  need(lv && lv.unit === 'proportion', `${id} has the level ${key}, a proportion`);
  const home = homeOf(id, key), base = [...S, id, 'levels', key];
  const iv = home === cardOfStudy(id) && Array.isArray(lv.interval)
    ? [figAt([...base, 'interval', 0], 'pct2'), figAt([...base, 'interval', 1], 'pct2')] as [ScFig, ScFig] : null;
  return { est: figAt([...base, 'estimate'], 'pct2'), iv, home, key, study: id };
}
export interface ContrastFigs { est: ScFig; lo: ScFig; hi: ScFig; role: string; key: string; study: ScStudy; left: string; right: string; flags: Record<string, any> }
/** A paired difference at pp2 (pp2eq for two equal levels) with its own interval at sgn2 (sgn5 for a flagged bound). */
export function contrast(id: ScStudy, key: string): ContrastFigs {
  const c = studies[id].contrasts[key];
  need(c && c.unit === 'difference of proportions' && Array.isArray(c.interval), `${id} has the contrast ${key}`);
  const flags = c.flags ?? {}, low = flags.bound_below_two_decimals ?? [], base = [...S, id, 'contrasts', key];
  if (flags.levels_equal) need(Math.abs(c.estimate) < 1e-12 && studies[id].levels[c.left].estimate === studies[id].levels[c.right].estimate, `${key}: equal levels`);
  return {
    est: figAt([...base, 'estimate'], flags.levels_equal ? 'pp2eq' : 'pp2'),
    lo: figAt([...base, 'interval', 0], low.includes('lower') ? 'sgn5' : 'sgn2'),
    hi: figAt([...base, 'interval', 1], low.includes('upper') ? 'sgn5' : 'sgn2'),
    role: c.role, key, study: id, left: c.left, right: c.right, flags,
  };
}
/** Whether a contrast's interval includes zero, read from the interval itself (and checked against the flag). */
export function spansZero(x: ContrastFigs): boolean {
  const z = x.lo.raw < 0 && x.hi.raw > 0;
  if ('interval_includes_zero' in x.flags) need(x.flags.interval_includes_zero === (x.lo.raw <= 0 && x.hi.raw >= 0), `${x.key}: the flag matches the interval`);
  return z;
}

// --- Names ------------------------------------------------------------------------------------------------------
/** The site's names of this file (name_key and every study's display_names), in Chinese, keyed by the exact English. */
const NAME_ZH: Record<string, string> = {
  'harmonic sum (no training)': '谐波求和（无需训练）',
  'joint CCA': '联合 CCA',
  'common-direction sum': '共同方向求和',
  'eigenvalue head': '特征值分类头',
  'joint eigenvalue head': '联合特征值分类头',
  'spectral eigenvalue head': '频谱特征值分类头',
  'spectral harmonic sum (no training)': '频谱谐波求和（无需训练）',
  'coherence head': '相干分类头',
  'signed coherence head': '带符号的相干分类头',
  'top-three ridge': '三项主分量岭回归',
  'harmonic max (no training)': '谐波取最大（无需训练）',
  'all-component sum (no training)': '全分量求和（无需训练）',
  'joint all-component sum (no training)': '联合全分量求和（无需训练）',
  'cross-spectral ridge': '互谱矩阵岭回归',
  'whitened cross-spectral ridge': '白化互谱矩阵岭回归',
  'cross-spectral ridge with quadrature': '带正交分量的互谱矩阵岭回归',
  'cross-spectral MLP': '互谱 MLP',
  'filter-bank CCA (seven sub-bands)': '滤波器组 CCA（七个子带）',
  'joint CCA plus gap (diagnostic score)': '联合 CCA 加差距（诊断分数）',
  'harmonic sum with decay weights (no training)': '带衰减权重的谐波求和（无需训练）',
  'filter-bank CCA with flat sub-band weights (no training)': '子带等权的滤波器组 CCA（无需训练）',
  'rising weights 1, 1.5, 1.9 (no training)': '递增权重 1、1.5、1.9（无需训练）',
  'rising weights, exact profile (no training)': '递增权重，精确曲线（无需训练）',
};
const digitsOf = (s: string) => (s.match(/\d+/g) ?? []).join(',');
for (const [en, zh] of Object.entries(NAME_ZH)) need(digitsOf(en) === digitsOf(zh), `the Chinese name of "${en}" carries its digits`);
/** A site name in the page's language: this file's names, else the released module's. */
export function scName(english: string, locale: Locale): string {
  if (english in NAME_ZH) return locale === 'zh' ? NAME_ZH[english] : english;
  return releasedName(english, locale);
}
export interface ScNameKey { site_name: string; export_codes: string; codes: { study: ScStudy; code: string }[]; key: 'new' | 'released' | 'card'; note?: string; alias_of?: string[] }
export const scNameKey = sc.name_key as unknown as ScNameKey[];
for (const n of scNameKey) {
  scName(n.site_name, 'zh');
  for (const c of n.codes) need(studies[c.study]?.display_names?.[c.code] === n.site_name, `the name key's ${c.study} ${c.code} is "${n.site_name}"`);
}
for (const id of SC_STUDIES) for (const v of Object.values(studies[id].display_names as Record<string, string>)) scName(v, 'zh');
need(scNameKey.every(n => ['new', 'released', 'card'].includes(n.key)), 'every name is new to the key, released in it, or named on its card');
/** A study's export code by its site name. */
export function nameOf(id: ScStudy, code: string, locale: Locale): string {
  const en = studies[id].display_names[code];
  need(en, `${id} names the code ${code}`);
  return scName(en, locale);
}
/** The name key's notes for codes from different exports under one name, in both languages. */
const CODES_NOTE: Record<string, Record<Locale, string>> = {
  'S in the harmonic-gap export, H3-FLAT in the fixed-decay export, flat in the rising-weight export: one set of scores': {
    en: 'one set of scores: S in card 12’s export, H3-FLAT in card 13’s, flat in card 14’s', zh: '同一组分数：卡片 12 的导出中为 S，卡片 13 的为 H3-FLAT，卡片 14 的为 flat' },
  'J in the harmonic-gap export: the same scores as CCA-RAW': {
    en: 'J in card 12’s export; the same scores as CCA (no training) on BETA and matched CCA on Wearable-102', zh: '卡片 12 的导出中为 J；与 BETA 上的 CCA（无需训练）、Wearable-102 上的匹配 CCA 是同一组分数' },
  'FBCCA-DECAY in the fixed-decay export: the same scores as FBCCA-M3-N7-H5 at 2 s and 8 electrodes': {
    en: 'FBCCA-DECAY in card 13’s export: the same scores as card 11’s at 2 s and eight electrodes', zh: '卡片 13 的导出中为 FBCCA-DECAY：与卡片 11 在 2 秒、八个电极下是同一组分数' },
  'CCA-RAW-H3 in the practical B/D export: the same scores as CCA-RAW at 2 s and 8 electrodes': {
    en: 'CCA-RAW-H3 in card 11’s export: the same scores at 2 s and eight electrodes', zh: '卡片 11 的导出中为 CCA-RAW-H3：在 2 秒、八个电极下是同一组分数' },
};
for (const n of scNameKey) if (n.note) need(n.note in CODES_NOTE, `words for the name key note "${n.note}"`);
export const codesNote = (n: ScNameKey, locale: Locale): string | undefined => (n.note ? CODES_NOTE[n.note][locale] : undefined);
// "joint CCA" is the CCA scores under another name (one site name per set of scores; payload aliases).
const jointCca = scNameKey.find(n => n.site_name === 'joint CCA')!;
need(jointCca.alias_of?.join() === 'CCA (no training),matched CCA'
  && shared.filter(e => e.aliases?.includes('joint CCA')).map(e => `${e.site_name}/${e.endpoint}`).join() === 'CCA (no training)/u8,CCA (no training)/seen_ba,matched CCA/dry,matched CCA/wet',
  '“joint CCA” is an alias of CCA (no training) and matched CCA');
export const aliasWords = (n: ScNameKey, locale: Locale): string | undefined => n.alias_of?.length
  ? (locale === 'zh' ? `${n.alias_of.map(a => scName(a, locale)).join('、')}的别名` : `an alias of ${n.alias_of.map(a => scName(a, locale)).join(' and ')}`)
  : undefined;
export const cardsOfName = (n: ScNameKey): NewCard[] => [...new Set(n.codes.map(c => cardOfStudy(c.study)))].sort((a, b) => a - b);

// --- Training, in words -----------------------------------------------------------------------------------------
const TRAINING: Record<string, Record<Locale, string>> = {
  'no training': { en: 'no training', zh: '无需训练' },
  'ridge fitted on source people': { en: 'ridge fitted on the source people', zh: '在源被试上拟合的岭回归' },
  'MLP trained on source people': { en: 'MLP trained on the source people', zh: '在源被试上训练的 MLP' },
  'BETA heads, run unchanged': { en: 'BETA heads, run unchanged', zh: 'BETA 上的分类头，原样运行' },
};
export function trainingWords(t: string, locale: Locale): string {
  need(t in TRAINING, `words for the training "${t}"`);
  return TRAINING[t][locale];
}

// --- Interval methods, card by card --------------------------------------------------------------------------------
const CONDITIONAL: Record<string, Record<Locale, string>> = {
  'the fixed training and fold procedure': { en: 'conditional on the fixed training and fold procedure', zh: '以固定的训练与分折流程为条件' },
  'the fixed 35 source heads of each learned arm': { en: 'conditional on the fixed 35 source heads of each learned arm', zh: '以每个学习组固定的 35 个源分类头为条件' },
};
const PAIRED: Record<string, Record<Locale, string>> = {
  'arms, with each person’s five rotations kept together': { en: 'paired across arms, with each person’s five rotations kept together', zh: '在各组之间配对，每名被试的五个轮换放在一起抽样' },
  'methods and both sensors (one set of draws)': { en: 'paired across methods and both sensors, one set of draws', zh: '在各方法与两种电极之间配对，共用一组抽样' },
  'methods, cells and rotations within each sampled person': { en: 'paired across methods, cells and rotations within each sampled person', zh: '在每名抽中的被试内部，跨方法、单元格与轮换配对' },
};
const SHARED_DRAWS: Record<string, Record<Locale, string>> = {
  'Wearable-102 dry and wet share one set of person draws': { en: 'Wearable-102 dry and wet share one set of person draws', zh: 'Wearable-102 的干电极与湿电极共用一组被试抽样' },
};
for (const [k, m] of [['CONDITIONAL', CONDITIONAL], ['PAIRED', PAIRED], ['SHARED_DRAWS', SHARED_DRAWS]] as const)
  for (const [en, w] of Object.entries(m)) need(digitsOf(en) === digitsOf(w.zh), `${k}: the Chinese of "${en}" carries its digits`);
interface IntervalMethod { card: NewCard; study: ScStudy; method: string; draws: number; seed?: number; seeds?: Record<string, number>; level: number;
  conditional_on?: string; paired_across?: string; shared_draws?: string; family?: { comparisons: number; adjustment: string; level: number }; equivalence?: { level: number; margin: number } }
export const intervalMethods = sc.interval_methods as unknown as IntervalMethod[];
need(intervalMethods.map(m => `${m.card}:${m.study}`).join() === placements.flatMap(p => p.studies.map(s => `${p.card}:${s}`)).join(),
  'one interval method per study, in card order');
need(intervalMethods.every(m => m.method === 'paired person bootstrap, percentile interval' && m.level === 0.95
  && JSON.stringify(studies[m.study].interval_method) === JSON.stringify(Object.fromEntries(Object.entries(m).filter(([k]) => !['card', 'study'].includes(k))))),
  'every study: 95% percentile intervals from a paired person bootstrap, as its block states');
const adj = sc.interval_adjustment as any;
export const bonferroni = adj.adjusted.find((a: any) => a.adjustment === 'Bonferroni');
export const marginTest = adj.adjusted.find((a: any) => a.margin !== undefined);
need(adj.other_intervals_adjusted === false && adj.adjusted.length === 2 && bonferroni.card === 12 && bonferroni.comparisons === 9
  && Math.abs(bonferroni.level - (1 - 0.05 / 9)) < 1e-12 && marginTest.card === 13 && marginTest.level === 0.9 && marginTest.margin === 0.005
  && studies.harmonic_gap.family.comparisons === 9 && studies.harmonic_gap.family.members.length === 9 && studies.harmonic_gap.family.adjustment === 'Bonferroni'
  && studies.fixed_decay.equivalence.interval_level === 0.9 && studies.fixed_decay.equivalence.margin === 0.005,
  'card 12’s nine-comparison Bonferroni family and card 13’s 90% margin test are the only adjusted intervals');
/** Number words, for counts the copy says in words. */
const WORDS: Record<Locale, string[]> = {
  en: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen'],
  zh: ['零', '一', '两', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四'],
};
export function said(n: number, locale: Locale): string { need(WORDS[locale][n] !== undefined, `a word for ${n}`); return WORDS[locale][n]; }
const imPath = (i: number) => ['interval_methods', i];
/** One study's interval method, as a clause: draws as a figure, seeds as printed, the conditions in words. */
export function intervalText(id: ScStudy, locale: Locale): Bit[] {
  const i = intervalMethods.findIndex(m => m.study === id), m = intervalMethods[i], zh = locale === 'zh';
  const seeds = m.seed !== undefined ? (zh ? `（种子 ${m.seed}）` : ` (seed ${m.seed})`)
    : zh ? `（种子：BETA ${m.seeds!.BETA}，Wearable-102 ${m.seeds!['Wearable-102']}）` : ` (seeds ${m.seeds!.BETA} for BETA and ${m.seeds!['Wearable-102']} for Wearable-102)`;
  need(m.seed !== undefined || (m.seeds && Object.keys(m.seeds).join() === 'BETA,Wearable-102'), `${id}: its seeds`);
  const tail: Bit[] = [];
  for (const [k, words] of [['conditional_on', CONDITIONAL], ['paired_across', PAIRED], ['shared_draws', SHARED_DRAWS]] as const) {
    const v = (m as any)[k];
    if (v === undefined) continue;
    need(v in words, `words for ${id}'s ${k} "${v}"`);
    tail.push(zh ? '；' : '; ', words[v][locale]);
  }
  if (m.family) tail.push(...(zh
    ? ['；主要比较族的 ', countAt(...imPath(i), 'family', 'comparisons'), ' 个比较使用 Bonferroni 校正的 ', figAt([...imPath(i), 'family', 'level'], 'pct2'), ' 区间']
    : ['; the primary family’s ', countAt(...imPath(i), 'family', 'comparisons'), ' comparisons use Bonferroni-adjusted ', figAt([...imPath(i), 'family', 'level'], 'pct2'), ' intervals']));
  if (m.equivalence) tail.push(...(zh
    ? ['；主要对比的界值检验使用 ', figAt([...imPath(i), 'equivalence', 'level'], 'pct0'), ' 区间，界值为 ', figAt([...imPath(i), 'equivalence', 'margin'], 'pm1')]
    : ['; the primary contrast’s margin test uses a ', figAt([...imPath(i), 'equivalence', 'level'], 'pct0'), ' interval against a margin of ', figAt([...imPath(i), 'equivalence', 'margin'], 'pm1')]));
  return zh
    ? ['95% 百分位区间来自以被试为单位的 ', countAt(...imPath(i), 'draws'), ' 次配对 bootstrap 抽样', seeds, ...tail]
    : ['95% percentile intervals from ', countAt(...imPath(i), 'draws'), ' paired person bootstrap draws', seeds, ...tail];
}
/** The study's label inside a card that reads two studies (card 10). */
export const STUDY_LABEL: Partial<Record<ScStudy, Record<Locale, string>>> = {
  harmonic_pooling: { en: 'BETA', zh: 'BETA' },
  harmonic_pooling_wearable: { en: 'Wearable-102', zh: 'Wearable-102' },
};

// --- What was not run --------------------------------------------------------------------------------------------
const NOT_RUN: Record<string, Record<Locale, string>> = {
  'raw-time learned cell': { en: 'a learned cell on the raw time series', zh: '在原始时间序列上的学习单元' },
  'cross-harmonic second-order terms': { en: 'second-order terms across harmonics', zh: '跨谐波的二阶项' },
  'conventional averaged coherence estimator': { en: 'a conventional averaged (Welch) coherence estimator', zh: '常规的平均（Welch）相干估计' },
  'neural-network head': { en: 'a neural-network head', zh: '神经网络分类头' },
  'equivalence margin for the eigenvalue head against the harmonic sum': { en: 'an equivalence margin for the eigenvalue head against the harmonic sum', zh: '特征值分类头相对谐波求和的等效界值' },
  'equivalence margin': { en: 'an equivalence margin', zh: '等效界值' },
  'paired seen-32 contrasts': { en: 'paired contrasts on the seen 32-way task', zh: '见过频率 32 选 1 任务上的配对对比' },
  'target fitting, target scaling or head selection': { en: 'fitting, scaling or selecting heads on the target data', zh: '在目标数据上拟合、缩放或挑选分类头' },
  'one-factor attribution of units, window, reference, hardware or cohort': { en: 'attributing a change to one factor: units, window, reference, hardware or cohort', zh: '把变化归因于单个因素：单位、时间窗、参考、硬件或队列' },
  'minimum practical margin': { en: 'a minimum practical margin', zh: '最小实用界值' },
  'ablation of the filter bank, the harmonic count and the pooling': { en: 'ablations of the filter bank, the harmonic count and the pooling', zh: '对滤波器组、谐波数与汇总方式的消融' },
  'online performance or information transfer rate': { en: 'online performance or information transfer rate', zh: '在线性能或信息传输率' },
  'a physical four-electrode headset': { en: 'a physical four-electrode headset', zh: '实体的四电极头戴设备' },
  'a learned head on the same statistics': { en: 'a learned head on the same statistics', zh: '在同样统计量上的学习型分类头' },
  'eigenvector stability, source separation or a physiological intervention': { en: 'eigenvector stability, source separation or a physiological intervention', zh: '特征向量稳定性、源分离或生理干预' },
  'other exponents, offsets or harmonic counts': { en: 'other exponents, offsets or harmonic counts', zh: '其他指数、偏移量或谐波数' },
  'a pre-stimulus alpha or noise measurement': { en: 'a pre-stimulus alpha or noise measurement', zh: '刺激前的 alpha 或噪声测量' },
  'a weight search or frequency-dependent normalization': { en: 'a weight search or frequency-dependent normalisation', zh: '权重搜索或随频率变化的归一化' },
};
for (const id of SC_STUDIES) for (const x of studies[id].not_run as { item: string; run_in: string | null }[])
  need(x.item in NOT_RUN && x.run_in === null, `words for ${id}'s not-run item "${x.item}"`);
/** A card's not-run items, without repeats (card 10's two blocks both list the equivalence margin). */
export const notRunOf = (n: NewCard, locale: Locale): string[] =>
  [...new Set(placementOf(n).studies.flatMap(id => (studies[id].not_run as { item: string }[]).map(x => x.item)))].map(x => NOT_RUN[x][locale]);

// --- Engineering disclosures -------------------------------------------------------------------------------------
const DISCLOSURE: Record<string, Record<Locale, string>> = {
  'a package metadata and module version declaration that did not match, corrected before BETA was processed': {
    en: 'a package’s metadata and its module version declaration did not match and were corrected before BETA was processed',
    zh: '一个软件包的元数据与其模块版本声明不一致，在处理 BETA 之前已更正' },
  'float32 centring in a scalar identity diagnostic, corrected to float64 with the tolerances unchanged': {
    en: 'the centring in a scalar identity diagnostic ran in float32 and was corrected to float64, with the tolerances unchanged',
    zh: '一项标量恒等式诊断中的中心化原以 float32 计算，已改为 float64，容差不变' },
  'the frozen zero-channel-energy rule enforced where squaring the channel energy underflows, covered by a synthetic regression test': {
    en: 'the frozen zero-channel-energy rule is now enforced where squaring the channel energy underflows, covered by a synthetic regression test',
    zh: '冻结的零通道能量规则在通道能量平方下溢时也得到执行，并有合成数据的回归测试覆盖' },
  'an initial synthetic test suite timed out and is not counted as a pass; a bounded synthetic-only rerun passed all its tests': {
    en: 'an initial synthetic test suite timed out and is not counted as a pass; a bounded rerun on synthetic data only passed all {n} of its tests',
    zh: '最初的一套合成数据测试超时，不算作通过；之后一次只用合成数据、限定范围的重跑通过了全部 {n} 项测试' },
};
export interface Disclosure { card: NewCard; stage: string; what: string; [k: string]: unknown }
export const disclosures = sc.engineering_disclosures as unknown as Disclosure[];
need(disclosures.map(d => d.card).join() === '8,8,9,9' && disclosures.every(d => d.what in DISCLOSURE && d.scientific_protocol_changed !== true)
  && disclosures.filter(d => d.card === 8).every(d => d.stage === 'before scoring' && d.supervised_accuracy_used === false && d.scientific_protocol_changed === false)
  && disclosures.filter(d => d.card === 9).every(d => d.stage === 'before execution')
  && disclosures[2].real_inputs_processed_before === false && disclosures[3].counted_as_pass === false,
  'two corrections before card 8 scored anything, and card 9’s edge correction and timed-out suite before execution');
need(studies.xspec.limitations_keys.includes('pre_score_engineering_corrections') && studies.xspec.checks.pre_score_corrections.count === 2
  && studies.coherence_eigen.limitations_keys.includes('zero_energy_edge_fix') && studies.coherence_eigen.limitations_keys.includes('synthetic_suite_timeout_not_a_pass'),
  'the disclosures are the studies’ own');
/** A disclosure in words; the rerun's test count is a figure. */
export function disclosureBits(i: number, locale: Locale): Bit[] {
  const t = DISCLOSURE[disclosures[i].what][locale];
  if (!t.includes('{n}')) return [t];
  const [a, b] = t.split('{n}');
  return [a, countAt('engineering_disclosures', i, 'rerun_tests_passed'), b];
}

// --- What is not published ---------------------------------------------------------------------------------------
export const scNotPublished = sc.not_published as string[];
const NOT_PUBLISHED: Record<string, Record<Locale, string>> = {
  'Per-person, per-fold, per-rotation, per-seed and per-window values of any kind, predictions, scores, features, fitted heads and the sealed run files: only cohort levels, paired contrasts with their intervals, gap statistics, decision-change shares, check counts and CPU component medians are published.': {
    en: 'Per-person, per-fold, per-rotation, per-seed and per-window values of any kind, predictions, scores, features, fitted heads and the sealed run files: only cohort levels, paired contrasts with their intervals, gap statistics, decision-change shares, check counts and CPU component medians are published.',
    zh: '任何逐人、逐折、逐轮换、逐种子或逐时间窗的数值，以及预测、分数、特征、拟合好的分类头和封存的运行文件：只发布队列层面的水平、配对对比及其区间、差距统计量、决策变化比例、检查计数与 CPU 组件计时的中位数。' },
  'Per-frequency values of any kind, including the reference check’s candidate frequencies: the check is published as counts.': {
    en: 'Per-frequency values of any kind, including the reference check’s candidate frequencies: the check is published as counts.',
    zh: '任何逐频率的数值，包括参考检查所涉及的候选频率：该检查只以计数发布。' },
  'The cross-spectral per-seed MLP accuracies, the canary accuracies and the random-pairing accuracies of cards 8 and 9.': {
    en: 'The cross-spectral MLP’s per-seed accuracies, and the canary and random-pairing accuracies of cards 8 and 9.',
    zh: '互谱 MLP 各随机种子的准确率，以及卡片 8 与 9 的金丝雀检查和随机配对准确率。' },
  'The fixed-decay retrospective gap-to-gain ratio table and its dry reconstruction.': {
    en: 'Card 13’s retrospective gap-to-gain ratio table and its dry reconstruction.',
    zh: '卡片 13 的回溯差距—增益比值表及其干电极重建。' },
  'All-trial decision counts: the harmonic-gap decision changes on BETA held-out are published as shares of the 11,200 decisions; the Wearable-102 decision changes and the fixed-decay and rising-weight transitions are not published.': {
    en: 'Decision counts over all trials: card 12’s decision changes on BETA held-out frequencies are published as shares of the 11,200 decisions; the Wearable-102 decision changes and the transitions of cards 13 and 14 are not published.',
    zh: '全部试次上的决策计数：卡片 12 在 BETA 留出频率上的决策变化以 11,200 个决策中的比例发布；Wearable-102 上的决策变化，以及卡片 13 与 14 的决策转变，均不发布。' },
  'The harmonic-gap Delta means and the margins against the strongest joint-CCA distractor.': {
    en: 'Card 12’s Delta means and the margins against the strongest joint-CCA distractor.',
    zh: '卡片 12 的 Delta 均值，以及相对最强联合 CCA 干扰项的余量。' },
  'Run times of whole evaluations and audits, memory and process identifiers; the CPU-time readings of the component measurements and every host, processor, system and runtime label.': {
    en: 'Run times of whole evaluations and audits, memory and process identifiers; the CPU-time readings of the component measurements, and every host, processor, system and runtime label.',
    zh: '整轮评测与审计的运行时间、内存与进程标识；组件测量中的 CPU 时间读数，以及任何主机、处理器、系统与运行环境的标签。' },
  'Predictions from the comment thread on cards 8 to 14: each new card states its prespecified criteria only, and the thread’s prediction stays on card 4 of the released file.': {
    en: 'Predictions from the comment thread on cards 8 to 14: each of these cards states only its prespecified criteria, and the thread’s prediction stays on card 4.',
    zh: '评论串对卡片 8 至 14 的预测：这几张卡片只陈述各自预先设定的标准，讨论串中的预测只出现在卡片 4。' },
  'The commenter’s name.': { en: 'The commenter’s name.', zh: '评论者的名字。' },
  'The handoffs, protocols, freezes, receipts, reviews and approvals themselves: each is pinned by SHA-256 in the release manifest and checked by the export; several carry private storage paths.': {
    en: 'The handoffs, protocols, freezes, receipts, reviews and approvals themselves: each is pinned by SHA-256 in the release manifest and checked by the export; several carry private storage paths.',
    zh: '交接文档、协议、冻结记录、回执、审查与批准记录本身：每一份都在发布清单中以 SHA-256 固定，并由导出流程核对；其中几份含有私有存储路径。' },
};
for (const x of scNotPublished) need(x in NOT_PUBLISHED, `words for the not-published item "${x.slice(0, 60)}…"`);
for (const [en, w] of Object.entries(NOT_PUBLISHED)) need(digitsOf(w.en) === digitsOf(w.zh), `the Chinese of "${en.slice(0, 40)}…" carries its digits`);
export const notPublishedWords = (x: string, locale: Locale) => NOT_PUBLISHED[x][locale];
/**
 * The released file's not-published items that this file replaces: card 8's status entry (D28) and the measured-compute
 * item, which this file narrows to whole-evaluation run times now that card 11 prints CPU component timings (D25).
 */
export const RELEASED_REPLACED: Record<string, string> = {
  'The cross-spectral round: in progress at the freeze; its status card carries no figures, and it ships as its own file and release.':
    'card 8 now carries the cross-spectral round’s results (D28)',
  'Measured compute: run times, memory and process identifiers.':
    'Run times of whole evaluations and audits, memory and process identifiers; the CPU-time readings of the component measurements and every host, processor, system and runtime label.',
};
need(Object.keys(RELEASED_REPLACED).every(x => (released.not_published as string[]).includes(x))
  && scNotPublished.includes(RELEASED_REPLACED['Measured compute: run times, memory and process identifiers.']),
  'the two released items this file replaces, and the narrower item it adds');

// --- Rights and credits --------------------------------------------------------------------------------------------
export const scRights = sc.rights as any;
export const fbcca = scRights.credits.fbcca;
need(fbcca.method_page === '/methods/fbcca/' && fbcca.short === 'Chen et al. 2015' && fbcca.code_distributed === false
  && fbcca.cards.join() === '11,13' && fbcca.used_for === studies.practical_settings.design.fbcca.description.en
  && /^https:\/\/doi\.org\/10\.1088\/1741-2560\/12\/4\/046008$/.test(fbcca.reference_url), 'FBCCA: Chen et al. 2015, its method page, the recipe card 11 ran');
need(scRights.datasets.beta.license === (released.rights as any).datasets.beta.license && scRights.datasets.beta.rights_record === 'reused unchanged from the released record'
  && scRights.datasets.beta.citation === (released.rights as any).datasets.beta.citation
  && scRights.datasets.wearable_102.paper_citation === (released.rights as any).datasets.wearable_102.paper_citation
  && scRights.datasets.wearable_102.license === (released.rights as any).datasets.wearable_102.license
  && scRights.datasets.beta.cards.join() === NEW_CARDS.join() && scRights.datasets.wearable_102.cards.join() === newCardsOf('wearable_12').join(),
  'BETA and Wearable-102 keep their released records; BETA under every new card, Wearable-102 under the cards that report it');
need(/no code or weights are distributed/.test(sc.release_record.rights), 'no code or weights are distributed');

// --- The page-wide facts --------------------------------------------------------------------------------------------
export const betaPeople = studies.xspec.design.dataset.people as number;
export const wearPeople = studies.harmonic_pooling_wearable.design.dataset.people as number;
need(SC_STUDIES.every(id => { const d = studies[id].design; const b = d.dataset?.name === 'BETA' ? d.dataset : d.datasets?.BETA;
  return !b || b.people === betaPeople; }) && betaPeople === (released as any).cohort.people && wearPeople === (released as any).wearable.people
  && studies.harmonic_gap.design.datasets['Wearable-102'].people === wearPeople,
  'the BETA cohort and Wearable-102 of the released cards, the same people on every card');
// Repeated analyses of data already studied: every study says so (stated once on the page, in the scope line).
const REUSE_KEY: Record<ScStudy, string> = { xspec: 'same_cohort_follow_up', coherence_eigen: 'same_cohort_follow_up', harmonic_pooling: 'same_cohort_follow_up',
  harmonic_pooling_wearable: 'not_pristine_external_validation', practical_settings: 'same_cohort_follow_up', harmonic_gap: 'reused_benchmarks',
  fixed_decay: 'reused_datasets', rising_weights: 'reused_cohorts' };
need(SC_STUDIES.every(id => studies[id].limitations_keys.includes(REUSE_KEY[id])), 'every study is a repeated analysis of data already studied, not external replication');
/** Guard a sentence on a study's limitation key. */
export const keyed = (id: ScStudy, ...keys: string[]) => need(keys.every(k => studies[id].limitations_keys.includes(k)), `${id} carries ${keys.join(', ')}`);

// --- Sentences and table cells ----------------------------------------------------------------------------------------
const P = (locale: Locale) => (locale === 'zh' ? ['（', '）'] : [' (', ')']);
export const toWord = (locale: Locale) => (locale === 'zh' ? ' 至 ' : ' to ');
/** A level in a sentence: "68.03% (63.39%–73.05%)", or "57.45% (card 5)" with a link to the card carrying its interval. */
export function lvBits(l: LevelFigs, locale: Locale): Bit[] {
  const [o, c] = P(locale);
  return l.iv ? [l.est, o, l.iv[0], '–', l.iv[1], c] : l.home !== cardOfStudy(l.study) ? [l.est, o, cardLink(l.home, locale, true), c] : [l.est];
}
/** A range cell (CPU component medians): the median (class="metric"), then the fastest and slowest call. */
export function rangeCell(med: ScFig, lo: ScFig, hi: ScFig, locale: Locale): string {
  return figHtml(med, 'metric') + `<span class="interval">${toHtml([locale === 'zh' ? '范围 ' : 'range ', lo, '–', hi])}</span>`;
}
/** A level without its interval, naming the card that carries it when that is another card. */
export function lvShort(l: LevelFigs, locale: Locale, here: number): Bit[] {
  const [o, c] = P(locale);
  return l.home === here ? [l.est] : [l.est, o, cardLink(l.home, locale, true), c];
}
/** A paired difference in a sentence: "+10.58 pp (+9.05 to +12.28)". */
export function ctBits(x: ContrastFigs, locale: Locale): Bit[] {
  const [o, c] = P(locale);
  return [x.est, o, x.lo, toWord(locale), x.hi, c];
}
const IV_WORDS: Record<Locale, { iv: string; home: string }> = {
  en: { iv: 'interval', home: 'interval on ' },
  zh: { iv: '区间', home: '区间见' },
};
/** A table cell for a level: the estimate (class="metric"), then its interval, or the card that carries it. */
export function levelCell(l: LevelFigs, locale: Locale, ivLevel: Bit[] = ['95%']): string {
  const w = IV_WORDS[locale];
  return figHtml(l.est, 'metric') + (l.iv
    ? `<span class="interval">${toHtml([...ivLevel, ' ', w.iv, ' ', l.iv[0], '–', l.iv[1]])}</span>`
    : l.home !== cardOfStudy(l.study) ? `<span class="interval">${toHtml([w.home, cardLink(l.home, locale, true)])}</span>` : '');
}
/** A table cell for a paired difference: the estimate (class="metric"), then its own interval. */
export function contrastCell(x: ContrastFigs, locale: Locale, ivLevel: Bit[] = ['95%']): string {
  return figHtml(x.est, 'metric') + `<span class="interval">${toHtml([...ivLevel, ' ', IV_WORDS[locale].iv, ' ', x.lo, toWord(locale), x.hi])}</span>`;
}
/** A table cell for any other figure with an interval (gap statistics, win fractions, allocation shares). */
export function figCell(est: ScFig, lo: ScFig, hi: ScFig, locale: Locale, ivLevel: Bit[] = ['95%'], sep = '–'): string {
  return figHtml(est, 'metric') + `<span class="interval">${toHtml([...ivLevel, ' ', IV_WORDS[locale].iv, ' ', lo, sep, hi])}</span>`;
}
const ROLE: Record<string, Record<Locale, string>> = {
  primary: { en: 'primary', zh: '主要' },
  secondary: { en: 'secondary', zh: '次要' },
  rounding_check: { en: 'rounding check', zh: '舍入检查' },
};
export function roleWords(role: string, locale: Locale): string { need(role in ROLE, `words for the role ${role}`); return ROLE[role][locale]; }
const TASK: Record<string, Record<Locale, string>> = {
  u8: { en: 'BETA held-out', zh: 'BETA 留出' },
  seen_ba: { en: 'BETA seen 32-way', zh: 'BETA 见过的 32 选 1' },
  dry: { en: 'Wearable-102 dry', zh: 'Wearable-102 干电极' },
  wet: { en: 'Wearable-102 wet', zh: 'Wearable-102 湿电极' },
};
export const taskOf = (key: string) => key.slice(key.lastIndexOf('/') + 1);
export function taskWords(key: string, locale: Locale): string { const t = taskOf(key); need(t in TASK, `words for the task ${t}`); return TASK[t][locale]; }
/** A contrast's name: "left − right", each by its site name. */
export function contrastName(id: ScStudy, x: ContrastFigs, locale: Locale): string {
  return `${nameOf(id, codeOfKey(x.left), locale)} − ${nameOf(id, codeOfKey(x.right), locale)}`;
}
export const codeOf = codeOfKey;
