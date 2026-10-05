/**
 * The v9 foundation-model findings as the topic pages print them (release
 * foundation-models-update-20261004, owner approved 2026-10-04): the sleep and
 * BETA results and the EEGMAT adaptation on does-pretraining-help, with REVE Base
 * against Large and the masking ablation; BETA at eight and four electrodes and
 * the six-channel sleep column on fewer-electrodes.
 *
 * Nothing is computed here that the export does not state. Every figure is a `Fig`
 * naming the served file it is a leaf of (check-workbench.mjs re-reads it): v9
 * matrix figures from the per-protocol CSVs (foundation-models.ts), adaptation
 * arms and the export's own comparisons — above, overlapping or below a published
 * row; Large minus Base; four minus eight electrodes; which masking pairs separate
 * — from foundation-models-update.json, and the released rows they are read
 * against from experiments.json, as model-adaptation prints the matrix readout.
 * Two readings are derived, and both only from intervals, by the export's rule:
 * the chance flag (the core rule, as the protocol pages print it) and, for the
 * released rows on fewer-electrodes, whether their eight- and four-electrode
 * intervals overlap — the export states that comparison for its own rows only.
 *
 * The claims the pages make in words ("three encoders above every published row
 * on sleep", "none above standard CCA on BETA") are derived here from the export's
 * relations and checked when the site builds, so a changed export cannot leave a
 * sentence behind that it no longer supports.
 *
 * `TOPIC_PRINTS` lists, per topic, which released and v9 rows the page prints;
 * entities.ts reads it for the "Measured on" line, and check-workbench.mjs
 * re-derives it from the built pages.
 */
import data from './mvp.json';
import fmJson from './foundation-models-update.json';
import { FM_ADAPTATION_ANCHOR, FM_ANCHOR, FM_JSON, fmAblation, fmAdaptation, fmAdaptationContext, fmMatrixModels,
         fmModelById, fmRowsByProtocol, type FmAdaptation, type FmModel, type FmRow } from './foundation-models';
import type { Fig, Fmt } from './entities';

const V9 = (fmJson as any).results['foundation-models-v9'];
const MVP = 'experiments.json';
const fig = (raw: number, fmt: Fmt, src: string): Fig => ({ raw, fmt, src });

export type Relation = 'above' | 'overlap' | 'below';
export type ChanceFlag = 'at-or-below' | 'interval-reaches' | null;
/** The core rule: at or below chance, else an interval reaching it (the protocol pages print the same flags). */
const chanceFlagOf = (y: number, lo: number | undefined, chance: number | null): ChanceFlag =>
  chance === null ? null : y <= chance ? 'at-or-below' : lo !== undefined && lo <= chance ? 'interval-reaches' : null;
/** The export's rule for two marginal intervals. */
const overlaps = (a: [number, number], b: [number, number]) => a[0] <= b[1] && b[0] <= a[1];

/** A protocol's cohort and chance level as the v9 export states them (people a count, chance a proportion). */
export function protocolFacts(track: string): { people: Fig; chance: Fig } {
  const p = V9.protocols.find((x: any) => x.id === track);
  if (!p || p.chance_level == null) throw new Error(`foundation-topics.ts: the export has no chance level for ${track}`);
  return { people: fig(p.people, 'count', FM_JSON), chance: fig(p.chance_level, 'pct1', FM_JSON) };
}

/* --- Released rows, as the core matrix published them ------------------------------------- */

/** The method pages of the released rows a topic prints (spectral ridge has none). */
const CORE_SLUG: Record<string, string> = { cca: 'cca', eegnet: 'eegnet', labram: 'labram', cbramod: 'cbramod' };
export interface CoreRow { track: string; id: string; name: string; slug?: string; ba: Fig; interval: [Fig, Fig]; chance: Fig; chanceFlag: ChanceFlag }
export function coreRow(track: string, id: string): CoreRow {
  const t = data.tracks.find(x => x.id === track);
  const r = t?.rows.find(x => x.id === id) as { id: string; name: string; y: number; interval?: number[] | null } | undefined;
  if (!t || !r || !r.interval || t.chanceLevel == null) throw new Error(`foundation-topics.ts: no released row ${track} / ${id} with an interval`);
  return { track, id, name: r.name, slug: CORE_SLUG[id], ba: fig(r.y, 'pct1raw', MVP),
           interval: [fig(r.interval[0], 'pct1raw', MVP), fig(r.interval[1], 'pct1raw', MVP)],
           chance: fig(t.chanceLevel, 'pct1raw', MVP), chanceFlag: chanceFlagOf(r.y, r.interval[0], t.chanceLevel) };
}

