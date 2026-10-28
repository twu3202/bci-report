/**
 * The release log: every reviewed batch, what it added, what it held back.
 *
 * What a payload already records is read from the payload on the release archive
 * (/releases/archive/, release-record.ts): release IDs, dates, manifest hashes, and
 * the SHA-256 of every download, computed from the bytes being served. Only what no payload records is written here — which
 * pages a batch added, and the history of holds, including resolved ones.
 * check-workbench.mjs checks every id and date below against the payloads, and
 * every download on the archive against its file in dist/data.
 */

/**
 * Pages changed in each site update, newest first, for sitemap lastmod. A page
 * carries the date of the newest update that changed it; keeping the history
 * stops a later update from rolling an earlier page's date back.
 */
import { BINGO_HOLD, HANDWRITING_HOLD, bingoReleased, handwritingReleased } from './pilot-switch';
// The open-register release's four result files: the figures its notes print are read from them, never typed.
import ssvepFollowUps from './new-ssvep-frequencies-update.json';
import dataQuality from './data-quality-update.json';
import clinicalIesseeg from './clinical-iesseeg-update.json';
import neurolmEegmat from './neurolm-eegmat-update.json';
// The open register's files: the newest (its name is `openRegister.json` below; the two are checked equal), and the
// version before it, which its own release keeps listing (`earlierRegisters`).
import registerNow from './open-register-20261028.json';
import registerFile from './open-register-20261020.json';
// The 2026-10-28 round's four result files (owner decisions D14–D29); the round's register release is the fifth. The
// figures their entries, notes and holds print are read from them, never typed.
import ssvepCards from './ssvep-followups-update.json';
import neurorvq from './neurorvq-update.json';
import eegmatTen from './eegmat-ten-second-update.json';
import datasetChecks from './dataset-checks-update.json';
// The release log's highlights (owner decisions D17 and D29): the figures they print are read from these, never typed.
// The 2026-10-20 register file is imported by its own name, so the highlight of that day keeps its row count when a
// later register file becomes the newest.
import eegptCore from './eegpt-core-update.json';
import register20261020 from './open-register-20261020.json';

/**
 * The open register's newest version (owner decision D1): the release that ships it and its two files. The register
 * pages read these files; each later version is a new dated file and release, and earlier files stay served and
 * listed. Any link to a register page is guarded on `openRegister.json` being served (files.ts `isServed`).
 */
export const openRegister = {
  release: 'open-register-update-20261028',
  json: 'open-register-20261028.json',
  csv: 'open-register-20261028.csv',
} as const;
/**
 * The register's earlier versions, newest first. Each stays served byte for byte under its dated name (the served bytes
 * cite that release's hold ids) and is listed with its own release, which ships it.
 */
export const earlierRegisters = [
  { release: 'open-register-update-20261020', json: 'open-register-20261020.json', csv: 'open-register-20261020.csv' },
] as const;
const earlierRegister = earlierRegisters[0];

// The pilots a switch holds (pilot-switch.ts), named as the release text names them; none while every switch releases.
const pilotsHeld = [...(bingoReleased ? [] : ['bingo']), ...(handwritingReleased ? [] : ['handwriting'])];

const protocols = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target', 'semantic-target', 'sleep-scalp'];
// Every method page: the core methods' gained the Measured-on line on 2026-10-04, the v9 models' were
// first published then. Listed here because entities.ts imports this module (no cycle).
const methodPages = ['eegnet', 'labram', 'cbramod', 'shallowfbcspnet', 'deep4net', 'csp-lda', 'cca', 'fbcca', 'etrca',
  'reve', 'luna', 'brainomni', 'codebrain', 'eegmamba', 'st-eegformer', 'eeg-fm-masking', 'erp-fm', 'singlem', 'zuna', 'eegpt'];
// The seven core datasets' pages, which carry a group per core protocol (EEGPT's since 2026-10-13).
const coreDatasetPages = ['ds003810', 'eegmat', 'beta', 'ds006593', 'tmnred', 'eesm19', 'ds005342'].map(slug => `/datasets/${slug}/`);
export const siteUpdates = [
  {
    date: '2026-10-28',
    // Five releases on one day, one site version (owner decisions D14–D29): cards 8 to 14 on new-ssvep-frequencies, with
    // the route 3 page's and /jev-style/'s lines to them, fewer-electrodes' figure-free pointer to card 11 (D24) and
    // Wearable-102's link line to cards 10, 12, 13 and 14; pilot-studies' two separate panels (NeuroRVQ, the ten-second EEGMAT
    // probes) with figure-free pointers on the Arithmetic & rest, motor-imagery and P300 protocol pages (D19); four
    // cases on data-quality and Kim beta-range's dataset page (D21), which the dataset index lists; NeBULA's figure-free
    // related line on beyond-scalp-eeg (D34); the register's
    // newest file on both register pages, and the model count on the methods hub; the home holds band's three new holds
    // (Kim's amplitude-dependent models, Damm's and NeBULA's one-person scores) and the data-quality card there and on the
    // Questions hub, which names the new cases; the release log and its archive (D17), the API page and data use.
    paths: ['/', '/topics/', '/topics/new-ssvep-frequencies/', '/topics/questions-in-language/', '/jev-style/', '/topics/fewer-electrodes/',
            '/datasets/wearable-ssvep-102/', '/topics/pilot-studies/',
            '/protocols/arithmetic-rest/', '/protocols/mi-rest/', '/protocols/p300-target/',
            '/topics/data-quality/', '/topics/beyond-scalp-eeg/', '/datasets/', '/datasets/kim2025-beta-range/', '/datasets/register/', '/methods/', '/methods/register/',
            '/releases/', '/releases/archive/', '/api/', '/data-use/'],
  },
  {
    date: '2026-10-20',
    // The open-register release (owner decisions D1–D13): the two register pages, and the /datasets/ and /methods/ hubs'
    // lines to them; every dataset page's "Row in the open register" line (`datasetPages`), Shin2022's new page and its
    // group, Wearable-102's transfer group, BETA's link to the new question and its article; two new questions,
    // new-ssvep-frequencies and data-quality, with their cards on the home page and the Questions hub, and the home
    // holds band's two new holds (eldBETA's one-person score, ZuCo 2.0's converted-run timing); clinical-groups' IESSEEG
    // section and its dek; pilot-studies' separate NeuroLM panel, with its pointer on the Arithmetic & rest protocol
    // page; route 3's link to the follow-ups on questions-in-language and /jev-style/; the article lines on
    // later-sessions and model-adaptation; the release log, the API page and data use. The topic switcher on every
    // other topic page lists the two new questions too; that is navigation and is not counted here.
    paths: ['/', '/topics/', '/topics/new-ssvep-frequencies/', '/topics/data-quality/', '/topics/clinical-groups/',
            '/topics/pilot-studies/', '/protocols/arithmetic-rest/', '/topics/questions-in-language/', '/jev-style/',
            '/topics/later-sessions/', '/topics/model-adaptation/',
            '/datasets/', '/datasets/register/', '/datasets/shin2022/', '/datasets/beta/', '/datasets/wearable-ssvep-102/',
            '/methods/', '/methods/register/', '/releases/', '/api/', '/data-use/'],
    datasetPages: true,
  },
  {
    date: '2026-10-13',
    // EEGPT on the core matrix (owner decisions of 2026-10-12 and 2026-10-13): its frozen row beside the core matrix
    // on every protocol page and the protocols index, the home page's per-protocol table and masthead count, and the
    // two questions that read the further encoders (does-pretraining-help also gains EEGPT's attribution rows,
    // fewer-electrodes its BETA eight-to-four and six-channel sleep rows); its group on each core dataset page (and the
    // dataset index's group counts); its own method page, and the model directory, where its card is evaluated and it
    // leaves the not-in-the-matrix list; the pilot-studies page's link to that method page; the release log, the API
    // page and data use. The same day, before this release: one line on questions-in-language and on /jev-style/
    // linking the route-3 write-up. With it: the does-pretraining-help card on the Questions hub (three encoders,
    // EEGPT on sleep), and REFED's two source-only controls named for what they are on the pilot-studies page and on
    // REFED's dataset page (display only).
    paths: ['/', '/topics/', '/protocols/', ...protocols.map(id => `/protocols/${id}/`), '/datasets/', ...coreDatasetPages,
            '/datasets/refed/', '/methods/', '/methods/eegpt/', '/topics/does-pretraining-help/', '/topics/fewer-electrodes/',
            '/topics/pilot-studies/', '/topics/questions-in-language/', '/jev-style/', '/releases/', '/api/', '/data-use/'],
  },
  {
    date: '2026-10-12',
    // Two new questions in one version (owner decisions): beyond-scalp-eeg (fNIRS, macaque intracortical spiking, an
    // fNIRS coverage check; two sources prepared, not scored) and pilot-studies (Orthosis in three configurations of
    // one cohort, BINGO, the handwriting analysis, REFED; BINGO's and the handwriting dataset's pages only while their switches
    // release them). Their pages, their cards on the home page and the Questions hub;
    // the new dataset pages and the dataset index; /methods/, where EEGPT's directory card and its anchor say one
    // pilot comparison is published (directory-status.ts) and the not-in-the-matrix list says what it lists; the new
    // holds (the ds007420 classifier, and a pilot only while its switch holds it) on the home page and in the register;
    // the release log, the API page and data use.
    // does-pretraining-help gained one low-key pointer to the EEGPT comparison of the pilot studies (no figure).
    paths: ['/', '/topics/', '/topics/beyond-scalp-eeg/', '/topics/pilot-studies/', '/topics/does-pretraining-help/',
            '/datasets/', '/datasets/bak-fnirs/', '/datasets/nlb-mc-rtt/', '/datasets/ds007420/',
            '/datasets/orthosis-error-detection/', ...(bingoReleased ? ['/datasets/bingo-imagined-speech/'] : []),
            ...(handwritingReleased ? ['/datasets/eeg-fnirs-handwriting/'] : []), '/datasets/refed/',
            '/methods/', '/releases/', '/api/', '/data-use/'],
  },
  {
    date: '2026-10-08',
    // The later-sessions question (owner decision): its page; its card on the home page and the Questions hub, with
    // three transfer-map entries; the three new dataset pages and the dataset index; CBraMod's page (its WBCIC-SHU
    // group); one pointer on does-pretraining-help; the release log, the API page and data use. The same day the
    // site's prose stopped stating update dates and version labels (owner decision); like the "Research preview"
    // badge, that is a label about the site, not content, and is not counted here.
    // Then route 3 of the decision-research roadmap, questions in language (same version): its page; when-not-to-act's
    // roadmap, where route 3 is now run (its card lost the "Jev-style" kicker to the Jev-style card); the /jev-style/
    // page that gathers the three routes, with its card under the core matrix and on the Questions hub. Data use
    // gained the line on odd-numbered medians (Forenzo Main) and route 3's register entry (its five reused records, the
    // text encoders, REVE Large's terms, the wordings, BOAS under D11). Route-3 groups reached the BETA and BOAS pages and,
    // through their frozen-feature rows, the CBraMod page (already listed above).
    paths: ['/', '/topics/', '/topics/later-sessions/', '/topics/does-pretraining-help/',
            '/datasets/', '/datasets/wbcic-shu/', '/datasets/longitudinal-rsvp/', '/datasets/forenzo-continuous-tracking/',
            '/methods/cbramod/', '/releases/', '/api/', '/data-use/',
            '/topics/questions-in-language/', '/topics/when-not-to-act/', '/jev-style/', '/datasets/beta/', '/datasets/boas/'],
  },
  {
    date: '2026-10-07',
    // Route 2 of the decision-research roadmap, one representation and several questions: its boundary.
    // The release log, the API page and the home page's file count and Dataset markup list the batch's
    // file, and data use gains the batch's rights records (BOAS new, with its three stated gaps).
    // Then its pages (same day): the new question, shared-encoder, with its card on the home page and the
    // Questions hub; when-not-to-act's roadmap, where route 2 is now run; the BOAS dataset page and register
    // entry (and the dataset index's new row and its pointer to BOAS's gaps); route-2 groups on the OpenBMI and
    // EESM19 pages and, through them, the EEGNet and CBraMod pages. The topic switcher on every other topic page
    // lists the new question too; that is navigation and is not counted here.
    paths: ['/', '/releases/', '/api/', '/data-use/',
            '/topics/', '/topics/shared-encoder/', '/topics/when-not-to-act/',
            '/datasets/', '/datasets/boas/', '/datasets/openbmi/', '/datasets/eesm19/', '/methods/eegnet/', '/methods/cbramod/'],
  },
  {
    date: '2026-10-04',
    // Route 1 of the decision-research roadmap, reliable decisions: its results section on
    // when-not-to-act (before the roadmap, whose routes now carry their own status), the topic card
    // on the home page and the Questions hub, route-1 groups on the EEGMAT, BETA and ds003810 pages
    // (and their group counts on the dataset index) and through them the EEGNet, LaBraM, CBraMod and
    // CCA pages, the release log, data use and the API page. The v9 foundation-model files (same
    // day) reached the release log, the API page and the home page's file count and Dataset markup.
    paths: ['/', '/topics/', '/topics/when-not-to-act/', '/datasets/', '/datasets/eegmat/', '/datasets/beta/', '/datasets/ds003810/',
            '/methods/eegnet/', '/methods/labram/', '/methods/cbramod/', '/methods/cca/', '/releases/', '/data-use/', '/api/',
            // The v9 pages (same day): every protocol page and the protocols index carry the new rows;
            // the seven core dataset pages their groups (and the dataset index its group counts); the
            // model directory, the new method pages and, through the Measured-on line, every method
            // page; the LaBraM and CBraMod exposure wording on does-pretraining-help and model-adaptation.
            '/protocols/', ...protocols.map(id => `/protocols/${id}/`),
            '/datasets/ds006593/', '/datasets/tmnred/', '/datasets/eesm19/', '/datasets/ds005342/',
            '/methods/', ...methodPages.map(slug => `/methods/${slug}/`), '/topics/does-pretraining-help/', '/topics/model-adaptation/',
            // The v9 topics (same update): does-pretraining-help's new frozen encoders (sleep, BETA, the EEGMAT
            // adaptation, REVE Base against Large, the masking ablation), fewer-electrodes' BETA eight-to-four
            // and six-channel sleep comparison, model-adaptation's pointer to the v9 adaptation table; their
            // cards and the two transfer-map entries on the home page and the Questions hub.
            '/topics/fewer-electrodes/'],
  },
  {
    date: '2026-10-03',
    // The large-source batch: Dreem sleep staging got its own question,
    // sleep-staging, and dataset page; OpenBMI broadened calibration-budget to the
    // next session (new question, short answer and #next-session) and got a
    // dataset page. The home page and the Questions hub gained the sleep card and
    // the two transfer-map entries, the holds register a hold, and the dataset
    // index, data-use, API and release pages the batch. The Wearable SSVEP page
    // prints calibration-budget's question under "Where it appears", so its text
    // changed with it; model-adaptation's next-day section now points to the
    // next-session result. The topic switcher on every other topic page lists the
    // new question too; that is navigation, as the "Research preview" badge was
    // chrome, and is not counted here.
    paths: ['/', '/topics/', '/topics/sleep-staging/', '/topics/calibration-budget/', '/topics/model-adaptation/',
            '/datasets/', '/datasets/dreem-dod/', '/datasets/openbmi/', '/datasets/wearable-ssvep-102/',
            '/releases/', '/data-use/', '/api/'],
  },
  {
    date: '2026-10-02',
    // The YSU extension became the main non-control evidence on when-not-to-act
    // and reached its dataset page; LTRSVP joined screen-to-vr as a second
    // presentation change and got a dataset page; the home cards, the dataset
    // index, the API page and the release log name both. The LaBraM adaptation
    // and the next-day statuses moved from calibration-budget to their own
    // topic, model-adaptation; the EEGMAT and LaBraM pages now send readers there.
    // The home restructure (same day) moved the model directory and field notes
    // to /methods/ and the public-data register to /datasets/, and opened the
    // Questions hub at /topics/. Every other topic page and every dataset and
    // method page gained visible content the same day — a "Cite this page" block
    // and, on topics, the "Measured on" line — so they carry this date too.
    paths: ['/', '/topics/when-not-to-act/', '/topics/screen-to-vr/', '/releases/', '/data-use/', '/api/',
            '/datasets/', '/datasets/ysu-async-ssvep/', '/datasets/ltrsvp/',
            '/topics/model-adaptation/', '/topics/calibration-budget/', '/datasets/eegmat/', '/methods/labram/',
            '/topics/', '/methods/',
            '/topics/dry-vs-wet/', '/topics/fewer-electrodes/', '/topics/on-the-move/', '/topics/does-pretraining-help/',
            '/topics/clinical-groups/'],
    entityPages: true,
  },
  {
    date: '2026-10-01',
    // The adaptation results replaced the roadmap on calibration-budget and reached
    // the EEGMAT and LaBraM pages; ds003810 gained its requested citation; the API
    // page's Python example changed. Every page also lost the "Research preview"
    // badge that day, which is chrome, not content, and is not counted here.
    paths: ['/', '/topics/calibration-budget/', '/releases/', '/data-use/', '/api/',
            '/datasets/eegmat/', '/methods/labram/', '/datasets/ds003810/'],
  },
  {
    date: '2026-09-27',
    // Every topic page gained its question-form title and short answer on this
    // date; the dataset, method and API pages were first published on it.
    paths: ['/', '/topics/when-not-to-act/', '/releases/', '/topics/screen-to-vr/', '/topics/on-the-move/', '/data-use/',
            '/topics/dry-vs-wet/', '/topics/fewer-electrodes/', '/topics/calibration-budget/',
            '/topics/does-pretraining-help/', '/topics/clinical-groups/', '/api/'],
  },
] as const;

/** The current site update. */
export const pagesUpdated = siteUpdates[0];

type Text = { en: string; zh: string };

export interface Release {
  id: string;
  date: string;
  /** The payload whose release_id / releaseId this entry must match. */
  payload: 'mvp' | 'deployment' | 'evidence' | 'clinical' | 'context' | 'adaptation' | 'extension' | 'largeSource'
    | 'reliableDecisions' | 'foundationModels' | 'sharedRepresentation' | 'laterSessions' | 'questionsInLanguage'
    | 'beyondScalp' | 'pilotStudies' | 'eegptCore'
    | 'openRegister' | 'newSsvepFrequencies' | 'dataQuality' | 'clinicalIesseeg' | 'neurolmEegmat'
    | 'ssvepFollowups' | 'neurorvq' | 'eegmatTenSecond' | 'datasetChecks';
  files: string[];
  pages: string[];
  summary: Text;
  notes: Text[];
}

const protocolFiles = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target',
  'semantic-target', 'sleep-scalp'].flatMap(id => [`${id}-results.csv`, `${id}-protocol.json`]);

/** The v9 batch's per-protocol CSVs: the new rows in the core results CSVs' columns and units. */
export const foundationModelFiles = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target',
  'semantic-target', 'sleep-scalp'].map(id => `foundation-models-${id}.csv`);

/*
 * The figures the open-register release's notes print, read from the four result files and formatted as their pages
 * format them: levels at two decimals in percent, contrasts at two decimals in points with their sign, interval bounds
 * signed only when negative.
 */
