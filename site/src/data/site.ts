/**
 * Single source of truth for site-level identity and the public contact route.
 *
 * ⚠ LAUNCH BLOCKER — `contact` and `privacy` are deliberately `null`.
 * Publishing an address that does not yet deliver is worse than publishing none:
 * corrections and rights complaints would silently disappear. Fill these in only
 * after the mailbox exists AND a test message has been delivered and replied to
 * in both directions (see docs handoff §6). Until then every contact surface on
 * the site renders an honest "not yet published" state instead of a dead address.
 */
export const site = {
  name: 'BCI Arena',
  origin: 'https://bciarena.ai',
  /** Badge shown next to the wordmark. Keep in step with the release id. */
  stage: 'Research preview',
  releaseId: 'research-preview-20260920',
  description:
    'Public EEG decoding results reported with their protocol: motor imagery, SSVEP with 4 and 8 electrodes, ' +
    'P300 and semantic ERP, cognitive load, sleep staging, and idle false activations.',
} as const;

/** Verified, deliverable addresses only. `null` until tested in both directions. */
export const contact: { corrections: string | null; privacy: string | null } = {
  corrections: null, // e.g. 'contact@bciarena.ai'
  privacy: null, // e.g. 'privacy@bciarena.ai'
};

export const contactReady = contact.corrections !== null;

/** Subject line suggested to correspondents, per the handoff's operating process. */
export const correctionSubject = '[BCI Arena correction]';