/* --- v9 rows ------------------------------------------------------------------------------ */

/** One v9 matrix cell: the protocol CSV's row, with the chance flag its protocol page prints. */
export const fmCell = (track: string, model: string): FmRow => {
  const r = fmRowsByProtocol[track]?.find(x => x.model.id === model);
  if (!r) throw new Error(`foundation-topics.ts: no v9 row ${model} on ${track}`);
  return r;
};

/** The export's comparison of one v9 row with the three published rows of its protocol. */
export interface VsPublished { labram: Relation; cbramod: Relation; best: Relation; bestRow: string; bestName: string }
export function vsPublished(model: string, track: string): VsPublished {
  const c = V9.comparisons.vs_published_rows.find((x: any) => x.model === model && x.protocol === track);
  if (!c) throw new Error(`foundation-topics.ts: the export compares no ${model} on ${track}`);
  return { labram: c.labram.relation, cbramod: c.cbramod.relation, best: c.best_non_foundation.relation,
           bestRow: c.best_non_foundation.row, bestName: c.best_non_foundation.name };
}

export interface TopicRow { cell: FmRow; vs: VsPublished }
const matrixOn = (track: string): TopicRow[] => fmMatrixModels.map(m => ({ cell: fmCell(track, m.id), vs: vsPublished(m.id, track) }));

/* --- Sleep staging: the only protocol where new cells clear every published row --------------- */

export const SLEEP = 'sleep-scalp';
/** Every released sleep row (spectral ridge, LaBraM, CBraMod, EEGNet), in the matrix order. */
export const sleepPublished: CoreRow[] = data.tracks.find(t => t.id === SLEEP)!.rows.map(r => coreRow(SLEEP, r.id));
export const sleepRows: TopicRow[] = matrixOn(SLEEP);
/**
 * Above LaBraM, CBraMod and the best released non-foundation row by the export's
 * relations — and so above every released sleep row, which the build confirms
 * from the intervals (EEGNet's included), in the export's family order.
 */
export const sleepAboveAll: TopicRow[] = sleepRows.filter(r => r.vs.labram === 'above' && r.vs.cbramod === 'above' && r.vs.best === 'above');
for (const r of sleepAboveAll) for (const p of sleepPublished)
  if (!(r.cell.interval![0].raw > p.interval[1].raw))
    throw new Error(`foundation-topics.ts: ${r.cell.model.id} is not above the released ${p.name} sleep row`);
if (!sleepAboveAll.length) throw new Error('foundation-topics.ts: the sleep sentence names encoders above every released row; the export has none');
/** The best non-foundation row the export compares against on sleep. */
export const sleepBest: CoreRow = sleepPublished.find(p => p.id === sleepRows[0].vs.bestRow)!;
/** The page says sleep is the only scored protocol where a new row — ablation siblings included — clears that row. */
export const aboveBestElsewhere = V9.comparisons.vs_published_rows.filter((x: any) => x.protocol !== SLEEP && x.best_non_foundation.relation === 'above');
if (aboveBestElsewhere.length) throw new Error('foundation-topics.ts: a new row clears the best published row outside sleep; the sleep sentence says it does not');

/* --- BETA: above CBraMod, not above training-free CCA --------------------------------------- */