const pct2 = (v: number) => `${(v * 100).toFixed(2)}%`;
const pp2 = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v * 100).toFixed(2)}`;
const bound2 = (v: number) => `${v < 0 ? '−' : ''}${Math.abs(v * 100).toFixed(2)}`;
const count = (n: number) => n.toLocaleString('en-US');
const need = <T,>(value: T | undefined, what: string): T => {
  if (value === undefined || value === null) throw new Error(`releases.ts: ${what} is missing from its file`);
  return value;
};
const ssvepCohort = ssvepFollowUps.cohort, ssvepWearable = ssvepFollowUps.wearable;
const ssvepAdapter = ssvepFollowUps.studies.cca_adapter;
const ssvepCorrected = need(ssvepAdapter.levels['RAW-RESIDUAL/u8'], 'the corrected CCA level').estimate;
const ssvepCca = need(ssvepAdapter.levels['CCA-RAW/u8'], 'the CCA level').estimate;
const ssvepGain = need(ssvepAdapter.contrasts['RAW-RESIDUAL minus CCA-RAW/u8'], 'the correction contrast');
const ssvepDry = need(ssvepFollowUps.studies.wearable_transfer.contrasts['RAW-RESIDUAL_minus_CCA-RAW/dry'], 'the dry contrast');
const ssvepWet = need(ssvepFollowUps.studies.wearable_transfer.contrasts['RAW-RESIDUAL_minus_CCA-RAW/wet'], 'the wet contrast');
const shin = dataQuality.shin2022, eld = dataQuality.eldbeta.counts;
const shinArm = (arm: string) => need(shin.arms.find(a => a.arm === arm), `the Shin2022 arm ${arm}`);
const shinChain = (id: string) => need(shin.coverage_chain.find(c => c.id === id), `the Shin2022 coverage step ${id}`).count;
const shinLine = (arm: string, zh = false) => {
  const a = shinArm(arm), [lo, hi] = a.participant_bootstrap_percentile_95.map(v => pct2(v).slice(0, -1));
  return `${pct2(a.participant_mean_balanced_accuracy)}${zh ? `（${lo}–${hi}）` : ` (${lo}–${hi})`}`;
};
const iesCohort = clinicalIesseeg.cohort, iesBand = clinicalIesseeg.age_band, iesNeurolm = clinicalIesseeg.neurolm.method;
const neurolmContrast = need(neurolmEegmat.paired_contrasts.find(c => c.id === 'tokenizer-minus-band-power'), 'the tokenizer contrast').balanced_accuracy;
const neurolmCohort = neurolmEegmat.cohort;
if (registerNow.release_id !== openRegister.release)
  throw new Error(`releases.ts: ${openRegister.json} names the release ${registerNow.release_id}, not ${openRegister.release}`);
if (registerFile.release_id !== earlierRegister.release)
  throw new Error(`releases.ts: ${earlierRegister.json} names the release ${registerFile.release_id}, not ${earlierRegister.release}`);
const regCounts = registerFile.counts, regRows = regCounts.rows, regHf = regCounts.hf, regMoabb = regCounts.moabb;
// The snapshot's retrieval time, as a date and a UTC time (the counts are that snapshot's, owner decision D11).
const regSnapshot = { day: regHf.snapshot.retrieved_at.slice(0, 10), time: regHf.snapshot.retrieved_at.slice(11, 16) };
const regDay = (zh: boolean) => { const [y, m, d] = regSnapshot.day.split('-').map(Number);
  return zh ? `${y} 年 ${m} 月 ${d} 日` : `${d} ${['January','February','March','April','May','June','July','August','September','October','November','December'][m - 1]} ${y}`; };

/*
 * The 2026-10-28 round (owner decisions D14–D29): what its four entries and three holds print, read from the four result
 * files and formatted as above, a paired difference and both its bounds signed. A sentence a file states in English is
 * printed as stated, and its Chinese is keyed below by that English, so a changed sentence has no Chinese and stops the
 * build until it is reread.
 */
const zhOf = (map: Record<string, string>, en: string, what: string) => {
  const zh = map[en];
  if (!zh) throw new Error(`releases.ts: no Chinese for ${what} as its file states it`);
  return zh;
};
const WORDS = { en: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'],
                zh: ['零', '一', '两', '三', '四', '五', '六', '七', '八', '九', '十'] };
const said = (n: number, zh = false) => need((zh ? WORDS.zh : WORDS.en)[n], `a word for ${n}`);
const cap = (s: string) => s[0].toUpperCase() + s.slice(1);
const ivl = (i: number[], zh = false) => `${pp2(i[0])}${zh ? ' 至 ' : ' to '}${pp2(i[1])}`;
type Level = { estimate: number; interval: number[] };

// Cards 8 to 14 of new-ssvep-frequencies (ssvep-followups-update.json): their numbers, cohorts and interval rules.
const sc = ssvepCards as any;
const scCards: number[] = sc.placement.cards.map((c: { card: number }) => c.card);
const scFirst = Math.min(...scCards), scLast = Math.max(...scCards);
const scU8 = need(sc.endpoints.find((e: { id: string }) => e.id === 'u8'), 'the held-out endpoint');
const scWear = need(sc.endpoints.find((e: { id: string }) => e.id === 'wearable_12'), 'the Wearable-102 endpoint');
const scBetaPeople: number = sc.studies.xspec.design.dataset.people, scWearPeople: number = sc.studies.harmonic_pooling_wearable.design.dataset.people;
const scBonf = need(sc.interval_adjustment.adjusted.find((a: { adjustment?: string }) => a.adjustment === 'Bonferroni'), 'the Bonferroni family');
const scMargin = need(sc.interval_adjustment.adjusted.find((a: { margin?: number }) => a.margin !== undefined), 'the margin test');
if (sc.interval_adjustment.other_intervals_adjusted !== false || sc.interval_adjustment.adjusted.length !== 2)
  throw new Error('releases.ts: two cards adjust their intervals and the others do not');
const scP = sc.studies.practical_settings, scCpuCard: number = scP.card, scCpu = scP.cpu_components.measurement;
if (scCpu.summed !== false || scCpu.threads !== 1 || scCpu.buffers !== 'warm' || scCpu.gpu !== false)
  throw new Error('releases.ts: the CPU component timings are warm single-thread measurements of each component, never summed');
const scCode = (study: any, name: string) => need(Object.entries(study.display_names as Record<string, string>).find(([, v]) => v === name), `the set-up "${name}"`)[0];
// The cell with the longest window and the most electrodes: the one the short answer's filter-bank figure comes from (D22).
const fbCell = [...scP.design.cells].sort((a: any, b: any) => b.samples - a.samples || b.electrodes - a.electrodes)[0];
const fbCode = scP.design.fbcca.code, scCcaCode = scCode(scP, 'CCA (no training)');
const fbLevel: Level = need(scP.levels[`${fbCell.id}/${fbCode}/u8`], 'the filter-bank CCA level');
const fbCca: Level = need(scP.levels[`${fbCell.id}/${scCcaCode}/u8`], 'the CCA level in that cell');
const fbGain: Level = need(scP.contrasts[`${fbCell.id}/${fbCode} minus ${fbCell.id}/${scCcaCode}/u8`], 'filter-bank CCA minus CCA');
const fbOther = scP.design.fbcca.other_recipe_on_site;
const scEigen = sc.studies.coherence_eigen;
const eigVsSum: Level = need(scEigen.contrasts[`${scCode(scEigen, 'eigenvalue head')} minus ${scCode(scEigen, 'harmonic sum (no training)')}/u8`],
  'the eigenvalue head minus the harmonic sum');
if (fbGain.interval[0] <= 0 || !(eigVsSum.interval[0] < 0 && eigVsSum.interval[1] > 0) || fbOther.page !== '/topics/questions-in-language/')
  throw new Error('releases.ts: the notes say filter-bank CCA is above CCA, the eigenvalue head’s interval spans zero, and the other recipe is route 3’s');
const SC_RIGHTS_ZH: Record<string, string> = {
  'BETA keeps its released record: CC BY 4.0, cohort aggregates only, with participant consent described for noncommercial scientific research. Wearable-102 keeps its released record: CC BY 4.0, cohort aggregates only. Filter-bank CCA is credited to Chen et al. 2015; the code that ran is the project’s own SciPy realisation, and no code or weights are distributed.':
    'BETA 沿用其已发布的记录：CC BY 4.0，只发布队列聚合结果，被试知情同意所述的用途为非商业科学研究。Wearable-102 沿用其已发布的记录：CC BY 4.0，只发布队列聚合结果。滤波器组 CCA 归功于 Chen 等人 2015 年的方法；实际运行的是本项目自己用 SciPy 实现的代码，不分发任何代码或权重。',
};

// NeuroRVQ's frozen backbone on three tasks (neurorvq-update.json): each block's cohort, arms and paired difference.
const nr = neurorvq as any;
const nrBlock = (id: string) => need(nr.blocks.find((b: { id: string }) => b.id === id), `the NeuroRVQ ${id} block`);
const [nrEegmat, nrMi, nrP300] = ['eegmat', 'mi-rest', 'p300-target'].map(nrBlock);
const nrFolds: number = nrEegmat.cohort.folds, nrDim: number = nr.model.pooling.dimension;
if ([nrMi, nrP300].some(b => b.cohort.folds !== nrFolds) || nr.probe.hyperparameter_search !== false || nr.model.frozen !== true
    || nr.model.weights_distributed !== false || nr.rights.weights.weights_distributed !== false || nrEegmat.paired_difference.interval_includes_zero !== true
    || nrMi.paired_difference.interval_95[1] >= 0 || nrP300.paired_difference.interval_95[1] >= 0 || nr.pretraining_exposure.status !== 'unknown'
    || nr.pretraining_exposure.datasets.some((d: { named_in_list: boolean }) => d.named_in_list))
  throw new Error('releases.ts: the NeuroRVQ notes say one fold count, nothing tuned, a frozen undistributed backbone, EEGMAT’s interval spanning zero, the other two below it, and exposure unknown');
const nrComparator = (b: any) => need(b.arms.find((a: { id: string }) => a.id === b.paired_difference.b), `the ${b.id} comparator`);
// The notes name EEGMAT's comparator and one comparator for motor imagery and P300; the Chinese is written for these.
if (nrComparator(nrEegmat).label !== 'band power' || nrComparator(nrMi).label !== 'temporal means' || nrComparator(nrP300).label !== 'temporal means'
    || nr.model.variant !== 'the released backbone with parameter-free branch normalisation and mean-token pooling')
  throw new Error('releases.ts: the NeuroRVQ notes name band power on EEGMAT, temporal means on motor imagery and P300, and the variant that ran');
/** The protocols not run, each with its gate as the file states it, in Chinese keyed by that English. */
const NR_NOT_RUN_ZH: Record<string, string> = {
  'semantic-target|the original calibration evidence is still missing': '语义目标（仍缺少原始校准证据）',
  'beta-4ch|physical units and reference are unresolved': '4 通道 BETA（物理单位与参考电极尚未厘清）',
  'beta-8ch|physical units are unresolved, and PO5 and PO6 are missing from the model’s channel list': '8 通道 BETA（物理单位尚未厘清，模型的通道列表中也没有 PO5 与 PO6）',
  'idle|its inputs are missing, and it needs its own calibration, threshold and split protocol': '空闲（缺少输入，且需要自己的校准、阈值与划分方案）',
  'sleep-scalp|deferred to a separate study': '睡眠（推迟到单独的研究）',
};
const nrNotRun = (zh: boolean) => (nr.protocols_not_run as { protocol: string; gate: string }[])
  .map(p => zh ? zhOf(NR_NOT_RUN_ZH, `${p.protocol}|${p.gate}`, `the ${p.protocol} gate`) : `${p.protocol} (${p.gate})`).join(zh ? '、' : '; ');
const NR_RIGHTS_ZH: Record<string, string> = {
  'NeuroRVQ’s code and weights are CC BY-NC 4.0, the licence file of both repositories at the pinned revisions; only aggregate figures are published, no weights are distributed, and no endorsement by NeuroRVQ’s authors is implied. EEGMAT, ds003810 and ds006593 keep their released records.':
    'NeuroRVQ 的代码与权重均为 CC BY-NC 4.0，即两个仓库在固定版本下的许可文件；只发布聚合数字，不分发任何权重，也不代表 NeuroRVQ 作者的认可。EEGMAT、ds003810 与 ds006593 沿用其已发布的记录。',
};
const NR_READING_ZH: Record<string, string> = {
  'the interval spans zero, so neither is shown to be better, and the two are not shown to be equivalent': '区间跨过零，所以既不能说明哪一方更好，也不能说明两者等效',
};

// The ten-second EEGMAT panel (eegmat-ten-second-update.json): EEG-Captioner's encoder and AXON, each against Welch band power.
const ts = eegmatTen as any, tsCohort = ts.cohort, tsQc = ts.source_annotation_qc;
const tsArm = (enc: any, role: string) => need(enc.arms.find((a: { role: string }) => a.role === role), `${enc.name}’s ${role}`);
const [tsCap, tsAx] = [ts.eeg_captioner, ts.axon];
if (tsQc.windows !== tsCohort.windows || tsQc.windows_meeting_rules !== 0 || tsQc.recordings_flagged !== tsCohort.recordings
    || tsAx.numerical_input_check.windows_passed !== tsCohort.windows || ts.encoder_contrast.published !== false
    || tsCap.baseline.matched !== true || tsAx.baseline.matched !== false || tsCap.caption_result !== false
    || tsArm(tsCap, 'baseline').balanced_accuracy !== tsArm(tsAx, 'baseline').balanced_accuracy
    || ![tsCap, tsAx].every(e => e.paired_difference.interval_includes_zero === true))
  throw new Error('releases.ts: the ten-second notes say none of the windows meets the source QC, every recording is flagged, AXON’s own check passed every window, one shared band-power baseline matched only for EEG-Captioner, no caption result, no encoder contrast, and both intervals span zero');
const TS_RIGHTS_ZH: Record<string, string> = {
  'EEGMAT keeps its released record: Open Data Commons Attribution License 1.0, aggregate results only. EEG-Captioner’s source code is MIT. EEG-Captioner’s encoder weights are Apache-2.0 as its Hugging Face weight metadata states. AXON’s checkpoint is Apache-2.0 as its Hugging Face licence tag states; its Braindecode module carries per-file Apache-2.0 terms within a BSD-3-Clause project. No weights are distributed, and no endorsement by either model’s authors is implied.':
    'EEGMAT 沿用其已发布的记录：Open Data Commons Attribution License 1.0，只发布聚合结果。EEG-Captioner 的源代码为 MIT 许可。EEG-Captioner 编码器的权重按其 Hugging Face 权重元数据为 Apache-2.0。AXON 的检查点按其 Hugging Face 许可标签为 Apache-2.0；它在 Braindecode 中的模块带有逐文件的 Apache-2.0 条款，所在项目为 BSD-3-Clause。不分发任何权重，也不代表两个模型作者的认可。',
};

// Four dataset checks (dataset-checks-update.json): Kim's worked case, MIND's conditional case, Damm's and NeBULA's status.
const dc = datasetChecks as any, kim = dc['kim2025-beta-range'], mind = dc.mind2026, damm = dc.damm, nebula = dc.nebula;
const mindSchedules: number = mind.schedule.pairs[0].schedules, mindScheduleTrials: number = mind.schedule.pairs[0].trials_per_schedule;
if (dc.cases.map((c: { id: string; status: string }) => `${c.id}:${c.status}`).join() !== 'kim2025-beta-range:released,mind2026:released_conditional,damm:score_held,nebula:score_held'
    || kim.result.chance !== 1 / kim.cohort.targets || kim.method.training_free !== true || damm.design.classes !== 5
    || mind.primary.pairs.map((p: { pair: string }) => p.pair).join() !== '4/5,6/7'
    || mind.rights.terms.statements.map((s: { source: string; value: string }) => `${s.source}:${s.value}`).join()
       !== 'paper:CC BY 4.0,archive dataset description:CC BY 4.0,MOABB adapter:CC BY-NC 4.0,ScienceDB record page:CC BY-NC 4.0'
    || ![kim, mind, nebula].every(c => c.consent_and_ethics.ethics_approval.stated && c.consent_and_ethics.informed_consent.stated)
    || mind.consent_and_ethics.ethics_approval.body !== null || !damm.consent_and_ethics.ethics_approval.stated
    || damm.consent_and_ethics.informed_consent.stated !== false || !/^the data descriptor article only/.test(nebula.rights.terms.paper_licence.covers)
    || mind.schedule.pairs.some((p: { schedules: number; trials_per_schedule: number; complementary: boolean }) => p.schedules !== mindSchedules || p.trials_per_schedule !== mindScheduleTrials || !p.complementary)
    || mind.primary.pairs.some((p: { majority: number; ordinal_lookup: number }) => p.ordinal_lookup >= p.majority)
    || damm.flags.score_published !== false || nebula.flags.score_published !== false || nebula.flags.order_diagnostic_comparison_published !== false
    || nebula.design.assistance_conditions.join() !== 'free,low,high'
    || mind.rights.terms.terms_of_use_page_read !== false || damm.rights.terms.license_file_present !== false
    || dc.holds.map((h: { id: string }) => h.id).join() !== 'kim-amplitude-dependent-models,damm-one-participant-score,nebula-one-participant-scores')
  throw new Error('releases.ts: the dataset-check notes and holds no longer fit the file');
const mindLicences = [...new Set(mind.rights.terms.statements.map((s: { value: string }) => s.value))] as string[];
const [mind45, mind67] = mind.primary.pairs;
const figshareId = (r: { source: string }) => need(r.source.match(/figshare\.(\d+)/)?.[1], `the Figshare record of ${r.source}`);
const dcHold = (id: string) => need(dc.holds.find((h: { id: string }) => h.id === id), `the hold ${id}`);
const DC_HOLD_ZH: Record<string, string> = {
  'Amplitude units, channel gains and the saved reference history are not established, so models whose output depends on amplitude are held on these files.':
    '幅值单位、通道增益与保存下来的参考历史都没有确立，所以在这些文件上，输出依赖幅值的模型暂缓。',
};

/*
 * The register's 2026-10-28 file (open-register-update-20261028, owner decisions D14–D16, D19, D21, D26, D27): what it
 * adds to the file before it, read from both files and from the payloads its new rows rest on, never typed. The four
 * dataset checks become this site's rows, each folding in its MOABB record; three models scored on the pilot-studies page
 * reach step 4; five models identified from their papers stand at step 1 with their holds.
 */
const rn = registerNow as any, rp = registerFile as any;
const rnIds = new Set<string>(rn.entries.map((e: { id: string }) => e.id)), rpIds = new Set<string>(rp.entries.map((e: { id: string }) => e.id));
const rnAdded = rn.entries.filter((e: { id: string }) => !rpIds.has(e.id));
const dcAt = (e: any) => dc.placement.sections.indexOf(String(e.links.case).split('#')[1]);
const rnSite = rnAdded.filter((e: any) => e.group === 'site').sort((a: any, b: any) => dcAt(a) - dcAt(b));
const rnScoredIds = [nr.model.id, ts.eeg_captioner.id, ts.axon.id].map(id => `r-model-${id}`);
const rnScored = rnScoredIds.map(id => need(rnAdded.find((e: any) => e.id === id), `the register row ${id}`));
const rnIdentified = rnAdded.filter((e: any) => e.ladder === 'model' && e.level === 1);
const rnFolded = rp.entries.filter((e: any) => e.group === 'moabb' && !rnIds.has(e.id));
const rnRow = (slug: string) => need(rnSite.find((e: any) => e.id === `r-site-${slug}`), `the register row of ${slug}`);
const [rnKim, rnMind, rnDamm, rnNeb] = ['kim2025-beta-range', 'mind2026', 'damm-finger-imagery', 'nebula'].map(rnRow);
const rnReasons = [...new Set(rnIdentified.flatMap((e: any) => e.findings.filter((f: any) => f.code === 'hold').map((f: any) => f.params.reason_code)))].sort();
const rnUnreachable = rnIdentified.filter((e: any) => e.findings.some((f: any) => f.params?.reason_code === 'code_not_reachable'));
if (rnSite.length !== dc.cases.length || rnSite.length !== rnFolded.length || rnSite.some((e: any) => e.level !== 4 || dcAt(e) < 0)
    || rnAdded.length !== rnSite.length + rnScored.length + rnIdentified.length || rnScored.some((e: any) => e.level !== 4 || e.exposure !== 'unknown')
    || rn.counts.rows.total !== rp.counts.rows.total + rnScored.length + rnIdentified.length || rn.counts.rows.dataset !== rp.counts.rows.dataset
    || rn.counts.moabb.merged_into_site_rows !== rp.counts.moabb.merged_into_site_rows + rnFolded.length
    || rnReasons.join() !== 'code_not_reachable,no_release_found' || rnUnreachable.length !== 1
    || !rnKim.findings.some((f: any) => f.params?.reason_code === 'amplitude_units_unresolved')
    || !rnFolded.some((e: any) => e.findings.some((f: any) => f.params?.reason_code === 'onset_timing_unresolved'))
    || rnNeb.gaps.some((g: any) => g.step === 3) || nebula.rights.terms.data_licence.versions_listed !== 1)
  throw new Error('releases.ts: the register’s new rows no longer fit what its release says of them');
const rnName = (e: any) => String(e.name).split(' · ')[0];
// The dataset rows' names in Chinese, keyed by the English the register file gives (a name without Chinese stops the build).
const RN_NAME_ZH: Record<string, string> = {
  'Kim beta-range SSVEP': 'Kim beta 频段 SSVEP', MIND: 'MIND', 'Damm finger motor imagery': 'Damm 手指运动想象', NeBULA: 'NeBULA',
};
const rnNameZh = (e: any) => zhOf(RN_NAME_ZH, rnName(e), `the name of ${e.id}`);
// "a, b and c"; in Chinese "a、b 与 c", 与 spaced only beside a Latin name.
const rnList = (xs: string[], zh = false) => {
  if (xs.length < 2) return xs.join('');
  const head = xs.slice(0, -1).join(zh ? '、' : ', '), last = xs.at(-1)!;
  return zh ? `${head}${/[\x21-\x7e]$/.test(head) ? ' ' : ''}与${/^[\x21-\x7e]/.test(last) ? ' ' : ''}${last}` : `${head} and ${last}`;
};
const rnStatus = (s: string, zh = false) => rnSite.filter((e: any) => e.status === s).map(zh ? rnNameZh : rnName);
// A row's gaps at step 3, by the file's own labels.
const rnGaps3 = (e: any, zh = false) => e.gaps.filter((g: any) => g.step === 3).map((g: any) => (zh ? g.label_zh : g.label_en));
// A part stated as two licences in a fixed order (AXON's code: the module's file terms, then the project's root licence,
// as open-register.ts words the `by` token) is printed as two parts, each named; any other part as one value.
const rnTerms = (e: any, zh = false) => {
  const t = e.terms_by_part;
  const code = t.code.by === 'module_and_project_licence'
    ? (([m, p]) => (zh ? `模块代码 ${m}、项目代码 ${p}` : `module code ${m}, project code ${p}`))(
        need(String(t.code.value).match(/^([^,]+), ([^,]+)$/)?.slice(1), `the two code licences of ${e.id}`))
    : (zh ? `代码 ${t.code.value}` : `code ${t.code.value}`);
  return zh ? `${e.name}：${code}，权重 ${t.weights.value}` : `${e.name}: ${code}, weights ${t.weights.value}`;
};

export const releases: Release[] = [
  // The 2026-10-28 round (owner decisions D14–D29): five release ids, one site version (D20). The register release is the
  // headline and the one CITATION.cff names, and goes first; these four follow in the plan's order.
  {
    id: openRegister.release, date: '2026-10-28', payload: 'openRegister',
    files: [openRegister.json, openRegister.csv],
    // Its two pages, and the methods hub, whose line counts the model rows.
    pages: ['/datasets/register/', '/methods/register/', '/methods/'],
    summary: {
      en: `The open register in a new dated file of ${count(rn.counts.rows.total)} rows: ${count(rn.counts.rows.dataset)} dataset rows and ${rn.counts.rows.model} model rows. The ${said(rnSite.length)} datasets checked end to end on the data-quality page become this site’s rows at step 4 of the dataset ladder, each with its MOABB record folded in: ${rnList(rnStatus('published'))} with their results published, and ${rnList(rnStatus('score_held'))} with their scores held. ${cap(said(rnScored.length))} models scored on the pilot-studies page enter the model ladder at step 4: ${rnList(rnScored.map(rnName))}. ${cap(said(rnIdentified.length))} more models are identified from their papers at step 1, each with its hold: ${rnList(rnIdentified.map(rnName))}. ${earlierRegister.json} stays served byte for byte.`,
      zh: `开放登记册的一份新的带日期文件，共 ${count(rn.counts.rows.total)} 行：数据集 ${count(rn.counts.rows.dataset)} 行，模型 ${rn.counts.rows.model} 行。数据质量页面上从头到尾核过的${said(rnSite.length, true)}个数据集成为本站的条目，处在数据集登记的第 4 步，各自并入其 MOABB 记录：${rnList(rnStatus('published', true), true)} 的结果已发布，${rnList(rnStatus('score_held', true), true)} 的分数暂缓。在试点研究页面上计算过分数的${said(rnScored.length, true)}个模型进入模型登记的第 4 步：${rnList(rnScored.map(rnName), true)}。另有${said(rnIdentified.length, true)}个模型依据其论文列入第 1 步，各附暂缓原因：${rnList(rnIdentified.map(rnName), true)}。${earlierRegister.json} 按原有字节继续提供。`,
    },
    notes: [
      { en: `${rnName(rnKim)}: its row links its dataset page and its case on the data-quality page, and holds models whose output depends on amplitude, in place of the onset-timing hold its MOABB record carried. ${rnName(rnMind)}: both licences side by side (${rnMind.terms_as_stated.value}), with ${rnList(rnGaps3(rnMind))} as gaps at step 3. ${rnName(rnDamm)}: ${rnList(rnGaps3(rnDamm))} as gaps at step 3. ${rnName(rnNeb)}: its Figshare record at its only version, with no gap at step 3.`,
        zh: `${rnNameZh(rnKim)}：条目链接到它的数据集页面和数据质量页面上的案例，暂缓的是输出依赖幅值的模型，取代其 MOABB 记录原有的刺激起始时间暂缓。${rnNameZh(rnMind)}：两种许可并列（${rnMind.terms_as_stated.value.split(', ').join('、')}），第 3 步缺${rnGaps3(rnMind, true).join('与')}。${rnNameZh(rnDamm)}：第 3 步缺${rnGaps3(rnDamm, true).join('与')}。${rnNameZh(rnNeb)}：Figshare 记录，只有一个版本，第 3 步没有缺口。` },
      { en: `${rnList(rnScored.map(rnName))}: each links its panel on the pilot-studies page and has no method page; pretraining exposure is unknown for all ${said(rnScored.length)}. Terms by part: ${rnScored.map(e => rnTerms(e)).join('; ')}. ${rnList(rnIdentified.map(rnName))}: each links its paper; ${rnList(rnUnreachable.map(rnName))} is held because its code repository could not be reached, and the other ${said(rnIdentified.length - rnUnreachable.length)} because no official release of code or weights was found. Not published: the register use statements drafted for some rows, which stay internal, and third-party conversions of ${rnName(rnScored[0])}’s checkpoint.`,
        zh: `${rnList(rnScored.map(rnName), true)}：各自链接到试点研究页面上的那一栏，没有方法页面；${said(rnScored.length, true)}者是否出现在预训练数据中都是未知的。各部分条款：${rnScored.map(e => rnTerms(e, true)).join('；')}。${rnList(rnIdentified.map(rnName), true)}：各自链接到论文；${rnList(rnUnreachable.map(rnName), true)} 暂缓，因为其代码仓库无法访问，其余${said(rnIdentified.length - rnUnreachable.length, true)}个暂缓，因为没有找到官方发布的代码或权重。不发布：为部分条目起草的登记册用途说明，仍只在内部；${rnName(rnScored[0])} 检查点的第三方转换版本。` },
    ],
  },
  {
    id: sc.release_id, date: '2026-10-28', payload: 'ssvepFollowups',
    files: ['ssvep-followups-update.json'],
    // Cards 8 to 14 of the question page the 2026-10-20 release opened; that release's file keeps its bytes.
    pages: ['/topics/new-ssvep-frequencies/'],
    summary: {
      en: `${cap(said(scCards.length))} more follow-ups on SSVEP frequencies a decoder never trained on, as cards ${scFirst} to ${scLast} of the same question page, each read from its own audited aggregate: the cross-spectral round’s results, which take the place of card ${scFirst}’s status entry; eigenvalue pooling; harmonic pooling, on BETA and on Wearable-102; filter-bank CCA with shorter windows and fewer electrodes; the gap between harmonics; a fixed decay over harmonics; and rising harmonic weights. All ${said(scCards.length)} use route 3’s BETA cohort (${scBetaPeople} people), and ${said(scWear.cards.length)} of them also run on Wearable-102’s dry and wet headbands (${scWearPeople} people). Seen and held-out frequencies are separate tasks, reported side by side, and each set-up sits beside its untrained control. Each card carries its own interval method: card ${scBonf.card}’s primary family is Bonferroni-adjusted over ${scBonf.comparisons} comparisons, card ${scMargin.card}’s margin test uses a ${Math.round(scMargin.level * 100)}% interval, and no other interval is adjusted. Card ${scCpuCard} adds CPU timings: warm, single-thread measurements of each component, never summed, and no sensor-to-decision latency.`,
      zh: `解码器没训练过的 SSVEP 频率又有${said(scCards.length, true)}项后续检验，作为同一问题页的第 ${scFirst} 至 ${scLast} 张卡片，每项都读自各自经审计的聚合结果：互谱一轮的结果，取代第 ${scFirst} 张卡片原来的状态说明；特征值合并；谐波合并（BETA 与 Wearable-102）；更短时间窗、更少电极下的滤波器组 CCA；谐波之间的差距；谐波的固定衰减权重；以及递增的谐波权重。${said(scCards.length, true)}项都使用第三条路线的 BETA 队列（${scBetaPeople} 名被试），其中${said(scWear.cards.length, true)}项也在 Wearable-102 的干、湿两种头带上运行（${scWearPeople} 名被试）。已见频率与留出频率是两项任务，并列报告；每种设置旁边都有不需要训练的对照。每张卡片各有自己的区间方法：第 ${scBonf.card} 张卡片的主要比较族对 ${scBonf.comparisons} 个比较做了 Bonferroni 校正，第 ${scMargin.card} 张卡片的界值检验用 ${Math.round(scMargin.level * 100)}% 区间，其余区间都没有校正。第 ${scCpuCard} 张卡片附 CPU 计时：各组件在预热后单线程测得，从不相加，也不是从传感器到决策的延迟。`,
    },
    notes: [
      { en: `On the held-out ${scU8.candidates}-way task with ${fbCell.window_s}-second windows and ${fbCell.electrodes} electrodes, filter-bank CCA with no training reached ${pct2(fbLevel.estimate)} against ${pct2(fbCca.estimate)} for CCA on the same windows (${pp2(fbGain.estimate)} points, ${ivl(fbGain.interval)}; ${scBetaPeople} people). The learned eigenvalue head differs from the harmonic sum, which needs no training, by ${pp2(eigVsSum.estimate)} points (${ivl(eigVsSum.interval)}). Route 3’s questions-in-language page runs another filter-bank recipe on the same task, with ${fbOther.sub_bands} ${fbOther.filter} sub-bands.`,
        zh: `在留出频率 ${scU8.candidates} 选 1 的任务上，用 ${fbCell.window_s} 秒时间窗、${fbCell.electrodes} 个电极，不需要训练的滤波器组 CCA 达到 ${pct2(fbLevel.estimate)}，同一批时间窗上的 CCA 为 ${pct2(fbCca.estimate)}（${pp2(fbGain.estimate)} pp，${ivl(fbGain.interval, true)}；${scBetaPeople} 名被试）。学习得到的特征值分类头与不需要训练的谐波求和相差 ${pp2(eigVsSum.estimate)} pp（${ivl(eigVsSum.interval, true)}）。第三条路线的“用语言提问”页面在同一任务上运行另一种滤波器组方案，用 ${fbOther.sub_bands} 个 ${fbOther.filter} 子带。` },
      { en: `${sc.release_record.rights} This file’s card ${scFirst} replaces the status entry that new-ssvep-frequencies-update.json carries for it; that file keeps its bytes.`,
        zh: `${zhOf(SC_RIGHTS_ZH, sc.release_record.rights, 'the SSVEP follow-ups’ rights')}本文件的第 ${scFirst} 张卡片取代 new-ssvep-frequencies-update.json 中它的状态说明；那个文件保持原有字节。` },
      { en: 'Not published: per-person, per-fold, per-rotation, per-seed, per-window and per-frequency values of any kind, predictions, scores, features, fitted heads and the sealed run files; the cross-spectral round’s per-seed, canary and random-pairing accuracies; the fixed-decay retrospective ratio table; all-trial decision counts beyond the harmonic-gap shares, and that card’s Delta means and distractor margins; run times of whole evaluations and audits, memory, CPU-time readings and every host, processor, system and runtime label; the comment thread’s predictions on these cards; the commenter’s name; and the handoffs, protocols, freezes, receipts, reviews and approvals themselves, pinned by hash in the release manifest because several carry private storage paths.',
        zh: '不发布：逐人、逐折、逐轮换、逐随机种子、逐时间窗与逐频率的任何数值，预测、分数、特征、拟合好的分类头与封存的运行文件；互谱一轮各随机种子的准确率、金丝雀检查与随机配对的准确率；固定衰减的回溯比值表；除谐波差距那张卡片的比例之外的全试次判定计数，以及那张卡片的 Delta 均值与干扰项余量；整轮评测与审计的运行时间、内存、CPU 时间读数，以及任何主机、处理器、系统与运行环境的标签；评论串对这几张卡片的预测；评论者的名字；以及交接文件、协议、冻结记录、回执、审核与批准记录本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。' },
    ],
  },
  {
    id: nr.release_id, date: '2026-10-28', payload: 'neurorvq',
    files: ['neurorvq-update.json'],
    // A separate panel on the pilot-studies page, outside its pilot count (D19); three protocol pages point to it, with no figure.
    pages: ['/topics/pilot-studies/'],
    summary: {
      en: `A separate panel on the pilot-studies page, outside the pilot count and every leaderboard: NeuroRVQ’s released backbone, kept frozen and read by one fixed ridge head, on three existing tasks: EEGMAT’s arithmetic and rest (${nrEegmat.cohort.people} people, ${count(nrEegmat.cohort.windows)} ${said(nrEegmat.cohort.window_seconds)}-second windows), motor imagery against rest on ${nrMi.dataset} (${nrMi.cohort.people} people, ${count(nrMi.cohort.windows)} windows) and P300 target against non-target on ${nrP300.dataset} (${nrP300.cohort.people} people, ${count(nrP300.cohort.windows)} ${said(nrP300.cohort.window_seconds)}-second epochs), ${nrFolds} participant-held-out folds each, nothing tuned. Each task sets the backbone’s ${nrDim} pooled values beside simple features of the same windows, with participant-mean balanced accuracy and macro-F1 for each, and one paired difference with its participant-bootstrap interval. Pointers on the three protocol pages lead to it and carry no figure; the core matrix keeps its rows.`,
      zh: `试点研究页面上单独的一栏，不计入试点数量，也不进入任何排行榜：NeuroRVQ 发布的主干保持冻结，用一个固定的岭回归分类头读取，用于三项现有任务：EEGMAT 的心算与静息（${nrEegmat.cohort.people} 名被试，${count(nrEegmat.cohort.windows)} 个${said(nrEegmat.cohort.window_seconds, true)}秒时间窗）、${nrMi.dataset} 上的运动想象对静息（${nrMi.cohort.people} 名被试，${count(nrMi.cohort.windows)} 个时间窗），以及 ${nrP300.dataset} 上的 P300 目标对非目标（${nrP300.cohort.people} 名被试，${count(nrP300.cohort.windows)} 个${said(nrP300.cohort.window_seconds, true)}秒分段），各 ${nrFolds} 折、整名被试留出，不调任何参数。每项任务都把主干的 ${nrDim} 维池化值与同一批时间窗的简单特征并列，各给出按被试平均的平衡准确率与宏平均 F1，以及一个配对差值及其被试 bootstrap 区间。三个协议页面上各有一条指向它的链接，不带任何数字；核心矩阵的各行保持不变。`,
    },
    notes: [
      { en: `NeuroRVQ minus its comparator, in balanced-accuracy points: on EEGMAT ${pp2(nrEegmat.paired_difference.difference)} (${ivl(nrEegmat.paired_difference.interval_95)}) against ${nrComparator(nrEegmat).label}: ${nrEegmat.paired_difference.reading}; on motor imagery ${pp2(nrMi.paired_difference.difference)} (${ivl(nrMi.paired_difference.interval_95)}) and on P300 ${pp2(nrP300.paired_difference.difference)} (${ivl(nrP300.paired_difference.interval_95)}) against ${nrComparator(nrMi).label}, both below zero. Pretraining exposure is unknown: none of the three datasets is named in the paper’s list of ${nr.pretraining_exposure.published_pretraining_list.corpora} pretraining corpora, ${nr.pretraining_exposure.published_pretraining_list.proprietary} of them proprietary. There is no random-initialisation arm, so the panel says nothing about pretraining. The authors’ inference wrapper does not restore strictly (${nr.model.authors_wrapper.missing_normalisation_tensors} normalisation tensors missing), so what ran is ${nr.model.variant}.`,
        zh: `NeuroRVQ 减其对照，以平衡准确率的百分点计：EEGMAT 上为 ${pp2(nrEegmat.paired_difference.difference)}（${ivl(nrEegmat.paired_difference.interval_95, true)}），对照是频带功率：${zhOf(NR_READING_ZH, nrEegmat.paired_difference.reading, 'the EEGMAT reading')}；运动想象上为 ${pp2(nrMi.paired_difference.difference)}（${ivl(nrMi.paired_difference.interval_95, true)}），P300 上为 ${pp2(nrP300.paired_difference.difference)}（${ivl(nrP300.paired_difference.interval_95, true)}），对照都是时域均值，两者都在零以下。是否出现在预训练数据中：未知。这三个数据集都不在论文列出的 ${nr.pretraining_exposure.published_pretraining_list.corpora} 个预训练语料中（其中 ${nr.pretraining_exposure.published_pretraining_list.proprietary} 个是私有的）。没有随机初始化的对照组，所以这一栏不能说明预训练的作用。作者的推理封装不能严格加载（缺少 ${nr.model.authors_wrapper.missing_normalisation_tensors} 个归一化张量），所以实际运行的是发布的主干，各分支用无参数的归一化，并对词元取均值池化。` },
      { en: `${nr.release_record.rights} Not run: ${nrNotRun(false)}. Not published: per-person, per-fold and per-window values of any kind, fold assignments, identifiers, labels, extracted values, fitted heads, predictions and the sealed files; how many people each arm scored above 50%; per-arm intervals and macro-F1 differences, none of which was computed; measured compute; the checkpoint and the authors’ source; third-party conversions of the checkpoint and the licence tags they carry; and the handoffs, protocols, configurations, receipts and reviews themselves, pinned by hash in the release manifest because several carry private storage paths.`,
        zh: `${zhOf(NR_RIGHTS_ZH, nr.release_record.rights, 'NeuroRVQ’s rights')}没有运行：${nrNotRun(true)}。不发布：任何逐人、逐折与逐时间窗的数值，折的分配、标识、标签、提取的数值、拟合好的分类头、预测与封存文件；每一组有多少人得分高于 50%；各组的区间与宏平均 F1 的差值——都没有计算；实测的计算量；检查点与作者的源代码；第三方对检查点的转换及其所带的许可标签；以及交接文件、协议、配置、回执与审核记录本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。` },
    ],
  },
  {
    id: ts.release_id, date: '2026-10-28', payload: 'eegmatTenSecond',
    files: ['eegmat-ten-second-update.json'],
    // A second separate panel on the pilot-studies page, after NeuroRVQ's; the Arithmetic & rest page points to both.
    pages: ['/topics/pilot-studies/'],
    summary: {
      en: `Another separate panel on the pilot-studies page, outside the pilot count and every leaderboard: two frozen encoders on ${said(tsCohort.window_seconds)}-second EEGMAT windows of arithmetic and rest (${tsCohort.people} people, ${tsCohort.recordings} recordings, ${tsCohort.windows} windows, ${tsCohort.folds} subject-disjoint folds), each read by one fixed ridge head and set against Welch band power on the same windows, in a subsection of its own: EEG-Captioner’s encoder (${tsCap.representation.dimension} dimensions; only the encoder ran, with no caption) and AXON (${tsAx.representation.dimension} dimensions). Participant-mean balanced accuracy and a paired difference with its participant-bootstrap interval for each; beside every score, ${tsQc.windows_meeting_rules} of ${tsQc.windows} windows meet EEG-Captioner’s source annotation-QC rules. No difference between the two encoders is computed, and the panel is kept apart from the two-second results on this site.`,
      zh: `试点研究页面上另一个单独的一栏，不计入试点数量，也不进入任何排行榜：两个冻结编码器，用于 EEGMAT 心算与静息的${said(tsCohort.window_seconds, true)}秒时间窗（${tsCohort.people} 名被试，${tsCohort.recordings} 段记录，${tsCohort.windows} 个时间窗，${tsCohort.folds} 个被试不重叠的折），各用一个固定的岭回归分类头读取，并与同一批时间窗上的 Welch 频带功率比较，各占一小节：EEG-Captioner 的编码器（${tsCap.representation.dimension} 维；只运行了编码器，没有生成描述）与 AXON（${tsAx.representation.dimension} 维）。各给出按被试平均的平衡准确率，以及一个配对差值及其被试 bootstrap 区间；每个分数旁边都注明：${tsQc.windows} 个时间窗中有 ${tsQc.windows_meeting_rules} 个符合 EEG-Captioner 来源的标注质量控制规则。不计算两个编码器之间的差值；这一栏与本站的两秒时间窗结果分开。`,
    },
    notes: [
      { en: `EEG-Captioner’s encoder reached ${pct2(tsArm(tsCap, 'encoder').balanced_accuracy)} against ${pct2(tsArm(tsCap, 'baseline').balanced_accuracy)} for Welch band power fitted in the same run (${pp2(tsCap.paired_difference.difference)} points, ${ivl(tsCap.paired_difference.interval_95)}). AXON reached ${pct2(tsArm(tsAx, 'encoder').balanced_accuracy)} against the same band-power predictions, reused without refitting and matched for neither normalisation nor parameter count (${pp2(tsAx.paired_difference.difference)} points, ${ivl(tsAx.paired_difference.interval_95)}). Both intervals span zero. AXON’s own numerical input check passed ${tsAx.numerical_input_check.windows_passed} of ${tsAx.numerical_input_check.windows} windows, a different check from the source QC, which flags whole recordings (${tsQc.recordings_flagged} of ${tsQc.recordings}) and does not say that each window has an artifact. AXON ran after the EEG-Captioner and Welch outcomes were known; rest is recorded before arithmetic; pretraining exposure is unknown for both encoders.`,
        zh: `EEG-Captioner 的编码器达到 ${pct2(tsArm(tsCap, 'encoder').balanced_accuracy)}，同一次运行中拟合的 Welch 频带功率为 ${pct2(tsArm(tsCap, 'baseline').balanced_accuracy)}（${pp2(tsCap.paired_difference.difference)} pp，${ivl(tsCap.paired_difference.interval_95, true)}）。AXON 达到 ${pct2(tsArm(tsAx, 'encoder').balanced_accuracy)}，对照是同一组频带功率预测，没有重新拟合，归一化与参数量都没有匹配（${pp2(tsAx.paired_difference.difference)} pp，${ivl(tsAx.paired_difference.interval_95, true)}）。两个区间都跨过零。AXON 自己的数值输入检查在 ${tsAx.numerical_input_check.windows} 个时间窗中通过了 ${tsAx.numerical_input_check.windows_passed} 个；这与来源的质量控制是两回事，后者按整段记录标记（${tsQc.recordings} 段中标记了 ${tsQc.recordings_flagged} 段），并不说明每个时间窗都有伪迹。AXON 是在 EEG-Captioner 与 Welch 的结果已知之后运行的；静息在心算之前记录；这些数据是否出现在两个编码器的预训练数据中，都是未知的。` },
      { en: `${ts.release_record.rights} Not published: per-person, per-fold and per-window values of any kind, fold assignments, identifiers, features, fitted heads, predictions and the sealed files; confusion matrices and pooled macro-F1; the source-QC breakdown beyond its totals; forward counts, head-fit counts, CPU and wall time and memory; a difference between the two encoders; AXON’s paper reference, until it is checked; the checkpoints and weights, whose SHA-256 identifies each file and grants nothing; and the handoffs, protocols, approvals, reviews, audits and receipts themselves, pinned by hash in the release manifest because several carry private storage paths.`,
        zh: `${zhOf(TS_RIGHTS_ZH, ts.release_record.rights, 'the ten-second panel’s rights')}不发布：任何逐人、逐折与逐时间窗的数值，折的分配、标识、特征、拟合好的分类头、预测与封存文件；混淆矩阵与合并计算的宏平均 F1；来源质量控制除总数之外的细分；前向计算次数、分类头拟合次数、CPU 与实际耗时以及内存；两个编码器之间的差值；AXON 的论文出处，核实之前不引用；检查点与权重——其 SHA-256 只用于标识文件，不授予任何权利；以及交接文件、协议、批准、审核、审计与回执本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。` },
    ],
  },
  {
    id: dc.release_id, date: '2026-10-28', payload: 'datasetChecks',
    files: ['dataset-checks-update.json'],
    // Four cases on the data-quality page (D15, D16, D18); Kim beta-range's dataset page carries its result (D21).
    pages: ['/topics/data-quality/'],
    summary: {
      en: `${cap(said(dc.cases.length))} more public EEG datasets checked end to end on the data-quality page, each read from its own files. Kim beta-range SSVEP is a worked case: training-free CCA on all ${kim.cohort.participants} participants (${count(kim.cohort.trials)} trials, ${kim.cohort.targets} targets from ${kim.intake.frequency_lowest_hz.toFixed(1)} to ${kim.intake.frequency_highest_hz.toFixed(1)} Hz), with a dataset page of its own. MIND is a conditional case on record IDs: CSP + LDA on ${said(mind.primary.pairs.length)} stored-code pairs beside an ordinal lookup and a majority control, with record-ID resampling ranges and the facts of its label schedules. Damm finger motor imagery and NeBULA are one-person status cases: design, counts and file facts, with every score held. The one-person rule is stated once on the page, before eldBETA, Damm and NeBULA.`,
      zh: `数据质量页面上又有${said(dc.cases.length, true)}个公开 EEG 数据集从头到尾核了一遍，都从各自的文件读起。Kim beta 频段 SSVEP 是完整的案例：在全部 ${kim.cohort.participants} 名被试上运行不需要训练的 CCA（${count(kim.cohort.trials)} 个试次，${kim.cohort.targets} 个目标，${kim.intake.frequency_lowest_hz.toFixed(1)} 至 ${kim.intake.frequency_highest_hz.toFixed(1)} Hz），并有自己的数据集页面。MIND 是以记录编号为单位的有条件案例：在${said(mind.primary.pairs.length, true)}对存储编码上运行 CSP + LDA，与按位置查表的对照和多数类对照并列，附记录编号重抽样范围与标签排程的事实。Damm 手指运动想象与 NeBULA 是单人状态案例：只给设计、计数与文件事实，所有分数暂缓。单人规则在页面上只说一次，放在 eldBETA、Damm 与 NeBULA 之前。`,
    },
    notes: [
      { en: `Kim: mean participant accuracy ${pct2(kim.result.mean_participant_accuracy)} (${pct2(kim.result.accuracy_interval_95[0])} to ${pct2(kim.result.accuracy_interval_95[1])}), against chance of one in ${kim.cohort.targets}; the amplitudes are as stored, and models whose output depends on amplitude are held. MIND, primary panel of ${mind.primary.record_ids} record IDs and ${count(mind.primary.trials)} trials: CSP + LDA ${pct2(mind45.csp_lda)} on stored codes ${mind45.pair} and ${pct2(mind67.csp_lda)} on ${mind67.pair}, against ${pct2(mind45.majority)} for the majority control; the ordinal lookup sits below the majority control because each pair follows one of only ${said(mindSchedules)} complementary ${mindScheduleTrials}-trial label schedules. Record IDs are not verified people. Damm: ${damm.design.delivered_cues} delivered cues over ${said(damm.design.classes)} fingers and ${damm.files.scalp_channels} scalp channels. NeBULA: ${nebula.design.trials} delivered trials, ${nebula.eeg.channels} EEG channels and ${nebula.file_facts.emg_channel_rows} EMG rows where the metadata states ${nebula.file_facts.emg_channels_in_metadata}.`,
        zh: `Kim：按被试平均的准确率为 ${pct2(kim.result.mean_participant_accuracy)}（${pct2(kim.result.accuracy_interval_95[0])} 至 ${pct2(kim.result.accuracy_interval_95[1])}），随机水平为 ${kim.cohort.targets} 选 1；幅值按存储原样，输出依赖幅值的模型暂缓。MIND，主面板 ${mind.primary.record_ids} 个记录编号、${count(mind.primary.trials)} 个试次：CSP + LDA 在存储编码 ${mind45.pair} 上为 ${pct2(mind45.csp_lda)}，在 ${mind67.pair} 上为 ${pct2(mind67.csp_lda)}，多数类对照为 ${pct2(mind45.majority)}；按位置查表的对照低于多数类对照，是因为每一对编码只遵循${said(mindSchedules, true)}种互补的 ${mindScheduleTrials} 试次标签排程之一。记录编号并非核实过的人。Damm：${said(damm.design.classes, true)}个手指共 ${damm.design.delivered_cues} 个实际呈现的提示，${damm.files.scalp_channels} 个头皮通道。NeBULA：${nebula.design.trials} 个实际进行的试次，${nebula.eeg.channels} 个 EEG 通道，EMG 文件有 ${nebula.file_facts.emg_channel_rows} 行通道，而元数据写的是 ${nebula.file_facts.emg_channels_in_metadata}。` },
      { en: `Licences, from each record: Kim ${kim.rights.license} (Figshare ${figshareId(kim.rights)}, version ${kim.rights.terms.data_licence.pinned_version}, which the research used; the paper cites version ${kim.rights.terms.paper_cited_version.version}, also ${kim.rights.terms.paper_cited_version.licence}); MIND ${mindLicences.join(' and ')} side by side, as the paper and the archive’s dataset description state the first and the MOABB adapter and the ScienceDB record’s metadata the second, with ScienceDB’s terms-of-use page not read; Damm ${damm.rights.license} as its dataset description states, while its README cites a LICENSE file the tree does not hold; NeBULA ${nebula.rights.license} (Figshare ${figshareId(nebula.rights)}), the paper’s own licence covering the article only. Kim’s, MIND’s and NeBULA’s papers state ethics approval and consent, MIND’s without naming its committee; Damm’s dataset description names its ethics approval, and no consent statement was found. Not published: values per person, per record ID, per fold, per run or per trial, identifiers, features, fitted models, predictions and raw signals; every Damm and NeBULA score and any comparison of NeBULA’s order diagnostic with its EEG or EMG arms; MIND’s pooled metrics, confusion matrices, secondary schedule census and model-fit counts; Kim’s per-participant accuracies; compute, hosts and storage locations; and the research aggregates, audits, reviews, protocols and handoffs themselves, pinned by hash in the release manifest because several carry private storage paths.`,
        zh: `许可来自各自的记录：Kim 为 ${kim.rights.license}（Figshare ${figshareId(kim.rights)}，研究所用的第 ${kim.rights.terms.data_licence.pinned_version} 版；论文引用的是第 ${kim.rights.terms.paper_cited_version.version} 版，同样为 ${kim.rights.terms.paper_cited_version.licence}）；MIND 的 ${mindLicences.join(' 与 ')} 并列给出：论文与压缩包中的数据集说明写的是前者，MOABB 适配器与 ScienceDB 记录的元数据写的是后者，ScienceDB 的使用条款页面没有读取；Damm 按其数据集说明为 ${damm.rights.license}，而其 README 提到的 LICENSE 文件并不在仓库中；NeBULA 为 ${nebula.rights.license}（Figshare ${figshareId(nebula.rights)}），论文自己的许可只涵盖文章本身。Kim、MIND 与 NeBULA 的论文都写明了伦理批准与知情同意，MIND 的论文没有写出伦理委员会的名称；Damm 的数据集说明写明了伦理批准，没有找到知情同意声明。不发布：逐人、逐记录编号、逐折、逐 run 与逐试次的数值，标识、特征、拟合好的模型、预测与原始信号；Damm 与 NeBULA 的任何分数，以及 NeBULA 的顺序诊断与其 EEG 或 EMG 组之间的任何比较；MIND 合并计算的指标、混淆矩阵、次要面板的排程统计与模型拟合次数；Kim 的逐被试准确率；计算量、主机与存储位置；以及研究聚合文件、审计、审核、协议与交接文件本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。` },
    ],
  },
  // The open-register release (owner decisions D1–D13, 2026-10-19): five release ids, one site version. The register
  // is the headline, the one CITATION.cff and the home Dataset cite; the four result files follow in the plan's order.
  {
    id: earlierRegister.release, date: '2026-10-20', payload: 'openRegister',
    files: [earlierRegister.json, earlierRegister.csv],
    // Its two pages, and the dataset and method hubs, which link them.
    pages: ['/datasets/register/', '/methods/register/', '/datasets/', '/methods/'],
    summary: {
      en: `The open register: every EEG dataset we know of and every EEG model and paper we track, each with the furthest step we have checked and what that step showed, in ${count(regRows.total)} rows (${count(regRows.dataset)} dataset rows and ${regRows.model} model rows). Two ladders with their own step names: a dataset is listed, read, traced, run here and in the core matrix; a model is identified, has its terms recorded and its files checked, is scored here and in the core matrix. Each row keeps the evidence for every step as pass, gap or not applicable, with its source, so its step is the furthest one whose evidence is on file and its gaps stay visible. The dataset rows come in five groups: uploads on Hugging Face that hold brain-signal data, from a frozen snapshot of ${regHf.snapshot.search_terms} search terms and ${regHf.snapshot.tag_filters} tag filters read on ${regDay(false)} at ${regSnapshot.time} UTC (${count(regHf.snapshot.listings)} listings, ${count(regHf.snapshot.eegdash_mirrors)} of them EEGDash mirrors, and ${count(regHf.in_scope)} other uploads in scope); OpenNeuro’s mirrors on EEGDash, as one family row; this site’s own datasets; the catalog of MOABB release ${regMoabb.release}, one row per source record (${regMoabb.loaders} loaders over ${regMoabb.record_groups} records, ${regMoabb.merged_into_site_rows} of them merged into this site’s rows); and corpora that require an agreement or request, with their access terms as captured from the source. Anything can be listed here; the score tables keep their own rules.`,
      zh: `开放登记册：我们知道的每个 EEG 数据集、关注的每个 EEG 模型与论文，各自核验到了哪一步、那一步看到了什么，共 ${count(regRows.total)} 行（数据集 ${count(regRows.dataset)} 行，模型 ${regRows.model} 行）。两条核验序列，各有自己的步骤名称：数据集依次为已列出、已读取、已追溯、在本站运行、进入核心矩阵；模型依次为已识别、已记录条款、已检查文件、在本站评分、进入核心矩阵。每一行都保留每一步的证据——通过、缺口或不适用，并注明出处——所以一行所处的步骤，就是证据已在案的最远一步，缺口也一直可见。数据集分五组：Hugging Face 上含脑信号数据的上传，来自冻结的一次检索快照（${regHf.snapshot.search_terms} 个检索词与 ${regHf.snapshot.tag_filters} 个标签筛选，于 ${regDay(true)} UTC ${regSnapshot.time} 读取：${count(regHf.snapshot.listings)} 条列表，其中 ${count(regHf.snapshot.eegdash_mirrors)} 条是 EEGDash 镜像，另有 ${count(regHf.in_scope)} 个上传在收录范围内）；EEGDash 上的 OpenNeuro 镜像，合为一个系列行；本站自己的数据集；MOABB ${regMoabb.release} 版的目录，每个原始记录一行（${regMoabb.loaders} 个加载器对应 ${regMoabb.record_groups} 个记录，其中 ${regMoabb.merged_into_site_rows} 个并入本站的行）；以及需要签署协议或提出申请的语料，附从来源页面存档的访问条款。任何数据集都可以列在这里；分数表照旧按自己的规则。`,
    },
    notes: [
      { en: 'The rules, stated once on the register: gated data, or data that needs a signed or requested agreement, stays at step 1 unless we accept its terms; suspected re-uploads stay at step 1 whatever their gating, compared by metadata only, with none of their files downloaded; a finding about a re-upload is stated only when an independent check confirms it and a captured page of the original terms backs it, and then in factual words: that an upload matches another source’s metadata, or that its declared terms differ from the original terms; rows state facts; and every row has a correction route, a mail that names the row’s id. The CSV carries no findings; they are in the JSON. Repository ids and usernames appear in a row’s text, never in a link or an anchor; an uploader’s series of repositories is one family row; card text, download counts and modification dates are not shown.',
        zh: '登记册上只说一次的规则：需要授权才能获取的数据，或需要签署、申请协议的数据，除非我们接受其条款，否则停留在第 1 步；疑似转传的数据无论是否需要授权都停留在第 1 步，只按元数据比对，不下载任何文件；关于转传的发现，只有经独立核查确认、并有原始条款页面的存档为据时才会写出，而且只用陈述事实的措辞：某个上传与另一来源的元数据一致，或其声明的条款与原始条款不同；每一行只陈述事实；每一行都有更正途径，即一封写明该行编号的邮件。CSV 不含任何发现，发现都在 JSON 里。仓库编号与用户名只出现在行的正文里，从不出现在链接或锚点中；同一上传者的一系列仓库合为一个系列行；不显示数据卡片原文、下载次数与修改日期。' },
      { en: 'The register now lists sources that give a reader nothing to run, such as L-FAME (CC BY-NC 4.0), because it records what was checked. Each later register version is a new dated file and release; this file stays served and listed.',
        zh: '登记册现在也列出那些读者无从运行的数据源，例如 L-FAME（CC BY-NC 4.0），因为它记录的是核验过什么。之后每一版登记册都是一个新的带日期的文件和一次新的发布；这个文件会继续提供下载，并保留在列表中。' },
    ],
  },
  {
    id: ssvepFollowUps.release_id, date: '2026-10-20', payload: 'newSsvepFrequencies',
    files: ['new-ssvep-frequencies-update.json'],
    // Its own question page; Wearable-102's dataset page carries the transfer group, and the route 3 page one link.
    pages: ['/topics/new-ssvep-frequencies/'],
    summary: {
      en: `Route 3’s follow-ups on SSVEP frequencies a decoder never trained on, on a new question page: seven audited studies that answer questions from a reader’s comments on Hugging Face. Six reuse route 3’s BETA cohort and splits (${ssvepCohort.people} people, ${ssvepCohort.person_folds} participant folds by ${ssvepCohort.frequency_rotations} frequency rotations, ${ssvepCohort.seen_frequencies} seen and ${ssvepCohort.held_out_frequencies} held-out frequencies; trained heads over ${ssvepCohort.training_seeds} seeds), each testing one idea: asking with the reference spectrum; the head, the spectrum or the question; a random delay on a phase-carrying query; a random phase ramp with magnitude queries; where CCA’s lead comes from; and a bounded learned correction on top of CCA. The seventh runs the correction’s models unchanged on Wearable-102’s dry and wet headbands (${ssvepWearable.people} people). Each card gives its question, what changed, the matched control, the result and its limit; every interval is its own study’s, and no multiplicity correction was applied. A status card for the cross-spectral round carries no figures; that round ships as its own release.`,
      zh: `第三条路线关于“解码器没训练过的 SSVEP 频率”的后续检验，放在一个新的问题页上：七项经审计的研究，回答一位读者在 Hugging Face 的评论中提出的问题。其中六项沿用第三条路线的 BETA 队列与数据划分（${ssvepCohort.people} 名被试，${ssvepCohort.person_folds} 个被试折 × ${ssvepCohort.frequency_rotations} 种频率轮换，${ssvepCohort.seen_frequencies} 个已见频率与 ${ssvepCohort.held_out_frequencies} 个留出频率；训练的分类头各跑 ${ssvepCohort.training_seeds} 个随机种子），每项检验一个想法：用参考谱来提问；是分类头、频谱还是提问方式；带相位查询上的随机延迟；幅度查询下的随机相位斜坡；CCA 的领先从哪里来；以及在 CCA 之上加一个有界的学习修正。第七项把这个修正的模型原样用在 Wearable-102 的干、湿两种头带上（${ssvepWearable.people} 名被试）。每张卡片依次给出问题、改了什么、匹配的对照、结果与局限；每个区间都是该项研究自己的区间，没有做多重比较校正。互谱一轮只有一张没有数字的状态卡，那一轮将作为单独的发布上线。`,
    },
    notes: [
      { en: `On frequencies left out of training, temporal CCA with a small learned correction reached ${pct2(ssvepCorrected)} against ${pct2(ssvepCca)} for CCA alone, choosing among ${ssvepCohort.held_out_frequencies} frequencies (${pp2(ssvepGain.estimate)} points, ${bound2(ssvepGain.interval[0])} to ${bound2(ssvepGain.interval[1])}; ${ssvepCohort.people} people). Run unchanged on Wearable-102, the same models changed CCA’s score by ${pp2(ssvepDry.estimate)} points on dry electrodes (${bound2(ssvepDry.interval[0])} to ${bound2(ssvepDry.interval[1])}) and ${pp2(ssvepWet.estimate)} on wet (${bound2(ssvepWet.interval[0])} to ${bound2(ssvepWet.interval[1])}). Learned heads that read reference spectra or stimulus phase stayed far below CCA.`,
        zh: `在训练时留出的频率上，时域 CCA 加一个小的学习修正，${ssvepCohort.held_out_frequencies} 选 1 达到 ${pct2(ssvepCorrected)}，CCA 单独为 ${pct2(ssvepCca)}（${pp2(ssvepGain.estimate)} pp，${bound2(ssvepGain.interval[0])} 至 ${bound2(ssvepGain.interval[1])}；${ssvepCohort.people} 名被试）。同一批模型原样用于 Wearable-102，相对 CCA 的变化为干电极 ${pp2(ssvepDry.estimate)} pp（${bound2(ssvepDry.interval[0])} 至 ${bound2(ssvepDry.interval[1])}）、湿电极 ${pp2(ssvepWet.estimate)} pp（${bound2(ssvepWet.interval[0])} 至 ${bound2(ssvepWet.interval[1])}）。读参考谱或刺激相位的学习型分类头远低于 CCA。` },
      { en: `${ssvepFollowUps.release_record.rights} The stimulus phases of one query come from the BETA authors’ corrigendum, read at a pinned revision of the Hugging Face mirror ${ssvepFollowUps.rights.corrigendum.mirror}. The Wearable-102 documentation cannot rule out that some of its participants also appear in BETA.`,
        zh: `BETA 沿用其已发布的记录：CC BY 4.0，只发布队列聚合结果，被试知情同意所述的用途为非商业科学研究。Wearable-102 沿用其已发布的记录：CC BY 4.0，只发布队列聚合结果。冻结的 CBraMod 特征就是第三条路线所用的那一份，不分发任何权重。其中一种查询所用的刺激相位，取自 BETA 作者的更正说明，读自 Hugging Face 镜像 ${ssvepFollowUps.rights.corrigendum.mirror} 的一个固定版本。Wearable-102 的文档无法排除其中部分被试也出现在 BETA 中。` },
      { en: 'Not published: per-person, per-fold, per-rotation, per-seed, per-window and per-frequency values, predictions, scores, features, fitted heads and the sealed run files; the adapter’s per-seed accuracies and the transitions of the cropped-match correction; the Wearable-102 contrast against the cropped-spectrum check; the commenter’s name; measured compute; and the handoffs, protocols, freezes, receipts and reviews themselves, pinned by hash in the release manifest because several carry private storage paths.',
        zh: '不发布：逐人、逐折、逐轮换、逐随机种子、逐时间窗与逐频率的任何数值，预测、分数、特征、拟合好的分类头与封存的运行文件；修正模型各随机种子的准确率，以及裁剪谱匹配加修正那一组的判定转变；Wearable-102 上相对裁剪谱核查的对比；评论者的名字；实测的计算量；以及交接文件、协议、冻结记录、回执与审核记录本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。' },
    ],
  },
  {
    id: dataQuality.release_id, date: '2026-10-20', payload: 'dataQuality',
    files: ['data-quality-update.json'],
    // Its own question page; Shin2022's new dataset page carries its three arms.
    pages: ['/topics/data-quality/'],
    summary: {
      en: `A new question page: what do the files show once a public EEG dataset is checked end to end? Three public datasets, each read from its own files. Shin2022 is the worked case: a participant-held-out diagnostic over ${shin.scope.participants} people with three arms (a participant-weighted training prior, a normalised spectral ridge on the first second of cursor feedback, and a retrospective control that reads only the feedback duration), scored on the signal-valid windows that its coverage chain counts from the runs in the release. eldBETA and ZuCo 2.0 are status cases with no score: one participant’s eldBETA recordings, as counts, and a timing hold on one converted ZuCo 2.0 run.`,
      zh: `一个新的问题页：把公开 EEG 数据集从头到尾核一遍，文件里能看到什么？三个公开数据集，都从各自的文件读起。Shin2022 是完整的案例：在 ${shin.scope.participants} 名被试上做整名被试留出的诊断，共三个组（按被试等权的训练集先验、在光标反馈第一秒上的归一化 spectral ridge，以及只读反馈时长的回溯对照）；评分所用的是信号有效的时间窗，由覆盖链从发布中的 run 一路清点而来。eldBETA 与 ZuCo 2.0 是没有分数的状态案例：eldBETA 一名被试的记录，只给计数；ZuCo 2.0 一个转换后记录的时间问题，暂缓。`,
    },
    notes: [
      { en: `Shin2022: in the release, ${shinChain('byte_identical_pairs')} pairs of runs are byte-identical, so the files hold ${shinChain('distinct_runs')} distinct runs, and one incomplete run is held whole. On the signal-valid windows the normalised spectral ridge reached ${shinLine('normalized_spectral_ridge')} participant-mean balanced accuracy and the duration control ${shinLine('retrospective_duration_ridge')}, against ${pct2(shinArm('training_prior').participant_mean_balanced_accuracy)} for the prior. ${shin.caveat} ${shin.catalog.reading}`,
        zh: `Shin2022：发布中有 ${shinChain('byte_identical_pairs')} 对 run 逐字节相同，所以文件里实际是 ${shinChain('distinct_runs')} 个不同的 run；另有一个不完整的 run 整个暂缓。在信号有效的时间窗上，归一化 spectral ridge 按被试平均的平衡准确率为 ${shinLine('normalized_spectral_ridge', true)}，时长对照为 ${shinLine('retrospective_duration_ridge', true)}，训练集先验为 ${pct2(shinArm('training_prior').participant_mean_balanced_accuracy)}。分数只覆盖信号有效的时间窗：反馈至少持续一秒，且第一秒在全部 ${shin.scope.channels} 个通道上都是有限值、${shin.method.reference_band_hz.join('–')} Hz 功率为正。标签是闭环光标记录中指示的目标，带有视觉、控制器与行为上的混杂。时长对照读的是整段反馈时长，要到试次结束才知道，所以它检验的是一个混杂；频谱这一组与它相差无几，组间没有做检验。${shin.scope.participants} 名被试，每人一个记录日；区间是描述性的。目录中 ${shin.catalog.catalog_trial_seconds} 秒的试次时长，是每个 run 的文件头都设定的反馈上限（MaxFeedbackDuration）。` },
      { en: `eldBETA: the raw-recording route runs end to end on one participant’s ${eld.blocks} blocks: all ${eld.trials} trials pass the reader and the quality checks, and ${eld.trials_dropped === 0 ? 'none is dropped' : `${eld.trials_dropped} are dropped`}. The continuous recordings hold ${count(eld.non_finite_values_outside_analysed_windows)} non-finite values outside the analysed windows, left as recorded. With one person every score is that person’s, so the accuracy is held, by the owner’s decision. The header calibration was applied, and the derived MATLAB epochs were not used. ZuCo 2.0: in one converted run on NEMAR, some fixation times fall outside the recording, so no EEG–text score is computed until the converter’s timing rules and a source-checksummed fixture are available.`,
        zh: `eldBETA：从原始记录读起的流程，在一名被试的 ${eld.blocks} 个组块上从头到尾跑通：全部 ${eld.trials} 个试次都通过了读取与质量检查，${eld.trials_dropped === 0 ? '没有一个被剔除' : `剔除 ${eld.trials_dropped} 个`}。连续记录中，分析时间窗之外有 ${count(eld.non_finite_values_outside_analysed_windows)} 个非有限值，按记录原样保留。只有一个人时，任何分数都是这个人的分数，所以准确率按所有者的决定暂缓。读取时应用了文件头中的定标，没有使用派生的 MATLAB 分段。ZuCo 2.0：在 NEMAR 上一个转换后的记录中，有些注视时间落在记录之外，所以在转换程序的时间规则与带源校验和的测试样例具备之前，不计算任何 EEG–文本分数。` },
      { en: `Licences, from each record: Shin2022 ${shin.rights.license} (Figshare 20383716), eldBETA ${dataQuality.eldbeta.rights.license} (Figshare 18032669), ZuCo 2.0 ${dataQuality.zuco2.source.licence_as_stated} as its NEMAR dataset description states, with the original terms on OSF and the terms of the quoted text excerpts unverified. Shin2022’s paper names its approving board and states written informed consent; eldBETA’s data descriptor gives its board’s approval number and states written consent; for ZuCo 2.0 no consent or ethics statement was read in this release. Not published: participant rows of any kind and raw signals; Shin2022’s per-participant figures, feedback-duration distribution and per-channel census counts; eldBETA’s one-participant accuracy and its comparator; ZuCo 2.0’s converted-run code, timing values and marker counts; compute; and the research exports, audits, reviews, protocols and handoffs themselves, pinned by hash in the release manifest because several carry private storage paths. MOABB’s catalog counts for Shin2022 are findings on its row in the open register.`,
        zh: `许可来自各自的记录：Shin2022 为 ${shin.rights.license}（Figshare 20383716），eldBETA 为 ${dataQuality.eldbeta.rights.license}（Figshare 18032669），ZuCo 2.0 按其 NEMAR 数据集说明为 ${dataQuality.zuco2.source.licence_as_stated}，OSF 上的原始条款与刺激所引文本片段的条款尚未核实。Shin2022 的论文写明了批准研究的伦理委员会，并说明被试签署了书面知情同意；eldBETA 的数据描述论文给出了伦理批件编号，并说明被试签署了书面同意；ZuCo 2.0 在本次发布中没有读到知情同意或伦理声明。不发布：任何形式的逐被试数据与原始信号；Shin2022 的逐被试数字、反馈时长的分布与逐通道的普查计数；eldBETA 那一名被试的准确率及其对照；ZuCo 2.0 转换后记录的编号、时间数值与标记计数；计算量；以及研究导出文件、审计、审核、协议与交接文件本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。MOABB 目录中 Shin2022 的计数，作为发现写在开放登记册中它的那一行。` },
    ],
  },
  {
    id: clinicalIesseeg.release_id, date: '2026-10-20', payload: 'clinicalIesseeg',
    files: ['clinical-iesseeg-update.json'],
    // A section of the clinical-groups page (owner decision D13); no dataset page and no count.
    pages: ['/topics/clinical-groups/'],
    summary: {
      en: `A new section on the clinical-groups page, with its own question: do EEG case-control results survive age and recording-setting controls? IESSEEG, a public infant EEG dataset (${iesCohort.people} people: ${iesCohort.cases} cases of infantile epileptic spasms syndrome and ${iesCohort.controls} controls, one awake minute each), on the publisher’s ${iesCohort.folds} participant-disjoint folds: six arms with and without EEG, including an age-only control, a recording-settings-only control and EEG after age is regressed out inside each training fold, and four arms that read frozen NeuroLM features with the same probes. Out-of-fold point estimates of balanced accuracy and AUROC, both shown for every arm, for everyone and for the ${iesBand.people} people aged ${iesBand.maximum_age_years} or under. The page’s Parkinson’s question, short answer and card keep their wording, and IESSEEG adds no dataset page or count.`,
      zh: `临床分组页面上新增的一节，有自己的问题：EEG 病例对照结果经得起年龄与采集设置校正吗？IESSEEG 是一个公开的婴儿 EEG 数据集（${iesCohort.people} 名被试：${iesCohort.cases} 例婴儿癫痫性痉挛综合征病例与 ${iesCohort.controls} 名对照，每人一分钟清醒期记录），使用发布者给出的 ${iesCohort.folds} 个被试不重叠的折：六个使用或不使用 EEG 的组，包括只用年龄的对照、只用采集设置的对照，以及在每个训练折内回归掉年龄后的 EEG；另有四个组用同样的分类头读冻结的 NeuroLM 特征。给出平衡准确率与 AUROC 的折外点估计，每个组两项都列出，分别针对全部被试与 ${iesBand.maximum_age_years} 岁及以下的 ${iesBand.people} 名被试。该页面关于帕金森病的问题、简答与卡片保持原有措辞；IESSEEG 不新增数据集页面，也不计入任何计数。`,
    },
    notes: [
      { en: `${clinicalIesseeg.caption} ${clinicalIesseeg.audit_boundary} ${clinicalIesseeg.neurolm.footnote}`,
        zh: `折外点估计；事先没有指定区间或检验。每人一段清醒期记录，取前 ${iesCohort.seconds_analysed} 秒。两组之间年龄与采集设置不同；回归掉年龄是一项敏感性分析。分类头与每一个分数都经过独立复现；NeuroLM 特征本身没有用第二套实现重新提取。NeuroLM 的预处理与频谱流程不同：两段 ${count(Math.max(...clinicalIesseeg.input_qc.sampling_hz.map(x => x.hz)))} Hz 的记录先重采样到 ${iesNeurolm.sampling_hz} Hz，再做 ${iesNeurolm.bandpass_hz.join('–')} Hz 带通、${iesNeurolm.notch_hz.join(' 与 ')} Hz 陷波并除以 ${iesNeurolm.amplitude_divisor}，所以两条流程之间的差异混合了预处理与模型结构。检查点的训练阶段，以及它此前是否接触过这些被试，都是未知的。` },
      { en: `IESSEEG: ${clinicalIesseeg.dataset.licence.replace(/^CC-BY-4\.0$/, 'CC BY 4.0')} for ${clinicalIesseeg.dataset.licence_scope}, from the release card and LICENSE at revision ${clinicalIesseeg.dataset.revision.slice(0, 8)} of ${clinicalIesseeg.dataset.repository}, cited by the title the card requests: “${clinicalIesseeg.dataset.requested_citation}”. ${clinicalIesseeg.rights.privacyReview} The card declares that the ${clinicalIesseeg.dataset.prior_reuse.case_segments} case segments were previously analysed by ${clinicalIesseeg.dataset.prior_reuse.study}; the participant-level crosswalk to that analysis is unresolved. NeuroLM-B is used frozen and identified by its checkpoint’s SHA-256; no weights are distributed. Not published: participant rows of any kind, per-fold metrics, per-group age and sex composition, intervals and tests, signals, code, the checkpoint and its features, and runtimes and storage locations.`,
        zh: `IESSEEG：许可为 CC BY 4.0，涵盖数据集与标注，依据 ${clinicalIesseeg.dataset.repository} 在版本 ${clinicalIesseeg.dataset.revision.slice(0, 8)} 时的发布卡片与 LICENSE 文件；按卡片要求的标题引用：“${clinicalIesseeg.dataset.requested_citation}”。发布卡片写明，这项回顾性研究获得了机构审查委员会的批准，并豁免了知情同意与 HIPAA 研究授权，同时要求任何人不得尝试重新识别被试。发布边界与帕金森病比较相同：只发布聚合分数，不发布逐被试数据、预测、年龄，也不发布各组的年龄与性别构成；${iesBand.maximum_age_years} 岁及以下一栏只给出该年龄段的人数及其病例与对照人数。卡片声明，其中 ${clinicalIesseeg.dataset.prior_reuse.case_segments} 个病例片段此前已由 ${clinicalIesseeg.dataset.prior_reuse.study} 分析过；与那项分析在被试层面的对应关系尚未厘清。NeuroLM-B 以冻结方式使用，并以检查点的 SHA-256 标识；不分发任何权重。不发布：任何形式的逐被试数据、逐折指标、各组的年龄与性别构成、区间与检验、信号、代码、检查点及其特征，以及运行时间与存储位置。` },
    ],
  },
  {
    id: neurolmEegmat.release_id, date: '2026-10-20', payload: 'neurolmEegmat',
    files: ['neurolm-eegmat-update.json'],
    // A separate panel on the pilot-studies page, outside its pilot count; the Arithmetic & rest page points to it.
    pages: ['/topics/pilot-studies/'],
    summary: {
      en: `A separate panel on the pilot-studies page, outside the pilot count and every leaderboard: NeuroLM-B kept frozen on EEGMAT’s arithmetic and rest (${neurolmCohort.people} people, ${count(neurolmCohort.windows)} two-second windows, whole participants held out in ${neurolmCohort.folds} folds), with one fixed ridge head fitted on each of three representations of the same windows: NeuroLM’s tokenizer features, its GPT hidden states and band power. Equal-person balanced accuracy and macro-F1 for each, and three paired differences with paired participant-bootstrap intervals. A pointer on the Arithmetic & rest protocol page leads to it; the core matrix keeps its rows.`,
      zh: `试点研究页面上单独的一栏，不计入试点数量，也不进入任何排行榜：在 EEGMAT 的心算与静息上冻结使用 NeuroLM-B（${neurolmCohort.people} 名被试，${count(neurolmCohort.windows)} 个两秒时间窗，${neurolmCohort.folds} 折、整名被试留出），在同一批时间窗的三种表示上各拟合一个固定的岭回归分类头：NeuroLM 的分词器特征、它的 GPT 隐藏状态，以及频带功率。给出每种表示按被试等权的平衡准确率与宏平均 F1，以及三个配对差值及其配对被试 bootstrap 区间。“心算与静息”协议页面上有一条指向它的链接；核心矩阵的各行保持不变。`,
    },
    notes: [
      { en: `Tokenizer features minus band power is ${pp2(neurolmContrast.difference)} points (paired 95% participant-bootstrap interval ${bound2(neurolmContrast.interval_95[0])} to ${pp2(neurolmContrast.interval_95[1])}): ${neurolmContrast.reading}. Pretraining exposure is unknown: EEGMAT is NeuroLM’s ${neurolmEegmat.pretraining_exposure.eegmat_instruction_task} task, one of the ${neurolmEegmat.pretraining_exposure.instruction_tasks.length} instruction tasks in its pinned code, and this checkpoint’s training stage is unresolved. The pilot has its own adapter and band-power features, so its scores sit in their own panel; rest is recorded before the task, so recording order moves with the label.`,
        zh: `分词器特征减频带功率为 ${pp2(neurolmContrast.difference)} pp（配对的 95% 被试 bootstrap 区间 ${bound2(neurolmContrast.interval_95[0])} 至 ${pp2(neurolmContrast.interval_95[1])}）：区间跨过零，所以既不能说明哪一方更好，也不能说明两者等效。是否出现在预训练数据中：未知。EEGMAT 就是 NeuroLM 固定版本代码中 ${neurolmEegmat.pretraining_exposure.instruction_tasks.length} 个指令任务之一的 ${neurolmEegmat.pretraining_exposure.eegmat_instruction_task}，而这个检查点处于哪个训练阶段尚未厘清。这个试点有自己的适配流程与频带功率特征，所以分数单独成栏；静息在任务之前记录，所以记录顺序与标签一起变化。` },
      { en: `${neurolmEegmat.release_record.rights} Not published: per-person, per-fold and per-window values of any kind, demographics, measured compute, the checkpoint and the NeuroLM source, and the handoff, protocol, producer, receipts and reviews themselves, pinned by hash in the release manifest because several carry private storage paths.`,
        zh: `EEGMAT 沿用其已发布的记录：${neurolmEegmat.rights.dataset.license}，只发布聚合结果。NeuroLM 的代码在固定的提交版本下为 ${neurolmEegmat.rights.code.licence} 许可。NeuroLM-B 检查点按其 Hugging Face 仓库的许可标签为 ${neurolmEegmat.rights.checkpoint.licence}，其 ${neurolmEegmat.rights.checkpoint.model_card_bytes} 字节的模型卡没有附加任何条款。不分发任何权重，也不代表 NeuroLM 作者的认可。不发布：任何逐人、逐折与逐时间窗的数值，人口学信息，实测的计算量，检查点与 NeuroLM 源代码，以及交接文件、协议、生成脚本、回执与审核记录本身——其中几份含有私有存储路径，只在发布清单中以哈希固定。` },
    ],
  },
  {
    id: 'eegpt-core-update-20261013', date: '2026-10-13', payload: 'eegptCore',
    files: ['eegpt-core-update.json'],
    // A frozen row beside the core matrix, placed as the further foundation encoders' rows are: every protocol page and
    // the home page's per-protocol table; EEGPT's method page and its directory card on /methods/; its attribution rows
    // beside LaBraM's and CBraMod's on does-pretraining-help, and its BETA and sleep rows on fewer-electrodes.
    pages: ['/', '/protocols/', '/methods/', '/topics/does-pretraining-help/', '/topics/fewer-electrodes/'],
    summary: {
      en: 'EEGPT on the core matrix: its eight core-matrix cells, computed in the same runs as the published LaBraM rows and, except on idle, the CBraMod rows, with only the encoder swapped, published as computed, without a re-run, as a frozen row beside the core matrix, where the further foundation encoders sit. On seven protocols, balanced accuracy with its participant-bootstrap interval, macro F1 and the chance level; on the idle protocol, counts (idle false activations, commands detected within 3 s, people who always abstained) with the window balanced accuracy and AUROC, and no interval. Beside the published LaBraM and CBraMod rows, EEGPT’s pretraining-attribution rows on mi-rest and EEGMAT: the pretrained encoder against the mean of three random initialisations, under a fixed and a train-selected readout, with paired intervals. Grouped by family, never ranked: EEGPT is above or below a published row only where their 95% intervals do not overlap, and the gap between the intervals is given in percentage points. Each cell says whether its dataset is in EEGPT’s published pretraining list, checked on 12 October 2026 with the source (none of the seven core datasets is), and each footnote sits beside the cells it bears on.',
      zh: '核心矩阵旁边的 EEGPT：它在 8 个核心协议上的单元格，与已发布的 LaBraM 各行、以及除空闲协议外的 CBraMod 各行出自同一批运行，只替换了编码器，按当时算出的结果原样发布，没有重新运行；作为冻结编码器的一行放在核心矩阵旁边，与更多基础模型编码器的位置相同。7 个协议上给出平衡准确率及其被试 bootstrap 区间、宏平均 F1 与随机水平；空闲协议上给出计数（空闲误触发、3 秒内检出的指令、始终拒识的被试人数）以及窗口平衡准确率与 AUROC，不给区间。在已发布的 LaBraM 与 CBraMod 各行旁边，给出 EEGPT 在 mi-rest 与 EEGMAT 上的预训练归因各行：预训练编码器对比三个随机初始化编码器的均值，分别用固定分类头与训练集内选定的分类头，附配对区间。按模型类别分组，从不排名：只有 95% 区间不重叠时，才说 EEGPT 高于或低于某个已发布的行，并以百分点给出两个区间之间的差距。每个单元格都注明该数据集是否在 EEGPT 作者公开的预训练数据清单中（2026 年 10 月 12 日核查，附来源；7 个核心数据集都不在其中），每条脚注都放在它所涉及的单元格旁边。',
    },
    notes: [
      { en: 'Several gaps are narrow. On sleep staging EEGPT’s interval lies above every core-matrix row’s, the nearest by 0.10 pp; on P300 it lies above LaBraM’s by 0.28 pp, on the semantic target above the spectral ridge’s by 0.78 pp, and on BETA with four channels above LaBraM’s by 0.90 pp. On BETA, EEGPT lies below standard CCA, which needs no training, at both channel counts. The idle row comes from the same run as the published LaBraM idle row; the published CBraMod idle row comes from another run, so a comparison with it is across runs. Pretraining attribution: on both datasets and under both readouts the pretrained encoder scored above the mean of its random initialisations, with paired intervals above zero; a frozen-encoder result conditional on these splits, readouts and initialisations, not a model ranking.',
        zh: '有几处差距很窄。在睡眠分期上，EEGPT 的区间高于核心矩阵每一行的区间，最近的只差 0.10 pp；在 P300 上高于 LaBraM 0.28 pp，在语义目标上高于 spectral ridge 0.78 pp，在 4 通道 BETA 上高于 LaBraM 0.90 pp。在 BETA 上，两种通道数下 EEGPT 都低于无需训练的标准 CCA。空闲行与已发布的 LaBraM 空闲行出自同一次运行；已发布的 CBraMod 空闲行来自另一次运行，所以与它的比较是跨运行的。预训练归因：两个数据集、两种分类头下，预训练编码器的得分都高于其随机初始化的均值，配对区间都在零以上；这是以这些数据划分、分类头与初始化为条件的冻结编码器结果，不是模型排名。' },
      { en: 'Owner decisions of 12 and 13 October 2026: publish EEGPT’s eight core-matrix cells as computed, without a re-run, as a frozen row beside the core matrix, and its pretraining-attribution rows beside the published LaBraM and CBraMod rows. The rights reasoning is the pilot comparison’s of 12 October: independently computed aggregate results are a separate output from the weights; no publisher prohibition was found; the checkpoint’s licence is unresolved; no original or converted weights are distributed; Apache-2.0 covers the repository’s code only. No author endorsement is implied. Four of the eight cells (mi-rest, EEGMAT and both BETA protocols) and EEGPT’s attribution controls have been in audit records in the public repository since 20 September 2026; the public attribution audit still labels the four EEGPT contrasts “hold-unresolved-weight-license”, as it did then, and keeps its bytes. With this release they are published.',
        zh: '所有者 2026 年 10 月 12 日与 13 日的决定：把 EEGPT 在 8 个核心协议上的单元格按当时算出的结果原样发布，不重新运行，作为冻结编码器的一行放在核心矩阵旁边；把它的预训练归因各行放在已发布的 LaBraM 与 CBraMod 各行旁边。权利方面的理由与 10 月 12 日那项试点比较相同：独立计算的聚合结果是与权重分开的产出；没有找到发布者的禁止规定；检查点的许可仍未厘清；不分发任何原始或转换后的权重；Apache-2.0 只涵盖代码仓库中的代码。不代表作者的认可。8 个单元格中的 4 个（mi-rest、EEGMAT 和两个 BETA 协议）以及 EEGPT 的预训练归因对照，自 2026 年 9 月 20 日起就在公开代码仓库的审计记录里；公开的归因审计文件至今仍把 EEGPT 的四个对比标为“hold-unresolved-weight-license”，那是当时的标记，文件保持原有字节。这些结果随本次发布正式公开。' },
      { en: 'How EEGPT differs from EEG-DINO: EEG-DINO stays catalogue-only by the owner’s decision of 4 October 2026 — its upstream weights carry no licence, and it was neither downloaded nor run. EEGPT was evaluated in the same runs as the published rows and was held only because its checkpoint’s licence could not be read, a hold the reassessment of 12 October found to be this project’s own choice. EEG-DINO is not re-reviewed by this decision.',
        zh: 'EEGPT 与 EEG-DINO 的区别：EEG-DINO 按所有者 2026 年 10 月 4 日的决定仍只列入目录——它的上游权重没有附带许可，本站也从未下载或运行它。EEGPT 则与已发布的各行在同一批运行中评测过，暂缓发布只是因为读不到检查点的许可；10 月 12 日的重新评估认定，这一暂缓是本项目自己的选择。本次决定不重新审查 EEG-DINO。' },
      { en: 'Not published: per-trial, per-person, per-fold and per-class values, features, fitted heads, idle thresholds and calibration grids, and how many people had a negative attribution difference; the per-seed scores of the three random initialisations (their mean is published, as for LaBraM and CBraMod); BETA’s duration-group summaries; timings, devices and memory; EEGPT results outside the eight core protocols; the checkpoint and its tensor conversion, whose SHA-256 identifies them and grants nothing; and the run summaries, protocols, independent audits and verification records themselves, pinned by hash in the release manifest because they carry private storage paths. Nothing was re-run: experiments.json, deployment-topics.json and the further-encoder files keep their bytes.',
        zh: '不发布：逐试次、逐人、逐折与逐类别的数值，特征、拟合好的分类头、空闲阈值与校准网格，以及归因差值为负的人数；三个随机初始化各自的分数（与 LaBraM、CBraMod 一样，只发布均值）；BETA 按记录时长分组的汇总；耗时、设备与显存；EEGPT 在 8 个核心协议之外的结果；检查点及其张量转换文件——其 SHA-256 只用于标识，不授予任何权利；以及运行汇总、协议、独立审计与核查记录本身——它们含有私有存储路径，只在发布清单中以哈希固定。没有重新运行任何东西：experiments.json、deployment-topics.json 与更多基础模型编码器的文件保持原有字节。' },
    ],
  },
  {
    id: 'pilot-studies-update-20261012', date: '2026-10-12', payload: 'pilotStudies',
    files: ['pilot-studies-update.json'],
    // Its own question page; /methods/ carries EEGPT's changed directory status (directory-status.ts), whose one
    // published figure set is this batch's Orthosis comparison.
    pages: ['/topics/pilot-studies/', '/methods/'],
    summary: {
      en: `Small pilots on four sources, each from its own approved aggregate export, all kept outside every leaderboard and model ranking. The Orthosis error-detection dataset (8 people, 83 runs, 2,407 recorded device events: one cohort, counted once) in three results: a 64-channel classical EEG baseline, the same baseline on the 58 channels EEGPT supports, and frozen EEGPT with the same fixed supervised probe against those matched classical features.${bingoReleased ? ' BINGO’s Greek and English inner speech (17 source-defined subject fields): a fixed spectral baseline across people and across languages, a negative result near its 15-class prior.' : ''}${handwritingReleased ? ' A mask-aware EEG analysis of an imagined-handwriting competition dataset (5 people, four released coded labels): with channels that sit flat at a digital rail masked, relative EEG is slightly above the training-majority control and above the missingness-mask and mask-plus-time controls, and not separated from elapsed time and trial order; a data-quality and methods case study, not handwriting recognition.' : ''} REFED (two nominal participant folders, 30 stored clips): a computational diagnostic in which simple source-only controls have smaller errors than EEG band power. ${pilotsHeld.length === 2 ? 'Two pilots are built and audited but held for their rights reviews, with no figure: BINGO’s Greek and English inner speech, and a mask-aware EEG analysis of a handwriting dataset. ' : pilotsHeld.length ? `${pilotsHeld[0] === 'bingo' ? 'BINGO’s Greek and English inner-speech pilot' : 'A mask-aware EEG analysis of a handwriting dataset'} is built and audited but held for its rights review. ` : ''}Nothing is pooled across datasets, configurations or conditions.`,
      zh: `四个数据源上的小规模试点，每项都来自各自已批准的聚合导出文件，全部不进入任何排行榜或模型排名。Orthosis 错误检测数据集（8 名被试、83 个 run、2,407 个记录下来的设备事件：同一个队列，只计一次）给出三项结果：64 通道经典 EEG 基线、同一基线在 EEGPT 支持的 58 个通道上的配置，以及冻结的 EEGPT 加同样固定的有监督分类头、与这组匹配的经典特征的比较。${bingoReleased ? 'BINGO 的希腊语与英语内部言语（17 个按数据源定义的被试字段）：一个固定的频谱基线跨被试、跨语言的结果，是接近 15 类先验的阴性结果。' : ''}${handwritingReleased ? '一个想象书写竞赛数据集上的掩码感知 EEG 分析（5 名被试，四个已发布的编码标签）：屏蔽停在数字量程边界上的平直通道之后，相对频带功率 EEG 略高于训练集多数类对照，也高于只看缺失掩码的对照与掩码 + 时间的对照，但与经过时间与试次顺序的对照没有区分开；这是一项数据质量与方法案例研究，不是手写识别。' : ''}REFED（两个标称被试文件夹，30 个存储片段）：一项计算诊断，其中简单的、不用 EEG、只用训练集信息的对照，误差都比 EEG 频带功率小。${pilotsHeld.length === 2 ? '有两项试点已完成并通过审计，但因权利审查暂缓，不发布任何数字：BINGO 的希腊语与英语内部言语，以及手写数据集上的掩码感知 EEG 分析。' : pilotsHeld.length ? `${pilotsHeld[0] === 'bingo' ? 'BINGO 的希腊语与英语内部言语试点' : '手写数据集上的掩码感知 EEG 分析'}已完成并通过审计，但因权利审查暂缓。` : ''}不跨数据集、配置或条件合并。`,
    },
    notes: [
      { en: 'EEGPT: the comparison is published from its approved export, after an independent check of that exact file. The earlier hold on EEGPT aggregate scores was this project’s own conservative choice, not a publisher’s rule; this pilot comparison is the first EEGPT result on the site’s pages. The core-matrix EEGPT scores are not on the site’s pages, but some of them (mi-rest, EEGMAT and both BETA protocols, with EEGPT’s pretraining-attribution controls on mi-rest and EEGMAT) have been in audit records in the public repository since 20 September 2026. The checkpoint’s licence remains unresolved, and no original or converted weights are distributed; Apache-2.0 covers the repository’s code only. The paired interval spans zero, so neither arm is shown to be better, and the two are not shown to be equivalent. The probe is trained on the other seven people’s labels (supervised transfer, not zero-shot), and overlap with EEGPT’s pretraining data has not been excluded. Corrected the same day: this note first said the pilot comparison was the only EEGPT figure published. The core-matrix cells followed on 13 October 2026, in eegpt-core-update-20261013.',
        zh: 'EEGPT：这项比较依据经批准的导出文件发布，发布前对这份文件做过独立核查。此前暂不发布 EEGPT 聚合分数，是本项目自己的保守选择，不是发布者的规定；这项试点比较是网站页面上第一个 EEGPT 结果。核心矩阵中的 EEGPT 分数没有出现在网站页面上，但其中一部分（mi-rest、EEGMAT 和两个 BETA 协议，以及 EEGPT 在 mi-rest 与 EEGMAT 上的预训练归因对照）自 2026 年 9 月 20 日起就在公开代码仓库的审计记录里。检查点的许可仍未厘清，不分发任何原始或转换后的权重；Apache-2.0 只涵盖代码仓库中的代码。配对区间跨过零，所以既不能说明哪一方更好，也不能说明两者等效。分类头用另外 7 名被试的标签训练（有监督迁移，不是零样本），也没有排除这个数据集出现在 EEGPT 预训练数据中的可能。同日更正：本说明最初写的是，这项试点比较是唯一发布的 EEGPT 数字。核心矩阵中的单元格已于 2026 年 10 月 13 日随 eegpt-core-update-20261013 发布。' },
      // BINGO follows its publication switch (pilot-switch.ts): its rights note while released, its hold while held.
      ...(bingoReleased ? [
        { en: 'BINGO: the source states no licence. Consent is as the project’s public deliverable D3.1 (version 3.0) reports it: signed consent forms, stated for the project’s NATO-alphabet recordings in the same CERTH laboratory; the cross-language dataset’s own documentation has no ethics or consent statement, and no ethics-approval reference is published. The aggregates are published on that basis by the owner’s decision. The project documents artifact cleaning (ASR and FORCe) on the continuous recordings before trials were cut; that statement is printed beside the result, attributed to D3.1 (version 2.0), and was not re-verified against the file. The project’s own result on its NATO-alphabet dataset is printed as reported by the project, not run here.',
          zh: 'BINGO：数据源没有说明许可。知情同意按项目公开交付文件 D3.1（3.0 版）的表述：被试签署了知情同意书，但这句话针对的是该项目在同一个 CERTH 实验室记录的 NATO 字母表数据集；跨语言数据集自己的文档没有伦理或知情同意声明，也没有公布伦理批件编号。聚合结果依据所有者的决定，在此基础上发布。项目说明在切分试次之前，已在连续记录上用 ASR 与 FORCe 去除了伪迹；这句话印在结果旁边，注明出自 D3.1（2.0 版），没有对照数据文件重新核实。项目自己在 NATO 字母表数据集上的结果，按项目报告的原样列出，不是本站运行的。' },
      ] : [
        { en: 'BINGO: run and independently audited, and held by its publication switch, so no figure or dataset page is published. The source states no licence, the cross-language dataset’s own documentation has no ethics or consent statement, the only consent statement available is the project’s, for its NATO-alphabet recordings in the same CERTH laboratory, and no ethics-approval reference is published.',
          zh: 'BINGO：已运行并通过独立审计，由它的发布开关暂缓，所以不发布任何数字，也没有数据集页面。数据源没有说明许可；跨语言数据集自己的文档没有伦理或知情同意声明；能找到的知情同意声明只有项目针对同一个 CERTH 实验室所记录的 NATO 字母表数据集的那一句；也没有公布伦理批件编号。' },
      ]),
      // The handwriting analysis follows its switch too: its rights line while released, its hold while held.
      ...(handwritingReleased ? [
        { en: 'Handwriting: published by the owner’s decision with its rights gap stated. No ethics-approval or informed-consent statement was found, on the dataset card or in a participating team’s challenge paper, and the organisers’ paper is listed as forthcoming; to be rechecked when it appears. The earlier analysis of the same five people is printed as context, not as a second cohort.',
          zh: '手写：依据所有者的决定发布，并说明其权利缺口。在数据集卡片和一支参赛队伍的挑战赛论文中都没有找到伦理批准或知情同意声明，组织方的论文标注为即将发表；待其发表后重新核查。对同样五名被试较早的一次分析作为背景列出，不是第二个队列。' },
      ] : [
        { en: 'Handwriting: run and independently audited, and held by its publication switch, so no figure or dataset page is published. No ethics-approval or informed-consent statement was found, on the dataset card or in a participating team’s challenge paper.',
          zh: '手写：已运行并通过独立审计，由它的发布开关暂缓，所以不发布任何数字，也没有数据集页面。在数据集卡片和一支参赛队伍的挑战赛论文中都没有找到伦理批准或知情同意声明。' },
      ]),
      { en: `Not published: per-person, per-field, per-folder, per-clip and per-record values; the Orthosis response-clean subset’s scores (its counts are published); individual permutation and label-shuffle replicates (their mean and observed range are published); confusion matrices; ${pilotsHeld.length ? `every figure of the held ${pilotsHeld.length === 2 ? 'BINGO and handwriting analyses' : `${pilotsHeld[0] === 'bingo' ? 'BINGO' : 'handwriting'} analysis`}; ` : ''}${handwritingReleased ? 'the handwriting mask-only control’s interval, because with five people its bounds would show individual people’s scores; ' : ''}and the handoffs, approval records and independent audits themselves, pinned by hash in the review manifest because they carry private storage paths. Status only, with no figure: Orthosis EMG, TinyMyo and EEG–EMG fusion; handwriting fNIRS and fusion; REFED physiological and fusion evaluation; and a meditation dataset, in which RR means heartbeat RR intervals, not respiratory rate.`,
        zh: `不发布：逐人、逐字段、逐文件夹、逐片段与逐记录的数值；Orthosis“响应干净”子集的分数（只发布它的计数）；单次标签置换与标签打乱的结果（发布其均值与观察到的范围）；混淆矩阵；${pilotsHeld.length ? `暂缓的${pilotsHeld.length === 2 ? ' BINGO 与手写分析' : pilotsHeld[0] === 'bingo' ? ' BINGO 分析' : '手写分析'}的任何数字；` : ''}${handwritingReleased ? '手写分析中只看缺失掩码的对照的区间（只有五名被试，区间端点能反推出个人的分数）；' : ''}以及交接文件、批准记录与独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。只列状态、没有任何数字的：Orthosis 的 EMG、TinyMyo 与 EEG–EMG 融合；手写数据集的 fNIRS 与融合；REFED 的生理信号与融合评测；以及一个冥想数据集——其中 RR 指心跳的 RR 间期，不是呼吸频率。` },
    ],
  },
  {
    id: 'beyond-scalp-update-20261012', date: '2026-10-12', payload: 'beyondScalp',
    files: ['beyond-scalp-update.json'],
    // Its own question page, in the same site version as the pilot studies.
    pages: ['/topics/beyond-scalp-eeg/'],
    summary: {
      en: 'Locally executed analyses beyond scalp EEG, each its own species, signal and metric: none is compared with scalp EEG, none joins the core matrix, and they share no ranking. Human fNIRS (Bak et al., 30 people): executed right-hand, left-hand and foot tapping classified by a fixed shrinkage LDA in a person left out of training, against a training-prior comparator. One macaque’s motor-cortex spiking (MC_RTT, prepared for the Neural Latents Benchmark; one session): x/y finger velocity decoded by a fixed ridge on held-out trials of the same session, against the training mean, on five metrics, including the one on which the ridge is worse. A numerical coverage check of human fNIRS recordings (ds007420, 12 people, 60 recordings): counts only, no decoding. Two sources are prepared and not scored: FALCON H2 human intracortical handwriting and Rabut et al. human functional ultrasound.',
      zh: '在头皮 EEG 之外由本站在本地运行的分析，每项都有各自的物种、信号与指标：都不与头皮 EEG 比较，都不进入核心矩阵，彼此也不排名。人类 fNIRS（Bak 等人，30 名被试）：用固定的收缩 LDA，对训练时留出的被试区分右手、左手手指敲击与脚部敲击这三种实际动作，与训练集先验对照比较。一只猕猴运动皮层的神经元放电（MC_RTT，为 Neural Latents Benchmark 整理的数据；一次会话）：用固定的岭回归在同一次会话的留出试次上解码手指的 x/y 速度，与训练集均值对照比较，共五个指标，其中包括岭回归更差的那一个。人类 fNIRS 记录的数值覆盖核查（ds007420，12 名被试，60 段记录）：只有计数，没有解码。另有两个数据源已完成准备、尚未评分：FALCON H2 人类皮层内手写，以及 Rabut 等人的人类功能超声。',
    },
    notes: [
      { en: 'Bak: the participant-macro balanced accuracy is well above the training prior, with a descriptive interval that resamples fixed participant scores (not a refit bootstrap). Executed movement, not motor imagery; offline over a 15-second window, and systemic or motion effects are not excluded. MC_RTT: not an official Neural Latents Benchmark score; with one animal every figure is that animal’s, and no interval is reported. ds007420: coverage counts say nothing about signal quality, and no classifier score exists, because its task codes have no verified lookup and its event durations disagree.',
        zh: 'Bak：按被试平均的平衡准确率远高于训练集先验，描述性区间是对固定的逐人分数重抽样得到的（不是重新拟合的 bootstrap）。任务是实际动作，不是运动想象；离线分析，时间窗为 15 秒，也没有排除全身性生理或运动的影响。MC_RTT：不是 Neural Latents Benchmark 的官方分数；只有一只动物，每个数字都是这只动物的，也不报告区间。ds007420：覆盖计数说明不了信号质量；没有任何分类器分数，因为它的任务编码没有经过核实的对照表，事件时长的几处记录也互相矛盾。' },
      { en: 'Licences, from each repository’s record: Bak CC BY 4.0, MC_RTT CC BY 4.0, ds007420 CC0, FALCON H2 CC BY 4.0, Rabut et al. CC BY-NC 4.0 (non-commercial). Bak’s ethics and consent statement was read from an Internet Archive capture of the publisher’s article page, because the publisher refused automated requests. MC_RTT is animal data collected under procedures approved by institutional animal care and use committees, so informed consent does not apply. Not published: per-person, per-recording, per-channel, per-trial and per-row values; confusion matrices; signals, features, predictions and coefficients; measured compute; demographics; and the handoff, reviews and independent audits themselves, pinned by hash in the review manifest because they carry private storage paths.',
        zh: '许可来自各自数据仓库的记录：Bak 为 CC BY 4.0，MC_RTT 为 CC BY 4.0，ds007420 为 CC0，FALCON H2 为 CC BY 4.0，Rabut 等人的数据为 CC BY-NC 4.0（非商业）。Bak 的伦理与知情同意声明读自出版方文章页面在互联网档案馆的存档，因为出版方拒绝了自动化请求。MC_RTT 是动物数据，在各机构动物护理与使用委员会批准的程序下采集，因此不涉及知情同意。不发布：逐人、逐段记录、逐通道、逐试次与逐行的数值；混淆矩阵；信号、特征、预测与模型系数；实测的计算量；人口学信息；以及交接文件、审核记录与独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'questions-in-language-update-20261008', date: '2026-10-08', payload: 'questionsInLanguage',
    files: ['questions-in-language-update.json', 'questions-in-language-wordings.json'],
    // Route 3 of the decision-research roadmap, in the same site version as the later-sessions question: its own
    // question page, and the roadmap on when-not-to-act, where route 3 is run.
    pages: ['/topics/questions-in-language/', '/topics/when-not-to-act/'],
    summary: {
      en: 'Route 3 of the decision-research roadmap, questions in language: can an EEG model be asked its questions in words, including ones it was never trained on? One small question-conditioned head over frozen features is asked each question by a question number, a label template or a natural-language description. SSVEP on BETA (a plain spectrum and frozen CBraMod features) and sleep on BOAS (frozen CBraMod features) are primary, three seeds each; EESM19, OpenBMI motor imagery, REVE-L features, a second text encoder, Chinese wordings, a negation probe, a contiguous held-out band of frequencies and Wearable-102 are secondary. Seen questions in their training wording, rewordings and questions the EEG head was never trained on are reported apart, never pooled into one zero-shot number, and every entry carries two flags: whether its interval excludes zero, and how it stands against a margin fixed before any result (2 pp for accuracy; a ratio of remaining error of 1.25 for the unseen sleep questions; the primary comparisons with the numeric code, the neighbour average and the shuffled templates are read for a difference only). “Jev-style” here means the interface of a decision model like TypeSafe’s Jev, applied to EEG: encode the recording once, then answer several explicit, typed questions about it, each with a probability. The roadmap started from a vision paper (Yu & Yao, 2026) that applies that idea to images.',
      zh: '决策研究路线图的第三条路线——用语言提问：能不能用文字向 EEG 模型提问，包括它从未训练过的问题？在冻结特征上训练一个以问题为条件的小分类头，每个问题分别用三种方式提出：题号、标签模板、自然语言描述。主分析是 BETA 上的 SSVEP（普通频谱与冻结的 CBraMod 特征）和 BOAS 上的睡眠（冻结的 CBraMod 特征），各 3 个随机种子；次要分析包括 EESM19、OpenBMI 运动想象、REVE-L 特征、另一个文本编码器、中文问法、否定探针、一段连续留出的频率，以及 Wearable-102。用训练时的问法问已见过的问题、改写后的问题、EEG 分类头从未训练过的问题，三者分开报告，从不合并成一个“零样本”数字；每个条目都带两个标记——区间是否排除零，以及相对于任何结果出来之前就定下的界值处在什么位置（准确率为 2 pp；未见过的睡眠问题为剩余错误之比 1.25；主分析中与数值编码、相邻平均和错配模板的比较只读差异）。“Jev-style”（Jev 式）在这里指把 TypeSafe 的 Jev 这类决策模型的接口用在 EEG 上：一段记录只编码一次，再回答关于它的多个明确的、规定输出类型的问题，每个回答都带一个概率。路线图从一篇视觉论文（Yu & Yao, 2026）出发，它把同样的思路用在图像上。',
    },
    notes: [
      { en: 'Mostly a negative, boundary result. On sleep, asking a seen question with a template or a description was equivalent to a question number within 2 pp; on SSVEP it cost accuracy with both kinds of features. A new sentence frame cost nothing measurable on sleep, while synonyms and new descriptions lowered accuracy on both datasets (on SSVEP with frozen CBraMod features the synonyms stayed within the margin). Questions the EEG head was never trained on were not answered well: in every wording, each unseen sleep question did worse than adding up the head’s own stage answers, and every comparison of an unseen flicker frequency with CCA, which needs no training, fell far short. Negated wordings were answered as if they asked for what they negate.',
        zh: '主要是阴性的、划定边界的结果。在睡眠上，用标签模板或描述来问已见过的问题，与用题号提问在 2 pp 的界值内等效；在 SSVEP 上，两种特征下用语言提问都有准确率代价。在睡眠上换一个新句式没有可测的代价，同义词和新描述则在两个数据集上都降低了准确率（SSVEP 冻结 CBraMod 特征下的同义词仍在界值内）。EEG 分类头从未训练过的问题没有答好：无论哪种问法，每一个未见过的睡眠问题都不如把分类头自己的各期答案加起来；未见过的闪烁频率与无需训练的 CCA 的每一项比较，都远远落后。否定的问法被当成在问被否定的那一项本身。' },
      { en: 'Before any result, the pre-run permutation canary failed twice (revisions 3 and 4; every failing cell was on BOAS, one of them below chance). The owner overrode revision 4’s “no further revision” and approved revision 5, which passed; revision 4’s centring diagnostic was not run, and both failed records are kept and disclosed. For the Chinese text encoder the SSVEP token rule was reported instead of stopping the run (decision S0b-6); an engineering amendment before the first fit (EA-1) changed no question, partition, wording, arm, metric, margin or gate; the declared numeracy prediction was not activated, because its premise did not hold. There are 35 pre-declared primary comparisons, not corrected for multiplicity, and most secondary results are single-seed and were declared likely inconclusive before the run.',
        zh: '在任何结果出来之前，运行前的标签置换金丝雀检查失败了两次（修订 3 与修订 4；失败的格子全在 BOAS 上，其中一个低于随机水平）。所有者推翻了修订 4 写下的“不再修订”，批准了修订 5，修订 5 通过；修订 4 的按人中心化诊断没有运行，两次失败的记录都保留并披露。对于中文文本编码器，SSVEP 的分词规则改为报告而不停止运行（决定 S0b-6）；第一次拟合之前的一项工程修订（EA-1）没有改动任何问题、划分、问法、臂（ID、TPL、DESC 等各组）、指标、界值或门槛；预先声明的数感预测没有触发，因为它的前提不成立。主分析共 35 个预先声明的比较，没有做多重比较校正；次要分析大多只有 1 个随机种子，并在运行前就声明多半无法下结论。' },
      { en: 'BOAS figures are published under the owner’s approval of 7 October 2026, extended to route 3 the same day (D11): with its three stated gaps and its attribution, participants pseudonymised in the public release, and every BOAS cell pooling at least 20 people; neither Bitbrain’s headband nor its automatic scoring is used or evaluated. Not published: per-person, per-night and per-fold values; the S10 per-frequency and interior-only breakdowns, which no independent audit covers; any value of a pre-run check, which is published as pass or fail and counts only; measured compute; and the handoff, the aggregates, the protocol and the four independent audits themselves, pinned by hash in the review manifest because they carry private storage paths. The wording lists, the held-out partition and the derangements of the shuffled control are published in their own file.',
        zh: 'BOAS 的数值依据所有者 2026 年 10 月 7 日的批准发布，该批准于同日扩展到第三条路线（D11）：附三个已说明的缺口与署名，被试在公开发布中是假名化的，每个 BOAS 单元格至少汇总 20 名被试；Bitbrain 的头带及其自动分期既没有使用，也没有被评估。不发布：逐人、逐夜与逐折的数值；没有任何独立审计覆盖的 S10 按频率与仅内部频率的细分结果；运行前检查的任何数值（只以通过或失败及计数发布）；实测的计算量；以及交接文件、聚合文件、协议与四份独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。问法清单、留出频率的划分与打乱对照的错位排列以单独的文件发布。' },
    ],
  },
  {
    id: 'later-sessions-update-20261008', date: '2026-10-08', payload: 'laterSessions',
    files: ['later-sessions-update.json'],
    // Its own question page; the four results come from the large-source batch's approved releases.
    pages: ['/topics/later-sessions/'],
    summary: {
      en: 'Four results under one question — does a decoder trained on an earlier session still work later? — each from its own approved release, and none uses labels from the later session. WBCIC-SHU (62 people in two separate cohorts, 51 with two-class and 11 with three-class motor imagery): a source-majority prior and a relative spectral ridge trained on each person’s recording session 1 and tested on session 3, and frozen CBraMod with a ridge readout fitted on session 1, on the same people and trials. A longitudinal RSVP dataset (15 people): one ERP baseline trained at the first visit and scored at the publisher’s nominal Day 7, 80 and 200 visits. Forenzo’s continuous cursor-tracking dataset (23 admitted records in two cohorts, two response arms): a fixed spectral ridge from each record’s earliest to its latest complete session, against a source-mean comparator, published as a negative result. Nothing is pooled across datasets, cohorts or response arms, and the results share no ranking.',
      zh: '同一个问题下的四项结果——在较早会话上训练的解码器，到后来还管用吗？——每项都来自各自已批准的发布文件，都不使用后一次会话的任何标签。WBCIC-SHU（62 名被试，分为两个独立队列：51 名做二分类、11 名做三分类运动想象）：在每名被试的第 1 次记录会话上训练、在第 3 次会话上测试的源会话多数类先验与相对频谱功率 + 岭回归（relative spectral ridge），以及在同一批被试与试次上、分类头用第 1 次会话拟合的冻结 CBraMod。一个纵向 RSVP 数据集（15 名被试）：在第一次访次训练的 ERP 基线，在发布者标称的第 7、80、200 天访次上评分。Forenzo 的连续光标追踪数据集（两个队列共 23 条纳入记录，两种响应变量）：从每条记录最早的完整会话到最晚的完整会话的固定 spectral ridge，与源会话均值对照比较，作为阴性结果发布。不跨数据集、队列或响应变量合并，各结果之间不排名。',
    },
    notes: [
      { en: 'WBCIC-SHU: in both cohorts the spectral ridge is above the source prior and frozen CBraMod above the spectral ridge, each with a paired interval above zero. The CBraMod arm was frozen after the spectral ridge results existed and reuses their test trials; there is no matched random-weight control, and whether this checkpoint saw WBCIC-SHU in pretraining is not established, so it does not show that pretraining caused the gain. Session numbers are recording-session ordinals, not a guaranteed time gap.',
        zh: 'WBCIC-SHU：两个队列中，spectral ridge 都高于源会话先验，冻结 CBraMod 又都高于 spectral ridge，配对区间均在零以上。CBraMod 这一组是在 spectral ridge 的结果出来之后才冻结的，并复用了同样的测试试次；没有结构相同的随机初始化对照，这个检查点的预训练数据中是否出现过 WBCIC-SHU 也没有确定，所以它不能说明提升来自预训练。会话编号只是记录会话的序号，不保证固定的时间间隔。' },
      { en: 'Longitudinal RSVP: AUROC is lower at the nominal Day 200 visit than at Day 7, with a paired interval below zero, and some people lost 0.05 AUROC or more; targets are rare, so average precision is printed beside AUROC. Day 7, 80 and 200 are the publisher’s nominal labels, and nothing here shows that elapsed time caused the change. Forenzo: the spectral ridge has a higher overall error than a constant source-mean comparator on every admitted record, in both cohorts and both response arms, with means far above medians; velocity imitates the publisher’s historical decoder output, not intended motion, and no online-control claim is made.',
        zh: '纵向 RSVP：标称第 200 天访次的 AUROC 低于第 7 天，配对区间在零以下，部分被试下降了 0.05 AUROC 及以上；目标事件很少，所以 AUROC 旁边同时给出平均精确率。第 7、80、200 天是发布者标称的访次标签，这里没有任何结果说明变化是由时间流逝造成的。Forenzo：在两个队列、两种响应变量下，spectral ridge 在每一条纳入记录上的总体误差都高于常数的源会话均值对照，均值远高于中位数；速度变量模仿的是发布者历史解码器的输出，不是意图运动，也不作任何在线控制方面的声明。' },
      { en: 'All three datasets are new to this site. Licences, from each repository’s record: WBCIC-SHU CC BY 4.0, the RSVP dataset CC0, Forenzo’s KiltHub record CC BY 4.0; each paper states ethics approval and written or signed informed consent. Not published: per-person and per-record values (minimums, percentiles and medians, except the Forenzo ridge medians the handoff requires beside their means), confusion matrices, the Forenzo recorded-decoder strata, measured compute, and the handoffs, release decisions and independent audits themselves, pinned by hash in the review manifest because they carry private storage paths.',
        zh: '这三个数据集都是本站新增的数据源。许可来自各自数据仓库的记录：WBCIC-SHU 为 CC BY 4.0，RSVP 数据集为 CC0，Forenzo 的 KiltHub 记录为 CC BY 4.0；每篇论文都写明了伦理批准，以及书面或签署的知情同意。不发布：逐人与逐条记录的数值（最小值、百分位数与中位数；交接文件要求与均值并列给出的 Forenzo spectral ridge 中位数除外）、混淆矩阵、Forenzo 按记录时所用解码器划分的分层结果、实测的计算量，以及交接文件、发布决定与独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'shared-representation-update-20261007', date: '2026-10-07', payload: 'sharedRepresentation',
    files: ['shared-representation-update.json'],
    // Its own question since the pages of the same day; the roadmap on when-not-to-act marks route 2 run.
    pages: ['/topics/shared-encoder/', '/topics/when-not-to-act/'],
    summary: {
      en: 'Route 2 of the decision-research roadmap, one representation and several questions: can one shared encoder with a fixed linear head per question answer several questions as well as a question-conditioned head, or as separate models, for less? Independent models, fixed heads, a shared hidden layer, and that layer conditioned on the question’s identity, compared at matched data and compute: EEGNet trained from scratch and frozen CBraMod features as the primary levels, three seeds each, and CBraMod adapted by LoRA, one seed, as a secondary level. Motor imagery on OpenBMI and sleep on BOAS are primary; EESM19 is a crude one-seed replication. Every contrast carries two flags — whether its interval excludes zero, and whether it lies within the 2 pp margin fixed before any result — and nothing is ranked where intervals overlap.',
      zh: '决策研究路线图的第二条路线——一份表征，多个问题：一个共享编码器、每个问题配一个固定的线性头，能不能像以问题为条件的头、或者每个问题单独建模那样答好几个问题，同时花得更少？在数据量与计算量匹配的条件下，比较四种设置：每个问题一个独立模型、固定头、共享隐藏层，以及按问题身份调制该隐藏层的条件头。主分析层级是从头训练的 EEGNet 与冻结的 CBraMod 特征，各 3 个随机种子；次要层级是用 LoRA 适配的 CBraMod，1 个随机种子。运动想象（OpenBMI）与睡眠（BOAS）是主分析，EESM19 是只跑一个随机种子的粗略重复。每个对比都带两个标记——区间是否排除零，以及区间是否落在任何结果出来之前就定下的 2 pp 的界值之内；区间重叠时不排名。',
    },
    notes: [
      { en: 'The fixed-heads sentence is supported on neither domain: the question-conditioned head was higher on imagery against rest, and on five-stage sleep scoring, while the fixed heads were the cheaper set-up in both. The question’s identity itself added nothing measurable: the same hidden layer without conditioning was equivalent to the conditioned head within 2 pp on both motor-imagery questions and non-inferior on sleep. On sleep that layer carries the lift over the fixed heads; on motor imagery its own contrast with the fixed heads was inconclusive. Against a separate model per question, sharing one small EEGNet trunk cost accuracy on which hand; on imagery against rest and on the sleep stage that comparison was inconclusive. Questions at floor are reported and never counted, and with 21 primary entries and no multiplicity correction about one in twenty entries with no true difference may show one by chance.',
        zh: '两个领域都不支持“固定头以更少的代价做得一样好”这句话：以问题为条件的头在“想象还是静息”上更高，在睡眠五期分期上也更高，而两个领域里固定头都是更省的设置。问题身份本身没有带来可测的增益：不加条件的同一个隐藏层，在两个运动想象问题上都与条件头在 2 pp 内等效，在睡眠上非劣。在睡眠上，比固定头高出的那部分来自这个隐藏层；在运动想象上，这个隐藏层与固定头的对比无法下结论。与每个问题单独一个模型相比，共享一个小的 EEGNet 主干在“哪只手”上损失了准确率；在“想象还是静息”和睡眠分期上，这项比较无法下结论。处于下限的问题照样报告，但从不计入；21 个主分析条目没有做多重比较校正，在没有真实差异的条目里，约每 20 个就可能有 1 个偶然显示出差异。' },
      { en: 'BOAS is new to this site. Its rights review was approved by the owner on 7 October 2026 as publishable with stated gaps. The consent statement does not say whether participants agreed to public sharing or secondary use. The ethics and consent statements come from the publisher’s dataset description and README. No peer-reviewed paper describes BOAS. The ethics reference was added to the release in version 1.1.1 (May 2025), and the release does not say when it was granted relative to the recordings. Only cohort aggregates of at least 20 people are published. Participants are pseudonymised in the public release, and neither Bitbrain’s headband nor its automatic scoring is used or evaluated.',
        zh: 'BOAS 是本站新增的数据源。它的权利审核于 2026 年 10 月 7 日经所有者批准，结论是“说明缺口后可以发布”：知情同意声明没有说明被试是否同意公开共享或二次使用；伦理与知情同意的陈述只来自发布者的数据集说明与 README，没有任何同行评审论文描述 BOAS；伦理批件编号是在 1.1.1 版（2025 年 5 月）才加入发布的，发布中没有说明它是在记录之前还是之后批准的。只发布至少 20 人的队列汇总。被试在公开发布中是假名化的；Bitbrain 的头带及其自动分期既没有使用，也没有被评估。' },
      { en: 'E2 sleep — CBraMod adapted by LoRA on BOAS — ran on 7 October 2026 by the owner’s decision, after every other result was known; its design and run condition were fixed at the freeze and nothing about it was chosen from results. It ran with temporary private resume checkpoints: none outlived its fit, and none remains. Not published: per-window and per-person values, including the per-person percentiles the release candidate carries for OpenBMI; measured compute totals (GPU-hours, wall time per fit and per block, training steps per outer fold), while the cost ledger publishes, labelled indicative, the two times measured interleaved on a shared GPU; and the aggregates and the three independent audits themselves, pinned by hash in the review manifest because they carry private storage paths.',
        zh: 'E2 睡眠——在 BOAS 上用 LoRA 适配的 CBraMod——按所有者的决定，于 2026 年 10 月 7 日、在其他所有结果都已知之后运行；它的设计与运行条件在冻结时就已确定，没有任何一项是根据结果选的。运行时用了临时的私有续训检查点：没有一个留到对应的拟合结束之后，现在一个也不剩。不发布：逐窗口与逐人的数值，包括发布候选文件为 OpenBMI 携带的逐人百分位数；实测的计算总量（GPU 小时、每次拟合与每组的实际耗时、每个外层折的训练步数），代价表则以“仅供参考”的标注发布在共享 GPU 上交替测得的两项耗时；以及聚合文件与三份独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'foundation-models-update-20261004', date: '2026-10-04', payload: 'foundationModels',
    files: ['foundation-models-update.json', ...foundationModelFiles],
    // The rows are printed on every protocol page and the home page's per-protocol table; each
    // model has a method page and a directory card on /methods/. The two topics take the
    // batch's findings.
    pages: ['/protocols/', '/methods/', '/topics/does-pretraining-help/', '/topics/fewer-electrodes/'],
    summary: {
      en: 'The v9 foundation-model evaluation: eleven further EEG foundation models — sixteen encoder checkpoints — run as frozen probes on the eight core protocols with the published LaBraM and CBraMod recipe and only the encoder swapped (the same windows, people, folds, heads and scoring), and nine of them adapted on EEGMAT with the 1 October recipe, a head trained on the frozen encoder against rank-4 LoRA over three seeds. New rows beside the core matrix, in their own files: one JSON, and a CSV per protocol whose first columns are the core results CSVs’. Grouped by family, never ranked: a row is above or below another only where their 95% intervals do not overlap. Every cell says whether its dataset is in the model authors’ published pretraining list, checked on 4 October 2026 with the source, and every model carries its weights licence.',
      zh: '第九轮基础模型评测：另外 11 个 EEG 基础模型（共 16 个编码器检查点）作为冻结探针，在 8 个核心协议上沿用已发布的 LaBraM 与 CBraMod 冻结方案，只替换编码器（时间窗、被试、折、分类头与评分方式都不变）；其中 9 个模型又在 EEGMAT 上按 10 月 1 日的方案做了适配：在冻结编码器上只训分类头，对比秩为 4 的 LoRA，3 个随机种子。这些是放在核心矩阵旁边的新行，有自己的文件：一个 JSON，以及每个协议一个 CSV，其前几列与核心结果 CSV 完全相同。按模型类别分组，从不排名：只有 95% 区间不重叠时，才说一行高于或低于另一行。每个单元格都注明该数据集是否在模型作者公开的预训练数据清单中（2026 年 10 月 4 日核查，附来源），每个模型都注明其权重许可。',
    },
    notes: [
      { en: 'Sleep staging is the only protocol where new frozen cells — ST-EEGFormer Large and Base, and REVE Large — lie entirely above every published row. On the other six scored protocols no new cell lies entirely above the published non-foundation row with the highest point estimate; on BETA, no new row lies above standard CCA, which needs no training. On EEGMAT, frozen readouts and LoRA order the models differently: one fixed recipe on one task, with LoRA budgets that differ by model, not a ranking.',
        zh: '睡眠分期是唯一一个有新的冻结单元格——ST-EEGFormer Large、ST-EEGFormer Base 与 REVE Large——完全高于所有已发布行的协议。在其余 6 个有分数的协议上，没有任何新单元格完全高于已发布的非基础模型行中点估计最高的那一行；在 BETA 上，没有任何新行高于无需训练的标准 CCA。在 EEGMAT 上，冻结读出与 LoRA 给出的模型顺序并不一致：这是一项任务上的一个固定方案，各模型的 LoRA 参数量也各不相同，不是排名。' },
      { en: 'BETA is in ST-EEGFormer’s published pretraining list and TMNRED in SingLEM’s, so those cells are flagged; ZUNA 1.1 does not list its pretraining data, so every ZUNA 1.1 cell is marked unknown. Every other cell, LaBraM’s and CBraMod’s included, is not in the authors’ published pretraining list as checked on 4 October 2026: a sourced statement, not proof that the recordings were never seen. Weights licences travel with the rows: REVE under its Responsible Use License, LUNA under CC BY-ND 4.0, ERP-FM for non-commercial use only, and ZUNA 1.1’s model card limits it to research use, not diagnosis or clinical use.',
        zh: 'BETA 在 ST-EEGFormer 作者公开的预训练数据清单中，TMNRED 在 SingLEM 的清单中，这些单元格都已标出；ZUNA 1.1 没有公开其预训练数据清单，所以它的每个单元格都标为未知。其余单元格——包括 LaBraM 与 CBraMod 的——都不在作者公开的预训练数据清单中（2026 年 10 月 4 日核查）：这是有出处的陈述，并不证明这些记录从未被模型见过。权重许可随行标出：REVE 采用其负责任使用许可，LUNA 为 CC BY-ND 4.0，ERP-FM 仅限非商业用途，ZUNA 1.1 的模型卡限定仅供研究使用，不可用于诊断或临床。' },
      { en: 'Not published: per-trial, per-person and per-fold values, features, and timings and memory — measured on a shared GPU, so the CSVs leave the scoring-time column empty — the declared sensitivity runs beyond the row footnotes that state them, and the aggregate, the group summaries and the six independent audits themselves, pinned by hash in the review manifest because they carry private storage paths. Two BrainOmni cells were not run, because its tokenizer needs two-second windows: they are null with that reason, never zero. The released matrix keeps its bytes; the new rows never enter experiments.json.',
        zh: '不发布：逐试次、逐人与逐折的数值、特征，以及计算耗时与显存——它们在共享 GPU 上测得，所以 CSV 的评分耗时列留空；超出行脚注所述内容的预设敏感性分析；以及聚合文件、各组汇总与 6 份独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。BrainOmni 有两个单元格没有运行，因为它的分词器需要两秒的时间窗：这两格为空值并注明原因，而不是零。已发布的矩阵保持原有字节；新行不会进入 experiments.json。' },
    ],
  },
  {
    id: 'reliable-decisions-update-20261004', date: '2026-10-04', payload: 'reliableDecisions',
    files: ['reliable-decisions-update.json'],
    pages: ['/topics/when-not-to-act/'],
    summary: {
      en: 'Route 1 of the decision-research roadmap, reliable decisions: when a decoder should decline to decide, and what its confidence is worth. The saved test scores of models this site already publishes — spectral ridge, EEGNet and two LaBraM arms on EEGMAT (36 people); standard CCA, CBraMod and EEGNet on BETA (70 people) — rescored under a fixed confidence threshold, a coverage target, a certified selective risk and a learned reject option, with probability quality and a person-specific recalibration whose label cost is counted. No classifier was retrained, so every full-coverage accuracy equals the published one. Every protocol is balanced or uniform by design: these are method comparisons, never deployment error rates, and nothing is ranked where intervals overlap.',
      zh: '决策研究路线图的第一条路线——可靠的决策：解码器什么时候应当拒绝作出决定，它的置信度又值多少。本站已发布模型保存下来的测试分数——EEGMAT 上的 spectral ridge、EEGNet 与两种 LaBraM 配置（36 名被试），BETA 上的标准 CCA、CBraMod 与 EEGNet（70 名被试）——在固定置信度阈值、覆盖率目标、经认证的选择性风险和可学习的拒识选项四种策略下重新评分，另测概率质量，以及按人重新校准的效果和它所花费的标签。没有重新训练任何分类器，所以全覆盖时的准确率都与已发布的数值相同。每个协议在设计上都是类别平衡或均匀的：这些是方法之间的比较，从来不是部署时的错误率；区间重叠时不排名。',
    },
    notes: [
      { en: 'The certified selective risk certified no outer fold on EEGMAT, so it accepted nothing there: no error rate, not a zero one. On BETA its realised error exceeded a certified fold’s own target in some folds: a nominal guarantee across people, whose failure rate is measured here, not assumed. The learned reject option had a lower error than the model’s own calibrated confidence for no method.',
        zh: '经认证的选择性风险在 EEGMAT 上没有认证任何一个外层折，所以在那里什么都没有接受：没有错误率，而不是错误率为零。在 BETA 上，有些已认证折的实际错误率超过了该折自己的目标：这是跨被试的名义保证，它失效的频率在这里是测出来的，不是假设的。可学习的拒识选项在任何一种方法上都没有比模型自身校准后的置信度错得更少。' },
      { en: 'ds003810 (ten people) is shown as crude, in a collapsed robustness panel beside secondary seeds, two sensitivity arms (their risk-certification fold counts only) and an exploratory reject head trained jointly with its classifier. Left out: the idle protocol, whose route-1 window proportions are a different unit from the trial-level idle figures on the same page, and every figure of the BNCI2015-001 arm, whose editorial hold stands.',
        zh: 'ds003810（10 名被试）标为粗略，放在折叠的稳健性面板里，旁边是其余随机种子、两个敏感性分析（只给风险认证的折数），以及一个与分类器联合训练的探索性拒识头。没有放进来的：空闲协议——第一条路线在它上面得到的是按窗口的比例，与同一页上按试次统计的空闲数字单位不同；以及 BNCI2015-001 分析的全部数字——该数据源的编辑暂缓仍然有效。' },
      { en: 'Not published: per-trial, per-person and per-fold values, including the release candidate’s person-level percentiles and its median temperature over folds; the accuracies of the matched-holdout, map-sensitivity and jointly trained arms; and the independent audits themselves, pinned by hash in the review manifest because they carry private storage paths. The primary audit’s one failed check is a documentation error, not a computation error, and is stated as such.',
        zh: '不发布：逐试次、逐人和逐折的数值，包括发布候选文件中按人统计的百分位数，以及各折温度的中位数；匹配留出、映射敏感性与联合训练这几组分析的准确率；以及独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。主审计唯一没有通过的一项是文档错误，不是计算错误，这里如实说明。' },
    ],
  },
  {
    id: 'large-source-update-20261003', date: '2026-10-03', payload: 'largeSource',
    files: ['large-source-update.json'],
    pages: ['/topics/sleep-staging/', '/topics/calibration-budget/'],
    summary: {
      en: 'Two new sources, two separate questions, each with two fixed classical CPU baselines and no shared ranking. Dreem: five-stage sleep staging against the publisher’s consensus in 25 healthy sleepers (DOD-H) and 55 people with obstructive sleep apnoea (DOD-O), kept as separate experiments — a training prior and a spectral ridge, accuracy beside balanced accuracy, macro F1, Cohen’s kappa and the ridge’s stage-by-stage results. And OpenBMI: a motor-imagery decoder trained on a person’s first session and tested on their second after 0, 10, 20 or 40 labelled trials from it, in 51 people, with how many people declined beside every mean change. No foundation-model or fine-tuning result.',
      zh: '两个新来源、两个各自独立的问题，各有两个固定的经典 CPU 基线，彼此不排名。Dreem：以发布者的共识分期为标准的五期睡眠分期，25 名健康被试（DOD-H）与 55 名阻塞性睡眠呼吸暂停患者（DOD-O）作为两项独立实验——训练集先验与 spectral ridge，准确率与平衡准确率并排，另有宏平均 F1、Cohen kappa 系数，以及 spectral ridge 的逐期结果。另有 OpenBMI：运动想象解码器在被试的第一次会话上训练，加入第二次会话的 0、10、20 或 40 个校准试次后在第二次会话上测试，51 名被试，每个平均变化旁都给出有多少人下降。没有基础模型或微调结果。',
    },
    notes: [
      { en: 'The spectral ridge never predicts N1 in either cohort, so its N1 precision is not defined: it is published as null, never as zero. The training prior’s balanced accuracy sits slightly above one fifth because a night’s mean covers only the stages that night contains; it is a floor, not a chance level. Neural-network and foundation models on the Dreem cohorts are held, because the source’s physical units disagree.',
        zh: 'spectral ridge 在两个队列中都从未预测过 N1，所以它的 N1 精确率没有定义：发布为空值，而不是零。训练集先验的平衡准确率略高于五分之一，因为每晚的均值只涵盖该晚出现过的分期；它是一个下限，不是随机水平。Dreem 队列上的神经网络与基础模型暂缓，因为数据源的物理单位说法不一致。' },
      { en: 'OpenBMI is an expanded cohort under the same fixed method — the original 40 people with their results unchanged, plus 11 later-eligible people — not an independent replication; an earlier 40-person snapshot was prepared but never published here and is not a separate result. The relative-PSD change at 40 trials has an interval that includes zero and is not established.',
        zh: 'OpenBMI 是同一固定方法下扩大的队列——原有 40 名被试、结果不变，加上之后符合条件的 11 名被试——不是独立的重复验证；更早的 40 人快照已准备好、但从未在本站发布，它不是一个单独的结果。相对 PSD 基线在 40 个试次时的变化，区间包含零，不能认定。' },
      { en: 'Not published: per-person and per-night values (including the worst observed change, medians and 10th percentiles), Brier scores, log-likelihoods and calibration errors, the combined DOD-H plus DOD-O summary, and the independent audits themselves, which are pinned by hash in the review manifest because they carry private storage paths.',
        zh: '不发布：逐人与逐晚的数值（包括观察到的最差变化、中位数与第 10 百分位数）、Brier 分数、对数似然与校准误差、DOD-H 与 DOD-O 合并后的汇总，以及独立审计文件本身——它们含有私有存储路径，因此只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'extension-update-20261002', date: '2026-10-02', payload: 'extension',
    files: ['extension-update.json'],
    pages: ['/topics/when-not-to-act/', '/topics/screen-to-vr/'],
    summary: {
      en: 'Twenty further people of the asynchronous SSVEP release, scored with a rejection threshold fixed on the four-person pilot and with a personal one: detection, coverage, correct-and-accepted output and false acceptance per non-control state, side by side. And a new source, LTRSVP: a P300 decoder trained on one recording at 5 or 10 images a second and tested on a different, 10-Hz recording, with the full rate-by-rate matrix. Fixed classical baselines; no foundation-model or fine-tuning result.',
      zh: '异步 SSVEP 数据集中另外 20 名被试，分别用在四人试点上固定的拒识阈值和逐人阈值评分：检测、覆盖率、被接受且正确的输出，以及每种非控制状态下的误接受，并排给出。另有一个新来源 LTRSVP：P300 解码器在每秒 5 张或 10 张图像的一段记录上训练，在另一段 10 Hz 记录上测试，附完整的速率对速率矩阵。都是固定的经典基线，没有基础模型或微调结果。',
    },
    notes: [
      { en: 'The personal threshold raised detection balanced accuracy for 10 of 20 people and lowered it for 8, and did not raise the share of commands both accepted and correct. The image-rate difference has an interval that crosses zero, and rate and recording change together, as does time in the session (the original study presented the rates from the lowest to the highest, not randomised), so no rate effect is claimed.',
        zh: '逐人阈值使 20 名被试中 10 人的检测平衡准确率上升、8 人下降，被接受且正确的指令占比并没有提高。图像速率差值的区间跨过零，而且速率与记录一起变化，在实验中的时间位置也随之变化（原始研究按速率从低到高呈现，没有随机化），所以不声称存在速率效应。' },
      { en: 'Not published: per-person values, thresholds, predictions, and the independent audits themselves, which are pinned by hash in the review manifest because they carry private storage paths.',
        zh: '不发布：逐人数值、阈值、预测结果，以及独立审计文件本身——它们含有私有存储路径，因此只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'adaptation-update-20261001', date: '2026-10-01', payload: 'adaptation',
    files: ['adaptation-update.json'],
    // Published on calibration-budget; its own topic since 2026-10-02.
    pages: ['/topics/model-adaptation/'],
    summary: {
      en: 'New people, same task, zero labels from the test person: LaBraM adapted on mental arithmetic three ways — head only, last block, rank-4 LoRA — with the same checkpoint, folds, starting heads, batch order and five-epoch recipe, over three seeds. The next-day experiment is listed as status only.',
      zh: '新被试、同一任务、不使用测试被试的任何标签：在心算任务上用三种方式适配 LaBraM——只训分类头、最后一个 Transformer 块、秩为 4 的 LoRA——使用相同的检查点、数据划分、初始分类头、批次顺序和训练 5 轮的配方，跑了 3 个随机种子。次日实验只列状态。',
    },
    notes: [
      { en: "Printed beside the core matrix's frozen LaBraM readout on the same people and folds, because this batch's head-only arm is a short gradient-trained head and not the strongest frozen readout.",
        zh: '与核心矩阵中同一批被试、同一数据划分上的冻结 LaBraM 分类头结果并排给出，因为本批「只训分类头」那一组是短训练的梯度分类头，并不是冻结编码器能达到的最好结果。' },
      { en: 'Not published: memory figures (allocator samples are lower bounds, not per-method peaks) and any figure from the next-day experiment.',
        zh: '不发布：内存数据（分配器采样只是下界，不是各方法的峰值），以及次日实验的任何数字。' },
    ],
  },
  {
    id: 'context-update-20260927', date: '2026-09-27', payload: 'context',
    files: ['context-update.json'],
    pages: ['/topics/screen-to-vr/', '/topics/on-the-move/', '/topics/when-not-to-act/'],
    summary: {
      en: 'P300 calibration carried from a PC screen to a VR headset and back for 21 people; walking-speed scores from dry-electrode EEG printed beside a movement-nuisance comparator; and a four-person pilot of SSVEP windows accepted when no command was intended. Fixed CPU baselines; no foundation-model or fine-tuning result.',
      zh: '21 名被试的 P300 校准在电脑屏幕与 VR 头显之间来回迁移；行走时干电极 EEG 的步速分数，旁边并排放着运动干扰特征的对照基线；以及一个四人试点：无意发出指令时，SSVEP 窗口被误接受的情况。都是固定的 CPU 基线，没有基础模型或微调结果。',
    },
    notes: [
      { en: 'Not published although correct: the direction-specific transfer means, because the independent audit did not recompute them.',
        zh: '虽然正确也不发布：分方向的迁移均值，因为独立审计没有重新计算它们。' },
    ],
  },
  {
    id: 'clinical-update-20260923', date: '2026-09-23', payload: 'clinical',
    files: ['clinical-update.json'],
    pages: ['/topics/clinical-groups/'],
    summary: {
      en: 'A 149-person clinical case/control comparison, printed beside an age-and-sex-only comparator, and three holds that produced no score.',
      zh: '149 名被试的临床病例对照比较，旁边并排放着只用年龄和性别的对照基线；另有三项暂缓，都没有产生分数。',
    },
    notes: [
      { en: 'Not published although aggregate: the per-group age and sex composition of the clinical cohort.',
        zh: '虽然是聚合量也不发布：临床队列各组的年龄与性别构成。' },
    ],
  },
  {
    id: 'evidence-update-20260922', date: '2026-09-22', payload: 'evidence',
    files: ['evidence-update.json'],
    // The adaptation roadmap it carried was on calibration-budget; what is left of
    // it, the engineering check, has been on model-adaptation since 2026-10-02.
    pages: ['/topics/fewer-electrodes/', '/topics/on-the-move/', '/topics/model-adaptation/'],
    summary: {
      en: 'In-ear against scalp sleep staging, four posterior electrodes against sixteen, a physical-phantom motion test, and the status of planned adaptation experiments.',
      zh: '耳道内与头皮的睡眠分期比较、后部 4 个电极对全部 16 个电极、物理头模的运动测试，以及计划中的适配实验的状态。',
    },
    notes: [
      { en: 'Amended the EESM19 consent note (see data use). The core snapshot and the topic export were regenerated with one added citation; no score changed. Their current hashes, below, are the amended files.',
        zh: '修订了 EESM19 的同意书说明（见数据使用页）。核心快照与专题导出因此重新生成，只多了一条引用，没有任何分数变化。下方显示的是修订后文件的哈希。' },
    ],
  },
  {
    id: 'deployment-topics-20260920-v1', date: '2026-09-20', payload: 'deployment',
    files: ['deployment-topics.json'],
    pages: ['/topics/dry-vs-wet/', '/topics/on-the-move/', '/topics/calibration-budget/', '/topics/does-pretraining-help/'],
    summary: {
      en: 'Four deployment questions, each with its own protocol: paired contrasts, descriptive intervals and three-seed sensitivity groups.',
      zh: '四个部署问题，各有自己的协议：配对对比、描述性区间，以及三个随机种子的敏感性分组。',
    },
    notes: [],
  },
  {
    id: 'research-preview-20260920', date: '2026-09-20', payload: 'mvp',
    files: ['experiments.json', ...protocolFiles],
    pages: ['/'],
    summary: {
      en: 'The core matrix: eight fixed protocols on seven public data sets, with one file of results and one protocol descriptor per protocol.',
      zh: '核心矩阵：7 个公开数据集上的 8 个固定协议，每个协议一份结果文件和一份协议说明。',
    },
    notes: [],
  },
];

// Newest first is load-bearing: the home page's "Updated" date, the /api/
// citation, the home Dataset markup and CITATION.cff all take the first entry.
for (let i = 1; i < releases.length; i++)
  if (releases[i].date > releases[i - 1].date)
    throw new Error(`releases.ts: ${releases[i].id} is newer than ${releases[i - 1].id}; keep the list newest first`);

/** The newest release: the one the site, CITATION.cff and the home Dataset markup cite. */
export const latestRelease = releases[0];

/**
 * The releases that ship the given served files ('deployment-topics.json' or
 * '/data/deployment-topics.json'), newest first, each once. A page's "cite this
 * page" block names these, so it can only cite a release whose bytes the page's
 * figures come from.
 */
export function releasesFor(files: string[]): Release[] {
  const names = new Set(files.map(f => f.replace(/^\/data\//, '')));
  const found = releases.filter(r => r.files.some(f => names.has(f)));
  const shipped = new Set(found.flatMap(r => r.files));
  const unknown = [...names].filter(f => !shipped.has(f));
  if (unknown.length) throw new Error(`releases.ts: no release ships ${unknown.join(', ')}`);
  return found;
}

/*
 * The release log's index (owner decision D17, 2026-10-28). /releases/ shows the newest release days in full, each with
 * one to three short changes, and one line for every earlier release; /releases/archive/ carries every record above as
 * released. Ids released on one day are one site version (D20), so the index counts days, not ids.
 */

/** One short change of a release day: a sentence whose bracketed spans are its links, in the order of `links`. */
export interface Change {
  /** English and Chinese, each with one `[…]` span per link. */
  text: Text;
  /** One or two site paths, each with its anchor where the change has one. */
  links: string[];
}

/** How many release days the index shows in full. */
export const LATEST_DAYS = 3;

/** The release days, newest first, each with its ids in the order of `releases`. */
export function releaseDays(): { date: string; releases: Release[] }[] {
  const days: { date: string; releases: Release[] }[] = [];
  for (const r of releases) {
    const last = days.at(-1);
    if (last?.date === r.date) last.releases.push(r);
    else days.push({ date: r.date, releases: [r] });
  }
  return days;
}

// Every figure a highlight prints, as each language prints it; the checks below admit no other (D29: counts computed
// from the payloads).
const printed = { en: new Set<string>(), zh: new Set<string>() };
const hlWord = (n: number) => {
  const en = said(n), zh = said(n, true);
  printed.en.add(en); printed.zh.add(zh);
  return { en, zh, En: cap(en) };
};
const hlFigure = (n: number) => { const s = count(n); printed.en.add(s); printed.zh.add(s); return s; };
// 2026-10-28: the four result files of the round.
const hlCards = hlWord(scCards.length);
const hlFirstCard = need([...sc.placement.cards].sort((a: { card: number }, b: { card: number }) => a.card - b.card)[0], 'the first follow-up card');
const hlCases = hlWord(dc.cases.length);
const hlWindow = hlWord(ts.cohort.window_seconds);
if ((nr.blocks as { id: string }[]).map(b => b.id).join() !== 'eegmat,mi-rest,p300-target')
  throw new Error('releases.ts: the NeuroRVQ highlight names arithmetic, motor imagery and P300; the file’s blocks changed');
// 2026-10-20: that day's register file, and the questions that day opened (topic pages no earlier release names).
const hlRows = hlFigure(register20261020.counts.rows.total);
const openedOn = (date: string) => {
  const before = new Set(releases.filter(r => r.date < date).flatMap(r => r.pages));
  return [...new Set(releases.filter(r => r.date === date).flatMap(r => r.pages))].filter(p => /^\/topics\/[^/]+\/$/.test(p) && !before.has(p));
};
const hlQuestions = openedOn('2026-10-20');
if (hlQuestions.join() !== [ssvepFollowUps.placement.page, dataQuality.placement.page].join())
  throw new Error(`releases.ts: the 2026-10-20 highlight names the two questions that day opened, not ${hlQuestions.join(', ')}`);
const hlNewQuestions = hlWord(hlQuestions.length);
// 2026-10-13: EEGPT's channel counts on the two protocols fewer-electrodes shows.
const eegptChannels = (id: string) => need(eegptCore.protocols.find(p => p.id === id), `EEGPT’s ${id} protocol`).channels;
const [hlBeta, hlSleep] = [hlWord(eegptChannels('beta-4ch')), hlWord(eegptChannels('sleep-scalp'))];

/**
 * What each of the newest release days changed (owner decision D29: the plan's drafts, counts computed from the
 * payloads). A day leaves the index when it is no longer among the newest LATEST_DAYS, and its entry here is unused.
 */
export const highlights: Record<string, Change[]> = {
  '2026-10-28': [
    { text: { en: `${hlCards.En} more follow-ups on [SSVEP frequencies a decoder never trained on], among them filter-bank CCA, shorter windows, fewer electrodes and fixed harmonic weights, each beside its untrained control.`,
              zh: `[解码器没训练过的 SSVEP 频率]又有${hlCards.zh}项后续检验，包括滤波器组 CCA、更短的时间窗、更少的电极和固定的谐波权重，每项都与不训练的对照并列。` },
      links: [`${sc.placement.page}#${hlFirstCard.anchor}`] },
    { text: { en: `Frozen-encoder probes in panels of their own: [NeuroRVQ] on arithmetic, motor imagery and P300, and [EEG-Captioner and AXON] on ${hlWindow.en}-second arithmetic and rest windows.`,
              zh: `冻结编码器探针各成一栏：[NeuroRVQ] 用于心算、运动想象与 P300；[EEG-Captioner 与 AXON] 用于${hlWindow.zh}秒心算与静息窗口。` },
      links: [`${nr.placement.page}#${nr.placement.anchor}`, `${ts.placement.page}#${ts.placement.anchor}`] },
    { text: { en: `${hlCases.En} more datasets [checked end to end], with a CCA baseline on Kim’s beta-range SSVEP, and [the open register] extended to match.`,
              zh: `又有${hlCases.zh}个数据集[从头核到尾]，其中有 Kim beta 频段 SSVEP 的 CCA 基线；[开放登记册]随之扩充。` },
      links: [dc.placement.page, '/methods/register/'] },
  ],
  '2026-10-20': [
    { text: { en: `The open register: [every EEG dataset we know of] and [every EEG model we track], in ${hlRows} rows, each at the furthest step checked, with its gaps listed.`,
              zh: `开放登记册：[我们知道的每个 EEG 数据集]和[我们关注的每个 EEG 模型]，共 ${hlRows} 行，每行停在核验到的最远一步，并列出缺口。` },
      links: ['/datasets/register/', '/methods/register/'] },
    { text: { en: `${hlNewQuestions.En} new questions: what lets a decoder answer [SSVEP frequencies it never trained on], and [what public EEG files show when checked end to end].`,
              zh: `${hlNewQuestions.zh}个新问题：解码器靠什么回答[没训练过的 SSVEP 频率]，以及[公开 EEG 文件从头核到尾后能看到什么]。` },
      links: hlQuestions },
    { text: { en: '[IESSEEG] infant case-control results with age and recording-setting controls, and [NeuroLM’s frozen features on EEGMAT] in a panel of their own.',
              zh: '[IESSEEG] 婴儿病例对照结果，附年龄与采集设置对照；[NeuroLM 在 EEGMAT 上的冻结特征]单独成一栏。' },
      links: [`${clinicalIesseeg.placement.page}#${clinicalIesseeg.placement.section}`, `${neurolmEegmat.placement.page}#${neurolmEegmat.placement.anchor}`] },
  ],
  '2026-10-13': [
    { text: { en: 'EEGPT’s frozen row beside the core matrix on [every core protocol], computed in the same runs as the published LaBraM rows.',
              zh: 'EEGPT 的冻结结果作为一行放在核心矩阵旁，覆盖[每个核心协议]，与已发布的 LaBraM 各行出自同一批运行。' },
      links: ['/protocols/'] },
    { text: { en: `Its [pretraining-attribution rows] beside LaBraM’s and CBraMod’s, and its [${hlBeta.en}-channel BETA and ${hlSleep.en}-channel sleep rows].`,
              zh: `它的[预训练归因各行]与 LaBraM、CBraMod 的并列，另有[${hlBeta.zh}通道 BETA 与${hlSleep.zh}通道睡眠分期各行]。` },
      links: ['/topics/does-pretraining-help/', '/topics/fewer-electrodes/'] },
    { text: { en: 'A [method page for EEGPT]: its checkpoint, inputs and terms, and its pretraining exposure by dataset.',
              zh: 'EEGPT 的[方法页面]：检查点、输入与条款，以及各数据集是否出现在它的预训练数据中。' },
      links: ['/methods/eegpt/'] },
  ],
};

