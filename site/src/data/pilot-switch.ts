/**
 * The pilot studies' publication switches. One manifest field per source, sources[<id>].publication in
 * research/publication_review_20261012/pilot-studies-release-manifest.json, makes pilot-studies-update.json publish
 * that source's aggregates or hold them. Every page, register, card and check that names the source reads its flag
 * here, so holding it at preview is a re-export, not an edit.
 *
 * - BINGO (owner decision 3, 2026-10-12): released with its rights as they stand.
 * - The handwriting dataset's mask-aware analysis (owner decision, 2026-10-12): released with its rights gap stated —
 *   no ethics-approval or informed-consent statement was found.
 *
 * Released: the result, the dataset record and a dataset page, no hold. Held: no result, no dataset page, and the
 * export's own hold record, which the holds register (releases.ts) and the pilot-studies page print.
 */
import pilot from './pilot-studies-update.json';

export const BINGO_DATASET = 'bingo-imagined-speech';
export const BINGO_RESULT = 'bingo-cross-language';
export const BINGO_HOLD = 'bingo-cross-language-rights';
export const HANDWRITING_DATASET = 'eeg-fnirs-handwriting';
export const HANDWRITING_RESULT = 'handwriting-mask-aware';
export const HANDWRITING_HOLD = 'handwriting-mask-aware-rights';

/** A source is either released (its result, no hold) or held (its hold, no result), as the export says. */
function released(dataset: string, result: string, holdId: string, name: string): boolean {
  const record = (pilot.datasets as Record<string, { publication: string; results: string[] }>)[dataset];
  const hasResult = result in pilot.results;
  const hold = (pilot.holds as { id: string }[]).find(h => h.id === holdId);
  const on = record?.publication === 'released';
  if (!record || !['released', 'status_only'].includes(record.publication)
      || on !== hasResult || on === !!hold
      || (on ? record.results.join() !== result : record.results.length !== 0))
    throw new Error(`pilot-switch.ts: ${name} is either released (its result, no hold) or held (its hold, no result), as the export says`);
  return on;
}

/** True while the export publishes BINGO's aggregates. */
export const bingoReleased: boolean = released(BINGO_DATASET, BINGO_RESULT, BINGO_HOLD, 'BINGO');
/** True while the export publishes the handwriting analysis's aggregates. */
export const handwritingReleased: boolean = released(HANDWRITING_DATASET, HANDWRITING_RESULT, HANDWRITING_HOLD, 'the handwriting analysis');