export const BETA8 = 'beta-8ch', BETA4 = 'beta-4ch';
/** The released BETA rows, in the matrix order (standard CCA, spectral ridge, LaBraM, CBraMod, EEGNet). */
export const betaPublished = (track: string): CoreRow[] => data.tracks.find(t => t.id === track)!.rows.map(r => coreRow(track, r.id));
export const betaRows: TopicRow[] = matrixOn(BETA8);
export const betaAboveCbramod: TopicRow[] = betaRows.filter(r => r.vs.cbramod === 'above');
/** The best released non-foundation row on BETA: standard CCA, which needs no training. */
export const betaBest: CoreRow = coreRow(BETA8, betaRows[0].vs.bestRow);
if (betaRows.some(r => r.vs.best === 'above') || betaBest.id !== 'cca')
  throw new Error('foundation-topics.ts: the page says no new BETA row lies above standard CCA; the export no longer says so');
/** The three masking siblings on BETA, which the ablation table prints: above CBraMod too, as the page says. */
export const betaAblationAboveCbramod = fmAblation.checkpoints.filter(id => fmModelById[id].panel !== 'matrix' && vsPublished(id, BETA8).cbramod === 'above');
if (betaAblationAboveCbramod.length !== fmAblation.checkpoints.length - 1)
  throw new Error('foundation-topics.ts: the page says all three masking siblings lie above CBraMod on BETA; the export no longer says so');
/** ST-EEGFormer: its BETA cells are in the authors' list and still below CBraMod, as the page says. */
export const betaExposedBelow = betaRows.filter(r => r.cell.exposure.status === 'exposed');
if (!betaExposedBelow.length || betaExposedBelow.some(r => r.vs.cbramod !== 'below' || r.cell.model.slug !== 'st-eegformer'))
  throw new Error('foundation-topics.ts: the page says the exposed BETA cells are ST-EEGFormer\'s and lie below CBraMod; the export no longer says so');

/* --- EEGMAT: one fixed recipe on one task ------------------------------------------------- */

const ADAPT_TRACK = 'arithmetic-rest';
/** The frozen ridge readout of the matrix on the same people and folds: the CSV for a v9 encoder, the released row for LaBraM. */
export interface AdaptRow {
  id: string; name: string; slug: string; context: boolean; model?: FmModel;
  ridge: { ba: Fig; interval: [Fig, Fig]; chanceFlag: ChanceFlag };
  frozen: FmAdaptation['frozen'] & { chanceFlag: ChanceFlag };
  lora: FmAdaptation['lora'] & { chanceFlag: ChanceFlag };
  change: FmAdaptation['change'];
  exposure: 'not_exposed' | 'exposed' | 'unknown';
}
const ADAPT_CHANCE = V9.eegmat_adaptation.chance_level as number;
const withFlag = (a: FmAdaptation['frozen']) => ({ ...a, chanceFlag: chanceFlagOf(a.ba.raw, a.interval[0].raw, ADAPT_CHANCE) });
export const adaptRows: AdaptRow[] = [
  (() => {
    const core = coreRow(ADAPT_TRACK, 'labram');
    return { id: 'labram', name: fmAdaptationContext.model, slug: 'labram', context: true,
             ridge: { ba: core.ba, interval: core.interval, chanceFlag: core.chanceFlag },
             frozen: withFlag(fmAdaptationContext.frozen), lora: withFlag(fmAdaptationContext.lora), change: fmAdaptationContext.change,
             exposure: 'not_exposed' as const };
  })(),
  ...fmAdaptation.map(a => {
    const c = fmCell(ADAPT_TRACK, a.model.id);
    return { id: a.model.id, name: a.model.name, slug: a.model.slug, context: false, model: a.model,
             ridge: { ba: c.primary!, interval: c.interval!, chanceFlag: c.chanceFlag },
             frozen: withFlag(a.frozen), lora: withFlag(a.lora), change: a.change, exposure: a.exposure.status };
  }),
];
/** The adapted encoders whose LoRA change excludes zero, and those whose interval includes it. */
export const adaptResolved = fmAdaptation.filter(a => a.change.excludesZero).map(a => a.model.id);
export const adaptOpen = fmAdaptation.filter(a => !a.change.excludesZero).map(a => a.model.id);
/** SingLEM, the page's example: both frozen readouts reach chance, LoRA does not, and its change excludes zero. */
{
  const s = adaptRows.find(r => r.id === 'singlem');
  if (!s || !s.ridge.chanceFlag || !s.frozen.chanceFlag || s.lora.chanceFlag || !s.change.excludesZero)
    throw new Error('foundation-topics.ts: the SingLEM sentence no longer matches its EEGMAT arms');
}

