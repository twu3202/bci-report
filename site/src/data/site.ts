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
  /** Badge shown next to the wordmark. Keep in step with the release id. */
  stage: 'Research preview',
  releaseId: 'research-preview-20260920',
  description:
    'Public EEG decoding results reported with their protocol: motor imagery, SSVEP with 4 and 8 electrodes, ' +
    'P300 and semantic ERP, cognitive load, sleep staging, and idle false activations.',
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

export const contactReady = contact.corrections !== null;

/** Subject line suggested to correspondents. Derived so a rename cannot strand it. */
export const correctionSubject = `[${site.name} correction]`;
