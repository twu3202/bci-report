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
import pilot from './pilot-studies-update.json';
import { releases } from './releases';
import { EEGPT_SLUG, eegptDirectory, eegptPilot, eegptRelease } from './eegpt-core';
import type { L } from './entities';

type Model = typeof data.models[number];

export interface StatusOverride {
  /** The released status this replaces. */
  released: string;
  status: string;
  /** When the source was checked (ISO date). */
  checked: string;
  /** An external record that shows the change (REVE Base: its Hugging Face card). */
  source?: string;
  /**
   * A page of this site that shows the change beyond the card's own method page (EEGPT: its pilot comparison, outside
   * every leaderboard): a locale-free path with its anchor, which the topic page must carry, and the link's words.
   */
  page?: { path: string; label: L };
  /** What the source reported, in the words the note uses. */
  facts?: { licence: string; accepted: string };
  /**
   * Whether the card's released licence line is the code's alone (REVE Base: "MIT"), so it is marked as the code's;
   * otherwise it is marked as released (EEGPT's line names the code and the checkpoint).
   */
  licenceLine?: 'code';
  note: L;
}

const reve = { licence: 'REVE Responsible Use License v1.0', accepted: '2026-10-04' };

/**
 * EEGPT's pilot comparison: the Orthosis comparison of the pilot-studies release, frozen EEGPT against matched
 * 58-channel classical features, outside every leaderboard. The card and the method page link it only while the served
 * export carries it so: released, the model's checkpoint licence unresolved, no weights distributed, Apache-2.0 scoped
 * to the repository's code. Anything else fails the build.
 */
export const EEGPT_PILOT_PATH = '/topics/pilot-studies/#orthosis';
(() => {
  const r = (pilot.results as Record<string, any>)[eegptPilot.result];
  const ds = (pilot.datasets as Record<string, any>)[r?.dataset];
  const m = r?.model;
  if (eegptPilot.file !== 'pilot-studies-update.json' || !r || r.model_family !== 'foundation' || r.leaderboard !== false
      || ds?.publication !== 'released' || m?.name !== 'EEGPT' || m.weights_licence !== null || m.weights_distributed !== false
      || m.code_licence !== 'Apache-2.0' || !/source code only/.test(m.code_licence_scope))
    throw new Error('directory-status.ts: the EEGPT pilot comparison is not released as the card describes it');
})();
/** EEGPT's method page, which the card's name links (entities.ts gives it one from the EEGPT core release). */
export const EEGPT_METHOD_PATH = `/methods/${EEGPT_SLUG}/`;

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
    licenceLine: 'code',
    note: {
      // The date is the card's "Status checked" line, not the note's words (owner decision 2026-10-08).
      en: `The owner accepted the ${reve.licence}, and the foundation-model evaluation ran the base weights as a frozen probe on the eight core protocols and adapted them on EEGMAT. Aggregate scientific results only; no adapted weights are shared. The note above is the released one.`,
      zh: `站点所有者接受了 ${reve.licence}，基础模型评测把 REVE Base 的权重作为冻结探针在 8 个核心协议上运行，并在 EEGMAT 上做了适配。只发布聚合的科学结果；不分享任何适配后的权重。上面的备注译自发布时的原文。`,
    },
  },
  // EEGPT. Released as "Rights review pending" with no score: its checkpoint licence was unresolved, and the hold on
  // its aggregate scores was this project's own conservative choice, not a publisher's rule. On 2026-10-12 the owner
  // published one pilot comparison (pilot-studies-update.json, orthosis-eegpt-vs-58ch), shown here as "One pilot
  // comparison published"; on 2026-10-12 and 2026-10-13 the owner decided to publish its eight core-matrix cells,
  // computed in the same runs as the published LaBraM rows and, except on idle, the CBraMod rows, and its
  // pretraining-attribution rows (eegpt-core-update.json, release eegpt-core-update-20261013). So it is shown as evaluated, with the export's note,
  // and the released status beside it; the checkpoint licence stays unresolved and no weights are distributed.
  // experiments.json keeps its bytes.
  'EEGPT': {
    released: eegptDirectory.released,
    status: eegptDirectory.status,
    checked: eegptRelease.date,
    page: { path: EEGPT_PILOT_PATH, label: { en: 'The pilot comparison →', zh: '这项试点比较 →' } },
    // The released note above it says no score is published; this one says what now is, and where.
    note: {
      en: `${eegptDirectory.note.en} Its core-matrix cells and pretraining-attribution rows are published on its page; the cells also sit beside the core matrix on every protocol page. The note above is the released one.`,
      zh: `${eegptDirectory.note.zh}它在核心矩阵上的单元格与预训练归因各行已发布在它自己的页面上；这些单元格也列在每个协议页的核心矩阵旁边。上面的备注译自发布时的原文。`,
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
