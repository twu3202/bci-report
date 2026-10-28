// The open register's site rows at the freeze (package B8b of the 20261020 release; package R5 of the 20261028 round): one
// row for each dataset source this site lists, and one for each model or method it names, built from what the site itself
// serves (entities.ts, read through Vite as the build reads it) and from the step-evidence census, re-read against the
// live files. The census is the 20261020 A5 census and the 20261028 A3 census that extends it (the four dataset checks
// this round promotes from MOABB catalog rows: Kim beta-range, MIND, Damm finger imagery and NeBULA).
//
//   node scripts/export-site-register-rows.mjs            write research/publication_review_20261028/register/
//                                                          site-register-rows-20261028.json
//   node scripts/export-site-register-rows.mjs --check    build the rows and compare with that file and with the site
//                                                          rows of the served register; write nothing (exit 1 on drift)
//
// pipeline/publication/export_open_register.py --freeze runs this script, reads its file and merges the site rows with
// the external rows (B8a): it assigns nothing here but opaque ids, aliases from merged rows and public source labels.
//
// What "re-read at the freeze" means here:
//  1. every input the census hashed is hashed again, and a file that changed is listed (drift is reported, not fatal:
//     served files change between packages);
//  2. every census evidence item that carries a value is resolved again in the live file (JSON selectors: dotted
//     keys, [key=value] filters, [n] indices; Markdown and TypeScript sources by their quoted text; entities.ts and
//     releases.ts sources through the modules themselves), and a value that no longer matches stops the build;
//  3. the items the page and hold packages of this release change before the freeze (census `at_freeze`) are read from
//     the live site: Shin2022's page, IESSEEG's section, the eldBETA and ZuCo 2.0 holds; the gaps that result must be
//     the census's expected gaps;
//  4. a row's level is the furthest step whose anchor item is on file (plan section 2.6, as the dataset register states
//     it), with every earlier missing item a gap; it must equal the census's level, and its gaps the census's gaps;
//  5. every model and method fact (terms by part, records, checkpoints) is read from the file and field this script
//     names for it, and stops the build if that field no longer says what the row says;
//  6. the holds opened on this site's rows are findings (code `hold` with a reason code), sourced to the hold in releases.ts
//     and in the payload that opens it (eldBETA and ZuCo 2.0: data-quality-update.json; Kim beta-range, Damm and NeBULA:
//     dataset-checks-update.json); the exporter serves each once the page words its code.
//
// Nothing here is free text from a source: rows carry names, licence identifiers, tokens, paths with selectors and
// counts that the served files already print. Paths in the output are repo-relative; the exporter turns research paths
// into labels and record hashes before anything is served.
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PROJECT = resolve(SITE, '..');
const D = '20261028';
const FREEZE_DAY = `${D.slice(0, 4)}-${D.slice(4, 6)}-${D.slice(6)}`;
const REVIEW = `research/publication_review_${D}`;
const OUT = `${REVIEW}/register/site-register-rows-${D}.json`;
// The 20261020 census (A5) and the consent record it read; the 20261028 census (A3) extends it, with its own consent record.
const PREV = '20261020';
const A5_PATH = `research/publication_review_${PREV}/notes/site-step-evidence.json`;
const A3_PATH = `research/publication_review_${PREV}/evidence/consent-statements.json`;
const SUPP_PATH = `${REVIEW}/register/site-step-evidence-${D}.json`;
const A3_NOW_PATH = `${REVIEW}/evidence/consent-statements.json`;
const DQ = 'site/src/data/data-quality-update.json', DC = 'site/src/data/dataset-checks-update.json';
const SCHEMA = 'bci-report-site-register-rows-v1';

const fail = msg => { throw new Error(`export-site-register-rows: ${msg}`); };
const need = (ok, msg) => { if (!ok) fail(msg); };
const abs = p => join(PROJECT, p);
const sha = buf => createHash('sha256').update(buf).digest('hex');
const readJson = p => JSON.parse(readFileSync(abs(p), 'utf8'));
const canon = v => JSON.stringify(v, (k, x) => (x && typeof x === 'object' && !Array.isArray(x)
  ? Object.fromEntries(Object.keys(x).sort().map(key => [key, x[key]])) : x));

/* --- The site's own modules, as the build reads them ------------------------------------------------------------ */

async function siteModules() {
  const { createServer } = await import(join(SITE, 'node_modules/vite/dist/node/index.js'));
  const server = await createServer({
    root: SITE, configFile: false, logLevel: 'error', appType: 'custom',
    server: { middlewareMode: true, hmr: false, watch: null }, optimizeDeps: { noDiscovery: true, include: [] },
  });
  try {
    const entities = await server.ssrLoadModule('/src/data/entities.ts');
    const i18n = await server.ssrLoadModule('/src/data/i18n.ts');
    const releases = await server.ssrLoadModule('/src/data/releases.ts');
    return { entities, i18n, releases };
  } finally { await server.close(); }
}

/* --- Selectors (the census's grammar) --------------------------------------------------------------------------- */

/** Resolve "a.b[k=v].c[0]" in a JSON value; undefined where any step is missing. */
function select(root, selector) {
  let cur = root;
  for (const m of selector.matchAll(/([^.[\]]+)|\[([^\]]+)\]/g)) {
    if (cur === undefined || cur === null) return undefined;
    if (m[1] !== undefined) { cur = cur[m[1]]; continue; }
    const inner = m[2];
    if (/^\d+$/.test(inner)) { cur = Array.isArray(cur) ? cur[Number(inner)] : undefined; continue; }
    const eq = inner.indexOf('=');
    if (eq < 0) return undefined;
    const k = inner.slice(0, eq), v = inner.slice(eq + 1);
    cur = Array.isArray(cur) ? cur.find(x => x && String(x[k]) === v) : undefined;
  }
  return cur;
}

/* --- Re-reading the census at the freeze ------------------------------------------------------------------------ */

