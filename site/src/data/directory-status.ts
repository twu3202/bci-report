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
  facts: { sourceModified: string; licence: string };
  note: L;
}

const reve = { sourceModified: '2026-09-14', licence: 'REVE Responsible Use License v1.0' };
export const modelStatusOverrides: Record<string, StatusOverride> = {
  // The Hugging Face API (https://huggingface.co/api/models/brain-bzh/reve-base),
  // read on 2026-10-02: gated false, last modified 2026-09-14, card licence
  // "reve-responsible-use-license-v1.0". Access is no longer the blocker; the
  // licence has not been reviewed for this site.
  'REVE Base': {
    released: 'Access gated',
    status: 'Licence review pending',
    checked: '2026-10-02',
    source: 'https://huggingface.co/brain-bzh/reve-base',
    facts: reve,
    note: {
      en: `Checked 2026-10-02: Hugging Face reports the base weights as no longer gated (repository last modified ${reve.sourceModified}), under the ${reve.licence}. That licence has not been reviewed for this site, so the model stays unscored. The note above is the released one.`,
      zh: `2026-10-02 核查：Hugging Face 显示基础权重已不再受访问限制（仓库最后修改于 ${reve.sourceModified}），许可为 ${reve.licence}。本站尚未审查这份许可，所以该模型仍没有分数。上面的备注译自发布时的原文。`,
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
