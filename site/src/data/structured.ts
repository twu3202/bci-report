/**
 * schema.org Dataset markup, built from the published payloads.
 *
 * Why this exists: the site was not discoverable through the channel its
 * audience actually uses. Google Dataset Search indexes `Dataset` markup
 * specifically, and this project publishes exactly that — licensed, downloadable,
 * cohort-level measurements with named sources. Plain pages carrying the numbers
 * in a table are invisible to it.
 *
 * Every field is derived from `mvp.json` or `deployment-topics.json` rather than
 * written out here, because markup that drifts from the page is worse than no
 * markup: it is a claim to a crawler that the page does not support.
 *
 * `citation` credits the upstream datasets by DOI. The recordings are not
 * redistributed here, so this is the only place the machine-readable record can
 * point a reader back to the people who collected them.
 *
 * The home Dataset is the umbrella record: its version and dates come from the
 * release log (releases.ts), the same newest release CITATION.cff and /api/
 * cite, and its `distribution` is every file the releases ship. Until
 * 2026-10-02 it carried the core snapshot's 2026-09-20 version and only the
 * core files, so the record Dataset Search would show disagreed with the
 * citation the project asks for.
 */
import data from './mvp.json';
import deployment from './deployment-topics.json';
import evidence from './evidence-update.json';
import clinical from './clinical-update.json';
import context from './context-update.json';
import adaptation from './adaptation-update.json';
import extension from './extension-update.json';
import large from './large-source-update.json';
import reliable from './reliable-decisions-update.json';
import { archive, site } from './site';
import { plainAnswer } from './answer';
import { latestRelease, releases } from './releases';
import { servedFiles } from './files';
import { topicPages } from './topics';
import { topicCards } from './i18n';
import { datasets as datasetEntities } from './entities';
import { FM_JSON, fmFileOf, fmMatrixModels, fmRelease } from './foundation-models';

/** The aggregate results carry the licence the Hugging Face mirror declares. */
const LICENSE = 'https://creativecommons.org/licenses/by/4.0/';

const abs = (path: string) => new URL(path, site.origin).href;

/** A project byline, not a person: schema.org's Organization, which Google accepts for `creator`. */
export const creator = {
  '@type': 'Organization',
  name: site.name,
  url: site.origin,
} as const;

/** The same project elsewhere: the code repository and the Hugging Face mirror of the data. */
const sameAs = [site.mirror, site.repository];

/** DOIs and source URLs of the datasets that actually contributed a number. */
function sourceCitations(): string[] {
  const used = new Set(data.tracks.map(t => t.dataset));
  const core = data.datasets
    .filter(d => used.has(d.name))
    .map(d => d.source)
    .filter((s): s is string => Boolean(s));
  // Every dataset with a page has a published result in some release; its
  // sources are the credit the later batches carry.
  return [...new Set([...core, ...datasetEntities.flatMap(d => d.sources)])];
}

const formatOf = (file: string) => (file.endsWith('.csv') ? 'text/csv' : 'application/json');

function download(path: string, format: string) {
  return { '@type': 'DataDownload', encodingFormat: format, contentUrl: abs(path) };
}