function rereadCensus(a5, mods) {
  const drift = [];
  for (const inp of a5.inputs) {
    const p = abs(inp.file);
    if (!existsSync(p)) { drift.push({ file: inp.file, state: 'missing' }); continue; }
    const now = sha(readFileSync(p));
    if (now !== inp.sha256) drift.push({ file: inp.file, state: 'changed', census_sha256: inp.sha256, freeze_sha256: now });
  }
  const jsonCache = new Map();
  const json = f => { if (!jsonCache.has(f)) jsonCache.set(f, JSON.parse(readFileSync(abs(f), 'utf8'))); return jsonCache.get(f); };
  const textCache = new Map();
  const text = f => { if (!textCache.has(f)) textCache.set(f, readFileSync(abs(f), 'utf8')); return textCache.get(f); };
  const slugs = new Set(mods.entities.datasets.map(d => d.slug));
  const holdIds = new Set(mods.releases.holds.map(h => h.id));
  let checked = 0, fieldsChecked = 0;
  const mismatches = [], unresolved = [];
  const visit = (src, where) => {
    const f = src.file, field = src.field;
    if (!existsSync(abs(f))) { mismatches.push({ where, file: f, field, problem: 'file missing' }); return; }
    if (f.endsWith('.json')) {
      const live = select(json(f), field);
      if (!('value' in src)) {
        // No value recorded: the field must still be there (a selector ending in .text or a free key is checked as present).
        fieldsChecked++;
        if (live === undefined) mismatches.push({ where, file: f, field, problem: 'field no longer present' });
        return;
      }
      checked++;
      if (canon(live) !== canon(src.value)) mismatches.push({ where, file: f, field, census: src.value, live });
    } else if (/^text: /.test(field)) {
      checked++;
      if (!text(f).includes(field.slice(6))) mismatches.push({ where, file: f, field, problem: 'quoted text not found' });
    } else if (f === 'site/src/data/entities.ts') {
      const m = field.match(/slug '([^']+)'/);
      if (!m) { unresolved.push({ where, file: f, field }); return; }
      checked++;
      if (!slugs.has(m[1])) mismatches.push({ where, file: f, field, problem: 'no dataset entity with this slug' });
    } else if (f === 'site/src/data/releases.ts' && /^holds\[id=/.test(field)) {
      checked++;
      if (!holdIds.has(field.match(/^holds\[id=([^\]]+)\]/)[1])) mismatches.push({ where, file: f, field, problem: 'no such hold' });
    } else unresolved.push({ where, file: f, field });
  };
  for (const s of a5.sources) {
    for (const [step, items] of Object.entries(s.steps)) for (const it of items) for (const src of it.sources ?? []) visit(src, `${s.id}/${step}/${it.item}`);
    for (const fnd of s.findings ?? []) for (const fact of fnd.facts ?? []) for (const src of fact.sources ?? []) visit(src, `${s.id}/finding/${fnd.code}`);
    if (s.identity?.aliases_source) visit(s.identity.aliases_source, `${s.id}/aliases`);
  }
  // The consent record the census read (A5: Shin2022, eldBETA, IESSEEG and BI2013a; A3 of 20261028: the four dataset
  // checks), as it stands at the freeze.
  const rec = a5.summary.consent_record_from_A3 ?? a5.consent_record;
  const a3Now = sha(readFileSync(abs(rec.file)));
  return { inputs_hashed: a5.inputs.length, drift, values_checked: checked, fields_present: fieldsChecked, mismatches, unresolved,
           a3: { file: rec.file, census_sha256: rec.sha256, freeze_sha256: a3Now, unchanged: a3Now === rec.sha256 } };
}

/** The two censuses re-read as one: their counts added, each consent record kept (the 20261020 one under `a3`). */
function rereadBoth(a5, supp, mods) {
  const a = rereadCensus(a5, mods), b = rereadCensus(supp, mods);
  return { inputs_hashed: a.inputs_hashed + b.inputs_hashed, drift: [...a.drift, ...b.drift], values_checked: a.values_checked + b.values_checked,
           fields_present: a.fields_present + b.fields_present, mismatches: [...a.mismatches, ...b.mismatches],
           unresolved: [...a.unresolved, ...b.unresolved], a3: a.a3, a3_20261028: b.a3 };
}

/* --- Dataset rows ----------------------------------------------------------------------------------------------- */

const ANCHOR = { 1: 'host_record', 2: 'files_opened', 3: 'original_terms', 4: 'fixed_protocol_baseline', 5: 'comparable_on_protocol_page' };
const STATUS = { published: 'published', 'score held': 'score_held', 'status only': 'status_only', listed: 'listed', planned: 'planned' };
/** The census id's slug: its dataset page, else its id without the census prefixes and a version suffix (B8a's rule). */
const siteSlug = src => {
  const page = src.site?.page ?? src.site?.page_at_freeze;
  if (page && page.startsWith('/datasets/')) return page.split('/')[2];
  return src.id.replace(/^site-/, '').replace(/^register-/, '').replace(/-\d+\.\d+\.\d+$/, '');
};

/** The census's evidence items, one per source (B8a's shape): {item, state, source: "file#field" | null}. */
function evidenceItems(steps) {
  const out = {};
  for (const step of ['1', '2', '3', '4', '5']) {
    const items = [];
    for (const it of steps[step] ?? []) {
      const srcs = it.sources?.length ? it.sources : [null];
      for (const s of srcs) {
        const item = { item: it.item, state: it.state, source: s ? `${s.file}#${s.field}` : null };
        if (!items.some(x => canon(x) === canon(item))) items.push(item);
      }
    }
    const states = new Set(items.map(i => i.state));
    const st = items.length && [...states].every(x => x === 'pass' || x === 'not-applicable') ? 'pass' : (states.size === 1 && states.has('gap') ? 'gap' : 'partial');
    out[step] = { state: st, items };
  }
  return out;
}

/**
 * The plan rule, as the dataset register states it: the furthest step whose anchor item is on file, an earlier item
 * that is missing listed as a gap. The contiguous step (every anchor up to it on file) is kept beside it for the record;
 * where the two differ (a source traced from its host record whose files were never opened), the row shows the
 * furthest step with "files opened" as a gap at step 2.
 */
function levelOf(steps) {
  const anchorPass = k => (steps[String(k)] ?? []).some(it => it.item === ANCHOR[k] && it.state === 'pass');
  let plan = 0, contiguous = 0;
  for (const k of [1, 2, 3, 4, 5]) if (anchorPass(k)) plan = k;
  for (const k of [1, 2, 3, 4, 5]) { if (anchorPass(k)) contiguous = k; else break; }
  return { plan, contiguous, level: plan };
}

function gapsOf(steps, level, defs) {
  const gaps = [], next = [];
  for (const step of ['1', '2', '3', '4', '5']) for (const it of steps[step] ?? []) {
    if (it.state !== 'gap') continue;
    const g = { step: Number(step), item: it.item, label_en: defs[it.item].label_en, label_zh: defs[it.item].label_zh };
    if (g.step <= level && !gaps.some(x => x.item === g.item)) gaps.push(g);
    if (g.step === level + 1 && !next.some(x => x.item === g.item)) next.push(g);
  }
  return { gaps, next };
}

/**
 * The holds open on the site's rows, one per row: the hold's id (releases.ts, and the payload that opens it) and its
 * reason code (register_findings.py SITE_HOLD_REASONS, which takes the same row-by-row hold ids and which the exporter
 * checks this table against). The served file carries the finding once the page has words for the code
 * (open-register.ts holdReason). Kim beta-range's replaces the catalog's onset-timing hold on its MOABB row.
 */
const SITE_HOLD = {
  eldbeta: { id: 'eldbeta-one-participant-score', reason_code: 'one_person_score', file: DQ },
  zuco2: { id: 'zuco2-converted-run-timing', reason_code: 'converted_run_timing', file: DQ },
  'kim2025-beta-range': { id: 'kim-amplitude-dependent-models', reason_code: 'amplitude_units_unresolved', file: DC },
  'damm-finger-imagery': { id: 'damm-one-participant-score', reason_code: 'one_person_score', file: DC },
  nebula: { id: 'nebula-one-participant-scores', reason_code: 'one_person_score', file: DC },
};

/**
 * A licence as a name, from a census value: a string, a deposit record's {name}, or a list of licences this site's
 * rights record states side by side (MIND's two).
 */
const licenceName = v => (typeof v === 'string' ? v : Array.isArray(v) && v.length && v.every(x => typeof x === 'string') ? v.join(', ')
  : v && typeof v === 'object' && typeof v.name === 'string' ? v.name : null);

