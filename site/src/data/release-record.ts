/**
 * What the release log (/releases/), its archive (/releases/archive/) and the feed print about each release, computed
 * at build time (owner decision D17, 2026-10-28; moved here from releases.astro unchanged).
 *
 * Hashes are computed from the bytes the site serves, so no page can state a hash for a file it does not ship;
 * check-workbench.mjs recomputes each one from dist/data and compares. Each release's id and review manifest are read
 * from its payload, and every release in releases.ts must name its payload's id. A register release is read from the
 * dated register file it ships, so each later register version needs no change here.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import data from './mvp.json';
import deployment from './deployment-topics.json';
import evidence from './evidence-update.json';
import clinical from './clinical-update.json';
import context from './context-update.json';
import adaptation from './adaptation-update.json';
import extension from './extension-update.json';
import large from './large-source-update.json';
import reliable from './reliable-decisions-update.json';
import foundation from './foundation-models-update.json';
import shared from './shared-representation-update.json';
import later from './later-sessions-update.json';
import language from './questions-in-language-update.json';
import beyond from './beyond-scalp-update.json';
import pilot from './pilot-studies-update.json';
import eegpt from './eegpt-core-update.json';
import ssvep from './new-ssvep-frequencies-update.json';
import dataQuality from './data-quality-update.json';
import clinicalIesseeg from './clinical-iesseeg-update.json';
import neurolmEegmat from './neurolm-eegmat-update.json';
import ssvepCards from './ssvep-followups-update.json';
import neurorvq from './neurorvq-update.json';
import eegmatTen from './eegmat-ten-second-update.json';
import datasetChecks from './dataset-checks-update.json';
import { LATEST_DAYS, highlights, releaseDays, releases, type Change, type Release } from './releases';
import { registerCopy, topicCards, translatedPaths, type Locale } from './i18n';
import { modelRegisterPageBuilt, registerPageBuilt, releaseArchiveBuilt } from './files';
import { entityPaths } from './entities';
import { protocolPaths } from './protocols';

const served = (file: string) => readFileSync(resolve('public/data', file));

/** A served file's size and the SHA-256 of its bytes as served. */
export const fileFacts = (file: string) => {
  const bytes = served(file);
  return { file, bytes: bytes.length, sha: createHash('sha256').update(bytes).digest('hex') };
};

// Each payload's release id and the review manifest it was built from, where the payload records one.
type PayloadRecord = { id: string; manifest?: string };
const payloads: Record<string, PayloadRecord> = {
  mvp: { id: data.releaseId }, deployment: { id: deployment.release_id },
  evidence: { id: evidence.release_id, manifest: evidence.provenance.manifest_sha256 },
  clinical: { id: clinical.release_id, manifest: clinical.provenance.manifest_sha256 },
  context: { id: context.release_id, manifest: context.provenance.manifest_sha256 },
  adaptation: { id: adaptation.release_id, manifest: adaptation.provenance.manifest_sha256 },
  extension: { id: extension.release_id, manifest: extension.provenance.manifest_sha256 },
  largeSource: { id: large.release_id, manifest: large.provenance.manifest_sha256 },
  reliableDecisions: { id: reliable.release_id, manifest: reliable.provenance.manifest_sha256 },
  foundationModels: { id: foundation.release_id, manifest: foundation.provenance.manifest_sha256 },
  sharedRepresentation: { id: shared.release_id, manifest: shared.provenance.manifest_sha256 },
  laterSessions: { id: later.release_id, manifest: later.provenance.manifest_sha256 },
  questionsInLanguage: { id: language.release_id, manifest: language.provenance.manifest_sha256 },
  beyondScalp: { id: beyond.release_id, manifest: beyond.provenance.manifest_sha256 },
  pilotStudies: { id: pilot.release_id, manifest: pilot.provenance.manifest_sha256 },
  eegptCore: { id: eegpt.release_id, manifest: eegpt.provenance.manifest_sha256 },
  newSsvepFrequencies: { id: ssvep.release_id, manifest: ssvep.provenance.manifest_sha256 },
  dataQuality: { id: dataQuality.release_id, manifest: dataQuality.provenance.manifest_sha256 },
  clinicalIesseeg: { id: clinicalIesseeg.release_id, manifest: clinicalIesseeg.provenance.manifest_sha256 },
  neurolmEegmat: { id: neurolmEegmat.release_id, manifest: neurolmEegmat.provenance.manifest_sha256 },
  ssvepFollowups: { id: ssvepCards.release_id, manifest: ssvepCards.provenance.manifest_sha256 },
  neurorvq: { id: neurorvq.release_id, manifest: neurorvq.provenance.manifest_sha256 },
  eegmatTenSecond: { id: eegmatTen.release_id, manifest: eegmatTen.provenance.manifest_sha256 },
  datasetChecks: { id: datasetChecks.release_id, manifest: datasetChecks.provenance.manifest_sha256 },
};
// The open register's releases: each ships one dated register file, read as served.
const REGISTER_FILE = /^open-register-\d{8}\.json$/;
const recordOf = (r: Release): PayloadRecord => {
  if (payloads[r.payload]) return payloads[r.payload];
  const file = r.files.find(f => REGISTER_FILE.test(f));
  if (!file) throw new Error(`release-record.ts: ${r.id} names the payload ${r.payload}, which no file here records`);
  const register = JSON.parse(served(file).toString('utf8'));
  return { id: register.release_id, manifest: register.provenance?.manifest_sha256 };
};
/** The release id its payload records. */
export const idOf = (r: Release) => recordOf(r).id;
/** The review manifest its payload was built from, where the payload records one. */
export const manifestOf = (r: Release) => recordOf(r).manifest;
for (const r of releases)
  if (idOf(r) !== r.id) throw new Error(`releases.ts: ${r.id} does not match its payload (${idOf(r)})`);