/* --- REVE Base and Large: a size comparison, marginal intervals only --------------------------- */

export interface SizePair { base: string; large: string; track: string; baseCell: FmRow; largeCell: FmRow; diff: Fig; overlap: boolean }
export const SCORED_TRACKS: string[] = V9.comparisons.masking_ablation.map((x: any) => x.protocol);
const pairs: SizePair[] = V9.comparisons.base_vs_large.map((x: any) => ({
  base: x.base, large: x.large, track: x.protocol, baseCell: fmCell(x.protocol, x.base), largeCell: fmCell(x.protocol, x.large),
  diff: fig(x.large_minus_base, 'pp1', FM_JSON), overlap: x.marginal_intervals_overlap,
}));
export const revePairs = pairs.filter(p => p.base === 'reve-base');
if (revePairs.map(p => p.track).join() !== SCORED_TRACKS.join() || revePairs.some(p => p.diff.raw < 0))
  throw new Error('foundation-topics.ts: the page says REVE Large is at or above Base on every scored protocol; the export no longer says so');
/** Where each size pair's intervals separate: REVE's, and the two pairs the page says do not show its pattern. */
export const separatedOn = (base: string) => pairs.filter(p => p.base === base && !p.overlap).map(p => p.track);

/* --- Masking ablation: four checkpoints of one study ------------------------------------------- */

export interface MaskingRow { track: string; cells: FmRow[]; separated: [string, string][] }
export const maskingRows: MaskingRow[] = V9.comparisons.masking_ablation.map((x: any) => ({
  track: x.protocol, cells: fmAblation.checkpoints.map(id => fmCell(x.protocol, id)),
  separated: x.non_overlapping_pairs as [string, string][],
}));
export const maskingInseparable = maskingRows.filter(r => !r.separated.length).length;
/** The design of the 2 x 2: which factor each checkpoint sets (the export's checkpoint ids spell it). */
export const maskingFactors = (id: string) => ({ framework: /\/jepa-/.test(id) ? 'JEPA' : 'MAE', geometry: /r9cm/.test(id) ? 'r9cm' : 'rone' });
for (const r of maskingRows) for (const [a, b] of r.separated) {
  const fa = maskingFactors(a), fb = maskingFactors(b);
  if (fa.framework === fb.framework || fa.geometry === fb.geometry)
    throw new Error(`foundation-topics.ts: the page says the separated masking pair changes both factors; ${a} and ${b} share one`);
}

/* --- Fewer electrodes: BETA at eight and four, sleep on six -------------------------------- */

export interface MontageRow { cell8: FmRow; cell4: FmRow; sleep: FmRow; diff: Fig; overlap: boolean; inputFamily: string; model: FmModel }
export const montageRows: MontageRow[] = fmMatrixModels.map(m => {
  const x = V9.comparisons.fewer_electrodes_beta.find((c: any) => c.model === m.id);
  if (!x) throw new Error(`foundation-topics.ts: the export compares no ${m.id} at four and eight electrodes`);
  return { model: m, cell8: fmCell(BETA8, m.id), cell4: fmCell(BETA4, m.id), sleep: fmCell(SLEEP, m.id),
           diff: fig(x.four_minus_eight, 'pp1', FM_JSON), overlap: x.marginal_intervals_overlap, inputFamily: x.input_family };
});
/** The released rows at both montages, with whether their two intervals overlap (the export's rule), and sleep where the method was run. */
export interface MontagePublished { id: string; name: string; slug?: string; r8: CoreRow; r4: CoreRow; sleep?: CoreRow; overlap: boolean }
export const montagePublished: MontagePublished[] = betaPublished(BETA8).map(r8 => {
  const r4 = coreRow(BETA4, r8.id);
  const onSleep = data.tracks.find(t => t.id === SLEEP)!.rows.some(r => r.id === r8.id);
  return { id: r8.id, name: r8.name, slug: r8.slug, r8, r4, sleep: onSleep ? coreRow(SLEEP, r8.id) : undefined,
           overlap: overlaps([r8.interval[0].raw, r8.interval[1].raw], [r4.interval[0].raw, r4.interval[1].raw]) };
});
/** Single-channel and channel-wise encoders: the input families the page reads for a small-montage advantage. */
export const montageNonMontage = montageRows.filter(r => r.inputFamily !== 'montage');
if (montageNonMontage.some(r => r.diff.raw >= 0 || r.overlap))
  throw new Error('foundation-topics.ts: the page says the single-channel and channel-wise encoders lost accuracy at four electrodes; the export no longer says so');