function datasetRows(a5, supp, mods, notes) {
  const E = mods.entities;
  const profiles = readJson('site/src/data/entity-profiles.json').datasets;
  const dq = readJson(DQ), dc = readJson(DC);
  const payloadHolds = { [DQ]: dq.holds, [DC]: dc.holds };
  const ies = readJson('site/src/data/clinical-iesseeg-update.json');
  const shortlist = readJson('research/moabb_expansion_20261019/evidence/moabb-shortlist-verified.json');
  const holdsById = new Map(mods.releases.holds.map(h => [h.id, h]));
  const defs = a5.item_definitions;
  const rows = [];
  // Where a status-only source's own section is (the census's hold or status record, read from the live site).
  const STATUS_SECTION = {
    'site-falcon-h2': `${E.BEYOND_PATH}#${E.BEYOND_ANCHOR.falcon}`,
    'site-rabut-fus': `${E.BEYOND_PATH}#${E.BEYOND_ANCHOR.fus}`,
    'site-meditation-rest': `${E.PILOT_PATH}#${E.PILOT_ANCHOR.statusOnly}`,
  };
  // The data-quality page's three cases (data-quality-update.json `cases`).
  const dqCases = new Map(dq.cases.map(c => [c.id ?? c.case ?? c, c]));
  for (const src of [...a5.sources, ...supp.sources]) {
    if (src.census_group === 'adjacent_moabb') continue;
    const slug = siteSlug(src);
    // A dataset page that waits on the register version carrying its row (entities.ts pendingDatasets: Kim beta-range
    // until releases.ts names this register) is read from the same record, so the row is the same either side.
    const entity = E.datasetBySlug[slug] ?? (E.pendingDatasets ?? []).find(d => d.slug === slug);
    const steps = JSON.parse(JSON.stringify(src.steps));
    const where = src.id;

    // 3. The items this release's page and hold packages change, read from the live site.
    const setItem = (step, item, sources) => {
      const it = steps[step].find(x => x.item === item);
      need(it, `${where}: no ${item} item at step ${step}`);
      it.state = 'pass';
      it.sources = sources.map(([file, field]) => ({ file, field }));
    };
    if (src.at_freeze) {
      if (slug === 'shin2022') {
        need(entity, 'Shin2022 has no dataset page at the freeze');
        setItem('4', 'result_or_hold_on_page', [['site/src/data/entities.ts', "datasets: entry with slug 'shin2022' (a /datasets/shin2022/ page)"],
                                                ['site/src/data/data-quality-update.json', 'shin2022.arms']]);
        need(dq.shin2022?.arms?.length === 3, 'Shin2022: the data-quality file has no arms');
      } else if (slug === 'iesseeg') {
        need(ies.placement?.section === 'iesseeg' && existsSync(join(SITE, 'public/data/clinical-iesseeg-update.json')), 'IESSEEG: no served section');
        setItem('4', 'result_or_hold_on_page', [['site/src/data/clinical-iesseeg-update.json', 'placement.section']]);
      } else if (SITE_HOLD[slug]) {
        const { id, file } = SITE_HOLD[slug];
        need(payloadHolds[file].some(h => h.id === id) && holdsById.get(id) && !holdsById.get(id).closed, `${slug}: the hold ${id} is not open on the site`);
        setItem('4', 'result_or_hold_on_page', [[file, `holds[id=${id}]`],
                                                ['site/src/data/releases.ts', `holds[id=${id}]`]]);
      } else fail(`${where}: an at_freeze item this script does not know`);
    }

    // 4. Level and gaps from the evidence, against the census.
    const lv = levelOf(steps);
    const census = src.at_freeze?.level ?? src.level;
    need(lv.level === census && lv.contiguous === (src.at_freeze?.level_contiguous ?? src.level_contiguous),
      `${where}: level ${lv.level} (contiguous ${lv.contiguous}) from the evidence, ${census} in the census`);
    if (lv.level !== (src.level_recommended ?? src.level))
      notes.push(`${where}: at step ${lv.level} by the plan rule, with files opened as a gap at step 2; the census recommended its contiguous step ${src.level_recommended}`);
    const { gaps, next } = gapsOf(steps, lv.level, defs);
    const censusGaps = src.at_freeze?.gaps ?? src.gaps;
    need(canon(gaps.map(g => g.item).sort()) === canon(censusGaps.map(g => g.item).sort()),
      `${where}: gaps ${gaps.map(g => g.item)} from the evidence, ${censusGaps.map(g => g.item)} in the census`);

    // Terms as stated: the dataset page's own record where the site has a page, else the census's licence item.
    const licItem = (src.steps['1'] ?? []).find(it => it.item === 'licence_as_stated');
    const licSrc = (licItem?.sources ?? []).find(s => licenceName(s.value));
    let terms;
    if (entity) terms = { value: entity.license, by: 'site_release' };
    else if (licSrc) terms = { value: licenceName(licSrc.value), by: /\.json$/.test(licSrc.file) && /license_record|deposit_license/.test(licSrc.field) ? 'deposit_record' : 'site_release' };
    else terms = { value: null, by: 'none' };
    if (entity && licSrc && typeof licSrc.value === 'string' && licSrc.value !== entity.license)
      notes.push(`${where}: the census's licence "${licSrc.value}" and the page's "${entity.license}" differ; the page's is used`);

    // Names: the dataset page's, else the census's; aliases from the live entity profile, the census identity.
    const name = entity ? entity.name : src.name;
    const aliases = [];
    const addAlias = (value, kind) => { if (value && value !== name && !aliases.some(a => a.value.toLowerCase() === value.toLowerCase())) aliases.push({ value, kind }); };
    const prof = profiles[slug];
    if (src.identity.aliases_source) {
      need(prof, `${where}: the census names entity-profiles.json aliases for ${slug}, and there are none`);
      for (const a of prof.aliases) addAlias(a, 'name');
    }
    if (src.identity.alias) addAlias(src.identity.alias, 'name');
    if (src.identity.moabb_loader) addAlias(src.identity.moabb_loader, 'moabb_loader');
    if (src.identity.hf_repo) addAlias(src.identity.hf_repo, 'hf_repo');

    const rec = Array.isArray(src.identity.record) ? src.identity.record[0] : src.identity.record;
    const page = entity ? `/datasets/${slug}/` : null;
    const section = slug === 'iesseeg' ? `/topics/clinical-groups/#${ies.placement.section}` : null;
    const status = STATUS[src.site.register_status];
    need(status, `${where}: an unknown status ${src.site.register_status}`);

    // Findings: codes and parameters; each carries the census's sources where the census gives them.
    const findings = [];
    for (const f of src.findings ?? []) {
      const sources = (f.facts ?? []).flatMap(x => (x.sources ?? []).map(s => `${s.file}#${s.field}`));
      if (f.code === 'version_clarification') {
        const p = f.params;
        findings.push({ code: f.code, params: { current: p.current, earlier: p.earlier, recordings_source: p.recordings_source,
                                                recordings_evaluated: p.recordings_evaluated }, sources: [...new Set(sources)] });
      } else if (f.code === 'policy_note') findings.push({ code: f.code, params: { source: f.params.source }, sources: [...new Set(sources)] });
      else fail(`${where}: a census finding ${f.code} this script does not know`);
    }
    for (const cm of src.corpus_mentions ?? []) {
      if (/held-out evaluation/i.test(cm.text)) continue;
      const models = [...new Set(cm.models.map(x => x.replace(/\s*\(.*\)$/, '')))].sort();
      findings.push({ code: 'named_in_corpus', params: { models, release_resolved: /release resolved|resolved by name/.test(cm.text) },
                      sources: [`${cm.source.file}#${cm.source.field}`] });
    }
    if (src.hold) need(SITE_HOLD[slug]?.id === src.hold.id && SITE_HOLD[slug].reason_code === src.hold.reason_code,
      `${where}: the census's hold ${src.hold.id} (${src.hold.reason_code}) is not this script's`);
    if (SITE_HOLD[slug]) {
      // The hold open on the row (releases.ts and the payload that opens it), as a finding with its reason code.
      const { id, reason_code, file } = SITE_HOLD[slug];
      need(holdsById.get(id) && !holdsById.get(id).closed && payloadHolds[file].some(h => h.id === id), `${slug}: the hold ${id} is not open on the site`);
      findings.push({ code: 'hold', params: { reason_code },
                      sources: [`site/src/data/releases.ts#holds[id=${id}]`, `${file}#holds[id=${id}]`] });
    }
    if (slug === 'shin2022') {
      // MOABB's catalog counts for Shin2022, which differ from what its files hold (plan section 2.3; the data-quality case).
      const e = shortlist.entries.find(x => x.adapter === 'Shin2022');
      need(e, 'Shin2022 is not in the MOABB shortlist');
      const trials = Number(e.catalog_metadata['#Trials']), runs = Number(e.catalog_metadata['#Runs']);
      need(Number.isInteger(trials) && Number.isInteger(runs), 'Shin2022: MOABB catalog counts are not integers');
      need(dqCases.has('shin2022') || dq.cases.includes?.('shin2022'), 'the data-quality page has no Shin2022 case');
      findings.push({ code: 'catalog_differs_from_files', params: { case: 'shin2022', catalog_trials: trials, catalog_runs: runs },
                      sources: ['research/moabb_expansion_20261019/evidence/moabb-shortlist-verified.json#entries[adapter=Shin2022].catalog_metadata.#Trials',
                                'research/moabb_expansion_20261019/evidence/moabb-shortlist-verified.json#entries[adapter=Shin2022].catalog_metadata.#Runs',
                                'site/src/data/data-quality-update.json#shin2022.catalog'] });
    }

    // Links: the page; a case or the section that states a hold or a status; the exposure block for core rows.
    const links = {};
    if (page) links.page = page;
    else if (section) links.page = section;
    if (['shin2022', 'eldbeta', 'zuco2'].includes(slug)) links.case = `${E.DATA_QUALITY_PATH}#${slug}`;
    else if (src.census_group === 'dataset_checks') {
      // The four dataset checks: each row's case is its section on the data-quality page (entities.ts DATA_QUALITY_ANCHOR).
      const anchor = E.DATA_QUALITY_ANCHOR?.[slug];
      need(anchor && dc.placement.sections.includes(anchor) && src.site.case === `${E.DATA_QUALITY_PATH}#${anchor}`,
        `${where}: its case ${src.site.case} is not its section on the data-quality page`);
      links.case = src.site.case;
    } else if (src.site.hold && holdsById.get(src.site.hold)?.href) links.case = holdsById.get(src.site.hold).href;
    else if (STATUS_SECTION[src.id]) links.case = STATUS_SECTION[src.id];
    // The pretraining-exposure block sits on each core protocol page.
    const CORE_TRACK = { beta: 'beta-8ch', ds003810: 'mi-rest', ds005342: 'idle', ds006593: 'p300-target', eegmat: 'arithmetic-rest', tmnred: 'semantic-target', eesm19: 'sleep-scalp' };
    if (src.census_group === 'core') { need(CORE_TRACK[slug], `${slug}: no core protocol for its exposure link`); links.exposure = `/protocols/${CORE_TRACK[slug]}/#pretraining-exposure`; }

    rows.push({
      census_id: src.id, slug, name, aliases, urls: rec ? { record: rec } : {},
      site: { page: page ?? section, status, census_id: src.id },
      terms_as_stated: terms, access: 'open', level: lv.level, level_contiguous: lv.contiguous,
      step_evidence: evidenceItems(steps), gaps, next_step_gaps: next, status, findings, links, checked: FREEZE_DAY,
    });
  }
  return rows;
}