/** A release date as each language writes it. */
export const date = (iso: string, locale: Locale) => {
  const [y, m, d] = iso.split('-').map(Number);
  return locale === 'zh' ? `${y} 年 ${m} 月 ${d} 日`
    : `${d} ${['January','February','March','April','May','June','July','August','September','October','November','December'][m - 1]} ${y}`;
};
export const kib = (n: number) => n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} KiB`;

const hubTitle: Record<string, { en: string; zh: string }> = {
  '/protocols/': { en: 'Protocols', zh: '协议' }, '/methods/': { en: 'Methods', zh: '方法' }, '/datasets/': { en: 'Datasets', zh: '数据集' },
};
/** The title of a page a release names: a question, a hub, a register page, or the home page. */
export const pageTitle = (p: string, locale: Locale) => {
  const slug = p.match(/^\/topics\/([^/]+)\//)?.[1];
  if (slug) return topicCards[locale][slug].title;
  // A release can name a hub (the foundation-model rows sit on every protocol page and have method pages).
  if (hubTitle[p]) return hubTitle[p][locale];
  // The open register's two pages: a static segment beside the dataset and method pages.
  if (p === '/datasets/register/') return registerCopy[locale].datasets.title;
  if (p === '/methods/register/') return registerCopy[locale].methods.title;
  if (p !== '/') throw new Error(`release-record.ts: no title for the page ${p}`);
  return locale === 'zh' ? '核心矩阵（首页）' : 'Core matrix (home page)';
};

/** Every release with what the archive prints for it: its files' sizes and hashes, and its review manifest. */
export const records = () => releases.map(r => ({ ...r, facts: r.files.map(fileFacts), manifest: manifestOf(r) }));

// Pages a highlight may link: every page the site builds, the register pages and the archive only while built.
const unbuilt = new Set([...(registerPageBuilt ? [] : ['/datasets/register/']), ...(modelRegisterPageBuilt ? [] : ['/methods/register/']),
                         ...(releaseArchiveBuilt ? [] : ['/releases/archive/'])]);
const built = new Set<string>([...translatedPaths, ...entityPaths, ...protocolPaths].filter(p => !unbuilt.has(p)));

/** A change as text and links, in reading order: each bracketed span becomes its link. */
export const changeParts = (c: Change, locale: Locale) => {
  const parts: { text: string; href?: string }[] = [];
  let i = 0;
  for (const piece of c.text[locale].split(/(\[[^[\]]+\])/)) {
    if (!piece) continue;
    if (piece.startsWith('[')) parts.push({ text: piece.slice(1, -1), href: c.links[i++] });
    else parts.push({ text: piece });
  }
  return parts;
};

/** The newest release days in full, each with its ids, its files and its changes. */
export const latestDays = () => releaseDays().slice(0, LATEST_DAYS).map(d => ({ ...d, changes: highlights[d.date] }));
/** Every release on an earlier day, newest first. */
export const earlierReleases = () => releaseDays().slice(LATEST_DAYS).flatMap(d => d.releases);

for (const { date: day, changes } of latestDays())
  for (const c of changes) for (const link of c.links)
    if (!built.has(link.split('#')[0]))
      throw new Error(`release-record.ts: the ${day} highlight links ${link}, which the site does not build`);
