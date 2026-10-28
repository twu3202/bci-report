"""Release four dataset checks for the data-quality page, aggregate-only: Kim beta-range worked end to end, MIND as a
conditional worked case, Damm and NeBULA as one-person status cases with no score.

Kim beta-range (40 SSVEP targets from 14.0 to 21.8 Hz, 40 participants) is the worked case: a training-free CCA
baseline on the amplitudes as stored, its mean participant accuracy beside the fixed chance of 40 balanced targets,
with the intake facts that made the files usable. MIND is a conditional worked case (owner's decision D15): stored
class codes 4/5 and 6/7 classified by CSP + LDA on record IDs, beside an ordinal lookup and a majority control, with
the label-schedule facts that explain the lookup's values and a separate secondary panel. Damm and NeBULA are status
cases under the one-person rule (D16, D2 carried over): design, counts, file and timing facts, the variants and arms
that were run and audited, and the holds; no score. D14 publishes Kim, D18 places Damm and NeBULA beside eldBETA.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- release status from each study's own approval and review records, never from an aggregate's own status field (the
  MIND aggregate's pending field is resolved by the bound interpretation review, read unchanged);
- Kim's figures from the independent audit aggregate only, checked against the interpretation review's verified
  figures, never parsed from the handoff; cohort and method facts from the bound protocol, schema record and gate
  review; the intake facts from the asset manifest and the schema record;
- MIND's panels and contrasts from the audited aggregate, each contrast checked against the arithmetic review; the
  schedule facts from the frozen schedule structure the aggregate names; processing facts from the frozen protocol;
- Damm's and NeBULA's counts from their protocols, intake records, boundary diagnostics and structure receipts, each
  equal to the audit or admission that states it;
- consent, ethics and terms only from this release's A2 record, each capture it cites checked by SHA-256 and each
  quotation found verbatim in its capture.
The research files are copy and value sources only: several carry private storage paths, so they are pinned and
checked, never published, and the private names this export refuses are read from them at run time.

What this export refuses:
- values per person, per record ID, per fold, per run or per trial; predictions, features, fitted models, confusion
  matrices, macro-F1, pooled metrics and accounting, by key and, where the sources hold them, by value;
- any Damm or NeBULA score: no fraction or percentage field in those cases, no held value by value or by text, no
  comparison word in their text (so no comparison of NeBULA's order diagnostic with its EEG or EMG arms, with or
  without a number); MIND's secondary schedule census;
- a statement made twice where a page may print both: the one-person reasoning outside the lead sentence, Kim's
  sealing limit and pre-score checks, NeBULA's reference, MIND's secondary panel being reported apart;
- private paths and names, version labels, update markers, months used as labels, strings that have lost their
  spaces, "X, not Y" hedges, Jev, the commenter's figure, conference or submission references, and claims these
  results do not support unless negated.
data-quality-update.json keeps its bytes: its SHA-256 must equal the 2026-10-20 export audit's.

    python3 pipeline/publication/export_dataset_checks_update.py
"""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'dataset-checks-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'dataset-checks-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/dataset-checks-update.json',
           PROJECT / 'site/public/data/dataset-checks-update.json')
RELEASE_ID = 'dataset-checks-update-20261028'
SCHEMA = 'bci-report-dataset-checks-update-v1'

KIM, MIND, DAMM, NEBULA = 'kim2025-beta-range', 'mind2026', 'damm', 'nebula'
SECTIONS = (KIM, MIND, DAMM, NEBULA)
PAGE_ORDER = ('shin2022', KIM, MIND, 'eldbeta', DAMM, NEBULA, 'zuco2')
ONE_PERSON_CASES = ('eldbeta', DAMM, NEBULA)
HELD_CASES = (DAMM, NEBULA)
QUESTION = 'What do the files show once a public EEG dataset is checked end to end?'
KIM_QUESTION = 'What does training-free CCA give on 40 frequencies in the beta range?'
MIND_QUESTION = 'What do stored markers support in a motor-imagery release?'
ONE_PERSON_SENTENCE = ('With one person every score is that person’s, so these three cases publish counts and file facts '
                       'and hold every score.')
ATTRIBUTION_END = 'Derived analysis by BCI Report; not endorsed by the authors.'
DEED = 'https://creativecommons.org/licenses/by/4.0/'
DEED_NC = 'https://creativecommons.org/licenses/by-nc/4.0/'
KIM_DOI = '10.6084/m9.figshare.28806815.v3'
KIM_PAPER_DOI = '10.1038/s41597-025-06032-2'
KIM_ALIASES = ('Kim2025BetaRange', 'Figshare 28806815', 'doi:10.1038/s41597-025-06032-2')
KIM_DATASET_PAGE = '/datasets/kim2025-beta-range/'
NEBULA_DOI = '10.6084/m9.figshare.27301629.v1'
NEBULA_PAPER_DOI = '10.1038/s41597-025-05042-4'
MIND_DOI = '10.57760/sciencedb.34326'
MIND_PAPER = 'arXiv 2602.04299'
PAIRS = (('4_5', '4/5', [4, 5]), ('6_7', '6/7', [6, 7]))
MIND_ARMS = (('csp', 'csp_lda'), ('order', 'ordinal_lookup'), ('majority', 'majority'))
MIND_CONTRASTS = (('4_5', 'order'), ('4_5', 'majority'), ('6_7', 'order'), ('6_7', 'majority'))
CONDITIONS = ('free', 'low', 'high')
TOL = 1e-12
# Values a source figure can equal by design: chance levels (one half, one in five, one in 40), the interval level
# and unit bounds. 0.2 is five-class chance in Damm and, exactly, the upper bound of one published MIND range.
TRIVIAL = {0.0, 0.5, 1.0, 0.95, 0.025, 0.2}
TEXT_SUFFIXES = ('.md', '.txt', '.py')
WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}

# Per-person and per-record values, internals and accounting.
REFUSED_KEYS = PER_PERSON_KEYS | {'seconds', 'total_seconds', 'quantiles', 'samples', 'members', 'pooled_metrics',
                                  'fixture_participants', 'metadata_exclusions', 'metadata_primary_IDs',
                                  'metadata_secondary_IDs', 'secondary_all_two_same', 'secondary_mixed',
                                  'ordinal_census', 'run_manifest', 'calibration', 'scores'}
REFUSED_KEY_FRAGMENTS = ('per_fold', 'per_person', 'per_participant', 'per_subject', 'per_record', 'per_trial',
                         'per_window', 'participant_id', 'subject', 'prediction', 'probabilit', 'threshold',
                         'quantile', 'median', '_min', '_max', 'elapsed', 'cpu', 'wall', 'accounting', 'bytes', 'rss',
                         'memory', 'device', 'private', 'path', 'host', 'member', 'decision_values', 'confusion',
                         'f1', 'fit_calls', 'census')
# Inside the Damm and NeBULA cases: nothing that is, or bounds, a held score.
HELD_SCORE_KEY_FRAGMENTS = ('accuracy', 'correct', 'comparator', 'top1', 'residual', 'interval', 'chance',
                            'correlation', 'balanced', 'macro', 'difference', 'delta', 'percent', 'fraction',
                            'paired', 'gain', 'repeat', 'range', 'mean')

LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root|opt)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\w+|\bsubj\d+|\bS\d{1,3}\b|\brun-?\d+\b|\btask-\w+'
                        r'|\.(?:npz|npy|edf|mat|tsv|gdf|dat|vhdr|vmrk|eeg|csv|zip)\b', re.IGNORECASE)
OUT_OF_FILE = re.compile(r'BI2013a|Brain Invaders|ICLR|OpenReview|NeurIPS|submission|double-blind|iMINDBench'
                         r'|NEAR-Bench|\bTASER\b|CoLaP', re.IGNORECASE)
FIFTY_FIVE = re.compile(r'(?<![\d.])55(?:\.0+)?\s*(?:%|per ?cent)|fifty[- ]five|(?<![\d.])0\.55(?!\d)', re.IGNORECASE)
VERSION_LABEL = re.compile(r'(?<![./\w-])[vV]\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d'
                           r'|\bgenerated \d', re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
HEDGE = re.compile(r'[,;]\s+not\s', re.IGNORECASE)
CLAIMS = re.compile(r'significan|superior|outperform|\bbeats?\b|better than|worse than|\bbest\b|\bwinner|\branks? (?:first|second|third|top|above|below|highest|lowest)\b'
                    r'|\branked\b|\branking\b|state[- ]of[- ]the[- ]art|pure (?:motor )?imagery|\bonline\b|real-time'
                    r'|\bclinical\b|\bmedical\b|\bcausal|\bcaused\b|artifact-free|artefact-free|\bclean\b'
                    r'|units? (?:are |were |is |was )?verified|verified (?:microvolt|amplitude|unit)|preregist'
                    r'|leaderboard|\bsynerg|neural contribution|generali[sz]|\bpopulation\b|fatigue (?:reduc|relief|benefit)'
                    r'|assistance benefit|confidence interval', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none|nothing|outside)\b|n't\b", re.IGNORECASE)
HEX = re.compile(r'[0-9a-f]{16,}')
DATASET_ID = re.compile(r'[A-Z][a-z]+\d{4}[A-Za-z]*')
# Verbatim quotations, titles and citations: checked for paths, names, identifiers and labels, never reworded.
QUOTED = re.compile(r'(?:quote|\.title_as_recorded|\.citation|\.attribution|\.rights\.name)$')
SCORE_TEXT = re.compile(r'%|per ?cent|(?<![\w.])\d+\.\d{2}(?!\w|\.\d)|(?<![\w.])0\.\d+')
# Inside the Damm and NeBULA cases: no comparison of held scores, with or without a number.
COMPARISON = re.compile(r'\b(?:higher|lower|exceed\w*|above|below|compared?|comparison|comparable|better|worse|versus'
                        r'|vs\.?|outperform\w*|beats?|beaten|surpass\w*|more accurate|less accurate|ahead of|behind'
                        r'|at chance|over chance|under chance|beyond chance|than)\b', re.IGNORECASE)
# The owner's wording for Kim's sealing (one place only): its "process separation, not blinded labels" stays as worded.
KIM_SEALING = re.compile(r'All [\d,]+ outputs were sealed before a separate process scored them; this is process '
                         r'separation, not blinded labels, because the stored class order is known\.')
# The one-person reasoning: the lead sentence alone says it.
THAT_PERSON = re.compile(r'that person|this person|one person’s|one person\'s|that participant’s|that participant\'s'
                         r'|the participant’s own|would be (?:that|this|one|the) (?:person|participant)', re.IGNORECASE)


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool)


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def flat(text):
    return re.sub(r'\s+', ' ', text).strip()


def tight(text):
    return re.sub(r'\s+', '', text)


def stated(text, phrase, label):
    require(flat(phrase) in flat(text), f'{label}: the pinned record does not state {phrase!r}')


def stated_tight(text, phrase, label):
    """For records whose words have lost their spaces: compared with every space removed."""
    require(tight(phrase) in tight(text), f'{label}: the pinned record does not state {phrase!r}')


def visible(text):
    return flat(html.unescape(re.sub(r'<[^>]+>', ' ', text)))


def in_capture(quote, raw, label):
    require(flat(quote) in flat(raw) or flat(quote) in visible(raw), f'{label}: the quotation is not in its capture')


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def leaves(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, f'{trail}[{i}]')
    else:
        yield trail, value


def floats(value):
    return [v for _, v in leaves(value) if isinstance(v, float)]


def ints(value):
    return [v for _, v in leaves(value) if count(v)]


def names_and(names):
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


def word(n):
    return WORDS.get(n, f'{n:,}')


def first_last(name):
    """'Kim, Heegyu' -> 'Heegyu Kim'."""
    last, _, first = name.partition(', ')
    return f'{first} {last}' if first else name


def whole(x, label):
    require(abs(x - round(x)) < 1e-9, f'{label}: not a whole number')
    return int(round(x))


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {}
    for group in ('sources', 'withheldReference'):
        for k, ref in manifest[group].items():
            docs[k] = pinned_text(ref, k) if ref['path'].endswith(TEXT_SUFFIXES) else pinned(ref, k)[0]
    docs['consent'] = pinned(manifest['consent']['statements'], 'consent statements')[0]
    docs['captures'] = captures(docs['consent'])
    docs['released'] = released_unchanged(manifest)
    return docs


def capture_refs(value):
    """Every capture the A2 record cites with a SHA-256, at any depth."""
    if isinstance(value, dict):
        if value.get('capture_file') and value.get('capture_sha256'):
            yield value['capture_file'], value['capture_sha256']
        for v in value.values():
            yield from capture_refs(v)
    elif isinstance(value, list):
        for v in value:
            yield from capture_refs(v)


def captures(a2):
    """The A2 captures this release reads, each refused unless its bytes have the SHA-256 the A2 record gives."""
    out = {}
    for key in SECTIONS:
        for f, digest in capture_refs(a2['sources'][key]):
            raw = (PROJECT / f).read_bytes()
            require(sha(raw) == digest, f'A2 capture {f}: not the bytes the consent record names')
            out[f] = raw.decode('utf-8')
    return out


def released_unchanged(manifest):
    """data-quality-update.json keeps the bytes the 2026-10-20 export audit recorded, in both served copies."""
    p = manifest['published']
    raw = (PROJECT / p['dataQuality']['path']).read_bytes()
    require(sha(raw) == p['dataQuality']['sha256'], 'data-quality-update.json changed')
    public = PROJECT / p['dataQuality']['path'].replace('site/src/data', 'site/public/data')
    require(public.read_bytes() == raw, 'the two served copies of data-quality-update.json differ')
    audit = pinned(p['dataQualityExportAudit'], 'the 2026-10-20 data-quality export audit')[0]
    require(audit['status'] == 'pass' and audit['export_sha256'] == p['dataQuality']['sha256']
            and audit['manifest_sha256'] == p['dataQualityManifest']['sha256']
            and audit['release_id'] == 'data-quality-update-20261020',
            'data-quality-update.json is not the file the 2026-10-20 release recorded')
    dq = json.loads(raw)
    require(dq['provenance']['manifest_sha256'] == p['dataQualityManifest']['sha256'],
            'the released data-quality file names another manifest')
    pinned(p['dataQualityManifest'], 'the 2026-10-20 data-quality manifest')
    return {'data-quality-update.json': sha(raw), 'eldbeta_status_text': dq['eldbeta']['status_text']}