export function homeDataset() {
  const protocols = data.tracks.length;
  const comparisons = data.tracks.reduce((n, t) => n + t.rows.length, 0);
  const questions = topicPages.map(t => topicCards.en[t.slug].title.replace(/\?$/, ''));
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${site.name}: aggregate EEG decoding results`,
    description:
      `Cohort-level results for ${protocols} public EEG decoding protocols — ` +
      `${comparisons} model-by-protocol comparisons covering motor imagery, SSVEP at four ` +
      'and eight electrodes, P300 and semantic ERP, cognitive load, sleep staging and idle ' +
      'false activations. Every score is reported with the protocol that produced it: cohort ' +
      'size, electrode count, evaluation mode, chance level and training budget. ' +
      `Separately reviewed batches bear on ${topicPages.length} deployment questions (${questions.join('; ')}), ` +
      'each in its own file and never summed with the matrix. No raw EEG, no per-participant scores.',
    url: abs('/'),
    sameAs,
    license: LICENSE,
    creator,
    isAccessibleForFree: true,
    version: latestRelease.id,
    // The Zenodo concept DOI: it resolves to the newest archived release.
    identifier: archive.conceptUrl,
    datePublished: releases.at(-1)!.date,
    dateModified: latestRelease.date,
    measurementTechnique: 'Electroencephalography',
    keywords: ['EEG', 'brain-computer interface', 'benchmark', 'motor imagery', 'SSVEP',
               'P300', 'sleep staging', 'electroencephalography', 'EEG foundation models',
               'dry electrodes', 'calibration'],
    citation: sourceCitations(),
    // Every file any release ships, newest release first: the later batches are
    // part of this record, not only of the topic pages that print them.
    distribution: [...new Set(servedFiles.map(f => f.file))].map(f => download(`/data/${f}`, formatOf(f))),
    hasPart: topicPages.map(t => ({
      '@type': 'Dataset',
      name: `${site.name}: ${topicCards.en[t.slug].title}`,
      description: `${topicCards.en[t.slug].question} ${topicCards.en[t.slug].summary}`,
      url: abs(`/topics/${t.slug}/`),
      license: LICENSE,
      creator,
    })),
  };
}

/**
 * Topics whose figures come from a later export than deployment-topics.json,
 * and what they measure. A topic can use both (on-the-move), only the evidence
 * update (fewer-electrodes), or only the clinical update (clinical-groups);
 * `distribution` must name whichever actually holds its numbers.
 * calibration-budget gained one on 2026-10-01, when its adaptation roadmap was
 * replaced by measured results; until then it was absent on purpose, because a
 * Dataset entity must not imply a result a roadmap does not have. On 2026-10-02
 * those results moved to model-adaptation, and calibration-budget went back to
 * deployment-topics.json alone, until 2026-10-03 added the OpenBMI next-session
 * result (large-source-update.json) beside it. sleep-staging (2026-10-03) reads
 * that file only. model-adaptation also prints, for scale, the
 * core matrix's frozen LaBraM readout (experiments.json) and the adapter's
 * parameter counts from the 2026-09-22 engineering check (evidence-update.json),
 * so their releases are named too. Its next-day statuses carry no figure.
 * `metrics` feeds variableMeasured, which names what the page measures: a
 * parameter count is a property of the adapter, not a measurement, so the
 * engineering check has none (2026-10-02 review). It stays in `distribution`
 * and in the cite block, which name the files the printed figures come from.
 */
type LaterExport = { file: string; release: string; generated: string; metrics: string[] };
const contextExport = (metrics: string[]): LaterExport =>
  ({ file: '/data/context-update.json', release: context.release_id, generated: context.generated_at, metrics });
// The 2026-10-02 batch: the YSU extension on when-not-to-act, LTRSVP on screen-to-vr.
const extensionExport = (metrics: string[]): LaterExport =>
  ({ file: '/data/extension-update.json', release: extension.release_id, generated: extension.generated_at, metrics });
// The 2026-10-03 batch: Dreem on sleep-staging, OpenBMI on calibration-budget.
const largeSourceExport = (metrics: string[]): LaterExport =>
  ({ file: '/data/large-source-update.json', release: large.release_id, generated: large.generated_at, metrics });
// The 2026-10-04 v9 batch: its JSON (adaptation arms and the export's comparisons) and the CSV of each
// protocol a topic prints, then the core release whose rows they are read against.
const fmExports = (protocols: string[], core: boolean): LaterExport[] => [
  { file: `/data/${FM_JSON}`, release: fmRelease.id, generated: fmRelease.date, metrics: ['balanced_accuracy'] },
  ...protocols.map(p => ({ file: `/data/${fmFileOf(p)}`, release: fmRelease.id, generated: fmRelease.date, metrics: ['balanced_accuracy'] })),
  ...(core ? [{ file: '/data/experiments.json', release: data.releaseId, generated: data.generatedAt, metrics: ['balanced_accuracy'] }] : []),
];
const LATER_EXPORTS: Record<string, LaterExport | LaterExport[]> = {
  'sleep-staging': largeSourceExport(['accuracy', 'balanced_accuracy', 'macro_f1', 'cohen_kappa', 'recall', 'precision', 'f1']),
  'calibration-budget': largeSourceExport(['balanced_accuracy']),
  'screen-to-vr': [contextExport(['balanced_accuracy', 'auroc']), extensionExport(['balanced_accuracy', 'auroc'])],
  // Since 2026-10-04 also BETA at eight and four electrodes and the six-channel sleep column for the
  // v9 encoders (their CSVs, and the export's four-minus-eight comparison), beside the released rows.
  'fewer-electrodes': [{ file: '/data/evidence-update.json', release: evidence.release_id,
                         generated: evidence.generated_at,
                         metrics: ['person_mean_balanced_accuracy', 'macro_f1'] },
                       ...fmExports(['beta-8ch', 'beta-4ch', 'sleep-scalp'], true)],
  // Since 2026-10-04: the v9 frozen encoders on sleep, BETA and EEGMAT, REVE Base against Large and the
  // masking ablation (every scored core protocol's CSV), with the released rows they are read against.
  'does-pretraining-help': fmExports(['mi-rest', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target', 'semantic-target', 'sleep-scalp'], true),
  'on-the-move': [{ file: '/data/evidence-update.json', release: evidence.release_id,
                    generated: evidence.generated_at,
                    metrics: ['signed_correlation_r', 'predictive_r_squared'] },
                  contextExport(['balanced_accuracy', 'macro_f1'])],
  // The idle protocol of the core snapshot, the non-control batches, and since
  // 2026-10-04 route 1 of the roadmap, reliable decisions (its own export). The
  // roadmap section itself prints no figure and contributes nothing here.
  'when-not-to-act': [{ file: '/data/experiments.json', release: data.releaseId,
                        generated: data.generatedAt,
                        metrics: ['command_detection_within_3s', 'idle_false_activation'] },
                      contextExport(['control_window_acceptance', 'non_control_false_acceptance']),
                      extensionExport(['detection_balanced_accuracy', 'control_window_acceptance',
                                       'correct_and_accepted_rate', 'non_control_false_acceptance']),
                      { file: '/data/reliable-decisions-update.json', release: reliable.release_id,
                        generated: reliable.generated_at,
                        metrics: ['selective_coverage', 'selective_error', 'aurc', 'negative_log_likelihood',
                                  'expected_calibration_error', 'brier_score'] }],
  'model-adaptation': [{ file: '/data/adaptation-update.json', release: adaptation.release_id,
                         generated: adaptation.generated_at, metrics: ['balanced_accuracy', 'macro_f1'] },
                       { file: '/data/experiments.json', release: data.releaseId, generated: data.generatedAt,
                         metrics: ['balanced_accuracy'] },
                       { file: '/data/evidence-update.json', release: evidence.release_id, generated: evidence.generated_at,
                         metrics: [] }],
  'clinical-groups': { file: '/data/clinical-update.json', release: clinical.release_id,
                       generated: clinical.generated_at,
                       metrics: ['balanced_accuracy', 'macro_f1', 'auroc'] },
};

/**
 * The reviewed exports a topic's figures come from, as served paths. The topic
 * Dataset's `distribution` and the page's "cite this page" block both read this,
 * so the release a reader is asked to cite is the one whose file the markup names.
 */
export function topicFiles(id: string): string[] {
  const topic = deployment.topics.find(t => t.id === id);
  const later = [LATER_EXPORTS[id] ?? []].flat();
  return [...new Set([...(topic ? ['/data/deployment-topics.json'] : []), ...later.map(l => l.file)])];
}

export function topicDataset(id: string, name: string, description: string, path: string) {
  const topic = deployment.topics.find(t => t.id === id);
  const tracks = new Set(topic?.tracks ?? []);
  const rows = deployment.rows.filter(r => tracks.has(r.track));
  const later = [LATER_EXPORTS[id] ?? []].flat();
  const files = topicFiles(id).map(f => download(f, formatOf(f)));
  const dates = [...(topic ? [deployment.generated_at] : []), ...later.map(l => l.generated)];
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${site.name}: ${name}`,
    description,
    url: abs(path),
    license: LICENSE,
    creator,
    isAccessibleForFree: true,
    version: topic ? deployment.release_id : later[0].release,
    dateModified: dates.sort().at(-1)!.slice(0, 10),
    measurementTechnique: 'Electroencephalography',
    keywords: ['EEG', 'brain-computer interface', 'benchmark', id],
    variableMeasured: [...new Set([...rows.map(r => r.metric), ...later.flatMap(l => l.metrics)])],
    isPartOf: { '@type': 'Dataset', name: `${site.name}: aggregate EEG decoding results`, url: abs('/') },
    distribution: files,
  };
}

