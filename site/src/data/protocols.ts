/**
 * The core-matrix protocols as pages: /protocols/ and /protocols/<id>/.
 *
 * Why: the home page served one protocol in its HTML and swapped the other
 * seven in with JavaScript (src/scripts/workbench.ts), so seven protocols had no
 * address. A reader on a method page who saw "BETA 10.8%" could not reach the
 * split, the electrodes or the training mode behind it, and a search for
 * "LaBraM BETA 4 channels" had no page to land on.
 *
 * Built from each track exactly as released (mvp.json is byte-identical to
 * /data/experiments.json, and each /data/<id>-protocol.json is the track without
 * its rows). The pages add no number. Every figure is a `Fig` that cites the
 * protocol's own download it is a leaf of — row figures its results CSV,
 * protocol-level figures its protocol JSON — and check-workbench.mjs re-reads
 * both files. Prose (protocol steps, limitation, attribution, notes) is the
 * payload's own English text, printed verbatim and marked lang="en" on the
 * Chinese pages, as on the home page.
 *
 * Never printed: the track's `status`. It still says "Research preview" in the
 * released bytes; that badge came off on 2026-10-01 (src/data/site.ts).
 */
import data from './mvp.json';
import { corrections, requestedCitations, type Correction } from './releases';
import { datasetSlugOf, methodSlugOf, type Fig, type Fmt, type MethodSlug } from './entities';
import { trackTitle, type Locale } from './i18n';

type Track = typeof data.tracks[number];

export interface ProtocolRow {
  id: string;
  name: string;
  family: string;
  methodSlug?: MethodSlug;
  /** Training mode as the payload states it, e.g. "Frozen encoder + ridge head". */
  mode: string;
  channels: Fig;
  people: Fig;
  primary: Fig;
  interval?: [Fig, Fig];
  secondary: Fig;
  seconds: Fig;
  /** Tradeoff protocol only: people whose calibrated threshold always abstains. */
  abstain?: Fig;
  primaryDetail: string;
  secondaryDetail: string;
  /** The home table's chance flags, worded without a second copy of the figure. */
  chanceFlag: 'at-or-below' | 'interval-reaches' | null;
  /** Where the retained seed sits among the seeds run, on the row that was re-run. */
  seedRank: 'highest' | 'lowest' | 'middle' | null;
  note: string;
  modelRights: string;
}

export interface Protocol {
  id: string;
  title: string;
  short: string;
  subtitle: string;
  dataset: string;
  datasetSlug?: string;
  type: 'accuracy' | 'tradeoff';
  subjects: Fig;
  /** Absent on the tradeoff protocol, whose detection is read with false activations. */
  chance?: Fig;
  observations: string;
  exposure: string;
  yLabel: string;
  xLabel: string;
  limitation: string;
  steps: string[];
  selection: string;
  seed?: { model: string; values: Fig[]; mean: Fig; scope: string };
  pretrainingOverlap: string;
  protocolId: string;
  version: string;
  backend: string;
  elapsed: Fig;
  auditSha: string;
  /** Recorded on some protocols only. */
  summarySha?: string;
  protocolSha?: string;
  license: string;
  licenseUrl: string;
  attribution: string;
  privacyReview: string;
  rightsScope: string;
  reviewedAt: string;
  reviewBasis: string[];
  source: string;
  rows: ProtocolRow[];
  /** Matrix methods with no result under this protocol: blank cells, not failures. */
  notRun: { name: string; methodSlug?: MethodSlug }[];
  files: { results: string; protocol: string };
  requested?: { text: string; url: string; basis: string };
  corrections: Correction[];
}

const fig = (raw: number, fmt: Fmt, src: string): Fig => ({ raw, fmt, src });

/** Every method in the matrix, in the order the matrix first meets it, with its page. */
const matrixMethods = [...new Map(data.tracks.flatMap(t => t.rows.map(r => [r.name, methodSlugOf(r.id)] as const))).entries()]
  .map(([name, methodSlug]) => ({ name, methodSlug }));