def owner_decisions(manifest):
    """The quoted decisions are still the owner's: D14 Kim, D15 MIND, D16 the one-person rule, D18 placement, D2."""
    od = manifest['approval']['ownerDecisions']
    doc = json.loads((PROJECT / od['path']).read_bytes())
    d = doc['decisions']
    current = {'D14': d['D14']['answer'], 'D15': d['D15']['answer'], 'D16': d['D16']['answer'],
               'D18': d['defaults_stated_to_owner_and_not_objected']['D18 (Q4)']}
    require(set(od['quoted']) == set(current), 'the manifest quotes other decisions')
    for k, text in od['quoted'].items():
        require(current[k] == text, f'owner decision {k} changed; the release must be reviewed again')
    require('the Kim beta-range CCA baseline' in current['D14'], 'D14 does not publish Kim')
    require(current['D15'].startswith('Publish now as a conditional case on /topics/data-quality/')
            and 'record IDs, not verified people' in current['D15'], 'D15 does not publish MIND as a conditional case')
    require(current['D16'].startswith('Keep the rule') and 'the scores stay held' in current['D16'],
            'D16 no longer holds the Damm and NeBULA scores')
    require('Damm and NeBULA status cases on /topics/data-quality/ beside eldBETA' in current['D18']
            and 'one-person sentence stated once' in current['D18'], 'D18 places the cases elsewhere')
    co = manifest['approval']['carriedOver']
    d2 = json.loads((PROJECT / co['path']).read_bytes())['decisions']['D2']['answer']
    require(d2 == co['quoted']['D2'] and 'score is held' in d2, 'owner decision D2 changed')
    require('D2 (one-person scores held)' in doc['decisions']['carried_over'], 'D2 is no longer carried over')
    return current


def private_names(docs):
    """The home, storage and host names the research records use, read from them, never spelled in this file."""
    text = ''.join(docs[k] for k in ('kimHandoff', 'mindHandoff', 'dammHandoff', 'nebulaEegHandoff',
                                     'nebulaEmgIntakeHandoff', 'nebulaEmgPilotHandoff'))
    text += json.dumps(docs['mindProtocol']) + json.dumps(docs['nebulaEmgIntakeInterpretationReview'])
    text += json.dumps(docs['kimProtocol'])
    names = {n for pair in re.findall(r'/(?:home|Users|Volumes|mnt)/([^/\s`"]+)/([^/\s`"]+)', text) for n in pair}
    hosts = set(re.findall(r'\b(?:on|or) ([A-Z][A-Za-z]{1,8}\d+)\b', text))
    hosts |= set(re.findall(r'\b([A-Z]{3,6}\d*) under\b', text)) | set(re.findall(r'\bprivate ([A-Z]{3,6}\d*) Linux\b', text))
    hosts |= set(re.findall(r'site/([A-Z][a-z]{2,8}\d+)/', text))
    names |= hosts | {re.sub(r'\d+$', '', h) for h in hosts if re.fullmatch(r'[A-Z]+\d*', h)}
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- consent, ethics and terms (A2)
def gap_or(value):
    return None if value in (None, 'gap') else value


def consent_gaps(s):
    """The A2 gaps that concern ethics or consent; licence gaps are stated with the terms."""
    return [{'field': g['field'], 'note': g['note']} for g in s['gaps'] if g['field'].startswith(('consent', 'ethics'))]


def unversioned(text):
    """An arXiv identifier without its version suffix: no version label in a reader-facing string."""
    return re.sub(r'(\d)v\d+\b', r'\1', text)


def consent_block(s, label):
    """The A2 statements as recorded: quotes, committee, approval number, location and gaps."""
    e, c = s['ethics_committee_and_number'], s['consent']
    ethics_quote, consent_quote = gap_or(s['ethics_quote']), gap_or(s['consent_quote'])
    require((consent_quote is not None) == c['stated'], f'{label}: the consent quote and its flag disagree')
    informed = {'stated': c['stated'], 'kind': c.get('kind'), 'quote': consent_quote, 'location': c.get('location')}
    block = {
        'ethics_approval': {'stated': ethics_quote is not None, 'quote': ethics_quote,
                            'body': gap_or(e['committee']), 'approval_number': gap_or(e['number'])},
        'informed_consent': informed,
        'read_from': s['read_from'], 'read_section': s['read_section'], 'read_at': s['captured_at'],
        'capture_sha256': s['capture_sha256'],
        'gaps': consent_gaps(s),
    }
    return block


def figshare(docs, lic, doi, label):
    record = json.loads(docs['captures'][lic['capture_file']])
    versions = json.loads(docs['captures'][lic['latest_check']['capture_file']])
    latest = max(v['version'] for v in versions)
    require(lic['pinned_version_is_latest'] is True and record['version'] == latest and record['doi'] == doi,
            f'{label}: the pinned version is not the latest the record lists')
    require(record['license']['url'] == lic['url'] == DEED and lic['value'] == 'CC BY 4.0',
            f'{label}: another data licence')
    return record, versions


def paper_meta(raw, doi, label):
    """Title, authors, volume, article number and year from the capture's citation metadata."""
    def meta(name):
        return [html.unescape(m) for m in re.findall(rf'<meta name="{name}" content="([^"]*)"', raw)]
    require(meta('citation_doi') == [doi], f'{label}: the paper capture is another article')
    year = meta('citation_online_date')[0][:4]
    return {'title': meta('citation_title')[0], 'authors': [first_last(a) for a in meta('citation_author')],
            'journal': meta('citation_journal_title')[0], 'volume': meta('citation_volume')[0],
            'article': meta('citation_firstpage')[0], 'year': year}


def data_licence(lic, record, versions):
    return {'value': lic['value'], 'url': lic['url'], 'stated_by': lic['stated_by'], 'read_from': lic['read_from'],
            'read_at': lic['captured_at'], 'capture_sha256': lic['capture_sha256'],
            'pinned_version': record['version'], 'versions_listed': len(versions),
            'pinned_version_is_latest': record['version'] == max(v['version'] for v in versions)}


# ---------------------------------------------------------------------------- Kim beta-range (worked case)
def kim_release(docs, manifest):
    src, ag = manifest['sources'], docs['kimAggregate']
    ra = docs['kimReleaseApproval']
    require(ra['status'] == 'PASS_INTERNAL_AGGREGATE_HANDOFF', 'Kim: the release approval did not pass')
    require(ra['independent_audit_sha256'] == src['kimAggregate']['sha256']
            and ra['interpretation_review_sha256'] == src['kimInterpretationReview']['sha256']
            and ra['handoff_sha256'] == src['kimHandoff']['sha256']
            and ra['binding_sha256'] == ag['binding_sha256'] == src['kimBinding']['sha256'],
            'Kim: the release approval binds other files')
    require(ra['physical_units_verified'] is False and ra['amplitude_dependent_model_gate'] == 'HOLD'
            and ra['public_raw_or_participant_data'] is False, 'Kim: the release approval flags changed')
    ir = docs['kimInterpretationReview']
    require(ir['decision'] == 'PASS' and ir['aggregate_sha256'] == src['kimAggregate']['sha256'],
            'Kim: the interpretation review binds another aggregate')
    fa = docs['kimFinalApproval']
    require(fa['decision'] == 'PASS' and fa['binding_sha256'] == src['kimBinding']['sha256'], 'Kim: the execution approval')
    b = docs['kimBinding']['sha256']
    require(b['protocol.json'] == src['kimProtocol']['sha256'] and b['manifest.json'] == src['kimAssetManifest']['sha256']
            and b['schema.json'] == src['kimSchema']['sha256'], 'Kim: the binding pins other files')
    require(ag['decision'] == 'PASS' and ag['fixture_match_count'] == ag['fixture_count'], 'Kim: the audit did not pass')
    rd = docs['kimAuditReadiness']
    require(rd['binding_sha256'] == src['kimBinding']['sha256']
            and rd['audit_code_sha256'] == ag['execution_receipt']['code_sha256'], 'Kim: the audit readiness record')


def kim_result(docs):
    ag, pr = docs['kimAggregate'], docs['kimProtocol']
    targets = pr['targets']
    chance = ag['prior_chance']
    require(chance == 1 / targets, 'Kim: chance is not one in the number of targets')
    mean, diff = ag['mean_accuracy'], ag['mean_difference']
    lo, hi = ag['participant_bootstrap_95_percentile']
    require(all(number(v) for v in (mean, diff, lo, hi)) and abs(mean - chance - diff) < TOL and lo <= diff <= hi
            and 0 < lo + chance <= mean <= hi + chance < 1, 'Kim: the interval does not hold its estimate')
    ir = ' '.join(docs['kimInterpretationReview']['verified_interpretation'])
    stated_tight(ir, f'{100 * mean:.4f}% macro participant accuracy matches aggregate', 'Kim review')
    stated_tight(ir, f'Difference{100 * diff:.4f} percentage points and interval{100 * lo:.4f}..{100 * hi:.4f} points',
                 'Kim review')
    stated_tight(ir, f'accuracy interval{100 * (lo + chance):.4f}..{100 * (hi + chance):.4f}%', 'Kim review')
    stated_tight(ir, 'Complete class balance makes per-participant accuracy equal balanced accuracy', 'Kim review')
    stated_tight(pr['outcome'], f'{ag["bootstrap_replicates"]} draws seed{ag["seed"]}', 'Kim bootstrap')
    stated(ag['bootstrap_interpretation'], 'Participant resampling against fixed theoretical chance', 'Kim bootstrap')
    result = {
        'metric': 'mean participant accuracy; with six trials per target for every participant it equals balanced '
                  'accuracy in this cohort',
        'mean_participant_accuracy': mean,
        'equals_balanced_accuracy': True,
        'chance': chance,
        'chance_basis': f'one in {targets} balanced targets',
        'difference_from_chance': diff,
        'difference_interval_95': [lo, hi],
        'accuracy_interval_95': [lo + chance, hi + chance],
    }
    interval = {'kind': 'participant bootstrap percentile interval', 'level': 0.95,
                'resamples': ag['bootstrap_replicates'], 'seed': ag['seed'], 'unit': 'participant',
                'of': 'the difference from the fixed chance level; the accuracy interval adds chance back',
                'descriptive': True, 'test': False}
    return result, interval


def kim_cohort_method(docs):
    ag, pr, sc, gr = docs['kimAggregate'], docs['kimProtocol'], docs['kimSchema'], docs['kimGateReview']
    targets, blocks_each = pr['targets'], pr['blocks_per_participant']
    require(ag['participants'] == pr['participants'] and ag['blocks'] == pr['participants'] * blocks_each
            and ag['trials'] == pr['trials'] == ag['blocks'] * targets, 'Kim: the counts do not add up')
    require(sc['shape'][2] == targets and sc['shape'][3] == blocks_each, 'Kim: the schema record holds another design')
    per_target = ag['trials'] // (ag['participants'] * targets)
    require(per_target * ag['participants'] * targets == ag['trials'] and per_target == blocks_each,
            'Kim: the trials per target')
    stated(docs['kimHandoff'], 'Single-day blocks are not longitudinal sessions.', 'Kim recording days')
    cohort = {'participants': ag['participants'], 'blocks': ag['blocks'], 'blocks_each': blocks_each,
              'recording_days_each': 1, 'trials': ag['trials'], 'targets': targets,
              'trials_per_target_each': per_target, 'complete_cohort': True}
    channels = pr['channels']
    require(channels == gr['prospective_baseline']['channels'] and len(channels) == 11, 'Kim: the channels')
    fs = pr['sampling_rate']
    c0, c1 = pr['crop']
    require(fs == sc['sampling_rate_hz'] and c0 == sc['onset_zero_based'] and (c1 - c0) % fs == 0, 'Kim: the window')
    stated(sc['time_axis_note'], 'sample2048 derived exactly from start -2000ms and1024Hz', 'Kim onset')
    stated(sc['time_axis_note'], 'No measured trigger trace stored.', 'Kim onset')
    m = re.search(r'second-order Butterworth (\d+)-(\d+)Hz', pr['filter'])
    require(m is not None and 'CROP FIRST' in pr['filter'] and 'sosfiltfilt' in pr['filter'], 'Kim: the filter')
    band = [int(m.group(1)), int(m.group(2))]
    harmonics = gr['prospective_baseline']['harmonics']
    require(harmonics == [1, 2] and 'harmonics1,2' in pr['reference_signals'], 'Kim: the harmonics')
    require(pr['reference'] == 'Subtract stored mean(M1,M2); no unit conversion', 'Kim: the reference')
    stated(pr['cca'], 'No epsilon/ridge/repair/drop.', 'Kim: no tuning or repair')
    stated(docs['kimHandoff'], 'No fitted cohort parameter or label tuning.', 'Kim: no tuning')
    stated(docs['kimHandoff'], 'No participant, channel or trial was silently dropped or repaired.', 'Kim: nothing dropped')
    method = {
        'algorithm': 'standard CCA, largest canonical correlation over the stored target frequencies',
        'training_free': True, 'tuning': False, 'trials_dropped': 0,
        'channels': len(channels), 'channel_names': list(channels),
        'reference': 'the stored mean of M1 and M2 subtracted; no unit conversion',
        'sampling_hz': fs, 'window_seconds': (c1 - c0) // fs, 'window_samples': c1 - c0,
        'window': 'a nominal 2-second window from the stored onset, with no visual-delay shift',
        'band_hz': band, 'filter_order': 2,
        'filter': 'second-order Butterworth band-pass, forward and backward, inside the window only',
        'harmonics': len(harmonics),
        'reference_signals': 'sine and cosine at each stored target frequency and its second harmonic',
    }
    require('second-order' in pr['filter'], 'Kim: the filter order')
    return cohort, method