/* --- Model rows ------------------------------------------------------------------------------------------------- */

const MVP = 'site/src/data/mvp.json', FMU = 'site/src/data/foundation-models-update.json', EGP = 'site/src/data/eegpt-core-update.json';
const PROF = 'site/src/data/entity-profiles.json', V8 = 'research/expansion_v8_20261001/models';
const FM_SEL = id => `results.foundation-models-v9.models[id=${id}]`;
/**
 * Each part's terms, with the file and field that state them and the words that field must still hold at the freeze.
 * `state` is the register's terms state; `by` who states the terms (vocab.by). A part with no record says not_found.
 */
const part = (state, value, by, file, field, holds) => ({ state, value, by, at: file ? { file, field, holds } : null });
const SCRATCH = 'Trained from scratch / deterministic reference; no third-party pretrained weights. Braindecode BSD-3-Clause; MNE/scikit-learn BSD where used.';
const scratchTerms = name => ({
  code: part('stated', 'BSD-3-Clause', 'site_release', MVP, `models[name=${name}].license`, 'Braindecode BSD-3-Clause'),
  weights: part('not_applicable', null, 'site_release', MVP, `models[name=${name}].license`, 'no third-party pretrained weights'),
  // Trained on each dataset it is scored on: the data terms are each dataset's own, recorded on its row.
  data: part('per_source', null, 'none', MVP, 'datasets', null),
});
const deploymentTerms = () => ({
  code: part('not_found', null, 'none', null),
  weights: part('not_applicable', null, 'none', null),
  data: part('per_source', null, 'none', 'site/src/data/deployment-topics.json', 'dataset_citations', null),
});
/** Pretraining data: the sources each model's paper lists, as the site's pretraining-exposure record reads them. */
const corpus = key => part('per_source', null, 'paper', FMU, `results.foundation-models-v9.pretraining_exposure.models[key=${key}].corpus_summary`, null);
const fmTerms = (id, key, code, codeField, codeHolds, weights, weightsHolds) => ({
  code: code ? part('stated', code, 'repository_licence_file', codeField[0], codeField[1], codeHolds) : part('not_found', null, 'none', null),
  weights: part('stated', weights, 'site_release', FMU, `${FM_SEL(id)}.weights_licence`, weightsHolds),
  data: corpus(key),
});
const SITE_TERMS = {
  eegnet: scratchTerms('EEGNet'), shallowfbcspnet: scratchTerms('ShallowFBCSPNet'), deep4net: scratchTerms('Deep4Net'),
  'csp-lda': scratchTerms('CSP+LDA'), cca: scratchTerms('Standard CCA'),
  // FBCCA and ensemble TRCA run in the deployment topics; the TRCA reference code is pinned there, its licence is not.
  fbcca: deploymentTerms(), etrca: deploymentTerms(),
  labram: { code: part('stated', 'MIT', 'site_release', MVP, 'models[name=LaBraM].license', 'Code/repository: MIT'),
            weights: part('stated', 'MIT', 'site_release', MVP, 'models[name=LaBraM].license', 'Checkpoint: committed in that repository'),
            data: corpus('labram') },
  cbramod: { code: part('stated', 'MIT', 'site_release', MVP, 'models[name=CBraMod].license', 'Code: MIT'),
             weights: part('stated', 'Apache-2.0', 'model_card_metadata', MVP, 'models[name=CBraMod].license', 'Weights: Apache-2.0 (official model card)'),
             data: corpus('cbramod') },
  eegpt: { code: part('stated', 'Apache-2.0', 'repository_licence_file', EGP, 'model.code_licence', 'Apache-2.0'),
           weights: part('not_found', null, 'none', EGP, 'model.weights_licence_status', 'unresolved'),
           data: part('per_source', null, 'paper', EGP, 'pretraining_exposure.model', null) },
  reve: fmTerms('reve-base', 'reve-base', 'MIT', [MVP, 'models[name=REVE Base].license'], 'MIT', 'REVE Responsible Use License v1.0', 'REVE Responsible Use License v1.0'),
  luna: fmTerms('luna-base', 'luna', 'Apache-2.0', [`${V8}/verify-luna.json`, 'code_licence'], 'Apache-2.0', 'CC BY-ND 4.0', 'CC BY-ND 4.0'),
  brainomni: fmTerms('brainomni-base', 'brainomni', 'MIT', [`${V8}/verify-brainomni.json`, 'code_licence'], 'MIT', 'MIT', 'MIT'),
  codebrain: fmTerms('codebrain', 'codebrain', 'Apache-2.0', [`${V8}/verify-codebrain.json`, 'code_licence'], 'Apache-2.0', 'Apache-2.0', 'Apache-2.0'),
  eegmamba: fmTerms('eegmamba', 'eegmamba', 'MIT', [`${V8}/verify-eegmamba.json`, 'code.licence'], 'MIT', 'MIT', 'MIT'),
  'st-eegformer': fmTerms('steegformer-base', 'st-eegformer', 'MIT', [`${V8}/verify-steegformer.json`, 'code_licence'], 'MIT (upstream)', 'MIT', 'MIT'),
  'eeg-fm-masking': fmTerms('eeg-fm-masking/mae-r9cm-L2', 'eeg-fm-masking', 'MIT', [`${V8}/verify-eeg-fm-masking.json`, 'code_licence'], 'MIT', 'CC-BY-4.0', 'CC-BY-4.0'),
  'erp-fm': fmTerms('erp-fm-base', 'erp-fm', 'CC BY-NC-SA 4.0', [`${V8}/verify-erp-fm.json`, 'code.licence'], 'CC BY-NC-SA 4.0', 'CC BY-NC-SA 4.0', 'CC BY-NC-SA 4.0'),
  singlem: fmTerms('singlem', 'singlem', 'MIT', [`${V8}/verify-singlem.json`, 'licence.code'], 'MIT', 'MIT', 'MIT'),
  zuna: fmTerms('zuna', 'zuna-1.1', 'Apache-2.0', [`${V8}/verify-zuna.json`, 'code_licence'], 'Apache-2.0', 'Apache-2.0', 'Apache-2.0'),
};
/**
 * The code a row's code licence is the licence of, where the method's profile links another address (a model page):
 * the repository the licence record names, re-read at the freeze. The profile's model page then links the weights.
 */
