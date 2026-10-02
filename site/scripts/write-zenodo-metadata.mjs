// Write the repository's .zenodo.json: the metadata Zenodo reads when a GitHub
// release is archived. (When .zenodo.json exists Zenodo ignores CITATION.cff
// entirely, so the two have to agree; this file is derived from it.)
//
//     npm run build && node scripts/write-zenodo-metadata.mjs
//
// Nothing here is typed twice:
// - title, author and keywords come from CITATION.cff;
// - the site and the Hugging Face mirror come from the home page's Dataset
//   markup (`url`, `sameAs`), which reads src/data/site.ts;
// - every upstream source is the `isBasedOn` of a dataset page in dist/ — the
//   records of the recordings this project's figures were computed on. Only
//   datasets with released results have a page, so a held source cannot get in.
//   Listed as isDerivedFrom so the archive credits them in the DOI graph too.
//
// check-workbench.mjs fails when the committed file differs from what this
// writes, so a new dataset page cannot leave the archive's credits behind.
// Re-run it after adding one. The version is not set here: Zenodo takes it
// from the release tag, which should be the release id (e.g.
// adaptation-update-20261001).
import { readFileSync, readdirSync, existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = new URL('../../', import.meta.url);

const ld = html => [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));

/** The .zenodo.json object for a built site at `dist` (a directory URL). */
export function zenodoMetadata(dist) {
  const cff = readFileSync(new URL('CITATION.cff', ROOT), 'utf8');
  const title = cff.match(/^title: "([^"]+)"$/m)?.[1];
  const author = cff.match(/^authors:\n {2}- name: "([^"]+)"$/m)?.[1];
  const keywords = [...(cff.match(/^keywords:\n((?: {2}- .+\n?)+)/m)?.[1] ?? '').matchAll(/^ {2}- (.+)$/gm)].map(m => m[1].trim());
  const home = ld(readFileSync(new URL('index.html', dist), 'utf8')).find(x => x['@type'] === 'Dataset');
  if (!title || !author || !keywords.length || !home?.sameAs) throw new Error('write-zenodo-metadata: CITATION.cff or the home Dataset markup changed shape');
  const mirror = home.sameAs.find(u => new URL(u).hostname === 'huggingface.co');
  const upstream = new Set();
  for (const slug of readdirSync(new URL('datasets/', dist))) {
    const page = new URL(`datasets/${slug}/index.html`, dist);
    if (!existsSync(page)) continue;
    for (const node of ld(readFileSync(page, 'utf8')))
      if (node['@type'] === 'Dataset') for (const u of node.isBasedOn ?? []) upstream.add(u);
  }
  return {
    upload_type: 'dataset',
    title,
    creators: [{ name: author }],
    description:
      '<p>Cohort-level EEG decoding results, each published with the protocol that produced it: cohort, ' +
      'electrode count, evaluation split, chance level, interval and known limitations. No raw EEG, no ' +
      'per-participant scores, no model weights and no overall ranking.</p>' +
      `<p>The site, with every figure in context: <a href="${home.url}">${home.url}</a>. ` +
      'The release log, with the SHA-256 of every file: ' +
      `<a href="${new URL('/releases/', home.url).href}">${new URL('/releases/', home.url).href}</a>.</p>` +
      '<p>Cite BCI Report and the release you used (this archive’s version is the release id), and the ' +
      'upstream dataset each figure was computed on: every dataset page gives its credit, ' +
      `<a href="${new URL('/datasets/', home.url).href}">${new URL('/datasets/', home.url).href}</a>.</p>`,
    access_right: 'open',
    license: 'cc-by-4.0',
    notes: 'The aggregate results in this archive are CC BY 4.0 (LICENSE-DATA): measurements this project ' +
      'produced. The code is under the MIT License (LICENSE). The EEG recordings the results were computed ' +
      'from are not included and keep their own licences and terms.',
    keywords,
    language: 'eng',
    related_identifiers: [
      { identifier: home.url, relation: 'isDocumentedBy' },
      { identifier: mirror, relation: 'isVariantFormOf', resource_type: 'dataset' },
      ...[...upstream].sort().map(identifier => ({ identifier, relation: 'isDerivedFrom' })),
    ],
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const dist = new URL('../dist/', import.meta.url);
  const out = new URL('.zenodo.json', ROOT);
  writeFileSync(out, JSON.stringify(zenodoMetadata(dist), null, 2) + '\n');
  console.log(`wrote ${fileURLToPath(out)}`);
}
