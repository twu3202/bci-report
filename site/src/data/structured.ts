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
import { site } from './site';
import { plainAnswer } from './answer';
import { latestRelease, releases } from './releases';
import { servedFiles } from './files';
import { topicPages } from './topics';
import { topicCards } from './i18n';
import { datasets as datasetEntities } from './entities';

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
      `Separately reviewed batches answer ${topicPages.length} deployment questions (${questions.join('; ')}), ` +
      'each in its own file and never summed with the matrix. No raw EEG, no per-participant scores.',
    url: abs('/'),
    sameAs,
    license: LICENSE,
    creator,
    isAccessibleForFree: true,
    version: latestRelease.id,
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
 * Dataset entity must not imply a result a roadmap does not have.
 */
type LaterExport = { file: string; release: string; generated: string; metrics: string[] };
const contextExport = (metrics: string[]): LaterExport =>
  ({ file: '/data/context-update.json', release: context.release_id, generated: context.generated_at, metrics });
// The 2026-10-02 batch: the YSU extension on when-not-to-act, LTRSVP on screen-to-vr.
const extensionExport = (metrics: string[]): LaterExport =>
  ({ file: '/data/extension-update.json', release: extension.release_id, generated: extension.generated_at, metrics });
const LATER_EXPORTS: Record<string, LaterExport | LaterExport[]> = {
  'screen-to-vr': [contextExport(['balanced_accuracy', 'auroc']), extensionExport(['balanced_accuracy', 'auroc'])],
  'fewer-electrodes': { file: '/data/evidence-update.json', release: evidence.release_id,
                        generated: evidence.generated_at,
                        metrics: ['person_mean_balanced_accuracy', 'macro_f1'] },
  'on-the-move': [{ file: '/data/evidence-update.json', release: evidence.release_id,
                    generated: evidence.generated_at,
                    metrics: ['signed_correlation_r', 'predictive_r_squared'] },
                  contextExport(['balanced_accuracy', 'macro_f1'])],
  // Its measured part is the idle protocol of the core snapshot; the roadmap on
  // the same page has no result and contributes nothing here.
  'when-not-to-act': [{ file: '/data/experiments.json', release: data.releaseId,
                        generated: data.generatedAt,
                        metrics: ['command_detection_within_3s', 'idle_false_activation'] },
                      contextExport(['control_window_acceptance', 'non_control_false_acceptance']),
                      extensionExport(['detection_balanced_accuracy', 'control_window_acceptance',
                                       'correct_and_accepted_rate', 'non_control_false_acceptance'])],
  'calibration-budget': { file: '/data/adaptation-update.json', release: adaptation.release_id,
                          generated: adaptation.generated_at, metrics: ['balanced_accuracy', 'macro_f1'] },
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
  const files = topicFiles(id).map(f => download(f, 'application/json'));
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
    dateModified: data.generatedAt.slice(0, 10),
    measurementTechnique: 'Electroencephalography',
    keywords: ['EEG', 'brain-computer interface', 'benchmark', t.title, t.dataset, ...t.rows.map(r => r.name)],
    variableMeasured: [t.yLabel, t.xLabel],
    isBasedOn: t.source,
    // A citation the source asks for that the released credit line lacks (releases.ts).
    citation: requestedCitation ? [t.attribution, requestedCitation] : t.attribution,
    isPartOf: { '@type': 'Dataset', name: `${site.name}: aggregate EEG decoding results`, url: abs('/') },
    distribution: [
      download(`/data/${t.id}-results.csv`, 'text/csv'),
      download(`/data/${t.id}-protocol.json`, 'application/json'),
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