/**
 * One core-matrix protocol as a Dataset: its results CSV and protocol JSON are
 * the distribution, and it is part of the home page's core-matrix Dataset.
 * Name, description and every field come from the released track.
 */
export function protocolDataset(t: typeof data.tracks[number], description: string, requestedCitation?: string) {
  const path = `/protocols/${t.id}/`;
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${site.name}: ${t.title} on ${t.dataset} — protocol and results`,
    description,
    url: abs(path),
    license: LICENSE,
    creator,
    isAccessibleForFree: true,
    version: data.releaseId,
    // The page changed when the v9 rows joined it (2026-10-04); the core release keeps its version.
    dateModified: fmRelease.date,
    measurementTechnique: 'Electroencephalography',
    keywords: ['EEG', 'brain-computer interface', 'benchmark', t.title, t.dataset, ...t.rows.map(r => r.name),
               ...fmMatrixModels.map(m => m.name)],
    variableMeasured: [t.yLabel, t.xLabel],
    isBasedOn: t.source,
    // A citation the source asks for that the released credit line lacks (releases.ts).
    citation: requestedCitation ? [t.attribution, requestedCitation] : t.attribution,
    isPartOf: { '@type': 'Dataset', name: `${site.name}: aggregate EEG decoding results`, url: abs('/') },
    distribution: [
      download(`/data/${t.id}-results.csv`, 'text/csv'),
      download(`/data/${t.id}-protocol.json`, 'application/json'),
      // The v9 foundation-model rows the page prints beside the core table (2026-10-04).
      download(`/data/${fmFileOf(t.id)}`, 'text/csv'),
    ],
  };
}

/** The protocols index: a catalogue of the protocol Datasets. */
export function protocolCatalog(name: string, description: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'DataCatalog',
    name,
    description,
    url: abs('/protocols/'),
    creator,
    dataset: data.tracks.map(t => ({
      '@type': 'Dataset',
      name: `${site.name}: ${t.title} on ${t.dataset} — protocol and results`,
      url: abs(`/protocols/${t.id}/`),
    })),
  };
}

/**
 * The page's question and its short answer, as the page prints them. One
 * question per page; the text is the same string the page renders, with the
 * figure markers removed, so the markup cannot say more than the page does.
 */
export function topicFaq(question: string, answer: string, path: string) {
  return {
    '@type': 'FAQPage',
    url: abs(path),
    mainEntity: [{
      '@type': 'Question',
      name: question,
      acceptedAnswer: { '@type': 'Answer', text: plainAnswer(answer), url: `${abs(path)}#short-answer-heading` },
    }],
  };
}

/**
 * A page's breadcrumb as schema.org BreadcrumbList: the crumbs the page prints,
 * in order, each with its English canonical address (the markup lives on the
 * English canonical only, as every other node here does). The last crumb is the
 * page itself.
 */
export function breadcrumbList(crumbs: { name: string; path: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({ '@type': 'ListItem', position: i + 1, name: c.name, item: abs(c.path) })),
  };
}

export function websiteEntity() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: site.name,
    url: site.origin,
    description: site.description,
    inLanguage: 'en',
    sameAs: [site.repository, site.mirror],
    creator,
  };
}