const CODE_URL = {
  reve: { url: 'https://github.com/elouayas/reve_eeg', file: MVP, field: 'models[name=REVE Base].url' },
  luna: { url: 'https://github.com/pulp-bio/BioFoundation', file: `${V8}/verify-luna.json`, field: 'code_licence' },
  brainomni: { url: 'https://github.com/OpenTSLab/BrainOmni', file: `${V8}/verify-brainomni.json`, field: 'repo' },
  codebrain: { url: 'https://github.com/jingyingma01/CodeBrain', file: `${V8}/verify-codebrain.json`, field: 'code_licence' },
  'eeg-fm-masking': { url: 'https://github.com/PierreGtch/eeg-fm-masking', file: `${V8}/verify-eeg-fm-masking.json`, field: 'repo' },
  zuna: { url: 'https://github.com/Zyphra/zuna', file: `${V8}/verify-zuna.json`, field: 'sources' },
};
/** The checkpoint each foundation-model family was scored with (its first matrix checkpoint), for file listing and hash. */
const FM_CHECKPOINT = { reve: 'reve-base', luna: 'luna-base', brainomni: 'brainomni-base', codebrain: 'codebrain', eegmamba: 'eegmamba',
                        'st-eegformer': 'steegformer-base', 'eeg-fm-masking': 'eeg-fm-masking/mae-r9cm-L2', 'erp-fm': 'erp-fm-base',
                        singlem: 'singlem', zuna: 'zuna' };
/** The model directory's cards with no result (entities.ts unmeasuredModels) and the other measured baselines. */
const DIRECTORY_TERMS = {
  BIOT: { code: part('stated', 'MIT', 'site_release', MVP, 'models[name=BIOT].license', 'MIT'), weights: part('not_found', null, 'none', null), data: part('not_found', null, 'none', null) },
  'Signal-JEPA': { code: part('not_found', null, 'none', null), weights: part('stated', 'MIT', 'model_card_metadata', MVP, 'models[name=Signal-JEPA].license', 'MIT, as stated on the model card'), data: part('not_found', null, 'none', null) },
  BENDR: { code: part('not_found', null, 'none', null), weights: part('stated', 'BSD-3-Clause', 'model_card_metadata', MVP, 'models[name=BENDR].license', 'BSD-3-Clause on the Braindecode model card'), data: part('not_found', null, 'none', null) },
  CSBrain: { code: part('not_found', null, 'none', MVP, 'models[name=CSBrain].license', 'no LICENSE file was found'), weights: part('not_found', null, 'none', MVP, 'models[name=CSBrain].license', 'no separate weight license was identified'), data: part('not_found', null, 'none', null) },
  'Neuro-GPT': { code: part('stated', 'GPL-3.0', 'repository_licence_file', MVP, 'models[name=Neuro-GPT].license', 'GPL-3.0 for the official repository'), weights: part('stated', 'GPL-3.0', 'model_card_metadata', MVP, 'models[name=Neuro-GPT].license', 'and model card'), data: part('not_found', null, 'none', null) },
  'EEG-Conformer': { code: part('stated', 'GPL-3.0', 'site_release', MVP, 'models[name=EEG-Conformer].license', 'GPL-3.0'), weights: part('not_found', null, 'none', MVP, 'models[name=EEG-Conformer].note', 'no official pretrained checkpoint was found'), data: part('not_found', null, 'none', null) },
  EEGSimpleConv: { code: part('stated', 'BSD-3-Clause', 'site_release', MVP, 'models[name=EEGSimpleConv].license', 'BSD-3-Clause for the Braindecode implementation'), weights: part('not_found', null, 'none', MVP, 'models[name=EEGSimpleConv].note', 'no pretrained weights'), data: part('not_found', null, 'none', null) },
  MIRepNet: { code: part('stated', 'MIT', 'repository_licence_file', `${V8}/verify-mirepnet.json`, 'code_licence', 'MIT'), weights: part('stated', 'MIT', 'model_card_metadata', `${V8}/verify-mirepnet.json`, 'weights_licence', 'MIT (HF model card'), data: part('not_found', null, 'none', null) },
  'EEG-DINO': { code: part('not_found', null, 'none', null), weights: part('not_found', null, 'none', `${V8}/verify-eeg-dino.json`, 'licence.upstream_weights', 'NONE'), data: part('not_found', null, 'none', null) },
  'Spectral ridge': scratchTerms('Spectral ridge'), 'Temporal ridge': scratchTerms('Temporal ridge'),
};
/** Official records of the two directory cards whose served entries carry no address (research verification records). */
const DIRECTORY_RECORD = {
  MIRepNet: { url: 'https://github.com/staraink/MIRepNet', at: { file: `${V8}/verify-mirepnet.json`, field: 'code_licence', holds: 'https://github.com/staraink/MIRepNet' } },
  'EEG-DINO': { url: 'https://papers.miccai.org/miccai-2025/0278-Paper3347.html', at: { file: `${V8}/verify-eeg-dino.json`, field: 'paper.url', holds: 'https://papers.miccai.org/miccai-2025/0278-Paper3347.html' } },
};
/** A weight file named by a record (file listing read), for directory cards. */
const DIRECTORY_FILES = {
  'Signal-JEPA': { file: MVP, field: 'models[name=Signal-JEPA].note', holds: 'safetensors checkpoint' },
  BENDR: { file: MVP, field: 'models[name=BENDR].note', holds: 'The Braindecode checkpoint is' },
  'Neuro-GPT': { file: MVP, field: 'models[name=Neuro-GPT].note', holds: 'checkpoint' },
  MIRepNet: { file: `${V8}/verify-mirepnet.json`, field: 'weights_evidence', holds: 'MIRepNet.pth' },
  'EEG-DINO': { file: `${V8}/verify-eeg-dino.json`, field: 'weights.files', holds: 'model_EEG_DINO_M.pt' },
};
const KIND = { foundation: 'foundation_model', small: 'trained_from_scratch', classical: 'classical_method' };