def kim_intake(docs):
    """The intake facts. The checks every file passed before any score are stated once, in how_checked."""
    am, sc, pr = docs['kimAssetManifest'], docs['kimSchema'], docs['kimProtocol']
    files = am['files']
    require(am['file_count'] == len(files) == pr['participants'] and am['task_assets_only'] is True
            and am['rest_and_questionnaire_excluded'] is True, 'Kim: the asset manifest')
    matched = sum(1 for f in files if f['supplied_md5'] == f['computed_md5'])
    require(matched == len(files), 'Kim: an MD5 check failed')
    freqs = sc['stored_frequency_hz']
    rule = [14 + j + 0.2 * i for i in range(5) for j in range(8)]
    require(len(freqs) == pr['targets'] == len(set(freqs)) and all(abs(f - r) < 1e-9 for f, r in zip(freqs, rule)),
            'Kim: the stored target order is not 14 + j + 0.2 i')
    require(freqs != sorted(freqs), 'Kim: the stored order is ascending')
    se = docs['kimSourceEvidence']
    require('Metadata stimulus_frequencies list monotonically ascending is not stored class order'
            in se['moabb_adapter']['findings'], 'Kim: the MOABB order finding')
    stated(pr['eligibility'], 'pass before ANY CCA score', 'Kim: checks before any score')
    require(all(sc['checks'].values()), 'Kim: a schema check failed')
    return {
        'task_files': len(files), 'md5_checked': len(files), 'md5_matched': matched,
        'rest_and_questionnaire_acquired': False,
        'frequency_lowest_hz': min(freqs), 'frequency_highest_hz': max(freqs), 'distinct_frequencies': len(set(freqs)),
        'stored_target_order': '14 + j + 0.2·i Hz, for row i = 0…4 and column j = 0…7',
        'stored_order_ascending': False, 'moabb_list_ascending': True,
        'checks_before_any_score': True,
        'text': (f'All {matched} task files passed their MD5 checks; the rest and questionnaire files were not acquired. '
                 'The files store the targets in the order 14 + j + 0.2·i Hz, which differs from the ascending list in '
                 'MOABB’s metadata, and the references follow the stored order.'),
    }


def kim_checked(docs):
    ag, rd, hd = docs['kimAggregate'], docs['kimAuditReadiness'], docs['kimHandoff']
    stated(hd, 'drawn from four fixed participants, three fixed blocks and five fixed target indices', 'Kim fixtures')
    design = {'participants': len(rd['fixture_participants']), 'blocks': len(rd['fixture_block_indices']),
              'targets': len(rd['fixture_target_indices'])}
    require(design == {'participants': 4, 'blocks': 3, 'targets': 5} and rd['fixture_trials'] == ag['fixture_count']
            == design['participants'] * design['blocks'] * design['targets'], 'Kim: the fixture design')
    gr = docs['kimGateReview']
    require(gr['scope_decision'] == 'PASS_CONDITIONAL_FOR_AS_STORED_CCA_ONLY'
            and gr['amplitude_dependent_FM'].startswith('HOLD'), 'Kim: the scope review')
    trials = ag['trials']
    stated_tight(docs['kimProtocol']['sealing'], f'All{trials} predictions globally sealed', 'Kim: sealing')
    stated(docs['kimProtocol']['sealing'], 'Labels/correctness/bootstrap exist only in independent score process.',
           'Kim: the separate scoring process')
    stated(' '.join(docs['kimFinalApproval']['reporting_limits']),
           'Prediction sealing is auditable temporal/process separation, not independent label blindness',
           'Kim: the sealing limit')
    stated(docs['kimHandoff'], 'not independently blinded labels: the class axis is structurally known',
           'Kim: the sealing limit')
    sealing = (f'All {trials:,} outputs were sealed before a separate process scored them; this is process separation, '
               'not blinded labels, because the stored class order is known.')
    require(KIM_SEALING.fullmatch(sealing) is not None, 'Kim: the sealing sentence is not the owner’s wording')
    return [
        {'id': 'scope-review', 'state': 'pass',
         'text': 'A separate review admitted the as-stored, scale-invariant CCA arm before any score, and kept '
                 'amplitude-dependent models held.'},
        {'id': 'all-files-checked', 'state': 'pass',
         'text': 'Every file passed identity, shape, timing, frequency, phase, finite-value and rank checks before any '
                 'score.'},
        {'id': 'sealed-before-scoring', 'state': 'pass', 'text': sealing},
        {'id': 'independent-audit', 'state': 'pass', 'fixtures': ag['fixture_count'],
         'fixtures_matched': ag['fixture_match_count'], 'fixture_design': design,
         'text': 'An independent audit verified the counts and the bootstrap, and a separate CCA implementation '
                 'reproduced every fixed fixture.'},
        {'id': 'interpretation-review', 'state': 'pass',
         'text': 'An independent review checked the figures and the wording against the audit aggregate.'},
    ]


def kim_caveats(docs):
    hd, sc = docs['kimHandoff'], docs['kimSchema']
    stated(hd, 'This does not prove common channel gains, absence of clipping, or the original reference history.',
           'Kim caveat')
    stated(hd, 'comparing absolute scores across those tasks does not isolate the effect of frequency range',
           'Kim caveat')
    stated(hd, 'It is offline and noncausal inside the window', 'Kim caveat')
    require(sc['stored_window_ms'] == [-2000, 5000], 'Kim: the stored epoch start')
    return [
        {'id': 'as-stored-amplitudes',
         'text': 'The scores use amplitudes as stored. CCA does not depend on a common amplitude scale, but common '
                 'channel gains, freedom from clipping and the saved reference history are not established, so models '
                 'whose output depends on amplitude are held.'},
        {'id': 'nominal-onset',
         'text': 'The onset is nominal: it is derived from the stored start of each epoch, 2 seconds before the cue, at '
                 '1,024 Hz, and no trigger trace is stored.'},
        {'id': 'one-day', 'text': 'Each participant’s six blocks were recorded on one day.'},
        {'id': 'offline',
         'text': 'The filter runs forward and backward inside each window, so the pipeline is offline and gives no '
                 'response-time figure.'},
        {'id': 'own-pipeline', 'text': 'The pipeline is BCI Report’s fixed recipe; it does not reproduce the paper’s '
                                       'processing.'},
        {'id': 'other-ssvep-datasets',
         'text': 'Frequencies, people and channels differ from BETA and Wearable-102, so comparing absolute scores '
                 'across those datasets does not isolate the frequency range.'},
        {'id': 'interval',
         'text': 'The accuracy interval is the participant-bootstrap interval of the difference from the fixed 2.5% '
                 'chance level, shifted up by 2.5 points; no algorithm was run as chance and no test was run.'},
        {'id': 'fixtures', 'text': 'The independent audit reproduced 60 of 60 fixed fixtures; it did not rerun every '
                                   'trial.'},
    ]


def kim_rights(docs, a2):
    s = a2['sources'][KIM]
    lic = s['licence']['data']
    record, versions = figshare(docs, lic, KIM_DOI, 'Kim')
    require(s['paper'] == f'https://doi.org/{KIM_PAPER_DOI}' and s['dataset_record'] == f'https://doi.org/{KIM_DOI}',
            'Kim: another record')
    paper_raw = docs['captures'][s['capture_file']]
    paper = paper_meta(paper_raw, KIM_PAPER_DOI, 'Kim')
    require(paper['authors'] == ['Heegyu Kim', 'Kyungho Won', 'Minkyu Ahn', 'Sung Chan Jun'], 'Kim: other authors')
    creators = [a['full_name'] for a in record['authors']]
    cited = lic['paper_cited_version']
    v2 = json.loads(docs['captures'][cited['capture_file']])
    require(v2['version'] == cited['version'] == 2 and v2['license']['name'] == cited['licence'] == 'CC BY 4.0',
            'Kim: the version the paper cites')
    for q in (s['consent_quote'], s['data_sharing_consent_quote'], s['consent']['scope_note_quote'], s['ethics_quote'],
              s['licence']['paper']['quote'], cited['quote']):
        in_capture(q, paper_raw, 'Kim')
    e = s['ethics_committee_and_number']
    require(e['research_value_confirmed'] is True and e['number'] in e['research_value'], 'Kim: the IRB number')
    attribution = (f'{names_and(creators)} · {record["title"]}, figshare, doi:{KIM_DOI}, {record["license"]["name"]}. '
                   f'Paper: {names_and(paper["authors"])}, {paper["title"]}, {paper["journal"]} {paper["volume"]}:'
                   f'{paper["article"]} ({paper["year"]}), doi:{KIM_PAPER_DOI}. Modifications: the 40 task files only; '
                   'the mean of M1 and M2 subtracted, 11 channels, a 2-second window and a band-pass filter inside it; '
                   f'no data redistributed. {ATTRIBUTION_END}')
    privacy = (f'Ethics: {e["committee"]}, approval {e["number"]}. Consent: {s["consent"]["kind"]}. '
               f'{s["consent"]["scope_note"]} Published here: the mean participant accuracy with its participant-bootstrap interval and aggregate '
               'counts; no per-participant value, identifier, prediction or signal.')
    rights = {
        'name': s['name'],
        'task': 'Forty-target SSVEP speller selection with stimuli from 14.0 to 21.8 Hz, six blocks per person on one day.',
        'source': f'https://doi.org/{KIM_DOI}',
        'version': (f'Figshare record 28806815, version {record["version"]}, the latest of the {len(versions)} '
                    'versions the record lists'),
        'license': record['license']['name'], 'licenseUrl': DEED, 'attribution': attribution,
        'reviewedAt': s['captured_at'][:10],
        'reviewBasis': [lic['read_from'], s['read_from']],
        'privacyReview': privacy,
        'terms': {
            'data_licence': data_licence(lic, record, versions),
            'paper_licence': {'value': s['licence']['paper']['value'], 'quote': s['licence']['paper']['quote'],
                              'covers': s['licence']['paper']['covers']},
            'paper_cited_version': {'version': cited['version'], 'licence': cited['licence'], 'quote': cited['quote'],
                                    'note': cited['note']},
        },
    }
    consent = consent_block(s, 'Kim')
    consent['informed_consent'].update({'data_sharing_quote': s['data_sharing_consent_quote'],
                                        'scope_note': s['consent']['scope_note'],
                                        'scope_note_quote': s['consent']['scope_note_quote']})
    return rights, consent


def kim_case(docs, manifest, a2):
    kim_release(docs, manifest)
    result, interval = kim_result(docs)
    cohort, method = kim_cohort_method(docs)
    rights, consent = kim_rights(docs, a2)
    hold = next(h for h in manifest['holds'] if h['case'] == KIM)
    return {
        'id': KIM, 'kind': 'worked_case', 'section': KIM, 'status': 'released', 'name': 'Kim beta-range SSVEP',
        'question': KIM_QUESTION,
        'task': ('Which of 40 flickering targets from 14.0 to 21.8 Hz a participant attends, from a 2-second window, '
                 'with no training data.'),
        'cohort': cohort,
        'result': result,
        'interval': interval,
        'method': method,
        'intake': kim_intake(docs),
        'how_checked': kim_checked(docs),
        'caveats': kim_caveats(docs),
        # The reason is stated once, in the caveat as-stored-amplitudes; the top-level holds carry the /releases/ line.
        'hold': {'id': hold['id'], 'what': 'models whose output depends on amplitude, on these files'},
        'dataset_page': KIM_DATASET_PAGE,
        'method_link': False,
        'aliases': list(KIM_ALIASES),
        'rights': rights,
        'consent_and_ethics': consent,
    }


# ---------------------------------------------------------------------------- MIND (conditional worked case)
def mind_release(docs, manifest):
    src, ag = manifest['sources'], docs['mindAggregate']
    ir = docs['mindInterpretationReview']
    require(ir['decision'] == 'APPROVED_INTERNAL_CONDITIONAL_HANDOFF' and ir['required_corrections'] == []
            and ir['aggregate_sha256'] == src['mindAggregate']['sha256']
            and ir['handoff_sha256'] == src['mindHandoff']['sha256']
            and ir['ordinal_structure_sha256'] == src['mindScheduleStructure']['sha256']
            and ir['arithmetic_and_binding_check_sha256'] == src['mindArithmeticChecks']['sha256'],
            'MIND: the interpretation review binds other files')
    require(all(f['result'].startswith('PASS') for f in ir['approval_findings']), 'MIND: a review finding failed')
    require(any('pending-interpretation field is resolved by this separate bound review' in n
                for n in ir['nonblocking_notes']), 'MIND: the review does not resolve the aggregate field')
    wc = docs['mindWorkflowClosure']
    require(wc['interpretation_review_sha256'] == src['mindInterpretationReview']['sha256']
            and wc['aggregate_sha256'] == src['mindAggregate']['sha256'] and wc['handoff_sha256'] == src['mindHandoff']['sha256']
            and wc['ordinal_structure_sha256'] == src['mindScheduleStructure']['sha256']
            and wc['independent_model_replay'] == 'PASS_EXACT'
            and wc['independent_interpretation_review'] == 'APPROVED_INTERNAL_CONDITIONAL_HANDOFF',
            'MIND: the workflow closure binds other files')
    ac = docs['mindArithmeticChecks']
    require(ac['status'] == 'PASS_FILE_ONLY_RESULT_INTERPRETATION_CHECKS'
            and ac['aggregate_sha256'] == src['mindAggregate']['sha256'], 'MIND: the arithmetic checks')
    require(ag['status'] == 'AUDITED_CONDITIONAL_STORED_MARKER_BASELINE_COMPLETED'
            and ag['metric_comparison']['status'] == 'PASS'
            and ag['metric_comparison']['audit_scores_sha256'] == ag['metric_comparison']['producer_scores_sha256']
            and ag['independent_prediction_comparison']['hard_predictions_exact'] is True
            and ag['independent_prediction_comparison']['row_IDs_exact'] is True
            and ag['raw_arrays_or_per_record_outcomes_exported'] is False and ag['primary_and_secondary_not_pooled'] is True,
            'MIND: the aggregate audit did not pass')
    require(docs['mindScheduleStructure']['census_sha256'] == ag['evidence_sha256']['ordinal_census'],
            'MIND: the schedule structure reads another census')
    stated(docs['mindHandoff'], f'Frozen protocol: `{src["mindProtocol"]["sha256"]}`', 'MIND protocol')