function build(t: Track): Protocol {
  const results = `${t.id}-results.csv`, protocol = `${t.id}-protocol.json`;
  const tradeoff = t.type === 'tradeoff';
  const chance = (t as { chanceLevel?: number | null }).chanceLevel ?? null;
  const ss = (t as { seedSensitivity?: { model: string; balancedAccuracyPercent: number[]; meanPercent: number; scope: string } }).seedSensitivity;
  const rank = (): ProtocolRow['seedRank'] => {
    if (!ss) return null;
    const v = ss.balancedAccuracyPercent, hi = Math.max(...v), lo = Math.min(...v);
    return v[0] >= hi ? 'highest' : v[0] <= lo ? 'lowest' : 'middle';
  };
  const rows: ProtocolRow[] = t.rows.map(r => {
    const iv = (r as { interval?: number[] | null }).interval ?? null;
    const flag: ProtocolRow['chanceFlag'] = chance === null || tradeoff ? null
      : r.y <= chance ? 'at-or-below' : iv && iv[0] <= chance ? 'interval-reaches' : null;
    return {
      id: r.id, name: r.name, family: r.family, methodSlug: methodSlugOf(r.id), mode: r.mode,
      channels: fig(r.channels, 'count', results), people: fig(r.subjects, 'count', results),
      primary: fig(r.y, 'pct1raw', results),
      interval: iv ? [fig(iv[0], 'pct1raw', results), fig(iv[1], 'pct1raw', results)] : undefined,
      secondary: fig(r.x, tradeoff ? 'pct1raw' : 'num3', results),
      seconds: fig(r.seconds, 's1', results),
      abstain: tradeoff && r.abstain != null ? fig(r.abstain, 'count', results) : undefined,
      primaryDetail: r.yDetail, secondaryDetail: r.xDetail,
      chanceFlag: flag, seedRank: ss && ss.model === r.name ? rank() : null,
      note: r.note, modelRights: r.modelRights,
    };
  });
  const names = new Set(t.rows.map(r => r.name));
  const datasetSlug = datasetSlugOf(t.dataset);
  return {
    id: t.id, title: t.title, short: t.short, subtitle: t.subtitle, dataset: t.dataset, datasetSlug,
    type: tradeoff ? 'tradeoff' : 'accuracy',
    subjects: fig(t.subjects, 'count', protocol),
    chance: chance === null ? undefined : fig(chance, 'pct1raw', protocol),
    observations: t.observations, exposure: t.exposure, yLabel: t.yLabel, xLabel: t.xLabel,
    limitation: t.limitation, steps: t.protocol, selection: t.selection,
    seed: ss ? { model: ss.model, values: ss.balancedAccuracyPercent.map(v => fig(v, 'pct2raw', protocol)),
                 mean: fig(ss.meanPercent, 'pct2raw', protocol), scope: ss.scope } : undefined,
    pretrainingOverlap: t.pretrainingOverlap, protocolId: t.protocolId, version: t.version, backend: t.backend,
    elapsed: fig(t.elapsed, 's1', protocol),
    auditSha: t.auditSha,
    summarySha: (t as { summarySha?: string }).summarySha || undefined,
    protocolSha: (t as { protocolSha?: string }).protocolSha || undefined,
    license: t.license, licenseUrl: t.licenseUrl, attribution: t.attribution, privacyReview: t.privacyReview,
    rightsScope: t.rightsScope, reviewedAt: t.reviewedAt, reviewBasis: t.reviewBasis, source: t.source,
    rows, notRun: matrixMethods.filter(m => !names.has(m.name)),
    files: { results, protocol },
    requested: datasetSlug ? requestedCitations[datasetSlug] : undefined,
    // A correction that amends this protocol's own downloads (releases.ts).
    corrections: corrections.filter(c => c.files.includes(results) || c.files.includes(protocol)),
  };
}

export const protocols: Protocol[] = data.tracks.map(build);
export const protocolById = Object.fromEntries(protocols.map(p => [p.id, p])) as Record<string, Protocol>;

export const protocolPaths = ['/protocols/', ...protocols.map(p => `/protocols/${p.id}/`)];

/**
 * First published in this site update. The figures are the 2026-09-20 core
 * release; the pages, and the links to them from the dataset and method pages
 * and the matrix, are new. Sitemap `lastmod` only.
 */
export const protocolPagesDate = '2026-10-02';

/** The protocol's name as a link label: "Core-matrix protocol: SSVEP · 8 channels". */
export function protocolLinkLabel(path: string, locale: Locale): string | null {
  const id = path.match(/^\/protocols\/([^/#]+)\//)?.[1];
  const p = id ? protocolById[id] : undefined;
  if (!p) return null;
  return locale === 'zh' ? `核心矩阵协议：${trackTitle(p.title, locale)}` : `Core-matrix protocol: ${p.title}`;
}
