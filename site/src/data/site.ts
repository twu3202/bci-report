/**
 * Single source of truth for site-level identity and the public contact route.
 *
 * The rule these fields exist for: publishing an address that does not deliver
 * is worse than publishing none, because corrections and rights complaints then
 * disappear silently. While they are `null` every contact surface renders an
 * honest "not yet published" state instead of a dead address.
 */
export const site = {
  name: 'BCI Report',
  origin: 'https://bci.report',
  /**
   * Id of the core-matrix release. It keeps its 2026-09-20 name: an id is a
   * label for fixed bytes, not a claim about the site's stage. The "Research
   * preview" badge came off on 2026-10-01; the caveats it stood for (single
   * seeds, four-person cohorts) stay on the pages that carry them.
   */
  releaseId: 'research-preview-20260920',
  description:
    'Public EEG decoding results reported with their protocol: motor imagery, SSVEP with 4 and 8 electrodes, ' +
    'P300 and semantic ERP, cognitive load, sleep staging, and idle false activations.',
  /**
   * The project's other public homes. They link to the site; these let the site
   * link back — JSON-LD `sameAs`, the footers, /api/ and llms.txt all read them.
   * The citation file is the raw one, so a reference manager or an agent gets
   * the YAML rather than GitHub's page around it.
   */
  repository: 'https://github.com/twu3202/bci-report',
  mirror: 'https://huggingface.co/datasets/Twu31/bci-report',
  citationFile: 'https://raw.githubusercontent.com/twu3202/bci-report/main/CITATION.cff',
} as const;

/**
 * Things built on the site's published files, kept on the owner's Hugging Face
 * account rather than here. Linked low-key from the page each one belongs to,
 * never from the home page or the header, and kept out of the JSON-LD `sameAs`
 * list (which names the site's own homes).
 *
 * - `explorer`: a Space that reads the Hugging Face mirror at one pinned release
 *   and labels every answer with it; /api/ and llms.txt link it.
 * - `articles`: long-form write-ups, one line per article; `page` is the topic
 *   page that links it (/jev-style/ links the decision-research ones as well).
 *   The link label is the page's own copy and carries no "Jev-style".
 */
export const elsewhere = {
  explorer: 'https://huggingface.co/spaces/Twu31/bci-report-explorer',
  articles: [
    { id: 'when-should-an-eeg-decoder-abstain', page: '/topics/when-not-to-act/', published: '2026-10-07',
      url: 'https://huggingface.co/blog/Twu31/when-should-an-eeg-decoder-abstain' },
    { id: 'one-eeg-encoder-several-questions', page: '/topics/shared-encoder/', published: '2026-10-08',
      url: 'https://huggingface.co/blog/Twu31/one-eeg-encoder-several-questions' },
  ],
} as const;

/**
 * Inbound is verified; outbound is deliberately not configured.
 *
 * Verified end to end on 2026-09-20 before these were filled in: the MX and SPF
 * records resolve from public resolvers (1.1.1.1 and 8.8.8.8, not merely from
 * Cloudflare's own dashboard), the forwarding destination is verified rather
 * than pending, both rules are enabled, the catch-all stays disabled with
 * action `drop`, and a real message sent from an outside mailbox arrived.
 *
 * ⚠ The domain RECEIVES but does not SEND. Cloudflare Email Routing is inbound
 * forwarding only, and adding sending was declined for now as a cost decision.
 * So a reply to anyone writing here comes from the operator's own mailbox, not
 * from @bci.report — which is why /data-use/ says so rather than leaving a
 * correspondent to wonder whether the reply is a spoof. Replying-all to the
 * @bci.report address still works; it routes back in.
 *
 * If sending is ever added (Cloudflare Email Sending, or a mailbox provider's
 * custom domain), revisit the DMARC record at the same time: a non-sending
 * domain wants a strict policy, and a sending one needs SPF/DKIM aligned first.
 */
export const contact: { corrections: string | null; privacy: string | null } = {
  corrections: 'contact@bci.report',
  privacy: 'privacy@bci.report',
};

/**
 * The Zenodo archive (connected 2026-10-03). Every GitHub release is archived
 * as its own version with its own DOI; the concept DOI below always resolves to
 * the newest version, so it is the one to cite and the one CITATION.cff,
 * the /api/ BibTeX, the home Dataset and llms.txt carry (check-workbench.mjs
 * keeps them equal). The first archived version was extension-update-20261002,
 * DOI 10.5281/zenodo.23123297.
 */
export const archive = {
  conceptDoi: '10.5281/zenodo.23123296',
  conceptUrl: 'https://doi.org/10.5281/zenodo.23123296',
} as const;

export const contactReady = contact.corrections !== null;

/** Subject line suggested to correspondents. Derived so a rename cannot strand it. */
export const correctionSubject = `[${site.name} correction]`;