def mind_panels(docs):
    ag, ac = docs['mindAggregate'], docs['mindArithmeticChecks']
    prim, sec = ag['metrics']['primary'], ag['metrics']['secondary']
    checks = {(c['pair'], c['control']): c for c in ac['contrasts']}
    primary_pairs, contrasts, secondary_pairs = [], [], []
    for key, label, codes in PAIRS:
        m = prim[key]
        require(m['record_ID_count'] == ag['primary_record_IDs'] and m['bootstrap_performed'] is True,
                f'MIND {label}: the primary panel')
        ba = m['mean_record_ID_balanced_accuracy']
        primary_pairs.append({'pair': label, 'codes': codes, **{name: ba[k] for k, name in MIND_ARMS}})
        s = sec[key]
        require(s['record_ID_count'] == ag['secondary_record_IDs'] and s['bootstrap_performed'] is False
                and 'descriptive_ID_resampling_percentiles' not in s, f'MIND {label}: the secondary panel')
        secondary_pairs.append({'pair': label, 'codes': codes,
                                **{name: s['mean_record_ID_balanced_accuracy'][k] for k, name in MIND_ARMS}})
    for key, control in MIND_CONTRASTS:
        m = prim[key]
        ba = m['mean_record_ID_balanced_accuracy']
        diff = m['mean_paired_ID_differences'][control]
        lo, hi = m['descriptive_ID_resampling_percentiles'][control]
        require(all(number(v) for v in (diff, lo, hi)) and lo <= diff <= hi
                and abs(diff - (ba['csp'] - ba[control])) < TOL, f'MIND {key} {control}: the range does not hold it')
        c = checks[(key, control)]
        require(abs(c['difference_pp'] - 100 * diff) < 1e-9 and abs(c['range_pp'][0] - 100 * lo) < 1e-9
                and abs(c['range_pp'][1] - 100 * hi) < 1e-9, f'MIND {key} {control}: the arithmetic review differs')
        contrasts.append({'pair': key.replace('_', '/'), 'arm': 'csp_lda', 'control': dict(MIND_ARMS)[control],
                          'mean_difference': diff, 'resampling_range': [lo, hi], 'range_spans_zero': lo <= 0 <= hi})
    for row in ac['CM_metric_checks']:
        panel, key, arm, n, value = row
        mean = ag['metrics'][panel][key]['mean_record_ID_balanced_accuracy'][arm]
        require(abs(value - mean) < 1e-12, f'MIND {panel} {key} {arm}: the arithmetic review differs')
    return primary_pairs, contrasts, secondary_pairs


def mind_design(docs):
    ag, pr, hd = docs['mindAggregate'], docs['mindProtocol'], docs['mindHandoff']
    md, cb = pr['actual_metadata'], pr['cohort_before_EEG']
    excluded = len(cb['metadata_exclusions'])
    require(md['runs'] == md['record_subject_ids'] * md['runs_per_ID'] and excluded == ag['metadata_overfull_runs_excluded']
            and md['runs'] - excluded == cb['selected_runs'] == ag['numerically_eligible_runs'], 'MIND: the runs')
    stated_tight(cb['canonical_run_rule'], 'exactly10occurrences each (40total)', 'MIND: the markers per run')
    markers = 40
    require(ag['numeric_QC_failures'] == 0 and ag['total_trials'] == ag['numerically_eligible_runs'] * markers
            == ag['primary_trials'] + ag['secondary_trials'], 'MIND: the trials')
    require(ag['primary_runs'] == ag['primary_record_IDs'] * md['runs_per_ID']
            and ag['primary_trials'] == ag['primary_runs'] * markers
            and ag['secondary_runs'] == ag['secondary_record_IDs'] * (md['runs_per_ID'] - 1)
            and ag['secondary_trials'] == ag['secondary_runs'] * markers
            and ag['primary_record_IDs'] + ag['secondary_record_IDs'] == md['record_subject_ids'],
            'MIND: the panels do not add up')
    stated_tight(cb['primary'], 'threeouterfolds', 'MIND: three folds')
    stated(hd, 'They were excluded in full before waveform access; no restart suffix or selected trials were salvaged.',
           'MIND: the excluded runs')
    coverage = [
        {'id': 'runs_in_release', 'count': md['runs'], 'record_ids': md['record_subject_ids'],
         'runs_for_each_record_id': md['runs_per_ID'],
         'text': 'Runs in the release: three per record ID.'},
        {'id': 'overfull_first_runs', 'count': excluded, 'role': 'excluded', 'class_markers_required': markers,
         'text': 'First runs holding more class markers than the 40 a run requires, excluded whole before any waveform '
                 'was read; no trial was salvaged from them.'},
        {'id': 'runs_evaluated', 'count': ag['numerically_eligible_runs'], 'trials': ag['total_trials'],
         'numeric_check_failures': ag['numeric_QC_failures'],
         'text': 'Runs that passed the frozen finite and non-degenerate checks, which is every one; the checks do not '
                 'clear artifacts.'},
        {'id': 'primary_panel', 'count': ag['primary_runs'], 'record_ids': ag['primary_record_IDs'],
         'trials': ag['primary_trials'], 'text': 'Record IDs with three runs each: the primary panel.'},
        {'id': 'secondary_panel', 'count': ag['secondary_runs'], 'record_ids': ag['secondary_record_IDs'],
         'trials': ag['secondary_trials'],
         'text': 'The two record IDs whose first run was excluded keep two runs each: the secondary panel.'},
    ]
    return coverage


def mind_resampling(docs):
    pr, hd = docs['mindProtocol'], docs['mindHandoff']
    m = re.search(r'one common(\d+)xN index draw table from NumPy default_rng\((\d+)\)', pr['prediction_scoring']['uncertainty'])
    require(m is not None, 'MIND: the resampling plan')
    draws, seed = int(m.group(1)), int(m.group(2))
    stated_tight(pr['prediction_scoring']['uncertainty'], 'linear percentile2.5/97.5 of paired ID-mean differences',
                 'MIND: the percentiles')
    stated(hd, f'{draws:,} paired **record-ID resamples**, using one shared index table and seed {seed}', 'MIND: draws')
    stated(hd, 'not population confidence intervals or confirmatory significance tests', 'MIND: the ranges')
    return {'kind': 'record-ID resampling range', 'draws': draws, 'percentiles': [2.5, 97.5], 'seed': seed,
            'shared_index_table': True, 'confidence_interval': False, 'test': False,
            'text': ('Descriptive sensitivity ranges for this fixed set of record IDs: the 2.5th and 97.5th percentiles '
                     f'of {draws:,} paired record-ID resamples drawn from one shared index table. They are no confidence '
                     'intervals and no test.')}


def mind_schedule(docs):
    st, ag = docs['mindScheduleStructure'], docs['mindAggregate']
    pairs = []
    for key, label, _ in PAIRS:
        p = st['pairs'][key]
        require(p['unique_sequences'] == ag['ordinal_sequence_unique_hashes_per_pair'][key] == 2
                and p['exact_complements'] is True and p['Hamming_distance'] == p['length'] == 20
                and p['primary_all_three_same'] + p['primary_mixed'] == ag['primary_record_IDs'],
                f'MIND {label}: the schedule structure')
        pairs.append({'pair': label, 'schedules': p['unique_sequences'], 'trials_per_schedule': p['length'],
                      'complementary': True, 'primary_ids_repeating_one_schedule': p['primary_all_three_same'],
                      'primary_ids_mixing_schedules': p['primary_mixed']})
    stated(docs['mindHandoff'], 'two complementary 20-trial label schedules for each pair', 'MIND schedules')
    return {'panel': 'primary', 'pairs': pairs,
            'text': ('Each stored-code pair follows one of only two complementary 20-trial label schedules. In the '
                     'primary panel, 6 record IDs for 4/5 and 5 for 6/7 repeat one schedule across all three runs; the '
                     'others mix the two. Under the frozen ordinal lookup and its tie rule, this composition explains the '
                     'ordinal values below 50%: they describe this lookup and schedule rather than a chance floor. No '
                     'replacement control was fitted after the scores were seen.')}


def mind_processing(docs):
    pr = docs['mindProtocol']
    md, cd, pp, fh, lw = (pr['actual_metadata'], pr['channels_and_decode'], pr['preprocessing'],
                          pr['features_heads_controls'], pr['labels_and_windows'])
    require(len(cd['order']) == md['channels'], 'MIND: the channel list')
    stated_tight(cd['include'], 'noHEO/VEO/EKG/EMG/Trigger', 'MIND: no auxiliary channels')
    f = re.search(r'sfreq(\d+),l_freq(\d+),h_freq(\d+),methodfir', tight(pp['filter']))
    require(f is not None and int(f.group(1)) == md['sampling_hz'] and 'phasezero' in tight(pp['filter']), 'MIND: the filter')
    r = re.search(r'resample_poly\(up(\d+),down(\d+)', tight(pp['resample']))
    require(r is not None and md['sampling_hz'] * int(r.group(1)) % int(r.group(2)) == 0, 'MIND: the resampling')
    resampled = md['sampling_hz'] * int(r.group(1)) // int(r.group(2))
    w = re.search(r'\[(\d+),(\d+)\)secondsaftereachstoredclassmarker', tight(lw['window']))
    n = re.search(r'stop=start\+(\d+)', tight(lw['resampled_index']))
    require(w is not None and n is not None and int(n.group(1)) == (int(w.group(2)) - int(w.group(1))) * resampled,
            'MIND: the window')
    c = re.search(r'CSP\(n_components=(\d+),reg=oas', tight(fh['CSP']))
    require(c is not None and 'fitONLYtrainingruns' in tight(fh['CSP']), 'MIND: CSP')
    require('shrinkage=auto' in tight(fh['classifier']) and 'nohyperparametersearch' in tight(fh['classifier']),
            'MIND: the classifier')
    stated_tight(pp['no_extra'], 'ICA,artifactmask', 'MIND: no ICA')
    stated_tight(cd['include'], 'No interpolation,relabeling,rereference', 'MIND: no rereference')
    stated_tight(fh['order_only'], 'No EEGinput', 'MIND: the ordinal lookup has no EEG input')
    return {
        'channels': md['channels'], 'sampling_hz': md['sampling_hz'], 'auxiliary_channels_used': False,
        'band_hz': [int(f.group(2)), int(f.group(3))],
        'filter': 'FIR band-pass over each whole run, zero phase',
        'resampled_hz': resampled,
        'window_after_marker_seconds': [int(w.group(1)), int(w.group(2))], 'window_samples': int(n.group(1)),
        'csp_components': int(c.group(1)), 'csp_regularisation': 'OAS',
        'classifier': 'shrinkage LDA on the four CSP log-power features',
        'fitted_on_training_runs_only': True, 'search': False,
        'not_applied': 'ICA, interpolation, rereferencing, amplitude clipping, channel search and trial exclusion',
        'controls': [
            {'id': 'ordinal_lookup', 'input': 'no EEG',
             'text': 'For each of the 20 positions of a pair within a run, the code the training runs hold most often '
                     'at that position, ties to the lower code.'},
            {'id': 'majority', 'input': 'no EEG',
             'text': 'The code the training runs hold most often, ties to the lower code.'},
        ],
    }


def mind_checked(docs):
    ag, au = docs['mindAggregate'], docs['mindAggregate']['independent_prediction_comparison']
    require(au['rows'] == ag['total_trials'] and au['outside_tolerance_count'] == 0 and au['allclose'] is True,
            'MIND: the replay')
    return [
        {'id': 'sealed-before-scoring', 'state': 'pass', 'trials': au['rows'],
         'text': 'All out-of-fold outputs were sealed together before a separate scoring process.'},
        {'id': 'independent-replay', 'state': 'pass', 'max_decision_difference': au['max_abs_error'],
         'text': 'An independent replay reproduced every hard output, decision value, metric and resampling output '
                 'exactly.'},
        {'id': 'interpretation-review', 'state': 'pass',
         'text': 'An independent review approved the figures, the four contrasts, the schedule explanation and the '
                 'wording.'},
    ]


def mind_caveats(docs):
    pr, hd = docs['mindProtocol'], docs['mindHandoff']
    md = pr['actual_metadata']
    require(md['cue_to_class_within_frozen_one_sample_target2s'] == 0 and md['unmatched_class_cues'] > md['cue3_count'],
            'MIND: the cue markers')
    require(md['header_reference'] == 'empty' and md['BIDS_reference'] == 'parietal reference', 'MIND: the reference')
    stated_tight(pr['unit_of_analysis'], 'README describes30participants', 'MIND: the README count')
    stated(hd, 'does not establish superiority over temporal, visual, movement-artifact, or other non-neural explanations',
           'MIND caveat')
    stated(hd, 'Raw preprocessing and raw numerical QC were source-reviewed and hash-bound, not independently recomputed.',
           'MIND caveat')
    return [
        {'id': 'stored-marker-windows',
         'text': 'Windows run from 1 to 9 seconds after each stored class marker. Most class markers have no cue marker '
                 'before them and no cue marker sits exactly 2 seconds before its class marker, so the windows do not '
                 'certify pure imagery.'},
        {'id': 'record-ids',
         'text': 'The unit is the record ID. The release describes 30 participants, and whether record IDs and people '
                 'match one to one was not reconciled, so no claim about people follows.'},
        {'id': 'other-explanations',
         'text': 'Pair 4/5 above the majority control does not exclude temporal, visual or movement explanations.'},
        {'id': 'offline-filtering',
         'text': 'Each run is filtered whole, offline and in both directions, so no response-time figure follows.'},
        {'id': 'sealed-epochs',
         'text': 'The independent replay starts from the sealed epochs; raw preprocessing and the numerical checks were '
                 'source-reviewed and bound by hash and were not recomputed.'},
        {'id': 'reference',
         'text': 'The headers leave the reference field empty while the BIDS sidecars describe a parietal reference; the '
                 'declared calibration and reference were kept as stored and were not verified physiologically.'},
        {'id': 'terms',
         'text': 'The paper and the archive’s dataset description state CC BY 4.0; the MOABB adapter and the ScienceDB '
                 'record page’s metadata state CC BY-NC 4.0. ScienceDB’s terms-of-use page was not read. Aggregate '
                 'values only; no data are redistributed.'},
        {'id': 'ethics', 'text': 'Ethics and consent are quoted from the paper, which names no committee and gives no '
                                 'approval number.'},
    ]


