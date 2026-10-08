/**
 * Directory status as the pages show it: the model directory (/methods/) and the
 * public-data register (/datasets/).
 *
 * mvp.json is /data/experiments.json, a released file, so it keeps its bytes.
 * A status that changed after the release is overridden here, for display only,
 * with the date it was checked and the source that shows the change; the
 * released status and note stay on the page beside it. Every other row says
 * when its status was last checked: a dataset's own `reviewedAt`, and for a
 * model the date of the release that carried the directory.
 *
 * An override names the status it replaces and refuses to build once the
 * released file no longer carries that status: a newer release has taken over.
 */
import data from './mvp.json';
import { releases } from './releases';
import type { L } from './entities';

type Model = typeof data.models[number];

export interface StatusOverride {
  /** The released status this replaces. */
  released: string;
  status: string;
  /** When the source was checked (ISO date). */
  checked: string;
  source: string;
  /** What the source reported, in the words the note uses. */
  facts: { licence: string; accepted: string };
  note: L;
}

const reve = { licence: 'REVE Responsible Use License v1.0', accepted: '2026-10-04' };
export const modelStatusOverrides: Record<string, StatusOverride> = {
  // REVE Base. Released as "Access gated"; from 2026-10-02 to 2026-10-04 shown as
  // "Licence review pending" (Hugging Face reported the weights ungated under the REVE
  // Responsible Use License, which had not been reviewed). On 2026-10-04 the owner
  // accepted that licence and the v9 evaluation scored the model
  // (foundation-models-update.json: directory_status, weights_licence, rights_review),
  // so it is shown as evaluated, with the released status beside it.
  'REVE Base': {
    released: 'Access gated',
    status: 'Evaluated',
    checked: reve.accepted,
    source: 'https://huggingface.co/brain-bzh/reve-base',
    facts: reve,
    note: {
      // The date is the card's "Status checked" line, not the note's words (owner decision 2026-10-08).
      en: `The owner accepted the ${reve.licence}, and the foundation-model evaluation ran the base weights as a frozen probe on the eight core protocols and adapted them on EEGMAT. Aggregate scientific results only; no adapted weights are shared. The note above is the released one.`,
      zh: `站点所有者接受了 ${reve.licence}，基础模型评测把 REVE Base 的权重作为冻结探针在 8 个核心协议上运行，并在 EEGMAT 上做了适配。只发布聚合的科学结果；不分享任何适配后的权重。上面的备注译自发布时的原文。`,
    },
  },
};

/** The date the model directory was last checked: the release that ships experiments.json. */
const directoryRelease = releases.find(r => r.files.includes('experiments.json'));
if (!directoryRelease) throw new Error('directory-status.ts: no release ships experiments.json');
export const directoryCheckedOn = directoryRelease.date;

for (const [name, o] of Object.entries(modelStatusOverrides)) {
  const m = data.models.find(x => x.name === name);
  if (!m) throw new Error(`directory-status.ts: no model ${name} in the directory`);
  if (m.status !== o.released)
    throw new Error(`directory-status.ts: ${name} is released as "${m.status}", not "${o.released}"; the override is stale`);
  if (o.checked <= directoryCheckedOn) throw new Error(`directory-status.ts: the ${name} override predates the release it amends`);
}

/** A model's status as shown, the date it was checked, and the override behind it, if any. */
export function modelDirectoryStatus(m: Pick<Model, 'name' | 'status'>): { status: string; checked: string; override?: StatusOverride } {
  const override = modelStatusOverrides[m.name];
  return override ? { status: override.status, checked: override.checked, override }
                  : { status: m.status, checked: directoryCheckedOn };
}