function modelRows(mods, notes) {
  const E = mods.entities;
  const mvp = readJson(MVP), prof = readJson(PROF).methods, fmu = readJson(FMU), egp = readJson(EGP);
  const holdsAt = (at, where) => {
    if (!at) return;
    const v = select(readJson(at.file), at.field);
    need(v !== undefined, `${where}: ${at.file}#${at.field} is missing`);
    if (at.holds !== null && at.holds !== undefined) need(JSON.stringify(v).includes(JSON.stringify(at.holds).slice(1, -1)),
      `${where}: ${at.file}#${at.field} no longer says “${at.holds}”`);
  };
  const termsOf = (t, where) => {
    const out = {}, items = {};
    for (const k of ['code', 'weights', 'data']) {
      const p = t[k];
      holdsAt(p.at, `${where} ${k}`);
      out[k] = { state: p.state, value: p.value, by: p.by };
      const src = p.at ? `${p.at.file}#${p.at.field}` : null;
      // The item: on file when the terms are stated or recorded per source; not applicable where the part does not
      // exist; a gap where no terms were found.
      items[`${k}_terms`] = p.state === 'not_applicable' ? ['not-applicable', src]
        : p.state === 'not_found' ? ['gap', src] : ['pass', src];
    }
    return { terms: out, items };
  };
  const rows = [];
  const onProtocols = m => m.groups.some(g => g.path?.startsWith('/protocols/') && g.rows.length);
  const firstResult = m => {
    const g = m.groups.find(x => x.rows.length);
    return g ? `site/public/data/${g.rows[0].value.src}` : null;
  };
  for (const m of E.methods) {
    const slug = m.slug, where = `method ${slug}`;
    const t = SITE_TERMS[slug];
    need(t, `${where}: no terms record (SITE_TERMS)`);
    const { terms, items } = termsOf(t, where);
    const p = prof[slug];
    need(p, `${where}: no entity profile`);
    const ck = FM_CHECKPOINT[slug];
    const fmModel = ck ? fmu.results['foundation-models-v9'].models.find(x => x.id === ck) : null;
    if (ck) need(fmModel?.checkpoint_sha256, `${where}: no checkpoint hash for ${ck}`);
    const scoredFile = firstResult(m);
    need(scoredFile && existsSync(abs(scoredFile)), `${where}: no served result file (${scoredFile})`);
    const mvpModel = mvp.models.find(x => x.name === m.name || (slug === 'cca' && x.name === 'Standard CCA'));
    const track = mvp.tracks.find(tr => tr.rows.some(r => (r.id ?? '') === slug || r.name === m.name || (slug === 'cca' && r.name === 'Standard CCA')));
    // Step 5 is the core matrix (mvp.json tracks); encoders shown beside it on the protocol pages stay at step 4.
    const inMatrix = !!track;
    // Step items, each with its source.
    const ev = {
      official_record: ['pass', `${PROF}#methods.${slug}.reference_url`],
      ...items,
      file_listing: ck ? ['pass', `${FMU}#${FM_SEL(ck)}.revision`] : slug === 'eegpt' ? ['pass', `${EGP}#model.checkpoint.file`]
        : slug === 'cbramod' || slug === 'labram' ? ['pass', `${MVP}#models[name=${m.name}].license`] : ['not-applicable', null],
      files_checked: ck ? ['pass', `${FMU}#${FM_SEL(ck)}.checkpoint_sha256`] : slug === 'eegpt' ? ['pass', `${EGP}#model.checkpoint.sha256`]
        : track ? ['pass', `${MVP}#tracks[id=${track.id}].auditSha`] : ['pass', 'site/src/data/deployment-topics.json#provenance.independent_auditor_sha256'],
      scored_here: ['pass', scoredFile],
      in_matrix: inMatrix ? ['pass', `${MVP}#tracks[id=${track.id}].rows`] : ['gap', null],
    };
    if (slug === 'eegpt') need(egp.model.weights_licence_status.startsWith('unresolved'), 'EEGPT: its weights licence is no longer unresolved');
    if (slug === 'fbcca' || slug === 'etrca') need(!mvpModel, `${where}: mvp.json now has a directory entry; record its terms`);
    // Name, aliases (the profile's names; repo ids that are the official weights' are typed as such).
    const aliases = [];
    const add = (value, kind) => { if (value && value !== m.name && !aliases.some(a => a.value.toLowerCase() === value.toLowerCase())) aliases.push({ value, kind }); };
    const official = new Set(fmu.results['foundation-models-v9'].models.filter(x => E.methodSlugOf?.(x.id) === slug)
      .map(x => (x.revision ?? '').match(/^([\w.-]+\/[\w.-]+) @/)?.[1]).filter(Boolean));
    for (const a of p.aliases) add(a, official.has(a) ? 'official_weights' : 'name');
    for (const o of official) add(o, 'official_weights');
    const paper = p.reference_url && !/openreview/i.test(p.reference_url) ? p.reference_url : null;
    let code = p.code_url && p.code_url !== paper ? p.code_url : null, weights = null;
    if (CODE_URL[slug]) {
      const c = CODE_URL[slug];
      holdsAt({ file: c.file, field: c.field, holds: c.url }, `${where} code address`);
      if (code && /huggingface\.co/.test(code)) weights = code;
      code = c.url;
    } else if (t.code.at?.file === MVP && /^models\[name=[^\]]+\]\.license$/.test(t.code.at.field)) {
      // The code licence is the directory's record of the implementation run here: link that implementation.
      const u = select(mvp, t.code.at.field.replace(/\.license$/, '.url'));
      if (typeof u === 'string' && /^https:\/\//.test(u)) code = u !== paper ? u : null;
    }
    rows.push(modelRow({ key: slug, kind: 'site_model', name: m.name, aliases, urls: { paper, code, weights },
      model_kind: KIND[m.family] ?? 'classical_method', terms, ev, page: `/methods/${slug}/`, status: 'published', where }));
  }
  // The other baselines measured in the core matrix (no page), and the directory's cards with no result.
  const paged = new Set(E.methods.map(x => x.name));
  const otherEvaluated = mvp.models.filter(x => x.status === 'Evaluated' && !E.methods.some(y => y.name === x.name || (y.slug === 'cca' && x.name === 'Standard CCA')));
  for (const x of otherEvaluated) {
    const where = `baseline ${x.name}`;
    const t = DIRECTORY_TERMS[x.name];
    need(t, `${where}: no terms record (DIRECTORY_TERMS)`);
    const { terms, items } = termsOf(t, where);
    const tracks = mvp.tracks.filter(tr => tr.rows.some(r => r.name === x.name));
    need(tracks.length, `${where}: in no core-matrix track`);
    const ev = {
      official_record: ['pass', `${MVP}#models[name=${x.name}].url`], ...items, file_listing: ['not-applicable', null],
      files_checked: ['pass', `${MVP}#tracks[id=${tracks[0].id}].auditSha`],
      scored_here: ['pass', `${MVP}#tracks[id=${tracks[0].id}].rows[name=${x.name}]`],
      in_matrix: ['pass', `${MVP}#tracks[id=${tracks[0].id}].rows[name=${x.name}]`],
    };
    rows.push(modelRow({ key: slugify(x.name), kind: 'model', name: x.name, aliases: [], urls: { code: x.url }, model_kind: KIND[x.family],
      terms, ev, page: '/methods/#other-evaluated', status: 'published', where }));
  }
  for (const x of E.unmeasuredModels.filter(u => !paged.has(u.name))) {
    const where = `directory ${x.name}`;
    const t = DIRECTORY_TERMS[x.name];
    need(t, `${where}: no terms record (DIRECTORY_TERMS)`);
    const { terms, items } = termsOf(t, where);
    const rec = x.url ?? DIRECTORY_RECORD[x.name]?.url;
    if (!x.url) holdsAt(DIRECTORY_RECORD[x.name]?.at, `${where} record`);
    const recSrc = x.url ? (mvp.models.some(y => y.name === x.name) ? `${MVP}#models[name=${x.name}].url` : null)
      : DIRECTORY_RECORD[x.name] ? `${DIRECTORY_RECORD[x.name].at.file}#${DIRECTORY_RECORD[x.name].at.field}` : null;
    const files = DIRECTORY_FILES[x.name];
    if (files) holdsAt(files, `${where} files`);
    const ev = {
      official_record: rec ? ['pass', recSrc] : ['gap', null], ...items,
      file_listing: files ? ['pass', `${files.file}#${files.field}`] : t.weights.state === 'not_found' && /no (?:official )?pretrained/.test(t.weights.at?.holds ?? '') ? ['not-applicable', null] : ['gap', null],
      files_checked: ['gap', null], scored_here: ['gap', null], in_matrix: ['gap', null],
    };
    const anchor = x.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const onHf = rec && /huggingface\.co/.test(rec);
    rows.push(modelRow({ key: slugify(x.name), kind: 'model', name: x.name, aliases: [],
      // The record by what it is: a model page (weights), a repository or an implementation's documentation (code), a paper.
      urls: rec ? (onHf ? { weights: rec } : /github\.com|braindecode\.org/.test(rec) ? { code: rec } : { paper: rec }) : {},
      model_kind: KIND[x.family], terms, ev, page: `/methods/#${anchor}`, status: 'listed', where }));
  }
  return rows;
}