def sciencedb_record(raw):
    for m in re.finditer(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', raw, re.S):
        d = json.loads(m.group(1))
        if d.get('identifier') == f'https://doi.org/{MIND_DOI}':
            return d
    raise ValueError('MIND: no record metadata in the ScienceDB capture')


def mind_rights(docs, a2):
    s = a2['sources'][MIND]
    lic = s['licence']
    rec = lic['sciencedb_record']
    raw = docs['captures'][rec['capture_file']]
    ld = sciencedb_record(raw)
    require(ld['license'] == DEED_NC and ld['version'] == rec['record_version'] == '4.0.0'
            and rec['value'] == 'CC BY-NC 4.0', 'MIND: the record metadata states another licence or version')
    in_capture(rec['quote'], raw, 'MIND record licence')
    ecs = s['ethics_consent_source']
    receipt_ref_sha = sha((PROJECT / ecs['capture_file']).read_bytes())
    require(receipt_ref_sha == ecs['capture_sha256'] == lic['paper'].get('capture_sha256', ecs['capture_sha256']),
            'MIND: the intake receipt is not the one A2 quotes')
    receipt = json.dumps(docs['mindIntakeReceipt'], ensure_ascii=False)
    for q in (s['consent_quote'], s['ethics_quote'], lic['paper']['quote']):
        require(flat(q) in flat(receipt), 'MIND: a quotation is not in the intake receipt')
    require(lic['paper']['value'] == lic['archive_dataset_description']['value'] == 'CC BY 4.0'
            and lic['moabb_adapter']['value'] == 'CC BY-NC 4.0', 'MIND: the A2 licence statements')
    stated(docs['mindAdapter'], 'license="CC-BY-NC-4.0"', 'MIND: the MOABB adapter licence')
    stated_tight(docs['mindProtocol']['rights'], 'dataset_description declaresCCBY4.0', 'MIND: the archive licence')
    stated(docs['mindHandoff'], 'dataset description declares CC BY 4.0', 'MIND: the archive licence')
    require(docs['mindProtocol']['source']['publisher_checksum_verified'] is False
            and docs['mindProtocol']['scientific_limits_remain']['raw_redistribution'] == 'NOT_AUTHORIZED',
            'MIND: checksum and redistribution')
    title = ld['name'].replace('：', ': ')
    creators = [c['name'] for c in ld['creator']]
    stated(json.dumps(docs['mindIntakeReceipt']), 'A Multimodal fNIRS-EEG Dataset for Unilateral Limb Motor Imagery',
           'MIND: the paper title')
    attribution = (f'{names_and(creators)} · {title}, Science Data Bank, doi:{MIND_DOI}. Paper: {MIND_PAPER}. '
                   'Modifications: EEG only, filtered over each whole run, resampled and cut into stored-marker '
                   f'windows; no data redistributed. {ATTRIBUTION_END}')
    terms = {
        'statements': [
            {'source': 'paper', 'value': lic['paper']['value'], 'quote': lic['paper']['quote'],
             'read_from': lic['paper']['read_from'], 'read_in_this_release': False,
             'how_read': 'quoted from the research intake receipt of the paper page'},
            {'source': 'archive dataset description', 'value': lic['archive_dataset_description']['value'],
             'read_in_this_release': False,
             'how_read': 'as the research protocol records the dataset description inside the downloaded archive'},
            {'source': 'MOABB adapter', 'value': lic['moabb_adapter']['value'], 'read_in_this_release': False,
             'how_read': 'the licence field of the MOABB dataset adapter'},
            {'source': 'ScienceDB record page', 'value': rec['value'], 'url': ld['license'], 'quote': rec['quote'],
             'read_from': rec['read_from'], 'read_at': rec['captured_at'], 'capture_sha256': rec['capture_sha256'],
             'record_version': rec['record_version'], 'read_in_this_release': True,
             'how_read': 'the schema.org metadata the record page serves'},
        ],
        'terms_of_use_page_read': False,
        'aggregate_only': True, 'redistributed': False, 'publisher_checksum_verified': False,
    }
    privacy = ('The paper states that the study protocol was approved by an ethics committee it does not name, with no '
               'approval number, and that participants signed written informed consent. Published here: record-ID '
               'mean balanced accuracies, record-ID resampling ranges and aggregate counts; no per-record-ID value, '
               'identifier, prediction or signal.')
    rights = {
        'name': s['name'],
        'task': ('Four-class directional motor imagery of the right upper limb with EEG and fNIRS; here the EEG of '
                 'stored codes 4 versus 5 and 6 versus 7.'),
        'source': f'https://doi.org/{MIND_DOI}',
        'version': f'ScienceDB record {MIND_DOI}, record version {rec["record_version"]}',
        'licenses_stated': sorted({t['value'] for t in terms['statements']}),
        'attribution': attribution,
        'reviewedAt': rec['captured_at'][:10],
        'reviewBasis': [rec['read_from'], lic['paper']['read_from']],
        'privacyReview': privacy,
        'terms': terms,
    }
    e, c = s['ethics_committee_and_number'], s['consent']
    consent = {
        'ethics_approval': {'stated': True, 'quote': s['ethics_quote'], 'body': gap_or(e['committee']),
                            'approval_number': gap_or(e['number'])},
        'informed_consent': {'stated': c['stated'], 'kind': c['kind'], 'quote': s['consent_quote'],
                             'location': unversioned(c['location'])},
        'read_from': ecs['read_from'], 'read_section': 'participants paragraph', 'read_at': ecs['captured_at'],
        'quoted_from': 'the research intake receipt of the paper page', 'capture_sha256': ecs['capture_sha256'],
        'gaps': consent_gaps(s),
    }
    return rights, consent


def mind_case(docs, manifest, a2):
    mind_release(docs, manifest)
    primary, contrasts, secondary = mind_panels(docs)
    ag = docs['mindAggregate']
    rights, consent = mind_rights(docs, a2)
    return {
        'id': MIND, 'kind': 'conditional_worked_case', 'section': MIND, 'status': 'released_conditional', 'name': 'MIND',
        'question': MIND_QUESTION,
        'task': ('Stored class codes 4 versus 5 and 6 versus 7, each pair classified on its own, from the EEG of a '
                 'four-class motor-imagery release; the codes are as stored and are not verified imagery.'),
        'unit': 'record ID',
        'coverage': mind_design(docs),
        'primary': {
            'record_ids': ag['primary_record_IDs'], 'runs': ag['primary_runs'], 'trials': ag['primary_trials'],
            'folds_for_each_record_id': 3,
            'design': 'two whole runs train the pipeline and the third is held out, for each record ID and pair',
            'statistic': ('record-ID mean balanced accuracy: out-of-fold trials pooled within each record ID, then '
                          'record IDs weighted equally'),
            'pairs': primary,
        },
        'contrasts': contrasts,
        'resampling': mind_resampling(docs),
        'schedule': mind_schedule(docs),
        'secondary': {
            'record_ids': ag['secondary_record_IDs'], 'runs': ag['secondary_runs'], 'trials': ag['secondary_trials'],
            'design': 'one run trains the pipeline and the other is held out',
            'interval': None, 'pooled_with_primary': False,
            'pairs': secondary,
            'text': 'Reported apart with no interval and never pooled with the primary panel; its schedule composition '
                    'is not printed because with two record IDs it would show each one’s outcome.',
        },
        'processing': mind_processing(docs),
        'how_checked': mind_checked(docs),
        'caveats': mind_caveats(docs),
        'dataset_page': False,
        'rights': rights,
        'consent_and_ethics': consent,
    }


# ---------------------------------------------------------------------------- Damm (status case, D16 and D2)
DAMM_VARIANTS = {
    'primary_all62': ('primary', 'All 62 scalp channels, 1 to 5 seconds after the cue', True, 'all', 'primary'),
    'sensitivity_all62': ('window sensitivity', 'All 62 scalp channels over the full cue interval, 0 to 6 seconds',
                          True, 'all', 'sensitivity'),
    'precue_all62': ('precue control', 'All 62 scalp channels in the 2 seconds before the cue', True, 'all', 'precue'),
    'primary_central15': ('channel sensitivity', 'A fixed central subset of 15 channels, 1 to 5 seconds after the cue',
                          True, 'central', 'primary'),
    'order_index': ('order control', 'The trial index alone, with no signal input', False, None, None),
    'order_modulo5': ('order control', 'The trial index modulo five, with no signal input', False, None, None),
    'order_previous_delivered_cue': ('order control', 'The previous delivered cue, with no signal input: privileged '
                                     'context that no live system would have', False, None, None),
    'primary_all62_shuffle': ('shuffle sanity check', 'The primary features with the training labels shuffled once '
                              'with a fixed seed', True, 'all', 'primary'),
}


def damm_release(docs, manifest):
    src, wr = manifest['sources'], manifest['withheldReference']
    ra = docs['dammReleaseApproval']
    require(ra['status'] == 'PASS_INTERNAL_CONDITIONAL_PILOT_HANDOFF' and ra['handoff_sha256'] == src['dammHandoff']['sha256']
            and ra['interpretation_sha256'] == src['dammInterpretationReview']['sha256']
            and ra['numerical_audit_sha256'] == wr['dammAudit']['sha256'] and ra['publication_authorized'] is False,
            'Damm: the release approval binds other files')
    ir = docs['dammInterpretationReview']
    require(ir['decision'] == 'PASS_INTERPRETATION' and ir['audit_sha256'] == wr['dammAudit']['sha256']
            and ir['protocol_sha256'] == src['dammProtocol']['sha256'], 'Damm: the interpretation review')
    au = docs['dammAudit']
    require(au['status'].startswith('PASS_PRIVATE_NUMERICAL_AUDIT') and au['config_sha256'] == ir['config_sha256'],
            'Damm: the audit did not pass')
    require(docs['dammScopeAdjudication']['decision'] == 'PASS_CONDITIONAL_NEW_WITHIN_RANDOM_HELD_RUN_BRANCH'
            and docs['dammScopeAdjudication']['original_strict_sample_column_gate'] == 'HOLD_UNCHANGED',
            'Damm: the scope adjudication')


def damm_case(docs, manifest, a2):
    damm_release(docs, manifest)
    pr, au, qc, adj = docs['dammProtocol'], docs['dammAudit'], docs['dammIntakeQc'], docs['dammScopeAdjudication']
    sf = qc['scientific_schema_findings']
    runs = sorted({r for d in pr['directions'] for r in d})
    per_class = set(pr['class_counts_per_run'].values())
    require(len(per_class) == 1 and sum(pr['class_counts_per_run'].values()) == pr['cues_per_run']
            and len(pr['labels']) == len(pr['class_counts_per_run']), 'Damm: the classes are not balanced')
    require(au['trials'] == len(runs) * pr['cues_per_run'] and au['channels'] == len(pr['scalp_channels'])
            and au['variant_directions'] == len(pr['variants']) * len(pr['directions']), 'Damm: the audit counts otherwise')
    stated(docs['dammHandoff'], f'all {au["trials"]} delivered cues', 'Damm cues')
    require(sf['sampling_rate_hz_all'] == pr['sfreq'] and sf['n_samples_all'] == pr['expected_shape'][1]
            == sf['duration_s_all'] * pr['sfreq'] and sf['edf_channels_all'] == len(pr['scalp_channels'])
            + len(pr['excluded_channels']) and pr['excluded_channels'] == ['Ref1', 'Ref2', 'Marker'],
            'Damm: the file facts')
    ev = flat(adj['timing_basis']['evidence'])
    blocks = re.search(r'(\d+) state blocks; white/fixation(\d+) samples each; finger(\d+)', ev)
    require(blocks is not None and 'contiguous integer' in ev, 'Damm: the state blocks')
    stated_tight(docs['dammExecutionReview']['independently_verified'][2], f'{blocks.group(1)} blocks', 'Damm blocks')
    white = whole(int(blocks.group(2)) / pr['sfreq'], 'Damm white')
    finger = whole(int(blocks.group(3)) / pr['sfreq'], 'Damm finger')
    require(sf['actual_sample_column_present'] is False and pr['strict_sample_column_gate'] == 'HOLD_UNCHANGED',
            'Damm: the sample column')
    readme = docs['captures'][a2['sources'][DAMM]['licence']['readme']['capture_file']]
    m = re.search(r'This dataset contains EEG recordings from (\d+) participants', readme)
    require(m is not None, 'Damm: the README participant count')
    published = int(m.group(1))
    require(len(pr['central_channels']) == 15, 'Damm: the central subset')
    variants = []
    for vid in pr['variants']:
        role, name, signal, channels, window = DAMM_VARIANTS[vid]
        variants.append({'id': vid, 'role': role, 'name': name, 'signal_input': signal,
                         'channels': {'all': len(pr['scalp_channels']), 'central': len(pr['central_channels']),
                                      None: None}[channels],
                         'window_seconds': list(pr['windows_s'][window]) if window else None})
    require(len(variants) == 8 and pr['shuffle']['purpose'].startswith('sanity only'), 'Damm: the variants')
    stated(qc['aggregate_qc']['condition_order'], 'unresolved source counterbalancing contradiction', 'Damm order')
    stated(sf['annotation_independence'], 'Sequential event tables are one same-SHA source annotation object',
           'Damm sequential tables')
    rights, consent = damm_rights(docs, a2)
    hold = next(h for h in manifest['holds'] if h['case'] == DAMM)
    return {
        'id': DAMM, 'kind': 'status_case', 'section': DAMM, 'status': 'score_held', 'name': 'Damm finger motor imagery',
        'design': {
            'participants_run': 1, 'published_participants': published, 'runs_used': len(runs),
            'run_condition': 'random cue order', 'classes': len(pr['labels']),
            'class_names': ['thumb', 'index', 'middle', 'ring', 'little'],
            'delivered_cues': au['trials'], 'trials_per_held_out_run': pr['cues_per_run'],
            'trials_per_class_per_run': per_class.pop(), 'directions': len(pr['directions']),
            'evaluation': 'trained on one random-order run and tested on the other, in both directions',
            'pipeline': 'log band power from an 8–30 Hz filter on each epoch, with fixed shrinkage LDA fitted on the '
                        'training run only',
        },
        'files': {
            'edf_channels': sf['edf_channels_all'], 'scalp_channels': len(pr['scalp_channels']),
            'excluded_channels': list(pr['excluded_channels']), 'sampling_hz': pr['sfreq'],
            'run_seconds': sf['duration_s_all'], 'samples_per_run': sf['n_samples_all'],
            'state_blocks_per_run': int(blocks.group(1)), 'white_seconds': white, 'fixation_seconds': white,
            'cue_seconds': finger, 'sample_column_present': False, 'cue_samples_reconstructed': True,
            'edf_scaling_applied_once': True,
            'reference': 'linked mastoids as the source states; no second mastoid subtraction',
            'text': ('Each random-order run is 916 seconds of 65 EDF channels at 512 Hz: 62 scalp channels, two '
                     'reference channels and a marker channel. The event stream of each run holds 227 state blocks, '
                     'and every cue follows a 3-second white screen and a 3-second fixation cross and lasts 6 seconds. '
                     'The files carry no sample column, so cue samples are reconstructed from the stored onsets.'),
        },
        'variants': variants,
        'variant_directions_audited': au['variant_directions'],
        'flags': {'variants_fixed_before_scoring': True, 'all_variants_retained': True,
                  'independent_audit_passed': True, 'score_published': False, 'sequential_runs_evaluated': False,
                  'physical_trigger_timing_validated': False, 'additional_participant_acquired': False},
        'status_text': ('One participant’s two random-order runs, end to end: 150 delivered cues over five fingers, 75 '
                        'balanced trials in each held-out run, 62 scalp channels at 512 Hz, and 227 state blocks per run '
                        'checked against the fixed white, fixation and cue durations. A fixed log-bandpower and '
                        'shrinkage-LDA pipeline was trained on one run and tested on the other, in both directions; eight '
                        'variants and controls were fixed before scoring, and an independent audit rebuilt all 16 '
                        'reports.'),
        'held': {'id': hold['id'], 'what': 'every variant’s score in both directions', 'rule': 'one-person',
                 'decision': 'the owner’s decisions for this release, keeping the one-person rule'},
        'holds': [
            'Cue samples are reconstructed from the stored onsets; physical trigger timing is not validated.',
            'The EEG sidecars and the counterbalancing log disagree on which condition came first, so no order effect '
            'is inferred.',
            'The sequential-order runs were not evaluated: their two annotation tables are byte-identical copies of one '
            'file, and no transfer between the random and sequential orders was tested.',
            f'The other {published - 1} participants in the record are neither acquired nor evaluated.',
        ],
        'rights': rights,
        'consent_and_ethics': consent,
    }


def damm_rights(docs, a2):
    s = a2['sources'][DAMM]
    lic = s['licence']
    dd_raw = docs['captures'][lic['data']['capture_file']]
    dd = json.loads(dd_raw)
    require(dd['License'] == lic['data']['value'] == lic['openneuro_snapshot_licence'] == 'CC0', 'Damm: the licence')
    in_capture(lic['data']['quote'], dd_raw, 'Damm licence')
    in_capture(s['ethics_quote'], dd_raw, 'Damm ethics')
    in_capture(lic['readme']['quote'], docs['captures'][lic['readme']['capture_file']], 'Damm README')
    require(lic['license_file']['present'] is False and s['consent']['stated'] is False
            and {g['field'] for g in s['gaps']} == {'consent', 'licence.license_file'}, 'Damm: the A2 gaps')
    gq = json.loads(docs['captures'][s['capture_metadata']['openneuro_graphql']['capture_file']])['data']['dataset']
    tags = [x['tag'] for x in gq['snapshots']]
    snapshot = gq['latestSnapshot']['tag']
    require(snapshot == tags[-1] and dd['DatasetDOI'] == f'doi:10.18112/openneuro.ds008446.v{snapshot}'
            and s['dataset_record'] == f'https://doi.org/10.18112/openneuro.ds008446.v{snapshot}', 'Damm: the snapshot')
    authors = [first_last(a) for a in dd['Authors']]
    title = dd['Name'].strip()
    attribution = (f'{names_and(authors)} · {title}, OpenNeuro ds008446, doi:10.18112/openneuro.ds008446.v{snapshot}, '
                   f'{dd["License"]}. Funding: {"; ".join(dd["Funding"])}. Modifications: the first participant’s two '
                   'random-order runs only; no score from these data is published. ' + ATTRIBUTION_END)
    privacy = (f'Ethics: {s["ethics_committee_and_number"]["committee"]}, approval '
               f'{s["ethics_committee_and_number"]["number"]}. No consent statement was found in the dataset files or '
               'its metadata, and no paper is named. Published here: design, counts and file facts for one '
               'participant’s recordings and no score; no identifier, per-trial value or signal.')
    rights = {
        'name': s['name'],
        'task': 'Five-finger motor imagery cued in random and in sequential order; here the random-order runs only.',
        'source': s['dataset_record'],
        'version': 'OpenNeuro ds008446 at its latest snapshot, read at a pinned commit of its mirror',
        'pinned_snapshot': snapshot, 'pinned_commit': s['pinned_commit'],
        'license': dd['License'], 'licenseUrl': None, 'attribution': attribution,
        'reviewedAt': s['captured_at'][:10],
        'reviewBasis': [lic['data']['read_from'], lic['readme']['read_from']],
        'privacyReview': privacy,
        'terms': {
            'data_licence': {'value': lic['data']['value'], 'quote': lic['data']['quote'],
                             'stated_by': lic['data']['stated_by'], 'read_from': lic['data']['read_from'],
                             'read_at': lic['data']['captured_at'], 'capture_sha256': lic['data']['capture_sha256']},
            'readme': {'quote': lic['readme']['quote'], 'read_from': lic['readme']['read_from'],
                       'read_at': lic['readme']['captured_at'], 'capture_sha256': lic['readme']['capture_sha256']},
            'license_file_present': False,
            'license_file_note': ('The README cites a LICENSE file that the tree at the pinned commit does not '
                                  'hold; the only licence statement is CC0 in dataset_description.json.'),
        },
    }
    return rights, consent_block(s, 'Damm')


# ---------------------------------------------------------------------------- NeBULA (status case, D16 and D2)
NEBULA_EEG_ARMS = (
    ('primary', 'EEG, all 127 channels, 0 to 2 seconds after the Go cue', True),
    ('precue', 'EEG, all 127 channels, the 500 milliseconds before the Go cue', True),
    ('central', 'EEG, a fixed set of central channels, 0 to 2 seconds after the Go cue', True),
    ('order', 'Order diagnostic: trial position and the previous delivered target, with no signal input; privileged '
              'context that no live system would have', False),
    ('shuffle', 'The primary EEG features with the training labels shuffled once with a fixed seed', True),
)
NEBULA_EMG_ARMS = (
    ('emg', 'EMG, 11 rows, 0 to 2 seconds after the Go cue', True),
    ('fusion', 'The 127 EEG features and the 11 EMG features concatenated in a fixed order', True),
    ('emg_precue', 'EMG, the 500 milliseconds before the Go cue', True),
    ('emg_shuffle', 'The EMG features with the training labels shuffled once', True),
    ('fusion_shuffle', 'The concatenated features with the same shuffled training labels', True),
)


def nebula_release(docs, manifest):
    src, wr = manifest['sources'], manifest['withheldReference']
    ra = docs['nebulaEegReleaseApproval']
    require(ra['status'] == 'PASS_INTERNAL_CONDITIONAL_PILOT_HANDOFF'
            and ra['handoff_sha256'] == src['nebulaEegHandoff']['sha256']
            and ra['interpretation_review_sha256'] == src['nebulaEegInterpretationReview']['sha256']
            and ra['independent_audit_sha256'] == wr['nebulaEegAudit']['sha256'] and ra['publication_authorized'] is False
            and ra['original_failure_preserved'] is True and ra['budget_reset'] is False,
            'NeBULA: the EEG release approval binds other files')
    ir = docs['nebulaEegInterpretationReview']
    require(ir['decision'] == 'PASS_INTERPRETATION' and ir['audit_receipt_sha256'] == wr['nebulaEegAudit']['sha256']
            and ir['recovery_adjudication_sha256'] == src['nebulaBoundaryAdjudication']['sha256'],
            'NeBULA: the EEG interpretation review')
    ea = docs['nebulaEmgIntakeReleaseApproval']
    require(ea['status'] == 'PASS_STRUCTURAL_AND_STORED_INDEX_INTAKE_HANDOFF'
            and ea['handoff_sha256'] == src['nebulaEmgIntakeHandoff']['sha256']
            and ea['native_receipt_sha256'] == src['nebulaEmgReceipt']['sha256']
            and ea['independent_admission_sha256'] == src['nebulaEmgAdmission']['sha256']
            and ea['interpretation_review_sha256'] == src['nebulaEmgIntakeInterpretationReview']['sha256']
            and ea['physical_calibration_or_sync_verified'] is False and ea['publication_authorized'] is False,
            'NeBULA: the EMG intake release approval binds other files')
    pr = docs['nebulaEmgPilotReleaseReceipt']
    require(pr['status'] == 'INDEPENDENT_NUMERICAL_AND_INTERPRETATION_PASS'
            and pr['handoff_sha256'] == src['nebulaEmgPilotHandoff']['sha256']
            and pr['interpretation_review_sha256'] == src['nebulaEmgPilotInterpretationReview']['sha256']
            and pr['aggregate_sha256'] == wr['nebulaEmgPilotAggregate']['sha256'] and pr['website_edited'] is False,
            'NeBULA: the EMG pilot release receipt binds other files')
    pi = docs['nebulaEmgPilotInterpretationReview']
    require(pi['decision'] == 'PASS_INTERNAL_AGGREGATE_HANDOFF_INTERPRETATION' and pi['blockers'] == []
            and pi['reviewed_hashes']['Frozen Scientific Protocol.json'] == src['nebulaEmgPilotProtocol']['sha256']
            and pi['aggregate_sha256'] == wr['nebulaEmgPilotAggregate']['sha256'], 'NeBULA: the EMG pilot review')
    require(docs['nebulaBoundaryAdjudication']['evidence']['aggregate_sha256'] == src['nebulaBoundaryAggregate']['sha256'],
            'NeBULA: the boundary adjudication reads another aggregate')
    require(docs['nebulaEegAudit']['status'].startswith('PASS_PRIVATE_NUMERICAL_AUDIT')
            and docs['nebulaEmgPilotAggregate']['independent_audit']['status'] == 'PASS', 'NeBULA: an audit did not pass')


def nebula_file_facts(docs):
    bd, adj, rc, ad = (docs['nebulaBoundaryAggregate'], docs['nebulaBoundaryAdjudication'], docs['nebulaEmgReceipt'],
                       docs['nebulaEmgAdmission'])
    eeg = {re.search(r'task-(\w+)_eeg', r['marker']).group(1): r for r in bd['runs']}
    require(sorted(eeg) == sorted(CONDITIONS) and sorted(rc['conditions']) == sorted(CONDITIONS), 'NeBULA: the runs')
    ties = {c: eeg[c]['equal'] for c in CONDITIONS}
    require(ties == ad['admitted']['boundary_ties'] == {c: rc['conditions'][c]['events']['boundary_ties'] for c in CONDITIONS}
            and sorted(ties.values()) == sorted(adj['evidence']['ties']) and all(eeg[c]['negative'] == 0 for c in CONDITIONS),
            'NeBULA: the boundary ties')
    rows = {rc['conditions'][c]['structure']['rows'] for c in CONDITIONS}
    require(rows == {11} and docs['nebulaEmgMetadata']['channels_tsv']['rows'] == 11, 'NeBULA: the EMG rows')
    meta = {v['EMGChannelCount'] for v in docs['nebulaEmgMetadata']['emg'].values()}
    require(meta == {16}, 'NeBULA: the EMG metadata channel count')
    markers = sum(rc['conditions'][c]['events']['rows'] for c in CONDITIONS)
    quartets = sum(rc['conditions'][c]['events']['quartets'] for c in CONDITIONS)
    require(markers == 4 * quartets and all(rc['conditions'][c]['stored_marker_match'] == 'EXACT' for c in CONDITIONS),
            'NeBULA: the stored markers')
    equal = all(rc['conditions'][c]['structure']['columns'] == eeg[c]['n_samples_from_ZIP_size_only'] for c in CONDITIONS)
    require(equal, 'NeBULA: the EMG and EEG sample lengths differ')
    require(adj['decision'].startswith('PASS_NARROW_BOUNDARY_TIE_CORRECTION'), 'NeBULA: the parser fix review')
    stated_tight(docs['nebulaEegInterpretationReview']['checks']['recovery_history'], '<to<= correction',
                 'NeBULA: the parser fix')
    stated(docs['nebulaEegHandoff'], 'The first attempt stopped before QA completion, features, models or scores',
           'NeBULA: the first attempt')
    stated(docs['nebulaEmgIntakeHandoff'], 'The original JSON16 fields were not rewritten.', 'NeBULA: JSON16')
    stated(docs['nebulaEmgPilotProtocol']['fixed_signal_contract']['anatomy'], 'anatomical mapping unverified',
           'NeBULA: EMG anatomy')
    return {
        'boundary_ties': sum(ties.values()), 'boundary_ties_by_condition': ties, 'backward_overlaps': 0,
        'first_parse_stopped_before_features': True, 'parser_fix_reviewed': True,
        'rerun_within_original_budget': True,
        'emg_channel_rows': rows.pop(), 'emg_channels_in_metadata': meta.pop(), 'emg_rows_relabelled': False,
        'stored_markers': markers, 'complete_quartets': quartets, 'markers_match_eeg_files': True,
        'emg_eeg_sample_lengths_equal': equal,
        'text': [
            'The original markers hold 25 boundary ties where one trial’s end and the next trial’s start share a '
            'sample (7 free, 9 low, 9 high), with no backward overlap. The first parse stopped on them before any '
            'feature, model or score; a reviewed fix that accepts a shared boundary reran within the original budget.',
            'The EMG files hold 11 channel rows where their metadata states 16; the rows were not relabelled or mapped '
            'to muscles.',
            'All 356 stored markers of the 89 trials match the EEG marker files in label, order and sample position.',
            'The EMG and EEG files of each run have equal sample lengths.',
        ],
    }


def nebula_case(docs, manifest, a2):
    nebula_release(docs, manifest)
    au, qc, ep = docs['nebulaEegAudit'], docs['nebulaIntakeQc'], docs['nebulaEmgPilotProtocol']
    sf = qc['scientific_schema_findings']
    split = ep['population_and_splits']
    by_condition = {c: split['conditions'][c] for c in CONDITIONS}
    require(sum(by_condition.values()) == split['trials'] == au['trials'] == sf['marker_totals']['StartTrial']
            and split['fold_order'] == list(CONDITIONS) and len(split['targets']) == 3, 'NeBULA: the design')
    require(au['channels'] == sf['channels_all'] == 127 and sf['sampling_rate_hz_all'] == 1000, 'NeBULA: the EEG files')
    prot = docs['nebulaEegProtocol']
    w = re.search(r'Main epoch half-open \[(\d+),(\d+)\)s; precue \[(-?\.?\d+),(\d+)\)s', prot)
    b = re.search(r'Butterworth(\d+)–(\d+)Hz', prot)
    require(w is not None and b is not None and 'Five frozen models/fold' in prot, 'NeBULA: the EEG protocol')
    main_ms = [whole(1000 * float(w.group(1)), 'main'), whole(1000 * float(w.group(2)), 'main')]
    pre_ms = [whole(1000 * float(w.group(3)), 'precue'), whole(1000 * float(w.group(4)), 'precue')]
    require(au['heldout_fits'] == len(NEBULA_EEG_ARMS) * len(CONDITIONS), 'NeBULA: the EEG fits')
    fc = ep['fixed_signal_contract']
    eb = re.search(r'butter\(4,\[(\d+),(\d+)\]', ep['fixed_features']['filter'])
    require(eb is not None and fc['rows'] == 11 and fc['main_half_open_samples'] == [0, 2000]
            and fc['precue_half_open_samples'] == [-500, 0] and fc['sampling_rate_hz'].startswith('1000'),
            'NeBULA: the EMG contract')
    require(len(ep['arms']) == len(NEBULA_EMG_ARMS) and ep['learner']['max_fits'] == len(NEBULA_EMG_ARMS) * len(CONDITIONS)
            and ep['learner']['no_other_models'] is True, 'NeBULA: the EMG arms')
    stated(ep['fixed_features']['fusion'], 'concatenate sealed existing 127 EEG main features', 'NeBULA: fusion')
    stated(ep['fixed_features']['prohibited'], 'EEG recomputation', 'NeBULA: no EEG recompute')
    participants = nebula_participants(docs, a2)
    stated(docs['nebulaEegHandoff'], 'No nominal 90th trial is fabricated.', 'NeBULA: no fabricated trial')
    rights, consent = nebula_rights(docs, a2)
    hold = next(h for h in manifest['holds'] if h['case'] == NEBULA)
    return {
        'id': NEBULA, 'kind': 'status_case', 'section': NEBULA, 'status': 'score_held', 'name': 'NeBULA',
        'design': {
            'participants_run': 1, 'participant_counts': participants, 'targets': len(split['targets']),
            'assistance_conditions': list(CONDITIONS), 'trials': split['trials'], 'trials_by_condition': by_condition,
            'missing_trial_fabricated': False, 'folds': len(CONDITIONS),
            'evaluation': 'trained on two assistance runs and tested on the third; the assistance level is the '
                          'held-out run and the target is the class',
            'task_line': 'The source describes executed reaching with an upper-limb exoskeleton; the open register keeps '
                         'MOABB’s imagery label as MOABB lists it.',
        },
        'eeg': {'channels': au['channels'], 'sampling_hz': sf['sampling_rate_hz_all'], 'window_ms': main_ms,
                'precue_window_ms': pre_ms, 'band_hz': [int(b.group(1)), int(b.group(2))],
                'reference': 'FCz as the paper states; the header reference fields are blank, and the data keep the delivered '
                             'reference'},
        'emg': {'rows': fc['rows'], 'sampling_hz': 1000, 'window_ms': list(fc['main_half_open_samples']),
                'precue_window_ms': list(fc['precue_half_open_samples']),
                'band_hz': [int(eb.group(1)), int(eb.group(2))],
                'units': '1,000 Hz and microvolts as the source declares'},
        'arms': {
            'eeg': [{'id': i, 'name': n, 'signal_input': s} for i, n, s in NEBULA_EEG_ARMS],
            'eeg_fits': au['heldout_fits'],
            'emg_and_fusion': [{'id': i, 'name': n, 'signal_input': s} for i, n, s in NEBULA_EMG_ARMS],
            'emg_and_fusion_fits': ep['learner']['max_fits'],
            'pretrained_model': False, 'eeg_features_recomputed_for_fusion': False,
            'independently_audited': True,
        },
        'file_facts': nebula_file_facts(docs),
        'flags': {'score_published': False, 'order_diagnostic_comparison_published': False,
                  'additional_participant_acquired': False, 'physical_synchronisation_verified': False,
                  'amplitude_calibration_verified': False},
        'status_text': ('One participant reaching to three targets under free, low and high assistance: 89 delivered '
                        'trials (29, 30 and 30), 127 EEG channels at 1,000 Hz. The EEG pilot was trained on two '
                        'assistance runs and tested on the third, beside an order diagnostic with no signal input, a '
                        'precue window and a label shuffle. EMG and EEG plus EMG arms (15 new fits, no pretrained model) '
                        'were run on the same trials. An independent audit rebuilt every arm.'),
        'held': {'id': hold['id'], 'what': 'every EEG, EMG and EEG plus EMG score, and every control', 'rule': 'one-person',
                 'decision': 'the owner’s decisions for this release, keeping the one-person rule'},
        'holds': [
            'Go is a cue and the reach marker marks reaching the target; neither certifies physical movement onset.',
            'Stored marker agreement between the EEG and EMG files does not certify clock synchronisation or amplitude '
            'calibration.',
            # The reference is stated once, in eeg.reference; the participant counts once, in design.participant_counts.
            'The other participants’ files in the record are neither acquired nor evaluated.',
        ],
        'rights': rights,
        'consent_and_ethics': consent,
    }


def strip_html(text):
    return flat(html.unescape(re.sub(r'<[^>]+>', ' ', text)))


def participant_archives(files):
    return sorted(f['name'] for f in files if re.fullmatch(r'sub-\d+\.zip', f['name']))


def nebula_participants(docs, a2):
    """The participant count as each source states it, in one field: the paper and the Figshare record's description,
    the participant archives the record's files hold (the research intake's file manifest and A2's capture of the
    same record agree), and MOABB's catalogue."""
    lic = a2['sources'][NEBULA]['licence']['data']
    record = json.loads(docs['captures'][lic['capture_file']])
    m = re.search(r'Data were collected from (\d+) healthy participants', strip_html(record['description']))
    require(m is not None, 'NeBULA: the record description’s participant count')
    stated_count = int(m.group(1))
    paper = visible(docs['captures'][a2['sources'][NEBULA]['capture_file']])
    stated(paper, f'We enlisted {stated_count} healthy participants', 'NeBULA: the paper’s participant count')
    stated(paper, f'Data were collected from {stated_count} healthy participants', 'NeBULA: the paper’s participant count')
    intake = json.loads(docs['nebulaFileManifest'])
    require(intake['doi'] == record['doi'] == NEBULA_DOI and intake['version'] == record['version'],
            'NeBULA: the research file manifest is another record')
    archives = participant_archives(record['files'])
    require(archives == participant_archives(intake['files'])
            and {f['id'] for f in record['files']} == {f['id'] for f in intake['files']},
            'NeBULA: the research file manifest and the A2 capture list other files')
    require(0 < len(archives) <= stated_count, 'NeBULA: the participant archives')
    rows = [e for e in docs['moabbCatalog']['entries'] if e['Dataset'] == 'NeBULA2025']
    require(len(rows) == 1 and rows[0]['DOI'] == f'https://doi.org/{NEBULA_PAPER_DOI}', 'NeBULA: the MOABB catalogue row')
    moabb = int(rows[0]['#Subj'])
    return {
        'paper_and_record_description': stated_count,
        'participant_archives_in_record': len(archives),
        'moabb_catalog': moabb,
        'text': (f'The paper and the Figshare record’s description state {stated_count} participants; the record’s '
                 f'files hold {len(archives)} participant archives, and MOABB lists {moabb}.'),
    }


def nebula_rights(docs, a2):
    s = a2['sources'][NEBULA]
    lic = s['licence']
    record, versions = figshare(docs, lic['data'], NEBULA_DOI, 'NeBULA')
    require(record['license']['name'] == lic['data']['as_named_by_figshare'] == 'CC BY', 'NeBULA: the licence name')
    require(s['paper'] == f'https://doi.org/{NEBULA_PAPER_DOI}' and record['resource_doi'] == NEBULA_PAPER_DOI,
            'NeBULA: the record supplements another paper')
    paper_raw = docs['captures'][s['capture_file']]
    paper = paper_meta(paper_raw, NEBULA_PAPER_DOI, 'NeBULA')
    for q in (s['consent_quote'], s['consent']['second_quote'], s['ethics_quote'], lic['paper']['quote'],
              lic['paper_data_records_quote']):
        in_capture(q, paper_raw, 'NeBULA')
    z = lic['zenodo_13627307']
    require(z['resolves'] is False and z['terms'] == 'gap' and all(ev['http_status'] == 404 for ev in z['evidence']),
            'NeBULA: the Zenodo record')
    creators = [a['full_name'] for a in record['authors']]
    e = s['ethics_committee_and_number']
    attribution = (f'{names_and(creators)} · {record["title"]}, figshare, doi:{NEBULA_DOI}, CC BY 4.0. Paper: '
                   f'{names_and(paper["authors"])}, {paper["title"]}, {paper["journal"]} {paper["volume"]}:'
                   f'{paper["article"]} ({paper["year"]}), doi:{NEBULA_PAPER_DOI}. Modifications: the first '
                   'participant’s files only; no score from these data is published. ' + ATTRIBUTION_END)
    privacy = (f'Ethics: {e["committee"]}, approval {e["number"]} (database id {e["database_id"]}). Consent: '
               f'{s["consent"]["kind"]}. Published here: design, counts and file facts for one participant’s '
               'recordings and no score; no identifier, per-trial value or signal.')
    rights = {
        'name': s['name'],
        'task': 'Reaching to three targets with an upper-limb exoskeleton under free, low and high assistance, with '
                'EEG and EMG.',
        'source': f'https://doi.org/{NEBULA_DOI}',
        'version': (f'Figshare record 27301629, version {record["version"]}, the only version the record lists'
                    if len(versions) == 1 else f'Figshare record 27301629, version {record["version"]}'),
        'license': lic['data']['value'], 'licenseUrl': DEED, 'attribution': attribution,
        'reviewedAt': lic['data']['captured_at'][:10],
        'reviewBasis': [lic['data']['read_from'], s['read_from']],
        'privacyReview': privacy,
        'terms': {
            'data_licence': {**data_licence(lic['data'], record, versions),
                             'as_named_by_figshare': lic['data']['as_named_by_figshare']},
            'paper_licence': {'value': lic['paper']['value'], 'quote': lic['paper']['quote'],
                              'covers': lic['paper']['covers']},
            'repository_quote': lic['paper_data_records_quote'],
            'zenodo_13627307': {
                'named_by': 'the dataset description inside the data files',
                'registered_public_record': False, 'terms': None,
                'text': 'The files’ own dataset description names Zenodo 13627307, which is no registered public '
                        'record: the Zenodo API, the record page, DataCite and doi.org each return 404. The paper names '
                        'Figshare alone.',
            },
        },
    }
    consent = consent_block(s, 'NeBULA')
    consent['informed_consent']['second_quote'] = s['consent']['second_quote']
    consent['ethics_approval']['database_id'] = e['database_id']
    return rights, consent


# ---------------------------------------------------------------------------- the boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            if here.startswith(tuple(f'$.{c}' for c in HELD_CASES)):
                require(not any(f in k.lower() for f in HELD_SCORE_KEY_FRAGMENTS), f'held-score field in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def malformed(text):
    """In prose, a word that has lost its space against a number (the handoffs' “All40 participants”)."""
    if not re.search(r'\s', text):
        return None
    for token in text.split():
        t = re.sub(r"['’]s$", '', token.strip('.,;:()[]“”"‘’\''))
        if ('/' in t or ':' in t or t.startswith('10.') or HEX.fullmatch(t) or t.startswith('http')
                or DATASET_ID.fullmatch(t)):
            continue
        if re.search(r'[a-z]{3,}\d|\d[a-z]{3,}', t):
            return t
    return None


def prose_check(payload, private):
    for trail, text in strings(payload):
        require(not LOCAL_ROOTS.search(text), f'private path in export: {trail}')
        require(not SOURCE_IDS.search(text), f'source file or participant identifier in export: {trail}')
        require(not OUT_OF_FILE.search(text), f'{trail}: register-only, conference or submission content')
        require(not FIFTY_FIVE.search(text), f'{trail}: the commenter’s figure')
        for n in private:
            require(not re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.IGNORECASE),
                    f'private host or storage name in export: {trail}')
        require('jev' not in text.lower(), f'{trail}: Jev is not part of this release')
        if trail in ('$.schema_version', '$.release_id') or text.startswith(('http', '/')) or HEX.fullmatch(text):
            continue
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):    # the release record is dated by design (/releases/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if QUOTED.search(trail) or trail.startswith('$.provenance') or re.search(r'\.gaps\[\d+\]\.note$', trail):
            continue
        bad = malformed(text)
        require(bad is None, f'{trail}: a string that has lost its spaces ({bad!r})')
        require(not HEDGE.search(text) or KIM_SEALING.fullmatch(text), f'{trail}: an “X, not Y” hedge: {text!r}')
        if trail.startswith('$.release_record'):
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if sentence.rstrip().endswith('?'):
                continue          # a question asserts nothing
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: a claim these results do not support: {sentence!r}')