/** A change's text without its link brackets: what a reader sees. */
export const changeText = (t: string) => t.replace(/[[\]]/g, '');
// Build-time rules for the highlights (plan §4.4); release-record.ts adds that every link resolves to a built page.
{
  const LIMIT = { en: 220, zh: 110 };
  const DATE_OR_VERSION = /\b20\d\d\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\b(?:[Uu]pdated|[Ss]ince|[Nn]ew in|[Aa]dded)\b|(?<![\w./#-])[vV]\d+\b|\d+ ?[年月日]|更新|新增于|本次|这次|第[一二三四五六七八九十]+轮/;
  // Figures: digits not part of a name such as P300; number words, which are counts in this text.
  const FIGURES = /(?<![A-Za-z0-9.-])[0-9][0-9,.]*(?<![,.])/g;
  const WORDS_IN = { en: /\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten)\b/gi, zh: /[零一两二三四五六七八九十]+(?=个|项|名|秒|通道)/g };
  const days = new Set(releaseDays().map(d => d.date));
  for (const date of Object.keys(highlights))
    if (!days.has(date)) throw new Error(`releases.ts: highlights name ${date}, which is no release day`);
  for (const { date } of releaseDays().slice(0, LATEST_DAYS)) {
    const changes = highlights[date];
    if (!changes || changes.length < 1 || changes.length > 3)
      throw new Error(`releases.ts: the release day ${date} needs one to three highlights, not ${changes?.length ?? 0}`);
    for (const c of changes) {
      if (c.links.length < 1 || c.links.length > 2) throw new Error(`releases.ts: a ${date} highlight has ${c.links.length} links; one or two`);
      const digits = { en: '', zh: '' };
      for (const l of ['en', 'zh'] as const) {
        const t = c.text[l], spans = t.match(/\[[^[\]]+\]/g) ?? [], seen = changeText(t);
        const where = `releases.ts: the ${date} highlight “${seen.slice(0, 40)}…”`;
        if (spans.length !== c.links.length || seen.length !== t.length - 2 * spans.length)
          throw new Error(`${where} (${l}) needs one [bracketed] span per link (${c.links.length})`);
        if (seen.length > LIMIT[l]) throw new Error(`${where} (${l}) is ${seen.length} characters; at most ${LIMIT[l]}`);
        const label = seen.match(DATE_OR_VERSION);
        if (label) throw new Error(`${where} (${l}) carries a date, version or update word: “${label[0]}”`);
        const figs = [...seen.matchAll(FIGURES)].map(m => m[0]);
        for (const f of [...figs, ...[...seen.matchAll(WORDS_IN[l])].map(m => m[0].toLowerCase())])
          if (!printed[l].has(f)) throw new Error(`${where} (${l}) prints “${f}”, which no payload gave it`);
        digits[l] = figs.sort().join(' ');
      }
      if (digits.en !== digits.zh) throw new Error(`releases.ts: a ${date} highlight prints ${digits.en || 'no figure'} in English and ${digits.zh || 'no figure'} in Chinese`);
    }
  }
}

export interface Hold {
  /**
   * Stable slug: the register row on /releases/ is `#hold-<id>`, and a home card
   * without a page of its own links there. The payload's own id where it has one.
   */
  id: string;
  item: Text;
  /** Short state word for the home-page card. */
  state: Text;
  opened: string;
  closed: string | null;
  outcome: Text;
  /**
   * The home card's sentence, where the register's `outcome` tells the hold's history by date: what is held and
   * why, with no date (owner decision, 2026-10-08). The register keeps the dated outcome.
   */
  card?: Text;
  href?: string;
}

/** Every hold ever recorded, open or resolved. The home page shows the open ones. */
export const holds: Hold[] = [
  // The dataset-checks batch (dataset-checks-update.json `holds`, ids as the export gives them; owner decisions D15, D16).
  // Kim's amplitude-dependent models wait on physical units; Damm's and NeBULA's scores are held under the one-person
  // rule (D2), as eldBETA's are. MIND is published (D15) and opens no hold.
  {
    id: 'kim-amplitude-dependent-models',
    item: { en: 'Kim beta-range SSVEP · amplitude-dependent models', zh: 'Kim beta 频段 SSVEP · 依赖幅值的模型' },
    state: { en: 'Held', zh: '暂缓' },
    opened: dc.release_record.date, closed: null,
    outcome: { en: `${dcHold('kim-amplitude-dependent-models').reason} Training-free CCA, which does not depend on a common amplitude scale, is published for all ${kim.cohort.participants} participants.`,
               zh: `${zhOf(DC_HOLD_ZH, dcHold('kim-amplitude-dependent-models').reason, 'the Kim hold')}不需要训练的 CCA 不依赖共同的幅值尺度，全部 ${kim.cohort.participants} 名被试的结果已发布。` },
    card: { en: `${dcHold('kim-amplitude-dependent-models').reason} Training-free CCA, which does not depend on a common amplitude scale, is published.`,
            zh: `${zhOf(DC_HOLD_ZH, dcHold('kim-amplitude-dependent-models').reason, 'the Kim hold')}不需要训练的 CCA 不依赖共同的幅值尺度，已发布。` },
    href: `${dc.placement.page}#${kim.section}`,
  },
  {
    id: 'damm-one-participant-score',
    item: { en: 'Damm finger motor imagery · one-person score', zh: 'Damm 手指运动想象 · 单人分数' },
    state: { en: 'Status only', zh: '只发状态' },
    opened: dc.release_record.date, closed: null,
    outcome: { en: `One participant’s ${said(damm.design.runs_used)} random-order runs, checked end to end: ${damm.design.delivered_cues} delivered cues, and ${said(damm.variants.length)} variants and controls fixed before scoring and independently audited. Every score is held under the one-person rule, by the owner’s decision; design, counts and file facts are published.`,
               zh: `一名被试的${said(damm.design.runs_used, true)}个随机顺序 run 从头到尾跑通：${damm.design.delivered_cues} 个实际呈现的提示，${said(damm.variants.length, true)}种变体与对照在评分之前就已固定，并经过独立审计。按单人规则，所有分数依所有者的决定暂缓；设计、计数与文件事实已发布。` },
    card: { en: `One participant’s ${said(damm.design.runs_used)} random-order runs, checked end to end. The scores are held under the one-person rule; design, counts and file facts are published.`,
            zh: `一名被试的${said(damm.design.runs_used, true)}个随机顺序 run 从头到尾跑通。分数按单人规则暂缓；设计、计数与文件事实已发布。` },
    href: `${dc.placement.page}#${damm.section}`,
  },
  {
    id: 'nebula-one-participant-scores',
    item: { en: 'NeBULA · one-person scores', zh: 'NeBULA · 单人分数' },
    state: { en: 'Status only', zh: '只发状态' },
    opened: dc.release_record.date, closed: null,
    outcome: { en: `One participant reaching to ${said(nebula.design.targets)} targets under ${rnList(nebula.design.assistance_conditions)} assistance: ${nebula.design.trials} delivered trials, with EEG, EMG and EEG plus EMG arms run and independently audited. Every score is held under the one-person rule, by the owner’s decision; design, counts and file facts are published.`,
               zh: `一名被试在自由、低与高${said(nebula.design.assistance_conditions.length, true)}种辅助水平下伸手够向${said(nebula.design.targets, true)}个目标：${nebula.design.trials} 个实际进行的试次，EEG、EMG 与 EEG 加 EMG 各组都已运行并经过独立审计。按单人规则，所有分数依所有者的决定暂缓；设计、计数与文件事实已发布。` },
    card: { en: `One participant reaching to ${said(nebula.design.targets)} targets under ${said(nebula.design.assistance_conditions.length)} levels of assistance. The EEG, EMG and combined scores are held under the one-person rule; design, counts and file facts are published.`,
            zh: `一名被试在${said(nebula.design.assistance_conditions.length, true)}种辅助水平下伸手够向${said(nebula.design.targets, true)}个目标。EEG、EMG 与两者合并的分数都按单人规则暂缓；设计、计数与文件事实已发布。` },
    href: `${dc.placement.page}#${nebula.section}`,
  },
  // The data-quality batch (data-quality-update.json `holds`, ids as the export gives them). eldBETA's one-person score
  // is held by the owner's decision D2, keeping the one-person rule (Stieger, FALCON H2); its counts are published.
  {
    id: 'eldbeta-one-participant-score',
    item: { en: 'eldBETA · one-person score', zh: 'eldBETA · 单人分数' },
    state: { en: 'Status only', zh: '只发状态' },
    opened: '2026-10-20', closed: null,
    outcome: { en: `The raw-recording route runs end to end on one participant’s ${eld.blocks} blocks, and all ${eld.trials} trials pass the reader and the quality checks. With one person every score is that person’s, so the accuracy is held, by the owner’s decision; the counts are published.`,
               zh: `从原始记录读起的流程在一名被试的 ${eld.blocks} 个组块上跑通，全部 ${eld.trials} 个试次都通过了读取与质量检查。只有一个人时，任何分数都是这个人的分数，所以准确率按所有者的决定暂缓；计数已发布。` },
    card: { en: 'The raw-recording route runs end to end on one participant’s recordings. With one person every score is that person’s, so the accuracy is held; the counts are published.',
            zh: '从原始记录读起的流程在一名被试的记录上跑通。只有一个人时，任何分数都是这个人的分数，所以准确率暂缓；计数已发布。' },
    href: '/topics/data-quality/#eldbeta',
  },
  // ZuCo 2.0: one converted run's fixation timing. The card's heading names the dataset without its version number,
  // because a hold card carries no decimal figure; the register row's outcome names it in full.
  {
    id: 'zuco2-converted-run-timing',
    item: { en: 'ZuCo on NEMAR · converted-run timing', zh: 'NEMAR 上的 ZuCo · 转换后记录的时间' },
    state: { en: 'No score', zh: '没有分数' },
    opened: '2026-10-20', closed: null,
    outcome: { en: 'In one converted run of ZuCo 2.0 on NEMAR, some fixation times fall outside the recording. No EEG–text score is computed until the converter’s timing rules and a source-checksummed fixture are available; no timing was corrected and no row removed.',
               zh: '在 NEMAR 上 ZuCo 2.0 的一个转换后记录中，有些注视时间落在记录之外。在转换程序的时间规则与带源校验和的测试样例具备之前，不计算任何 EEG–文本分数；没有修正任何时间，也没有删除任何数据行。' },
    card: { en: 'In one converted run on NEMAR, some fixation times fall outside the recording. No EEG–text score is computed until the converter’s timing rules and a source-checksummed fixture are available.',
            zh: '在 NEMAR 上的一个转换后记录中，有些注视时间落在记录之外。在转换程序的时间规则与带源校验和的测试样例具备之前，不计算任何 EEG–文本分数。' },
    href: '/topics/data-quality/#zuco2',
  },
  // BINGO, while its publication switch holds it (pilot-switch.ts): the export's hold record, with no figure.
  ...(bingoReleased ? [] : [{
    id: BINGO_HOLD,
    item: { en: 'BINGO inner-speech dataset · cross-language baseline', zh: 'BINGO 内部言语数据集 · 跨语言基线' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-10-12', closed: null,
    outcome: { en: 'Run and independently audited. The source states no licence, the cross-language dataset’s own documentation has no ethics or consent statement, and the only consent statement available is the project’s, for its other dataset recorded in the same laboratory, so no figure is published.',
               zh: '已运行并通过独立审计。数据源没有说明许可，跨语言数据集自己的文档没有伦理或知情同意声明，能找到的知情同意声明只有项目针对同一实验室记录的另一个数据集的那一句，所以不发布任何数字。' },
    href: '/topics/pilot-studies/#bingo',
  } satisfies Hold]),
  // The handwriting analysis, while its publication switch holds it (pilot-switch.ts): the export's hold record, with no
  // figure. Released by the owner's decision of 2026-10-12 with its rights gap stated, so it is not in the register.
  ...(handwritingReleased ? [] : [{
    id: HANDWRITING_HOLD,
    item: { en: 'EEG-fNIRS handwriting dataset · mask-aware EEG', zh: 'EEG-fNIRS 手写数据集 · 掩码感知 EEG' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-10-12', closed: null,
    outcome: { en: 'Run and independently audited. The dataset card declares a non-commercial share-alike licence and gated access, but no ethics-approval or informed-consent statement was found, on the card or in a participating team’s challenge paper, so no figure is published until that basis is established.',
               zh: '已运行并通过独立审计。数据集卡片声明的是非商业、相同方式共享的许可，访问需申请，但无论在卡片上还是在一支参赛队伍的挑战赛论文中，都没有找到伦理批准或知情同意声明，所以在这一依据确立之前不发布任何数字。' },
    href: '/topics/pilot-studies/#handwriting',
  } satisfies Hold]),
  // The beyond-scalp batch (beyond-scalp-update.json `holds`): decoding of any kind on ds007420; its coverage counts are published.
  {
    id: 'ds007420-classifier',
    item: { en: 'ds007420 · fNIRS classifier', zh: 'ds007420 · fNIRS 分类器' },
    state: { en: 'No score', zh: '没有分数' },
    opened: '2026-10-12', closed: null,
    outcome: { en: 'Its numeric task codes have no verified lookup to hands or movements, and its event durations disagree between the events table, the optical files and the cited paper, so no classifier was scored. Its optical coverage counts are published.',
               zh: '它的数字任务编码没有经过核实的、与左右手或动作对应的对照表，事件时长在事件表、光学数据文件与所引论文之间也互相矛盾，所以没有对任何分类器评分。它的光学数值覆盖计数已发布。' },
    card: { en: 'Its numeric task codes have no verified lookup to hands or movements, and its event durations disagree between the events table, the optical files and the cited paper. Its optical coverage counts are published.',
            zh: '它的数字任务编码没有经过核实的、与左右手或动作对应的对照表，事件时长在事件表、光学数据文件与所引论文之间也互相矛盾。它的光学数值覆盖计数已发布。' },
    href: '/topics/beyond-scalp-eeg/#ds007420',
  },
  {
    id: 'dreem-amplitude-sensitive-models',
    item: { en: 'Dreem sleep cohorts · neural-network and foundation models', zh: 'Dreem 睡眠队列 · 神经网络与基础模型' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-10-03', closed: null,
    outcome: { en: 'The stored signal metadata says millivolts; the publisher’s own converter treats the same arrays as microvolts. Models that need absolute amplitude are not run on a guessed unit, so no such score exists. The published baselines do not depend on the unit.',
               zh: '存储的信号元数据写的是毫伏，发布者自己的转换程序却把同样的数组当作微伏。需要绝对幅值的模型不在猜测的单位上运行，所以没有这类分数。已发布的基线不依赖这个单位。' },
    card: { en: 'The stored signal metadata says millivolts; the publisher’s own converter treats the same arrays as microvolts. Models that need absolute amplitude are not run; the published baselines do not depend on the unit.',
            zh: '存储的信号元数据写的是毫伏，发布者自己的转换程序却把同样的数组当作微伏。需要绝对幅值的模型没有运行；已发布的基线不依赖这个单位。' },
    href: '/topics/sleep-staging/#held',
  },
  {
    id: 'ysu-async-ssvep-consent',
    item: { en: 'YSU asynchronous SSVEP · consent statement', zh: 'YSU 异步 SSVEP · 同意书声明' },
    state: { en: 'Released', zh: '已发布' },
    opened: '2026-09-27', closed: '2026-09-27',
    outcome: { en: 'Scored and audited, then held until the data paper’s consent and ethics statement was read; released the same day.',
               zh: '已评分并通过审计，暂缓到读到数据论文中的同意书与伦理声明为止；当天发布。' },
    href: '/topics/when-not-to-act/#non-control',
  },
  {
    id: 'stieger-longitudinal',
    item: { en: 'Stieger longitudinal BCI · one-person pilot', zh: 'Stieger 纵向 BCI · 单人试点' },
    state: { en: 'Status only', zh: '只发状态' },
    opened: '2026-09-27', closed: null,
    outcome: { en: 'The pipeline works on one person’s eleven sessions. With one person every score is that person’s, so none is published.',
               zh: '流程在一名被试的 11 次会话上跑通了。只有一个人时，任何分数都是这个人的分数，所以不发布。' },
    href: '/topics/model-adaptation/#cross-session',
  },
  {
    id: 'ds004902',
    item: { en: 'OpenNeuro ds004902 · paired sleep comparison', zh: 'OpenNeuro ds004902 · 配对睡眠比较' },
    state: { en: 'No score', zh: '没有分数' },
    opened: '2026-09-23', closed: null,
    outcome: { en: 'Five source payloads are shorter than their own headers declare. No score of any kind.',
               zh: '5 个源文件比自己的文件头声明的还短。没有任何分数。' },
    card: { en: 'Five source payloads are shorter than their own headers declare.',
            zh: '5 个源文件比自己的文件头声明的还短。' },
  },
  {
    id: 'clinical-foundation-models',
    item: { en: 'Foundation models on the clinical set', zh: '临床数据上的基础模型' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-09-23', closed: null,
    outcome: { en: 'The source states no physical amplitude unit. Not run on an assumed one.',
               zh: '数据源没有说明物理幅值单位。不按假设的单位去跑。' },
    card: { en: 'Not run: the source states no physical amplitude unit.',
            zh: '未运行：数据源没有说明物理幅值单位。' },
    href: '/topics/clinical-groups/',
  },
  {
    id: 'lfame',
    item: { en: 'L-FAME', zh: 'L-FAME' },
    state: { en: 'Described, not scored', zh: '只有描述，没有评分' },
    opened: '2026-09-22', closed: null,
    outcome: { en: 'Not included on 22 September (intake only). Since 23 September: described, not scored; its per-condition numbers withheld.',
               zh: '9 月 22 日未纳入（只完成了数据接收）。9 月 23 日起：只有描述、没有评分，按条件汇总的数值不发布。' },
    card: { en: 'Its per-condition numbers are withheld.',
            zh: '按条件汇总的数值不发布。' },
  },
  {
    id: 'alphawaves-consent',
    item: { en: 'Alpha Waves · primary consent source', zh: 'Alpha Waves · 一手同意书来源' },
    state: { en: 'Released', zh: '已发布' },
    opened: '2026-09-22', closed: '2026-09-22',
    outcome: { en: 'Released the same day, after the primary report’s consent statement was read.',
               zh: '当天读到原始报告中的同意书声明后发布。' },
    href: '/topics/fewer-electrodes/#posterior-subset',
  },
  {
    id: 'bnci2015-001-crossday',
    item: { en: 'BNCI2015-001 · next-day adaptation', zh: 'BNCI2015-001 · 次日适配' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-09-20', closed: null,
    outcome: { en: 'Run and independently replayed on 22 September. The catalogue licence is CC BY-NC-ND and the description names no ethics approval, so no figure is published until that review is done.',
               zh: '9 月 22 日已运行并通过独立复核。目录标注的许可是 CC BY-NC-ND，数据说明也没有写伦理批准，所以审查完成之前不发布任何数字。' },
    card: { en: 'Run and independently replayed. The catalogue licence is CC BY-NC-ND and the description names no ethics approval, so no figure is published until that review is done.',
            zh: '已运行并通过独立复核。目录标注的许可是 CC BY-NC-ND，数据说明也没有写伦理批准，所以审查完成之前不发布任何数字。' },
    href: '/topics/model-adaptation/#next-day',
  },
];
if (new Set(holds.map(h => h.id)).size !== holds.length) throw new Error('releases.ts: two holds share an id');

export interface Correction {
  date: string;
  /** The served files whose text the correction amends. Their bytes are not rewritten. */
  files: string[];
  what: Text;
  href?: string;
}

/**
 * Corrections to wording in files already released. A release is a record of
 * fixed bytes (their hashes are on the releases page and in the Hugging Face
 * mirror), so a wrong sentence in one is corrected here and on the page that
 * shows it, not by editing the file.
 */
export const corrections: Correction[] = [
  {
    date: '2026-10-01', files: ['deployment-topics.json'],
    what: { en: 'The ensemble-TRCA rows call the original method a three-filter-bank experiment. The original paper and the reference code’s tutorials use five sub-bands; three is only the default of the code’s functions. Our runs used one fixed band either way, and no score changes.',
            zh: '集成 TRCA 各行把原方法称为「三子带滤波器组实验」。原论文与参考代码的教程用的是 5 个子带，3 只是代码函数的默认值。我们的运行无论如何都只用一个固定频带，没有任何分数变化。' },
    href: '/topics/calibration-budget/#methods-and-limits',
  },
  {
    date: '2026-10-01', files: ['experiments.json', 'mi-rest-results.csv', 'mi-rest-protocol.json', 'deployment-topics.json'],
    what: { en: 'The ds003810 credit links only the 2022 Data in Brief description. The OpenNeuro record asks users to cite Peterson, Galván, Hernández and Spies, Heliyon 6(3):e03425 (2020); the dataset page now gives both.',
            zh: 'ds003810 的署名只链接了 2022 年的 Data in Brief 数据描述。OpenNeuro 记录要求引用 Peterson、Galván、Hernández 与 Spies 发表于 Heliyon 6(3):e03425（2020）的论文；数据集页面现在两者都给出。' },
    href: '/datasets/ds003810/#methods-and-limits',
  },
];

/** Citations a source asks for that a released file does not carry; shown on its dataset page. */
export const requestedCitations: Record<string, { text: string; url: string; basis: string }> = {
  ds003810: {
    text: 'Peterson V, Galván C, Hernández H, Spies R. A feasibility study of a complete low-cost consumer-grade brain-computer interface system. Heliyon 6(3):e03425 (2020).',
    url: 'https://doi.org/10.1016/j.heliyon.2020.e03425',
    basis: 'https://openneuro.org/datasets/ds003810',
  },
};