const slugify = s => s.toLowerCase().replace(/\+/g, '-').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const MODEL_STEPS = { 1: ['official_record'], 2: ['code_terms', 'weights_terms', 'data_terms', 'file_listing'], 3: ['files_checked'], 4: ['scored_here'], 5: ['in_matrix'] };
const MODEL_ANCHOR = { 1: 'official_record', 2: 'weights_terms', 3: 'files_checked', 4: 'scored_here', 5: 'in_matrix' };
const MODEL_LABEL = {
  official_record: ['official record', '官方记录'], code_terms: ['code licence', '代码许可'], weights_terms: ['weights licence', '权重许可'],
  data_terms: ['data terms', '数据条款'], file_listing: ['file listing', '文件列表'], files_checked: ['files checked', '文件核验'],
  scored_here: ['scored here', '本站评分'], in_matrix: ['core matrix', '核心矩阵'],
};

/** Weights that are reached only by accepting an agreement (the record that says so, re-read at the freeze). */
const GATED_WEIGHTS = { reve: { file: MVP, field: 'models[name=REVE Base].note', holds: 'require accepting the official access agreement' } };

/** A model row: step evidence per item, level by the plan rule (furthest step whose anchor item is on file), gaps. */
function modelRow({ key, kind, name, aliases, urls, model_kind, terms, ev, page, status, where }) {
  // How the weights are reached: open where they are released with stated terms or there are none; behind an
  // agreement where a record says so; unknown where their terms were not found.
  let access = terms.weights.state === 'not_found' ? 'unknown' : 'open';
  if (GATED_WEIGHTS[key]) {
    const g = GATED_WEIGHTS[key], v = select(readJson(g.file), g.field);
    need(typeof v === 'string' && v.includes(g.holds), `${where}: ${g.file}#${g.field} no longer says the weights are gated`);
    access = 'gated';
  }
  const se = {};
  for (const [k, list] of Object.entries(MODEL_STEPS)) {
    const its = list.map(i => { need(ev[i], `${where}: no evidence state for ${i}`); return { item: i, state: ev[i][0], source: ev[i][1] }; });
    const states = new Set(its.map(x => x.state));
    se[k] = { state: [...states].every(x => x === 'pass' || x === 'not-applicable') ? 'pass' : states.size === 1 && states.has('gap') ? 'gap' : 'partial', items: its };
  }
  let level = 0;
  for (const k of [1, 2, 3, 4, 5]) if (ev[MODEL_ANCHOR[k]][0] === 'pass') level = k;
  need(level >= 1, `${where}: no official record on file`);
  for (const k of [1, 2, 3, 4, 5]) if (k > level && se[k].state === 'gap') se[k] = { state: 'not_reached', items: se[k].items };
  const gaps = [], next = [];
  for (const k of [1, 2, 3, 4, 5]) for (const it of se[k].items) if (it.state === 'gap') {
    const g = { step: k, item: it.item, label_en: MODEL_LABEL[it.item][0], label_zh: MODEL_LABEL[it.item][1] };
    if (k <= level) gaps.push(g); else if (k === level + 1) next.push(g);
  }
  return { key, kind, name, aliases, urls: Object.fromEntries(Object.entries(urls).filter(([, v]) => v)), model_kind,
           signal: ['human_scalp_eeg'], terms_by_part: terms, access, level, step_evidence: se, gaps, next_step_gaps: next,
           status, links: { page }, checked: FREEZE_DAY };
}

