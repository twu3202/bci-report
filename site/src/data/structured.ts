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
 */
import data from './mvp.json';
import deployment from './deployment-topics.json';
import evidence from './evidence-update.json';
import { site } from './site';

/** The aggregate results carry the licence the Hugging Face mirror declares. */
const LICENSE = 'https://creativecommons.org/licenses/by/4.0/';

const abs = (path: string) => new URL(path, site.origin).href;

const creator = {
  '@type': 'Person',
  name: 'BCI Report',
  url: site.origin,
} as const;

/** DOIs and source URLs of the datasets that actually contributed a number. */
function sourceCitations(): string[] {
  const used = new Set(data.tracks.map(t => t.dataset));
  return data.datasets
    .filter(d => used.has(d.name))
    .map(d => d.source)
    .filter((s): s is string => Boolean(s));
}

function download(path: string, format: string) {
  return { '@type': 'DataDownload', encodingFormat: format, contentUrl: abs(path) };
}

export function homeDataset() {
  const protocols = data.tracks.length;
  const comparisons = data.tracks.reduce((n, t) => n + t.rows.length, 0);
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${site.name}: aggregate EEG decoding results`,
    description:
      `Cohort-level results for ${protocols} public EEG decoding protocols — ` +
      `${comparisons} model-by-protocol comparisons covering motor imagery, SSVEP at four ` +
      'and eight electrodes, P300 and semantic ERP, cognitive load, sleep staging and idle ' +
      'false activations. Every score is reported with the protocol that produced it: cohort ' +
      'size, electrode count, evaluation mode, chance level and training budget. No raw EEG, ' +
      'no per-participant scores.',
    url: abs('/'),
    license: LICENSE,
    creator,
    isAccessibleForFree: true,
    version: data.releaseId,
    dateModified: data.generatedAt.slice(0, 10),
    measurementTechnique: 'Electroencephalography',
    keywords: ['EEG', 'brain-computer interface', 'benchmark', 'motor imagery', 'SSVEP',
               'P300', 'sleep staging', 'electroencephalography'],
    citation: sourceCitations(),
    distribution: [
      download('/data/experiments.json', 'application/json'),
      ...data.tracks.map(t => download(`/data/${t.id}-results.csv`, 'text/csv')),
    ],
  };
}

/**
 * Topics that draw on the 2026-09-22 evidence export, and what they measure.
 * A topic can use both exports (on-the-move) or only the newer one
 * (fewer-electrodes); `distribution` must name whichever actually holds its
 * numbers. calibration-budget is absent on purpose: its new section is a
 * roadmap with no measured result, and a Dataset entity must not imply one.
 */
const EVIDENCE_METRICS: Record<string, string[]> = {
  'fewer-electrodes': ['person_mean_balanced_accuracy', 'macro_f1'],
  'on-the-move': ['signed_correlation_r', 'predictive_r_squared'],
};

export function topicDataset(id: string, name: string, description: string, path: string) {
  const topic = deployment.topics.find(t => t.id === id);
  const tracks = new Set(topic?.tracks ?? []);
  const rows = deployment.rows.filter(r => tracks.has(r.track));
  const fromEvidence = EVIDENCE_METRICS[id] ?? [];
  const files = [
    ...(topic ? [download('/data/deployment-topics.json', 'application/json')] : []),
    ...(fromEvidence.length ? [download('/data/evidence-update.json', 'application/json')] : []),
  ];
  const dates = [...(topic ? [deployment.generated_at] : []), ...(fromEvidence.length ? [evidence.generated_at] : [])];
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${site.name}: ${name}`,
    description,
    url: abs(path),
    license: LICENSE,
    creator,
    isAccessibleForFree: true,
    version: topic ? deployment.release_id : evidence.release_id,
    dateModified: dates.sort().at(-1)!.slice(0, 10),
    measurementTechnique: 'Electroencephalography',
    keywords: ['EEG', 'brain-computer interface', 'benchmark', id],
    variableMeasured: [...new Set([...rows.map(r => r.metric), ...fromEvidence])],
    isPartOf: { '@type': 'Dataset', name: `${site.name}: aggregate EEG decoding results`, url: abs('/') },
    distribution: files,
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
    creator,
  };
}