def held_texts(payload):
    """Every string about the Damm and NeBULA cases: the cases themselves, their release holds and release-record
    lines."""
    for case in HELD_CASES:
        yield from strings(payload[case], f'$.{case}')
        for i, h in enumerate(payload.get('holds', [])):
            if h.get('case') == case:
                yield from strings(h, f'$.holds[{i}]')
        if case in payload.get('release_record', {}):
            yield f'$.release_record.{case}', payload['release_record'][case]


def held_cases_have_no_score(payload, docs):
    """No fraction, percentage or held value anywhere in the Damm and NeBULA cases, by type, key, value or text; and no
    comparison of a held score, with or without a number."""
    held_floats = held_values(docs)
    for case in HELD_CASES:
        for trail, v in leaves(payload[case], f'$.{case}'):
            require(not isinstance(v, float), f'{trail}: a fraction in a one-person case')
            if isinstance(v, str) and not trail.endswith(('.attribution', '.source', '.read_from', 'capture_sha256',
                                                           '.reviewBasis[0]', '.reviewBasis[1]', '.pinned_commit')):
                require(not SCORE_TEXT.search(v), f'{trail}: a score-like figure in a one-person case')
    for trail, v in held_texts(payload):
        m = COMPARISON.search(v)
        require(m is None, f'{trail}: a comparison word in a one-person case ({m and m.group(0)!r})')
    body = json.dumps(payload, ensure_ascii=False)
    for v in held_floats:
        require(f'{100 * v:.2f}' not in body and (len(repr(v)) <= 6 or repr(v) not in body),
                f'a held score reached the export: {v!r}')
    require(not set(held_floats) & set(floats(payload)), 'a held score reached the export')