/** The montage encoders above CBraMod on both BETA montages: the comparison the page sets the non-montage ones beside. */
export const montageAboveCbramod = montageRows.filter(r => r.inputFamily === 'montage'
  && vsPublished(r.model.id, BETA8).cbramod === 'above' && vsPublished(r.model.id, BETA4).cbramod === 'above');
/** Standard CCA: the highest four-electrode score, released or new; no new row lies above it. */
export const cca4 = coreRow(BETA4, 'cca');
if (![...montagePublished.map(p => p.r4.ba.raw), ...montageRows.map(r => r.cell4.primary!.raw)].every(v => v <= cca4.ba.raw)
    || montageRows.some(r => vsPublished(r.model.id, BETA4).best === 'above'))
  throw new Error('foundation-topics.ts: the page says standard CCA keeps the highest four-electrode score; it no longer does');
/** New rows whose four-electrode interval overlaps CCA's. */
export const cca4Overlapping = montageRows.filter(r => vsPublished(r.model.id, BETA4).best === 'overlap');

/* --- What each topic prints, for its "Measured on" line ----------------------------------- */

/**
 * The released rows (by protocol and row id) and the v9 rows (by protocol, section
 * anchor and checkpoint id) a topic prints. A v9 matrix row is read with the
 * protocol page's v9 section; an adaptation arm with its EEGMAT section.
 */
export interface TopicPrint { track: string; anchor?: string; core?: string[]; models?: string[] }
const allMatrix = fmMatrixModels.map(m => m.id);
export const TOPIC_PRINTS: Record<string, TopicPrint[]> = {
  'does-pretraining-help': [
    { track: SLEEP, core: sleepPublished.map(r => r.id) },
    { track: SLEEP, anchor: FM_ANCHOR, models: allMatrix },
    { track: BETA8, core: betaPublished(BETA8).map(r => r.id) },
    { track: BETA8, anchor: FM_ANCHOR, models: allMatrix },
    { track: ADAPT_TRACK, core: ['labram'] },
    { track: ADAPT_TRACK, anchor: FM_ADAPTATION_ANCHOR, models: fmAdaptation.map(a => a.model.id) },
    { track: ADAPT_TRACK, anchor: FM_ANCHOR, models: fmAdaptation.map(a => a.model.id) },
    ...SCORED_TRACKS.map(track => ({ track, anchor: FM_ANCHOR, models: ['reve-base', 'reve-large', ...fmAblation.checkpoints] })),
  ],
  'fewer-electrodes': [
    { track: BETA8, core: montagePublished.map(r => r.id) },
    { track: BETA4, core: montagePublished.map(r => r.id) },
    { track: SLEEP, core: montagePublished.filter(r => r.sleep).map(r => r.id) },
    ...[BETA8, BETA4, SLEEP].map(track => ({ track, anchor: FM_ANCHOR, models: allMatrix })),
  ],
};
for (const prints of Object.values(TOPIC_PRINTS)) for (const p of prints) for (const id of p.models ?? [])
  if (!fmModelById[id]) throw new Error(`foundation-topics.ts: no checkpoint ${id}`);