/* --- The file --------------------------------------------------------------------------------------------------- */

async function main() {
  const check = process.argv.includes('--check');
  const a5 = readJson(A5_PATH), supp = readJson(SUPP_PATH);
  need(a5.release_freeze === PREV, `the census is for ${a5.release_freeze}, not ${PREV}`);
  need(supp.release_freeze === D && supp.extends?.file === A5_PATH && supp.extends.sha256 === sha(readFileSync(abs(A5_PATH))),
    `${SUPP_PATH} is not the ${D} census extending ${A5_PATH} as it stands`);
  need(supp.consent_record?.file === A3_NOW_PATH, `${SUPP_PATH} names another consent record than ${A3_NOW_PATH}`);
  const ids = new Set(a5.sources.map(s => s.id));
  for (const s of supp.sources) need(!ids.has(s.id) && s.census_group === 'dataset_checks', `${s.id}: already in the A5 census, or not a dataset check`);
  const mods = await siteModules();
  const reread = rereadBoth(a5, supp, mods);
  if (reread.mismatches.length) fail(`the census no longer matches the live files:\n${reread.mismatches.map(m => JSON.stringify(m)).join('\n')}`);
  const notes = [];
  const datasets = datasetRows(a5, supp, mods, notes);
  const models = modelRows(mods, notes);
  // The ladders and rules as the pages print them (i18n.ts), which the frozen file must state word for word.
  const ladder = l => l.map(s => ({ step: s.step, en: s.name.en, zh: s.name.zh, needs_en: s.needs.en, needs_zh: s.needs.zh }));
  const inputs = [A5_PATH, A3_PATH, SUPP_PATH, A3_NOW_PATH, DC, 'site/src/data/entities.ts', 'site/src/data/entity-profiles.json', 'site/src/data/i18n.ts',
    'site/src/data/releases.ts', MVP, FMU, EGP, 'site/src/data/data-quality-update.json', 'site/src/data/clinical-iesseeg-update.json',
    'research/moabb_expansion_20261019/evidence/moabb-shortlist-verified.json',
    ...['luna', 'brainomni', 'codebrain', 'eegmamba', 'steegformer', 'eeg-fm-masking', 'erp-fm', 'singlem', 'zuna', 'mirepnet', 'eeg-dino']
      .map(k => `${V8}/verify-${k}.json`)]
    .map(p => ({ path: p, sha256: sha(readFileSync(abs(p))) }));
  const doc = {
    schema_version: SCHEMA, freeze: D, freeze_day: FREEZE_DAY, producer: 'site/scripts/export-site-register-rows.mjs',
    census: { file: A5_PATH, generated_at: a5.generated_at, sha256: sha(readFileSync(abs(A5_PATH))) },
    census_supplement: { file: SUPP_PATH, generated_at: supp.generated_at, sha256: sha(readFileSync(abs(SUPP_PATH))) },
    reread, notes, inputs,
    ladders: { dataset: ladder(mods.i18n.datasetLadder), model: ladder(mods.i18n.modelLadder) },
    rules: { en: mods.i18n.registerCopy.en.rules, zh: mods.i18n.registerCopy.zh.rules },
    counts: { dataset_rows: datasets.length, model_rows: models.length, site_models: models.filter(m => m.kind === 'site_model').length },
    datasets, models,
  };
  const text = JSON.stringify(doc, null, 1) + '\n';
  // The bytes that do not depend on the moment: everything but the hashes of inputs that other packages may still edit.
  if (check) {
    const old = existsSync(abs(OUT)) ? JSON.parse(readFileSync(abs(OUT), 'utf8')) : null;
    const same = old && canon({ ...old, inputs: null, reread: null }) === canon({ ...doc, inputs: null, reread: null });
    console.log(same ? `site rows unchanged (${OUT})` : `site rows differ from ${OUT}`);
    // The served register (the newest open-register-<D>.json) against the live rows: each site row's facts as served.
    const served = served => {
      const R = JSON.parse(readFileSync(join(SITE, 'public/data', served), 'utf8'));
      const byId = new Map(R.entries.map(e => [e.id, e]));
      const drift = [];
      const pick = e => ({ name: e.name, level: e.level, status: e.status, links: e.links, gaps: e.gaps.map(g => `${g.step}:${g.item}`),
                           findings: (e.findings ?? []).map(f => [f.code, f.params]) });
      // A site hold whose code the served file does not declare is held back until the page has words for it.
      const declared = new Set(R.finding_codes.hold?.reason_codes ?? []);
      const servable = f => f.code !== 'hold' || declared.has(f.params.reason_code);
      const heldBack = datasets.flatMap(r => r.findings.filter(f => !servable(f)).map(f => `r-site-${r.slug} (${f.params.reason_code})`));
      if (heldBack.length) console.log(`site holds the served file does not declare yet (no words on the page): ${heldBack.join(', ')}`);
      for (const r of datasets) {
        const e = byId.get(`r-site-${r.slug}`);
        if (!e) { drift.push(`r-site-${r.slug}: not served`); continue; }
        const want = pick({ ...r, findings: r.findings.filter(servable).map(f => ({ code: f.code, params: Object.fromEntries(Object.entries(f.params).sort()) })) });
        if (canon(pick(e)) !== canon(want)) drift.push(`r-site-${r.slug}`);
      }
      for (const r of models) {
        const e = byId.get(`r-model-${r.key}`);
        if (!e) { drift.push(`r-model-${r.key}: not served`); continue; }
        if (canon({ ...pick(e), findings: [], terms: e.terms_by_part }) !== canon({ ...pick({ ...r, findings: [] }), terms: r.terms_by_part }))
          drift.push(`r-model-${r.key}`);
      }
      return { status: R.status, drift };
    };
    const file = readdirSync(join(SITE, 'public/data')).filter(f => /^open-register-\d{8}\.json$/.test(f)).sort().at(-1);
    const v = file ? served(file) : { status: 'none', drift: ['no register file served'] };
    console.log(v.drift.length ? `served ${file} differs from the live site rows: ${v.drift.join(', ')}` : `served ${file} (${v.status}) holds the live site rows`);
    process.exit(same && !v.drift.length ? 0 : 1);
  }
  writeFileSync(abs(OUT), text);
  console.log(`site rows: ${datasets.length} dataset rows, ${models.length} model rows (${doc.counts.site_models} with a method page); `
    + `census re-read: ${reread.values_checked} values, ${reread.drift.length} inputs changed since the census, `
    + `${reread.unresolved.length} sources read through other checks; A3 ${reread.a3.unchanged ? 'unchanged' : 'CHANGED'} → ${OUT}`);
  for (const n of notes) console.log(`  note: ${n}`);
}

main().catch(e => { console.error(e.message ?? e); process.exit(1); });