def stated_once(payload):
    """Statements a page may print together are each in one field: the one-person reasoning (the lead sentence only;
    the hold reasons name the rule), Kim's sealing limit, Kim's pre-score checks, NeBULA's reference and MIND's
    secondary panel being reported apart."""
    texts = list(strings(payload))
    person = [t for t, s in texts if THAT_PERSON.search(s)]
    require(person == ['$.one_person.sentence'], f'the one-person reasoning is stated outside the lead sentence: {person}')
    sealing = [t for t, s in texts if KIM_SEALING.fullmatch(s)]
    require(sealing == [f'$.{KIM}.how_checked[2].text'], 'Kim’s sealing sentence is not stated once')
    for word, case, where in (('process separation', KIM, [f'$.{KIM}.how_checked[2].text']),
                              ('blinded', None, [f'$.{KIM}.how_checked[2].text']),
                              ('finite-value', KIM, [f'$.{KIM}.how_checked[1].text']),
                              ('FCz', NEBULA, [f'$.{NEBULA}.eeg.reference']),
                              ('never pooled', MIND, [f'$.{MIND}.secondary.text']),
                              ('reported apart', MIND, [f'$.{MIND}.secondary.text']),
                              ('terms-of-use page', MIND, [f'$.{MIND}.caveats[6].text'])):
        found = [t for t, s in texts if word.lower() in s.lower() and (case is None or t.startswith(f'$.{case}.'))]
        require(found == where, f'{word!r} is stated in {found}, not once in {where}')


def held_values(docs):
    """Every Damm and NeBULA score the withheld records hold."""
    fl = set()
    for s in docs['dammAudit']['scores'].values():
        fl |= {s['accuracy'], s['balanced_accuracy']}
    for arm in docs['nebulaEegAudit']['scores'].values():
        fl.add(arm['descriptive_macro_balanced_accuracy'])
        for f in arm['folds']:
            fl |= {f['accuracy'], f['balanced_accuracy']}
    fl |= set(floats(docs['nebulaEmgPilotAggregate']['descriptive_scores']))
    return sorted(fl - TRIVIAL)


def withheld_values(docs):
    """Figures the sources hold that this release does not publish: held scores, pooled metrics, confusion counts,
    secondary differences, schema ranges, fixture identities and accounting."""
    fl, it = set(held_values(docs)), set()
    ag = docs['mindAggregate']
    published_means = {v for p in ag['metrics'].values() for m in p.values()
                       for v in m['mean_record_ID_balanced_accuracy'].values()}
    for panel in ag['metrics'].values():
        for m in panel.values():
            for arm in m['pooled_metrics'].values():
                fl |= {arm['accuracy'], arm['balanced_accuracy'], arm['macro_F1']}
    fl |= set(ag['metrics']['secondary']['4_5']['mean_paired_ID_differences'].values())
    fl -= published_means
    fl |= set(floats(ag['resource_accounting']))
    fl |= {docs['dammAudit']['audit_cpu_s'], docs['dammAudit']['audit_wall_s'], docs['dammAudit']['original_wall_charged_s']}
    # Confusion cells and paired counts cannot be told apart by value from published counts (one MIND cell is 150, the
    # Damm cue count); those keys are refused by name and the held text by pattern. By value: the distinctive counts.
    md = docs['mindProtocol']['actual_metadata']
    it |= set(md['two_noncanonical_run_event_counts']) | {md['cue3_count'], md['unmatched_class_cues']}
    it |= set(ints(docs['mindWorkflowClosure']['true_data_model_fit_calls']))
    it |= {ag['counts']['prepare']['EEG_bytes_extracted'], ag['counts']['prepare']['marker_bytes_read'],
           ag['resource_accounting']['peak_monitored_aggregate_RSS_bytes']}
    it |= {arm['n'] for p in ag['metrics'].values() for m in p.values() for arm in m['pooled_metrics'].values()}
    it -= {ag['secondary_trials'] // 2}           # the secondary pooled n is half its published trial count
    ka = docs['kimAggregate']
    fl |= {ka['elapsed_seconds'], ka['execution_receipt']['wall_seconds'], ka['execution_receipt']['CPU_seconds']}
    sq = docs['kimSchema']['qc']
    fl |= {sq['stored_value_min'], sq['stored_value_max'], sq['channel_epoch_DC_mean_min_stored_units'],
           sq['channel_epoch_DC_mean_max_stored_units']}
    it |= {docs['kimAssetManifest']['total_bytes'], docs['kimSchema']['sample_count'], sq['adjacent_equal_sample_pairs']}
    return fl - TRIVIAL, it


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    owner_decisions(manifest)
    docs = load(manifest)
    a2 = docs['consent']
    require(a2['package'] == 'A2' and a2['release_freeze'] == RELEASE_ID.rsplit('-', 1)[1], 'another consent record')
    kim = kim_case(docs, manifest, a2)
    mind = mind_case(docs, manifest, a2)
    damm = damm_case(docs, manifest, a2)
    nebula = nebula_case(docs, manifest, a2)
    require('With one person every score is that person’s' in docs['released']['eldbeta_status_text'],
            'the eldBETA case no longer carries the one-person sentence the lead takes over')
    rr, src = manifest['releaseRecord'], manifest['sources']
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['release_date'],
        'status': 'aggregate_preview',
        'title': 'Dataset checks',
        'question': QUESTION,
        'placement': {'page': '/topics/data-quality/', 'group': 'reliability', 'sections': list(SECTIONS),
                      'page_order': list(PAGE_ORDER), 'one_person_lead_before': 'eldbeta',
                      'leaderboard': False, 'core_matrix': False, 'dataset_pages': {KIM: KIM_DATASET_PAGE}},
        'one_person': {'sentence': ONE_PERSON_SENTENCE, 'cases': list(ONE_PERSON_CASES),
                       'decision': 'the owner’s decisions for this release, keeping the one-person rule'},
        'metric_units': ('accuracies, balanced accuracies, chance, differences and the bounds of intervals and ranges '
                         'are proportions in [0,1]; percentiles are in percent; frequencies in Hz; counts of '
                         'participants, record IDs, runs, trials, files, channels, markers and fits are whole numbers; '
                         'null means not stated, never zero'),
        'scope': ('Four public EEG datasets read from their files: Kim beta-range as a worked case with a training-free '
                  'CCA baseline on all 40 participants, MIND as a conditional case on record IDs with its controls and '
                  'label schedule, and Damm and NeBULA as one-person status cases with no score. Outside every '
                  'leaderboard and the core matrix.'),
        'cases': [{'id': KIM, 'kind': 'worked_case', 'status': 'released'},
                  {'id': MIND, 'kind': 'conditional_worked_case', 'status': 'released_conditional'},
                  {'id': DAMM, 'kind': 'status_case', 'status': 'score_held'},
                  {'id': NEBULA, 'kind': 'status_case', 'status': 'score_held'}],
        KIM: kim,
        MIND: mind,
        DAMM: damm,
        NEBULA: nebula,
        'holds': [dict(h) for h in manifest['holds']],
        'not_published': manifest['notPublished'],
        'release_record': {'date': rr['date'], 'decided': manifest['reviewed_at'], 'decision': rr['decision'],
                           KIM: rr['kim'], MIND: rr['mind'], DAMM: rr['damm'], NEBULA: rr['nebula'],
                           'placement': rr['placement']},
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {KIM: src['kimAggregate']['sha256'], MIND: src['mindAggregate']['sha256']},
            'release_approval_sha256': {
                KIM: src['kimReleaseApproval']['sha256'], MIND: src['mindInterpretationReview']['sha256'],
                DAMM: src['dammReleaseApproval']['sha256'], 'nebula_eeg': src['nebulaEegReleaseApproval']['sha256'],
                'nebula_emg_intake': src['nebulaEmgIntakeReleaseApproval']['sha256'],
                'nebula_emg_pilot': src['nebulaEmgPilotReleaseReceipt']['sha256']},
            'protocol_sha256': {KIM: src['kimProtocol']['sha256'], MIND: src['mindProtocol']['sha256'],
                                DAMM: src['dammProtocol']['sha256'], 'nebula_eeg': src['nebulaEegProtocol']['sha256'],
                                'nebula_emg_pilot': src['nebulaEmgPilotProtocol']['sha256']},
            'evidence_sha256': {'consent_statements': manifest['consent']['statements']['sha256'],
                                'kim_asset_manifest': src['kimAssetManifest']['sha256'],
                                'mind_schedule_structure': src['mindScheduleStructure']['sha256'],
                                'mind_workflow_closure': src['mindWorkflowClosure']['sha256'],
                                'nebula_emg_structure_receipt': src['nebulaEmgReceipt']['sha256']},
            'released_files_unchanged': ['data-quality-update.json'],
            'released_file_sha256': {'data-quality-update.json': docs['released']['data-quality-update.json']},
            'holds': [h['id'] for h in manifest['holds']],
        },
    }
    require([h['case'] for h in payload['holds']] == [KIM, DAMM, NEBULA]
            and [h['id'] for h in payload['holds']] == ['kim-amplitude-dependent-models', 'damm-one-participant-score',
                                                        'nebula-one-participant-scores'], 'the holds changed')
    # The hold reasons are lines of the /releases/ holds table: short, self-contained, one sentence each.
    for h in payload['holds']:
        require(len(h['reason']) <= 160 and h['reason'].endswith('.') and h['reason'].count('. ') == 0,
                f'hold {h["id"]}: the reason is not one short sentence')
    for h in payload['holds'][1:]:
        require(h['reason'].startswith('One participant; ') and h['reason'].endswith('under the site’s one-person rule.'),
                f'hold {h["id"]}: the reason does not name the one-person rule')
    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 4, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    held_cases_have_no_score(payload, docs)
    stated_once(payload)
    require('census' not in json.dumps(payload['mind2026']['secondary']).lower()
            and 'schedule' not in json.dumps(list(payload['mind2026']['secondary'])), 'the secondary schedule census')
    validate_public(payload)
    fl, it = withheld_values(docs)
    require(not (fl & set(floats(payload))), f'a withheld value reached the export: {sorted(fl & set(floats(payload)))[:3]}')
    require(not (it & set(ints(payload))), f'a withheld count reached the export: {sorted(it & set(ints(payload)))[:3]}')
    require(not any(number(v) and v in (55, 0.55) for _, v in leaves(payload)), 'the commenter’s figure as a value')
    return payload


def input_refs(manifest):
    refs = []

    def walk(v):
        if isinstance(v, dict):
            if 'path' in v and 'sha256' in v:
                refs.append(v)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(manifest)
    return refs


def inputs_available():
    """Whether the pinned inputs are on this machine. They are not in the public repository: the research folders and
    the review's evidence are local. A clone still checks the served file against the committed export audit's hash;
    only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest)) and (REVIEW / 'evidence/captures').is_dir()


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_dataset_checks_export
    return audit_dataset_checks_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
