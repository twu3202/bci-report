"""Release the paired-biosignal pilots, aggregate-only, on one page of small pilots kept outside every ranking.

From the paired-biosignal batch, each result from its own approved aggregate export, handoff and final approval
record, nothing shared between them but the page:

- Orthosis error events (Zenodo 8345429), ONE cohort of 8 people, 83 runs and 2,407 events, as three results: the
  64-channel classical baseline, the matched 58-channel classical configuration, and frozen EEGPT against that
  matched configuration. Counted once; never new coverage.
- BINGO inner speech in Greek and English: a cross-person, cross-language spectral ridge near its 15-class prior.
  Published under the owner's rights decision of 2026-10-12, behind one switch (sources[...].publication).
- Handwriting (EEG-fNIRS competition dataset, EEG only): the mask-aware analysis, five people. Published by the owner's
  decision of 2026-10-12 with its rights gap stated: no ethics-approval or informed-consent statement was found, on the
  dataset card or in a participating team's challenge paper (pinned and read for it). The same switch holds it again.
  The mask-only control's bootstrap interval is withheld: at five people its bounds would show individual scores.
- REFED: the stored-clip computational diagnostic, two nominal folders and 30 clips.
- Status only, with no figure: Orthosis EMG/TinyMyo/fusion, handwriting fNIRS/fusion, REFED physiological/fusion
  and the meditation dataset.

The website inputs are the approved export JSONs. The handoffs, approval and finalization records, QA records,
release decisions and independent audits are pinned by hash and checked against those exact bytes, never copied:
they carry private storage paths. The rights evidence (each source's official record, paper or deliverable) is
pinned the same way and its quotes are checked against it, and so is each absence a page states.

What this export refuses:
- per-person, per-field, per-folder, per-clip and per-record values: the Orthosis matched-difference range, the
  response-clean subset's scores (three people), every minimum, maximum and percentile, by key and by fragment, and
  the Orthosis per-person values by value;
- individual permutation replicates (the mean and the observed range are published, labelled as a range),
  confusion matrices, pooled metrics, per-axis errors, identifiers, predictions, features, thresholds, compute and
  private paths;
- a held source's figures anywhere in the file; an interval that does not hold its mean; a reading the numbers no
  longer support; a version label or an update date in the text; Jev; the EEGPT weights called Apache-2.0; and a
  claim of online use, recognition, equivalence, superiority, causation or zero-shot transfer that is not negated.

    python3 pipeline/publication/export_pilot_studies_update.py
"""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261012'
MANIFEST = REVIEW / 'pilot-studies-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'pilot-studies-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/pilot-studies-update.json',
           PROJECT / 'site/public/data/pilot-studies-update.json')
RELEASE_ID = 'pilot-studies-update-20261012'
SCHEMA = 'bci-report-pilot-studies-update-v1'
TITLE = 'Pilot studies'
QUESTION = 'What can a small pilot show, and what can it not?'
BATCH = 'research/paired_biosignal_pilots_20261011/'

ORTH64, ORTH58, ORTH_FM = 'orthosis-64ch-classical', 'orthosis-58ch-classical', 'orthosis-eegpt-vs-58ch'
BINGO, HAND, REFED = 'bingo-cross-language', 'handwriting-mask-aware', 'refed-stored-clip'
SOURCE_ORDER = (ORTH64, ORTH58, ORTH_FM, BINGO, HAND, REFED)
DATASETS = {'orthosis-error-detection': (ORTH64, ORTH58, ORTH_FM), 'bingo-imagined-speech': (BINGO,),
            'eeg-fnirs-handwriting': (HAND,), 'refed': (REFED,)}
PILOTS = (('orthosis', 'orthosis-error-detection', 'Orthosis error events'),
          ('bingo', 'bingo-imagined-speech', 'Inner speech in Greek and English'),
          ('handwriting', 'eeg-fnirs-handwriting', 'Mask-aware EEG on a handwriting dataset'),
          ('refed', 'refed', 'REFED stored clips'))
PUBLICATION = ('released', 'status_only')

# Per-person distributions, a decoder's internals and what this batch leaves out on purpose. Refused by exact key
# and by fragment; the one exception is a permutation or shuffle control's observed range (range_allowed()).
REFUSED_KEYS = PER_PERSON_KEYS | {'minimum', 'maximum', 'p10', 'p90', 'q1', 'q3', 'range', 'means', 'per_class',
                                  'private_audit', 'resources', 'perclass_recall', 'mean_field_confusion'}
REFUSED_KEY_FRAGMENTS = ('threshold', 'prediction', 'probabilit', 'feature', 'private', 'participant_id',
                         'record_id', 'per_person', 'per_participant', 'per_record', 'per_field', 'per_clip',
                         'per_folder', 'minimum', 'maximum', 'quantile', 'percentile', 'worst', 'p10', 'p90',
                         'confusion', 'per_class', 'perclass', 'pooled', 'combined', 'basename', 'wall_seconds',
                         'rss', 'elapsed', 'path', 'rmse', 'by_axis', 'strata', 'stratum')
# Upstream file and participant names: S12, sub-07, sub_07, and any raw-file extension.
SOURCE_IDS = re.compile(r'\bS\d{1,2}\b|\bsub[-_]\d+|\bsess\d+|\bsubj\d+'
                        r'|\.(?:mat|zip|h5|hdf5|npz|npy|bdf|edf|gdf|set|fif|vhdr|vmrk|xdf)\b'
                        r'|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|Gal4|TRX50|BCI_Arena|\btwu\b',
                            re.IGNORECASE)
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'\b(?:updated?|added)\b|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d', re.IGNORECASE)
# Claims these results do not support, allowed only in a sentence that negates them.
CLAIMS = re.compile(r'\bonline\b|real-time|closed-loop|intended[- ]motion|intention|\bclinical\b|\bmedical\b|zero-shot'
                    r'|\bcausal|\bcaused\b|unseen pretraining|certified unseen|\bendorse|recogni[sz]|superior'
                    r'|equivalen|significan|neural origin|state[- ]of[- ]the[- ]art|impossib', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|unsupported|unverified|unconfirmed|"
                      r"unestablished|none)\b|n't\b|\brules? out\b|\bruled out\b", re.IGNORECASE)
TOL = 1e-12
RANGE_NOTE = 'the lowest and highest replicate means: an observed range, not a confidence interval'


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def close(a, b, label, tol=TOL):
    require(number(a) and number(b) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def bounded(mean, interval, label, lo_bound=-math.inf, hi_bound=math.inf):
    """A published mean and its 95% interval: the interval holds the mean and stays in the metric's range."""
    require(isinstance(interval, list) and len(interval) == 2, f'{label}: no two-sided interval')
    lo, hi = interval
    require(all(number(v) for v in (mean, lo, hi)), f'{label}: a mean or bound is not a finite number')
    require(lo_bound <= lo and hi <= hi_bound, f'{label}: the interval leaves the metric range')
    require(lo <= mean <= hi, f'{label}: the interval does not contain its mean')
    return [lo, hi]


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def pinned_bytes(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw


def in_batch(ref):
    """A pinned file's path as the batch's own records name it (relative to the batch root)."""
    require(BATCH in ref['path'], f'{ref["path"]}: not in the paired-biosignal batch')
    return ref['path'].split(BATCH, 1)[1]


def stated(text, phrase, label):
    """The figure the page prints is the one the pinned handoff states."""
    require(phrase in text, f'{label}: the handoff does not state {phrase!r}')


def plain(markup):
    """Running text of a pinned page or full-text record: scripts dropped, tags dropped, entities decoded."""
    markup = re.sub(r'<(script|style)\b.*?</\1>', ' ', markup, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', markup))).strip()


def flat(text):
    return re.sub(r'\s+', ' ', text).strip()


def pct(x):
    return f'{100 * x:.2f}'


def numerals(text):
    return {n.replace(',', '') for n in re.findall(r'\d[\d,]*(?:\.\d+)?', text)}


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif isinstance(value, float):
        yield value


def written_from(result, sources, label, skip=('model', 'release_limits', 'pretraining_exposure')):
    """Every numeral in the prose this export writes is one a pinned handoff, export or source document states."""
    allowed = set().union(*(numerals(s) for s in sources))
    for key, value in result.items():
        if key in skip:
            continue
        for trail, text in strings(value, f'{label}.{key}'):
            missing = numerals(text) - allowed
            require(not missing, f'{trail}: the numerals {sorted(missing)} are in no pinned handoff or source')


def replicate_summary(values, label, n, mean=None, low=None, high=None):
    """A permutation or label-shuffle control: its mean and observed range, never the replicates themselves."""
    require(isinstance(values, list) and len(values) == n and all(number(v) for v in values),
            f'{label}: not {n} finite replicate means')
    if mean is None:
        mean = math.fsum(values) / n
    else:
        close(mean, math.fsum(values) / n, f'{label}: the stated mean', 1e-12)
    lo, hi = min(values), max(values)
    require(low in (None, lo) and high in (None, hi), f'{label}: the stated range is not the replicates’ range')
    return {'replicates': n, 'balanced_accuracy_mean': mean, 'observed_range': [lo, hi], 'range_is': RANGE_NOTE}


def all_true(record, label):
    """Every check passed: each flag true, each list of hits empty."""
    def walk(v):
        if isinstance(v, dict):
            return all(walk(x) for x in v.values())
        return v is True or v == []
    require(walk(record), f'{label}: not every check passed')


# ---------------------------------------------------------------------------- rights
def licence_record(record):
    """The licence as the source's own record states it."""
    label, ref = record['id'], record['licenseRecord']
    kind = ref['kind']
    if kind == 'zenodo_api':
        z, _ = pinned(ref, f'{label} licence record')
        require(z['metadata']['license']['id'] == 'cc-by-4.0' and record['license'] == 'CC BY 4.0'
                and record['licenseUrl'] == 'https://creativecommons.org/licenses/by/4.0/',
                f'{label}: the repository names another licence')
        require(z['metadata']['access_right'] == 'open', f'{label}: the repository record is not open')
        doi = record['source'].removeprefix('https://doi.org/')
        require(z['doi'] == doi and doi in record['version'] and doi in record['attribution'],
                f'{label}: the repository DOI differs from the record')
        require(any(z['links']['self'] in u for u in record['reviewBasis']), f'{label}: the API record is not a basis')
        rel = z['metadata']['relations']['version'][0]
        require(rel['is_last'] is True and rel['parent']['pid_value'] in record['version'],
                f'{label}: not the latest version of its concept record')
        for c in z['metadata']['creators']:
            last, first = (s.strip() for s in c['name'].split(',', 1))
            require(f'{first} {last}' in record['attribution'], f'{label}: the attribution omits {c["name"]}')
    elif kind == 'huggingface_api':
        h, _ = pinned(ref, f'{label} licence record')
        require(h['cardData']['license'] == 'cc-by-nc-sa-4.0' and 'license:cc-by-nc-sa-4.0' in h['tags']
                and record['license'] == 'CC BY-NC-SA 4.0'
                and record['licenseUrl'] == 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                f'{label}: the repository names another licence')
        require(h['sha'] in record['version'] and h['sha'] in ref['retrievedFrom'] and h['sha'] in record['attribution'],
                f'{label}: another revision')
        require(record['source'] == f'https://huggingface.co/datasets/{h["id"]}', f'{label}: another repository')
        require(h['gated'] in ('auto', 'manual') and 'gated' in record['version'], f'{label}: the gate is not stated')
        require(h['private'] is False, f'{label}: a private repository')
    elif kind == 'bingo_datasets_page':
        page = plain(pinned_text(ref, f'{label} datasets page'))
        require(record['license'] == 'No licence stated' and record['licenseUrl'] == record['source']
                == ref['retrievedFrom'], f'{label}: the licence field is not the page’s absence of one')
        for word in ('licen', 'ethic', 'consent', 'terms of use'):
            require(word not in page.lower(), f'{label}: the datasets page mentions {word!r}; the record must be reviewed')
        require('CROSS-LINGUISTIC INNER SPEECH ELICITATION' in page and 'D3.1 v2' in page,
                f'{label}: the page no longer offers the cross-linguistic dataset with its deliverable')
        raw = pinned_text(ref, f'{label} datasets page')
        require('https://bingo-project.gr/download/397' in raw, f'{label}: the page does not link D3.1 version 2.0')
    else:
        require(False, f'{label}: no rule for a {kind} licence record')


def consent_ethics(record):
    """Consent and ethics as the source states them, each quote found in the pinned text."""
    label, ce = record['id'], record['consentEthics']
    status = ce['status']
    out = {}
    if status == 'stated':
        rec = ce['record']
        if rec['kind'] == 'europepmc_xml':
            xml = pinned_text(rec, f'{label} paper')
            require(f'<article-id pub-id-type="doi">{ce["paperDoi"]}</article-id>' in xml,
                    f'{label}: the pinned full text is another paper')
            require(ce['paperDoi'] in record['attribution'], f'{label}: the attribution does not cite the paper read')
            text = plain(xml)
        elif rec['kind'] == 'pdf_text':
            pinned_bytes(ce['document'], f'{label} paper PDF')
            text = flat(pinned_text(rec, f'{label} paper text'))
            require(flat(ce['paperTitle']) in text and ce['paperTitle'].split(':')[0] in record['attribution'],
                    f'{label}: the pinned text is another paper')
        else:
            require(False, f'{label}: no rule for a {rec["kind"]} record')
        require(ce['source'] in record['reviewBasis'], f'{label}: consent and ethics are not from a listed source')
        for kind in ('ethics', 'consent'):
            quotes = [q['text'] for q in ce['quotes'] if q['statement'] == kind]
            require(len(quotes) == 1 and quotes[0] in text, f'{label}: the {kind} statement has no quote in the paper')
            require(ce[kind], f'{label}: no {kind} statement recorded')
        for name in ce.get('names', []):
            require(name in text and name in ce['ethics'] + record['privacyReview'], f'{label}: {name!r} is not stated')
        out = {
            'ethics_approval': {'stated': True, 'statement': ce['ethics'],
                                'quote': next(q['text'] for q in ce['quotes'] if q['statement'] == 'ethics')},
            'informed_consent': {'stated': True, 'statement': ce['consent'],
                                 'quote': next(q['text'] for q in ce['quotes'] if q['statement'] == 'consent')},
            'read_from': f'{ce["source"]}, {ce["section"]}, read {rec["retrievedAt"]}',
        }
    elif status == 'owner_decision':
        docs = record['sourceDocuments']
        v3 = flat(pinned_text(docs['consentDocument']['text'], f'{label} consent document'))
        v2 = flat(pinned_text(docs['datasetDocumentation']['text'], f'{label} dataset documentation'))
        pinned_bytes(docs['consentDocument']['pdf'], f'{label} consent document PDF')
        pinned_bytes(docs['datasetDocumentation']['pdf'], f'{label} documentation PDF')
        require('Dissemination level: Public (PU)' in v3 and 'Dissemination level: Public (PU)' in v2
                and 'Version: V3.0' in v3 and 'Version: V2.0' in v2, f'{label}: not the public deliverables pinned')
        quote = next(q['text'] for q in ce['quotes'] if q['statement'] == 'consent')
        require(quote in v3 and 'NATO phonetic alphabet' in v3 and 'CERTH EEG laboratory' in v3,
                f'{label}: the consent statement has no quote in D3.1 version 3.0')
        for word in ('consent', 'ethic', 'licen'):
            require(word not in v2.lower(), f'{label}: D3.1 version 2.0 mentions {word!r}; the record must be reviewed')
        require(ce['ethics'] is None and ce['ethicsNote'] and ce['ownerDecision'], f'{label}: the decision is incomplete')
        require(ce['source'] == docs['consentDocument']['url'] and ce['source'] in record['reviewBasis'],
                f'{label}: the consent source is not a listed basis')
        require('internalEvidence' not in record, f'{label}: the confidential plan belongs in the git-ignored evidence '
                                                   f'folder, not in this public manifest')
        out = {
            'ethics_approval': {'stated': False, 'statement': None, 'note': ce['ethicsNote']},
            'informed_consent': {'stated': True, 'statement': ce['consent'], 'quote': quote,
                                 'scope': ce['consentScope']},
            'basis': 'owner decision: aggregates published with these rights as they stand',
            'read_from': f'{docs["consentDocument"]["title"]} ({ce["source"]}), {ce["section"]}, read '
                         f'{record["reviewedAt"]}',
        }
    elif status == 'not_stated':
        page = plain(pinned_text(ce['record'], f'{label} dataset card'))
        require('Important Notes' in page and 'Recommended Usage' in page, f'{label}: the pinned page is not the card')
        for word in ('consent', 'ethic', 'IRB', 'Institutional Review'):
            require(word.lower() not in page.lower(), f'{label}: the card mentions {word!r}; the record must be reviewed')
        require(ce['ethics'] is None and ce['consent'] is None, f'{label}: a statement is recorded for an absent one')
        out = {
            'ethics_approval': {'stated': False, 'statement': None, 'note': ce['ethicsNote']},
            'informed_consent': {'stated': False, 'statement': None, 'note': ce['consentNote']},
            'read_from': f'{ce["source"]}, the dataset card, read {ce["record"]["retrievedAt"]}',
        }
        if 'challengePaper' in ce:
            out.update(searched_further(record, ce))
    else:
        require(False, f'{label}: no rule for consent status {status!r}')
    return out


def searched_further(record, ce):
    """Where else a statement was looked for, when the dataset's own record has none (the handwriting dataset, owner
    decision of 2026-10-12): a participating team's challenge paper, pinned as abstract page, HTML, PDF and the PDF's
    text. It must be the paper named, identify the competition in the words quoted, carry no ethics, consent or dataset-
    licence statement, and list the organisers' paper as forthcoming. The gap and the owner's decision are stated with it."""
    label, cp = record['id'], ce['challengePaper']
    abstract = pinned_text(cp['abstractPage'], f'{label} challenge paper abstract page')
    page = plain(pinned_text(cp['html'], f'{label} challenge paper HTML'))
    pinned_bytes(cp['pdf'], f'{label} challenge paper PDF')
    text = flat(pinned_text(cp['text'], f'{label} challenge paper text'))
    arxiv = cp['arxiv']
    require(cp['url'] == f'https://arxiv.org/abs/{arxiv}' == cp['abstractPage']['retrievedFrom'] and cp['url'] in record['reviewBasis'],
            f'{label}: the challenge paper is not a listed basis')
    require(f'[{arxiv}]' in abstract and f'arXiv:{arxiv}' in page and f'arXiv:{arxiv}' in text and cp['title'] in page,
            f'{label}: the pinned files are another paper or version')
    for q in cp['quotes']:
        require(q['text'] in page, f'{label}: the challenge paper does not say {q["text"]!r}')
    require(cp['competition'].removeprefix('the ') in page, f'{label}: the competition is not the one the paper names')
    for where, body in (('HTML', page), ('PDF text', text)):
        low = body.lower()
        for word in ('ethic', 'consent', 'institutional review', 'review board'):
            require(word not in low, f'{label}: the challenge paper ({where}) mentions {word!r}; the record must be reviewed')
        require(not re.search(r'\bIRB\b', body), f'{label}: the challenge paper ({where}) mentions an IRB')
    # The HTML carries arXiv's licence for the paper itself; the paper's own text states no dataset licence.
    require('licen' not in text.lower(), f'{label}: the challenge paper states a licence; the record must be reviewed')
    org = cp['organisersPaper']
    require(org['title'] in page and 'Forthcoming' in page and 'forthcoming' in org['status'],
            f'{label}: the organisers’ paper is not the one the challenge paper lists as forthcoming')
    require(ce['gap'] and ce['ownerDecision'] and ce['recheck'] and ce['recheck'] in ce['gap'],
            f'{label}: the gap, the decision or the recheck is not stated')
    for phrase in ('No ethics-approval or informed-consent statement was found', 'dataset card', 'challenge paper', 'forthcoming',
                   'owner’s decision'):
        require(phrase in ce['gap'], f'{label}: the gap does not say {phrase!r}')
    return {
        'searched': [
            {'source': 'the dataset card', 'url': ce['source'], 'statement_found': False},
            {'source': 'a participating team’s challenge paper', 'title': cp['title'], 'authors': cp['authors'],
             'url': cp['url'], 'identifies': cp['competition'], 'statement_found': False},
            {'source': 'the organisers’ paper', 'citation': org['citation'], 'status': org['status']},
        ],
        'gap': ce['gap'],
        'basis': 'owner decision: aggregates published with this gap stated',
        'recheck': ce['recheck'],
    }


def dataset_rights(record, publication):
    """The rights record the pages print, with what this release publishes on it."""
    label = record['id']
    require(approved({**record, 'decision': 'aggregate_preview'}), f'{label}: the rights record is incomplete')
    require(publication in PUBLICATION, f'{label}: publication must be released or status_only')
    licence_record(record)
    ce = consent_ethics(record)
    rights = {k: record[k] for k in ('name', 'task', 'source', 'version', 'license', 'licenseUrl', 'attribution',
                                      'reviewedAt', 'reviewBasis')}
    rights['privacyReview'] = record['privacyReview'] if publication == 'released' else record['heldStatement']
    out = {'publication': publication, 'rights': rights, 'consent_and_ethics': ce}
    if 'sourceDocuments' in record:
        out['documentation'] = [{'title': d['title'], 'url': d['url'], 'dissemination': d['dissemination']}
                                for k, d in record['sourceDocuments'].items() if k != 'deliverablesPage']
        pinned_text(record['sourceDocuments']['deliverablesPage'], f'{label} deliverables page')
    return out


# ---------------------------------------------------------------------------- Orthosis
ORTH_PEOPLE, ORTH_RUNS, ORTH_EVENTS = 8, 83, 2407
ORTH_CLASSES = {'standard': 1933, 'device_error': 474}
ORTH_METRICS = {'balanced_accuracy': 'balanced_accuracy', 'auroc': 'auroc', 'auprc': 'average_precision'}
ORTH_ARMS = {
    'eeg': ('Fixed EEG features + logistic regression, 64 channels', 'EEG',
            '576 fixed amplitude and log band-power values per event from 64 EEG channels; a training-only '
            'StandardScaler and a balanced L2 logistic regression with C=1, no tuning'),
    'classical58': ('Matched classical EEG features + the same probe, 58 channels', 'EEG',
                    '522 fixed amplitude and log band-power values per event from the 58 channels EEGPT supports, in '
                    'source order; the same scaler and probe'),
    'eegpt2048': ('Frozen EEGPT + the same fixed supervised probe, 58 channels', 'EEG',
                  'the frozen 25,287,168-parameter EEGPT target encoder at its native 58-by-128 input (resampled from '
                  '500 to 256 Hz, microvolts divided by 1000); two temporal patches averaged and four 512-dimensional '
                  'summary tokens flattened to 2,048 values; the same scaler and probe; the encoder’s weights unchanged, with no LoRA '
                  'or fine-tuning'),
    'confound': ('Direction/time confound probe', 'control',
                 'the same fixed probe on movement direction, run order within the person, position in the run and '
                 'time in the run: no EEG'),
    'majority': ('Training majority', 'control', 'predicts the most frequent class of the seven training people'),
    'prior': ('Training class prior', 'control', 'a constant probability, the error share of the seven training people'),
}
ORTH_TASK = ('Recorded injected orthosis device errors against standard device events with no error introduced, from '
             'the 0–0.5 second window after each event. The labels describe recorded device events, not whether the '
             'person noticed the error.')
ORTH_SPLIT = ('leave one whole person out: eight folds, all of a person’s runs held out together; the scaler and the '
              'probe are fitted on the other seven people')
ORTH_WEIGHTING = ('macro-person: the unweighted mean of the eight held-out people’s metrics, not pooled trial '
                  'accuracy; balanced accuracy is not ordinary accuracy')
ORTH_UNCERTAINTY = {
    'kind': 'pointwise 95% percentile interval from 10,000 person-level bootstrap draws',
    'limited_by': 'eight people give limited uncertainty estimation',
    'conditional_on': 'the fixed sealed predictions; refitting is not included',
}


def orth_arms(rows, arms, label):
    """Every arm by every metric, each row the eight-person primary cohort's, each interval holding its mean."""
    by = {}
    for r in rows:
        require(r['policy'] == 'primary' and r['defined_people'] == ORTH_PEOPLE,
                f'{label}: a row is not the eight-person primary cohort')
        require(r['arm'] in arms and r['metric'] in ORTH_METRICS, f'{label}: an unexpected row {r["arm"]}/{r["metric"]}')
        key = (r['arm'], r['metric'])
        require(key not in by, f'{label}: a duplicated row {key}')
        by[key] = r
    require(set(by) == {(a, m) for a in arms for m in ORTH_METRICS}, f'{label}: rows missing')
    out = {}
    for a in arms:
        name, kind, desc = ORTH_ARMS[a]
        entry = {'label': name, 'kind': kind, 'description': desc}
        for m, key in ORTH_METRICS.items():
            r = by[(a, m)]
            entry[key] = {'mean': r['mean'],
                          'interval_95': bounded(r['mean'], r['person_bootstrap_95ci'], f'{label}/{a}/{m}', 0.0, 1.0)}
        out[a] = entry
    for a in ('majority', 'prior'):
        require(out[a]['balanced_accuracy']['mean'] == 0.5 and out[a]['balanced_accuracy']['interval_95'] == [0.5, 0.5]
                and out[a]['auroc']['mean'] == 0.5, f'{label}/{a}: a constant control is not at chance')
    return out


def orth_cohort(method, label):
    require(method['eligible_people'] == ORTH_PEOPLE and method['eligible_runs'] == ORTH_RUNS
            and method['eligible_events'] == ORTH_EVENTS and method['class_counts'] == ORTH_CLASSES,
            f'{label}: not the eight-person, 83-run, 2,407-event cohort')
    require(method['split'] == 'leave one whole person out, all runs together' and method['modality'] == 'EEG only',
            f'{label}: another split or modality')
    require(method['sampling_hz'] == 500 and method['decision_window_seconds'] == [0, 0.5]
            and method['window_samples'] == 250, f'{label}: another window')
    return {
        'people': method['eligible_people'], 'runs': method['eligible_runs'], 'events': method['eligible_events'],
        'standard_events': method['class_counts']['standard'], 'error_events': method['class_counts']['device_error'],
        'error_share': method['class_counts']['device_error'] / method['eligible_events'],
        'counted_once': 'the same 8 people, 83 runs and 2,407 events in all three Orthosis results: one cohort, '
                        'never counted twice in coverage',
        'split': ORTH_SPLIT,
    }


def orth_signal(method, channels):
    require(method['eeg_channels'] == channels, f'not {channels} channels')
    return {'eeg_channels': method['eeg_channels'], 'sampling_hz': method['sampling_hz'],
            'window_seconds': method['decision_window_seconds'], 'window_samples': method['window_samples']}


def orth_row_stated(handoff, arm, name, label):
    ba, au, ap = arm['balanced_accuracy'], arm['auroc'], arm['average_precision']
    stated(handoff, f'| {name} | {pct(ba["mean"])}% | {pct(ba["interval_95"][0])}–{pct(ba["interval_95"][1])}% | '
                    f'{au["mean"]:.4f} | {ap["mean"]:.4f} |', label)


ORTH_DATA_ORIGIN = 'https://zenodo.org/records/8345429'


def orth_export_basics(export, label):
    d = export['data_origin']
    require(d['dataset_url'] == ORTH_DATA_ORIGIN and d['dataset_doi'] == '10.5281/zenodo.8345429'
            and d['paper_url'] == 'https://doi.org/10.3389/fnhum.2024.1304311', f'{label}: another dataset or paper')
    p = export['provenance']
    require(p['real_execution'] is True and p['synthetic_scores'] is False, f'{label}: not a real execution')


def orthosis_64(src):
    label = ORTH64
    export, export_sha = pinned(src['export'], f'{label} export')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    check, _ = pinned(src['approval'], f'{label} handoff check')
    audit, _ = pinned(src['resultAudit'], f'{label} result audit')

    require(check['status'] == 'approved_handoff_and_aggregate_payload' and check['necessary_corrections'] == []
            and check['website_publication_performed'] is False, f'{label}: the handoff check does not approve it')
    require(check['sha256'] == {Path(src['handoff']['path']).name: src['handoff']['sha256'],
                                in_batch(src['export']): export_sha},
            f'{label}: the handoff check names other handoff or export bytes')
    require(audit['status'] == 'passed_independent_result_audit' and audit['errors'] == []
            and audit['website_edits_or_publication_performed'] is False, f'{label}: the result audit did not pass')
    require(export['provenance']['independent_result_audit'] == in_batch(src['resultAudit'])
            and audit['scores_sha256'] == export['provenance']['scores_sha256'], f'{label}: another audit or scores')
    require(export['status'] == 'real_execution_complete_independent_result_audit_passed'
            and export['release_eligibility'] == 'aggregate_only_with_attribution_and_limitations',
            f'{label}: not the approved aggregate export')
    orth_export_basics(export, label)
    key = lambda r: (r['arm'], r['metric'])
    primary = sorted((a for a in audit['aggregates'] if a['policy'] == 'primary'), key=key)
    require(primary == sorted(export['primary_results'], key=key), f'{label}: the export rows differ from the audit')
    perm = export['permutation_control']
    require(audit['permutation_primary_ba']['means'] == perm['means'], f'{label}: the permutation series differs')
    md = export['matched_eeg_minus_confound_balanced_accuracy']
    require(audit['eeg_minus_confound_primary_ba'] == md, f'{label}: the matched difference differs from the audit')
    c, m = audit['counts'], export['method']
    require(c['people'] == m['eligible_people'] and c['runs'] == m['eligible_runs'] and c['trials'] == m['eligible_events']
            and c['class_counts'] == {'0': ORTH_CLASSES['standard'], '1': ORTH_CLASSES['device_error']},
            f'{label}: the audit counts another cohort')
    sec = export['secondary_results']
    require(sec['status'] == 'descriptive_only_not_headline' and sec['response_clean_events'] == c['response_clean_trials']
            == 451 and sec['class_counts'] == {'standard': 5, 'device_error': 446}
            and sec['defined_people_for_class_dependent_metrics'] == 3, f'{label}: another secondary subset')

    arms = orth_arms(export['primary_results'], ('eeg', 'confound', 'majority', 'prior'), label)
    perm_out = replicate_summary(perm['means'], f'{label} permutation', 20, perm['mean'], perm['min'], perm['max'])
    require(md['all_person_differences_positive'] is True, f'{label}: EEG was not above the confound for every person')
    close(md['matched_person_mean'],
          arms['eeg']['balanced_accuracy']['mean'] - arms['confound']['balanced_accuracy']['mean'],
          f'{label}: the matched mean', 1e-12)
    # Per-person values: the matched range and every response-clean (three-person) score. Never published.
    secret = list(md['range'])
    for a in sec['aggregates']:
        secret += [a['mean'], *a['person_bootstrap_95ci']]
    ba = arms['eeg']['balanced_accuracy']
    require(ba['interval_95'][0] > arms['confound']['balanced_accuracy']['interval_95'][1]
            and ba['interval_95'][0] > perm_out['observed_range'][1],
            f'{label}: the EEG interval no longer clears the controls; the reading must be reviewed')

    # Last: the figures the pages print are the ones the pinned handoff states.
    orth_row_stated(handoff, arms['eeg'], 'Fixed EEG features + logistic regression', label)
    orth_row_stated(handoff, arms['confound'], 'Direction/time confound features + same probe', label)
    for a in ('majority', 'prior'):
        orth_row_stated(handoff, arms[a], 'Training class prior / majority prediction', label)
    stated(handoff, f'mean balanced accuracy {pct(perm_out["balanced_accuracy_mean"])}%, with a range of '
                    f'{pct(perm_out["observed_range"][0])}–{pct(perm_out["observed_range"][1])}%', label)
    stated(handoff, f'difference was {pct(md["matched_person_mean"])} percentage points', label)
    stated(handoff, f'**{ORTH_PEOPLE} people, {ORTH_RUNS} main-task runs and {ORTH_EVENTS:,} events**: '
                    f'{ORTH_CLASSES["standard"]:,} standard events and {ORTH_CLASSES["device_error"]} injected-error '
                    'events.', label)
    stated(handoff, 'Eight baseline runs were excluded. Eighty-two targets lacked an observed subsequent movement '
                    'boundary and one window crossed a boundary.', label)
    stated(handoff, '**451 events: 446 errors and only 5 standards**. Only three people have both classes.', label)
    stated(handoff, 'Compute 576 fixed amplitude and log-bandpower features.', label)

    result = {
        'id': ORTH64, 'dataset': 'orthosis-error-detection', 'pilot': 'orthosis',
        'title': 'Orthosis error events: the 64-channel classical baseline',
        'question': 'Can a fixed EEG baseline tell injected orthosis errors from standard device events in a person it '
                    'was not trained on?',
        'configuration': {'label': '64-channel configuration', 'values_per_event': 576,
                          'note': 'the first configuration of this cohort; it stays beside the 58-channel one'},
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False, 'leaderboard': False,
        'task': ORTH_TASK,
        'cohort': {**orth_cohort(m, label),
                   'exclusions': {'baseline_runs': 8, 'targets_without_following_movement': 82,
                                  'windows_crossing_boundary': 1,
                                  'note': 'baseline runs are not main-task runs; a target needs an observed following '
                                          'movement and a complete window'}},
        'signal': orth_signal(m, 64),
        'metric': 'balanced_accuracy', 'secondary_metrics': ['auroc', 'average_precision'], 'chance_level': 0.5,
        'weighting': ORTH_WEIGHTING,
        'arms': arms,
        'eeg_minus_confound': {
            'comparison': 'EEG minus the direction/time confound probe, matched person by person',
            'balanced_accuracy_difference': {'mean': md['matched_person_mean'], 'interval_95': None},
            'interval_note': 'no interval was computed for this difference',
            'people_with_eeg_above_confound': ORTH_PEOPLE, 'people': ORTH_PEOPLE,
        },
        'permutation_control': {
            'balanced_accuracy': perm_out,
            'design': 'training labels shuffled within person and run, held-out labels untouched; a diagnostic '
                      'control, not a full permutation significance test',
        },
        'response_clean_subset': {
            'status': 'secondary: counts only, never a headline',
            'events': sec['response_clean_events'], 'error_events': sec['class_counts']['device_error'],
            'standard_events': sec['class_counts']['standard'],
            'people_with_both_classes': sec['defined_people_for_class_dependent_metrics'],
            'note': 'strongly label-selected and dominated by errors, so its high average precision is not comparable '
                    'with the primary cohort and its scores are not published',
        },
        'method': {
            'signal': '64 EEG channels at 500 Hz with the declared header scaling; three acceleration channels '
                      'excluded; the recorded reference kept',
            'filter': 'continuous forward-only fourth-order Butterworth 1–30 Hz filtering that uses no future samples, zero state at each run start and '
                      'a five-second warm-up',
            'window': 'the complete half-open 0–0.5 second window after each event',
            'probe': 'a training-only StandardScaler and a balanced L2 logistic regression; C=1 and the 0.5 decision '
                     'rule fixed before execution; no tuning',
            'eligibility': 'main-task runs only; inclusion does not depend on whether the person responded correctly',
            'sealing': 'every fold and control prediction was sealed before a separate scorer read the held-out labels',
        },
        'uncertainty': ORTH_UNCERTAINTY,
        'reading': 'The fixed EEG baseline is above the direction/time confound probe, the class prior and every '
                   'permutation control, with its interval clear of all three. It separates recorded device events; it '
                   'does not show that the person recognised the error, and movement, muscle or device artifacts may '
                   'contribute.',
        'limitations': [
            'Eight people in one dataset: person-bootstrap uncertainty is limited, and this is not a population-level '
            'ranking.',
            'The labels are recorded injected device events. The result does not show subjective error recognition, '
            'a mental state or isolated neural activity: movement, muscle and device-injection artifacts may '
            'contribute, and beating the direction/time confound probe does not isolate a neural origin.',
            'The permutation controls shuffle training labels within person and run: diagnostic controls, not a full '
            'permutation significance test.',
            'A response-clean subset of 451 events has only 5 standard events and 446 errors, and only three people '
            'have both classes. Its high average precision reflects that prevalence, so its scores are not published '
            'and it never replaces the primary result.',
            'EEG only: no EMG model, fusion or paired EEG–EMG clock claim.',
            'Offline, and a reanalysis by this site: not a reproduction of the authors’ competition score, and no '
            'real-time, clinical or state-of-the-art claim.',
        ],
        'release_limits': export['limitations'],
        'claims_not_supported': [
            'not subjective error recognition or isolated neural decoding',
            'no real-time, online, clinical or deployment claim',
            'not a population ranking and no state-of-the-art claim',
            'no EMG, fusion or foundation-model result in this configuration',
        ],
        'independent_audit': {
            'status': 'pass', 'people': ORTH_PEOPLE,
            'checked': 'all 384 score rows and 144 aggregate and interval rows recomputed from the sealed predictions, '
                       'agreeing within 1e-12; twelve synthetic checks passed before execution',
            'not_checked': 'no raw signal was read and no model was refitted',
        },
    }
    written_from(result, (handoff, json.dumps(export)), label)
    return result, export, secret


def orthosis_58(src):
    label = ORTH58
    export, export_sha = pinned(src['export'], f'{label} export')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    approval, _ = pinned(src['approval'], f'{label} parent approval')
    qa, qa_sha = pinned(src['releaseQa'], f'{label} release QA')
    audit, audit_sha = pinned(src['resultAudit'], f'{label} result audit')

    require(approval['status'] == 'approved_classical_aggregate_only' and approval['public_export_sha256'] == export_sha
            and approval['public_export'] == in_batch(src['export'])
            and approval['handoff_sha256'] == src['handoff']['sha256'] and approval['independent_review_sha256'] == qa_sha
            and approval['independent_result_audit_sha256'] == audit_sha
            and approval['prior64channel_results_unchanged'] is True
            and approval['raw_participant_trial_feature_prediction_release_authorized'] is False,
            f'{label}: the parent approval does not bind these bytes')
    rh = qa['reviewed_hashes']
    require(qa['verdict'] == 'pass' and qa['actionable_before_final'] == []
            and rh[in_batch(src['export'])] == export_sha and rh[Path(src['handoff']['path']).name]
            == src['handoff']['sha256'] and rh[in_batch(src['resultAudit'])] == audit_sha,
            f'{label}: the release QA did not pass these bytes')
    all_true(qa['checks'], f'{label} release QA')
    require(audit['verdict'] == 'pass' and audit['people'] == ORTH_PEOPLE and audit['runs'] == ORTH_RUNS
            and audit['trials'] == ORTH_EVENTS and audit['nonfinite_features_or_predictions'] == 0,
            f'{label}: the result audit did not pass')
    p = export['provenance']
    require(p['independent_result_audit_sha256'] == audit_sha and p['parent_handoff_approval_required'] is True
            and p['scores_sha256'] == audit['scores_sha256'], f'{label}: the export names another audit')
    require(export['status'] == 'real_execution_complete_independent_result_audit_passed'
            and export['publication_scope'].startswith('Only these classical/control aggregate results'),
            f'{label}: not the classical-only export')
    orth_export_basics(export, label)
    key = lambda r: (r['arm'], r['metric'])
    audited = {key(r): r for r in audit['aggregate'] if r['policy'] == 'primary'}
    for r in export['primary_results']:
        require(audited.get(key(r)) == r, f'{label}: the row {key(r)} differs from the result audit')
    m = export['method']
    require(m['features'].startswith('522 fixed') and m['eeg_channels'] == 58,
            f'{label}: not the 522-value, 58-channel classical representation')

    arms = orth_arms(export['primary_results'], ('classical58', 'confound', 'majority', 'prior'), label)
    perm = export['permutation_control']
    require(perm['replicates'] == 20, f'{label}: not twenty permutations')
    perm_out = replicate_summary(perm['means'], f'{label} permutation', 20, perm['mean'], perm['min'], perm['max'])
    ba = arms['classical58']['balanced_accuracy']
    require(ba['interval_95'][0] > arms['confound']['balanced_accuracy']['interval_95'][1]
            and ba['interval_95'][0] > perm_out['observed_range'][1],
            f'{label}: the interval no longer clears the controls; the reading must be reviewed')

    orth_row_stated(handoff, arms['classical58'], 'Matched 58-channel classical features + same probe', label)
    orth_row_stated(handoff, arms['confound'], 'Direction/time confound probe', label)
    for a in ('majority', 'prior'):
        orth_row_stated(handoff, arms[a], 'Source prior / majority', label)
    stated(handoff, f'{pct(perm_out["balanced_accuracy_mean"])}% ({pct(perm_out["observed_range"][0])}–'
                    f'{pct(perm_out["observed_range"][1])}%) for matched classical features', label)
    stated(handoff, 'Omit TP9, TP10, PO9, PO10, FT9 and FT10', label)

    result = {
        'id': ORTH58, 'dataset': 'orthosis-error-detection', 'pilot': 'orthosis',
        'title': 'Orthosis error events: the matched 58-channel classical configuration',
        'question': 'The same baseline on the 58 channels EEGPT supports: does it still separate the events?',
        'configuration': {'label': '58-channel configuration', 'values_per_event': 522,
                          'omitted_channels': ['TP9', 'TP10', 'PO9', 'PO10', 'FT9', 'FT10'],
                          'rule': 'the native-supported 58-channel intersection in source order, fixed before scoring; '
                                  'no substitution or score-based selection',
                          'note': 'a second configuration of the 64-channel baseline’s cohort, not a new cohort'},
        'same_cohort_as': ORTH64,
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False, 'leaderboard': False,
        'task': ORTH_TASK,
        'cohort': orth_cohort(m, label),
        'signal': orth_signal(m, 58),
        'metric': 'balanced_accuracy', 'secondary_metrics': ['auroc', 'average_precision'], 'chance_level': 0.5,
        'weighting': ORTH_WEIGHTING,
        'arms': arms,
        'permutation_control': {
            'balanced_accuracy': perm_out,
            'design': 'training labels shuffled within person and run, preserving run class counts, held-out labels '
                      'untouched; a diagnostic control, not a full permutation significance test',
        },
        'prior_exposure': 'The 64-channel scores were already seen before this configuration was frozen: an additional '
                          'prospective diagnostic, not a blind confirmation.',
        'method': {
            'signal': 'all 64 EEG channels filtered with continuous forward-only fourth-order 1–30 Hz filtering (zero state '
                      'per run, five-second warm-up), then the fixed 58-channel intersection selected; the recorded '
                      'FCz reference kept and acceleration excluded',
            'window': 'exactly the complete 0–0.5 second window after each event',
            'probe': 'a training-only StandardScaler and a balanced L2 logistic regression, C=1, liblinear, maximum '
                     '2,000 iterations and the 0.5 decision rule; no hyperparameter search',
            'sealing': 'all predictions were sealed before separate scoring',
        },
        'uncertainty': ORTH_UNCERTAINTY,
        'reading': 'The 58-channel configuration of the same baseline is also above the confound probe, the prior and '
                   'every permutation control. It is a second configuration on the same people, not a replication, '
                   'and the change from 64 to 58 channels says nothing about whether more channels help.',
        'limitations': [
            'The same eight people as the 64-channel result: not new coverage and not an independent replication.',
            'This configuration does not replace the 64-channel baseline, and the change in channel count was not the '
            'question: no conclusion about channel count follows.',
            'The 64-channel scores were seen before this configuration was frozen.',
            'The labels are recorded injected device events, not subjective error recognition or isolated neural '
            'activity; movement, muscle and device artifacts may contribute.',
            'The permutation controls are diagnostic, not a full permutation significance test.',
        ],
        'release_limits': export['limitations'],
        'claims_not_supported': [
            'not new dataset or person coverage',
            'no conclusion about how many channels are needed',
            'not subjective error recognition or isolated neural decoding',
            'no real-time, online or clinical claim',
        ],
        'independent_audit': {
            'status': 'pass', 'people': ORTH_PEOPLE,
            'checked': 'all 720 metric rows and 270 aggregate and interval rows recomputed within 1e-12; 24 '
                       'source-only refits reproduced the sealed probabilities exactly',
            'not_checked': 'the waveform features were not all re-extracted and the permutation probes were not all '
                           'refitted',
        },
    }
    written_from(result, (handoff, json.dumps(export)), label)
    return result, export


def orthosis_fm(src, classical_export, classical_sha):
    label = ORTH_FM
    export, export_sha = pinned(src['export'], f'{label} export')
    candidate, candidate_sha = pinned(src['auditedCandidate'], f'{label} audited payload')
    addendum = pinned_text(src['handoff'], f'{label} addendum')
    decision_doc = pinned_text(src['decisionDocument'], f'{label} decision document')
    final, _ = pinned(src['finalization'], f'{label} finalization')
    approval, approval_sha = pinned(src['parentApproval'], f'{label} parent approval')
    qa, qa_sha = pinned(src['payloadQa'], f'{label} payload QA')
    decision, decision_sha = pinned(src['releaseDecision'], f'{label} release decision')
    reassess, reassess_sha = pinned(src['reassessment'], f'{label} reassessment')
    terms, terms_sha = pinned(src['checkpointTerms'], f'{label} checkpoint terms')
    audit, audit_sha = pinned(src['resultAudit'], f'{label} result audit')
    licence = pinned_text(src['codeLicence'], f'{label} code licence')

    # Chain: finalization -> approved bytes, audited payload, QA, parent approval; approval -> payload, addendum, QA
    # and the evidence it verified; QA -> the same inputs.
    require(final['status'] == 'approved_final_export_for_website_session' and final['final_export_sha256'] == export_sha
            and final['final_export'] == in_batch(src['export']) and final['audited_candidate_sha256'] == candidate_sha
            and final['independent_payload_QA_sha256'] == qa_sha and final['parent_release_approval_sha256']
            == approval_sha and final['weight_redistribution'] is False and final['raw_or_individual_data_release']
            is False, f'{label}: the finalization does not bind these bytes')
    changed = final['changed_fields']
    require(changed == ['status', 'release_eligibility', 'integration_authorized']
            and set(export) == set(candidate) and [k for k in export if export[k] != candidate[k]] == changed,
            f'{label}: the approved export differs from the audited payload beyond the named fields')
    require(approval['status'] == 'approved_aggregate_only_ready_for_website_session'
            and approval['approved_payload_sha256'] == candidate_sha
            and approval['approved_handoff_sha256'] == src['handoff']['sha256'] and approval['independent_QA_sha256']
            == qa_sha and approval['public_aggregate_release_eligible'] is True
            and approval['weight_redistribution_authorized'] is False and approval['weight_use_license_resolved'] is False
            and approval['individual_result_release_authorized'] is False, f'{label}: the parent approval does not approve it')
    vh = approval['verified_hashes']
    for ref, digest in ((src['releaseDecision'], decision_sha), (src['resultAudit'], audit_sha),
                        (src['reassessment'], reassess_sha)):
        require(vh[in_batch(ref)] == digest, f'{label}: the approval verified other {in_batch(ref)} bytes')
    require(vh['exports/orthosis-matched58-classical-v1.json'] == classical_sha,
            f'{label}: the approval verified another classical export')
    require(qa['verdict'] == 'pass_final_hash_bound_aggregate_payload_QA' and qa['required_fix'] == []
            and qa['hash_bound_inputs'] == vh, f'{label}: the payload QA did not pass these bytes')
    all_true(qa['checks'], f'{label} payload QA')
    ev = decision['evidence']
    require(ev['candidate_export_sha256'] == candidate_sha and ev['addendum_sha256'] == src['handoff']['sha256']
            and ev['terms_reassessment_sha256'] == reassess_sha and ev['independent_numeric_audit_sha256'] == audit_sha
            and decision['weight_redistribution_authorized'] is False and decision['legal_certification'] is False,
            f'{label}: the release decision names other bytes')
    model = export['model']
    ci = reassess['checkpoint_identity']
    require(reassess['status'] == 'aggregate_hold_is_self_imposed_not_verified_publisher_ban'
            and reassess['supersedes_reasoning_only']['prior_review_sha256'] == terms_sha
            and ci['original_sha256'] == model['original_checkpoint_sha256'] == terms['checkpoint_identity']['original_sha256']
            and ci['tensor_derivative_sha256'] == model['tensor_checkpoint_sha256']
            and ci['original_filename'] == model['original_filename'] and ci['official_file_id'] == model['official_file_id'],
            f'{label}: another checkpoint')
    require(terms['resolved_checkpoint_license'] is None and terms['explicit_checkpoint_usage_terms_verified'] is False,
            f'{label}: the checkpoint terms are no longer unresolved; the model block must be reviewed')
    lic = next(s for s in terms['sources'] if s['url'].endswith('/LICENSE'))
    require(lic['retrieved_sha256'] == src['codeLicence']['sha256'] and model['source_revision'] in src['codeLicence']['retrievedFrom']
            and lic['identical_to_local_pinned_revision'] == model['source_revision'],
            f'{label}: the code licence read is not the one the terms review recorded')
    require(flat(licence).startswith('Apache License Version 2.0, January 2004'), f'{label}: the code licence is not Apache 2.0')
    require(model['source_code_license'] == 'Apache-2.0' and model['checkpoint_license'] == 'unverified'
            and model['weight_redistribution_authorized'] is False and model['name'] == 'EEGPT',
            f'{label}: the model’s licence fields changed')
    require(audit['verdict'] == 'pass' and audit['people'] == ORTH_PEOPLE and audit['all_metric_rows_recomputed'] == 720
            and audit['all_aggregates_recomputed'] == 270 and audit['source_only_refits'] == 24
            and audit['maximum_refit_probability_difference'] == 0.0, f'{label}: the result audit did not pass')
    p = export['provenance']
    require(p['independent_result_audit_sha256'] == audit_sha and p['classical_export_sha256'] == classical_sha
            and p['scores_sha256'] == audit['scores_sha256'] and p['numeric_audit_verdict'] == 'pass',
            f'{label}: the export names another audit or classical export')
    require(export['integration_authorized'] is True and export['release_eligibility'].startswith('approved_aggregate_only'),
            f'{label}: not the approved export')
    orth_export_basics(export, label)
    key = lambda r: (r['arm'], r['metric'])
    audited = {key(r): r for r in audit['aggregate'] if r['policy'] == 'primary'}
    require(len(export['primary_results']) == 15, f'{label}: not fifteen rows')
    for r in export['primary_results']:
        require(audited.get(key(r)) == r, f'{label}: the row {key(r)} differs from the result audit')
    shared = {key(r): r for r in classical_export['primary_results']}
    for r in export['primary_results']:
        if r['arm'] != 'eegpt2048':
            require(shared.get(key(r)) == r, f'{label}: the row {key(r)} is not the approved classical export’s')
    pd = export['paired_primary_difference']
    ad = next(d for d in audit['paired_differences'] if d['policy'] == 'primary')
    require(pd == ad and pd['contrast'] == 'eegpt2048_minus_classical58' and pd['metric'] == 'balanced_accuracy',
            f'{label}: the paired difference differs from the audit')

    arms = orth_arms(export['primary_results'], ('eegpt2048', 'classical58', 'confound', 'majority', 'prior'), label)
    d = pd['mean']
    close(d, arms['eegpt2048']['balanced_accuracy']['mean'] - arms['classical58']['balanced_accuracy']['mean'],
          f'{label}: the paired mean', 1e-12)
    iv = bounded(d, pd['person_bootstrap_95ci'], f'{label}: paired', -1.0, 1.0)
    require(iv[0] < 0 < iv[1] and d < 0, f'{label}: the paired interval no longer spans zero below a negative mean; '
                                         'the reading must be reviewed')
    pc = export['permutation_control']
    require(pc['replicates_per_fold'] == 20, f'{label}: not twenty permutations')
    perms = {}
    for a in ('eegpt2048', 'classical58'):
        s = pc['macro_person_balanced_accuracy'][a]
        require(s['count'] == 20, f'{label}/{a}: not twenty permutations')
        perms[a] = replicate_summary(s['means'], f'{label}/{a} permutation', 20, s['mean'], s['min'], s['max'])
    cp = classical_export['permutation_control']
    require(pc['macro_person_balanced_accuracy']['classical58']['means'] == cp['means'],
            f'{label}: the classical permutations are not the approved classical export’s')
    for a in ('eegpt2048', 'classical58'):
        lo = arms[a]['balanced_accuracy']['interval_95'][0]
        require(lo > perms[a]['observed_range'][1] and lo > arms['confound']['balanced_accuracy']['interval_95'][1],
                f'{label}/{a}: the interval no longer clears the controls; the reading must be reviewed')
    ms = export['method']
    require(ms['eeg_channels'] == 58 and ms['encoder_weight_update'] is False and ms['hyperparameter_search'] is False
            and ms['encoder_resampling']['output_samples'] == model['architecture']['img_size'][1] == 128
            and model['architecture']['img_size'][0] == 58 and ms['encoder_resampling']['output_sampling_hz'] == 256,
            f'{label}: another encoder input')
    fits = re.fullmatch(r'All eight folds and (\d+) prediction arms per fold sealed before separate scoring; '
                        r'(\d+) fitted probes\.', ms['prediction_seal'])
    require(fits is not None, f'{label}: the sealing statement changed')
    sealed_arms, probes = int(fits.group(1)), int(fits.group(2))

    # Last: the figures the pages print are the ones the pinned addendum and decision document state.
    e, c = arms['eegpt2048']['balanced_accuracy'], arms['classical58']['balanced_accuracy']
    stated(addendum, f'| Frozen EEGPT plus fixed supervised probe | {pct(e["mean"])}% | {pct(e["interval_95"][0])}–'
                     f'{pct(e["interval_95"][1])}% |', label)
    stated(addendum, f'| Matched 58-channel classical features plus same probe | {pct(c["mean"])}% | '
                     f'{pct(c["interval_95"][0])}–{pct(c["interval_95"][1])}% |', label)
    sg = lambda x, f: format(100 * x, f).replace('-', '−')
    stated(addendum, f'difference is {sg(d, ".4f")} percentage points, with a 95% person-bootstrap interval of '
                     f'{sg(iv[0], ".4f")} to {sg(iv[1], "+.4f")} points', label)
    stated(decision_doc, f'**{sg(d, ".2f")} percentage points**, interval **{sg(iv[0], ".2f")} to {sg(iv[1], "+.2f")} '
                         'points**', label)
    pe, pcl = perms['eegpt2048'], perms['classical58']
    stated(addendum, f'Mean macro balanced accuracy was {pct(pe["balanced_accuracy_mean"])}% (observed range '
                     f'{pct(pe["observed_range"][0])}–{pct(pe["observed_range"][1])}%) for EEGPT and '
                     f'{pct(pcl["balanced_accuracy_mean"])}% (observed range {pct(pcl["observed_range"][0])}–'
                     f'{pct(pcl["observed_range"][1])}%) for classical features.', label)
    stated(addendum, f'frozen {model["target_encoder_parameters"]:,}-parameter target encoder', label)

    result = {
        'id': ORTH_FM, 'dataset': 'orthosis-error-detection', 'pilot': 'orthosis',
        'title': 'Orthosis error events: frozen EEGPT against the matched classical features',
        'question': 'On the same people and channels, does a frozen EEG foundation model with a fixed supervised probe '
                    'do better than fixed classical features?',
        'configuration': {'label': '58-channel configuration', 'note': 'the same channels, people, folds and probe as '
                                                                      'the 58-channel classical result'},
        'same_cohort_as': ORTH64, 'classical_rows_same_as': ORTH58,
        'model_family': 'foundation', 'foundation_model': True, 'encoder': 'frozen', 'fine_tuning': False, 'lora': False,
        'leaderboard': False,
        'model': {
            'name': model['name'], 'method_slug': 'eegpt', 'paper': model['paper_url'], 'paper_title': model['paper_title'],
            'repository': model['official_repository_url'], 'source_revision': model['source_revision'],
            'checkpoint': {'file': model['original_filename'], 'sha256': model['original_checkpoint_sha256'],
                           'link': model['original_checkpoint_url'],
                           'tensor_conversion_sha256': model['tensor_checkpoint_sha256']},
            'encoder_parameters': model['target_encoder_parameters'],
            'code_licence': model['source_code_license'],
            'code_licence_scope': 'the repository’s source code only',
            'weights_licence': None,
            'weights_licence_status': 'unresolved: the checkpoint’s own licence and terms could not be read from its '
                                      'hosting record, and the repository’s code licence is not evidence that it covers '
                                      'the weights',
            'weights_distributed': False,
            'weights_note': 'no original or converted weights are distributed; the hashes identify the checkpoint used '
                            'and grant nothing',
        },
        'pretraining_exposure': {'status': 'not established',
                                 'statement': 'Overlap between this dataset and EEGPT’s pretraining data has not been '
                                              'excluded; nothing here certifies that these recordings were unseen.'},
        'transfer': 'supervised: the frozen encoder’s outputs feed a probe trained on the other seven people’s labels; '
                    'not zero-shot',
        'task': ORTH_TASK,
        'cohort': orth_cohort(ms, label),
        'signal': orth_signal(ms, 58),
        'encoder_input': {'channels': model['architecture']['img_size'][0],
                          'samples': ms['encoder_resampling']['output_samples'],
                          'sampling_hz': ms['encoder_resampling']['output_sampling_hz']},
        'metric': 'balanced_accuracy', 'secondary_metrics': ['auroc', 'average_precision'], 'chance_level': 0.5,
        'weighting': ORTH_WEIGHTING,
        'arms': arms,
        'paired': {
            'comparison': 'frozen EEGPT minus the matched 58-channel classical features, the same people and folds',
            'balanced_accuracy_difference': {'mean': d, 'interval_95': iv},
            'interval_excludes_zero': iv[0] > 0 or iv[1] < 0, 'people': ORTH_PEOPLE,
            'note': 'the two arms and their difference share the same 10,000 person-bootstrap draws',
        },
        'permutation_control': {
            'eegpt2048': perms['eegpt2048'], 'classical58': perms['classical58'],
            'design': 'twenty training-label shuffles within person and run per fold, preserving run class counts; each '
                      'shuffled label vector is used for both representations and held-out labels stay original; '
                      'diagnostic controls, not a full permutation significance test',
        },
        'fits': {'folds': ORTH_PEOPLE, 'sealed_arms_per_fold': sealed_arms, 'fitted_probes': probes},
        'prior_exposure': 'The 64-channel classical scores were seen before this comparison was frozen: a prospective '
                          'diagnostic, not a blind confirmatory comparison.',
        'method': {
            'signal': 'header scales applied once to obtain microvolts; the recorded FCz reference kept and acceleration '
                      'excluded; continuous forward-only fourth-order 1–30 Hz filtering of all 64 channels, then the fixed '
                      '58-channel intersection',
            'window': 'exactly the complete 0–0.5 second window after each event: 250 samples at 500 Hz',
            'encoder': 'fixed 64/125 polyphase resampling to 256 Hz with numerical boundary extension that adds no '
                       'observed time; microvolts divided by 1000; the encoder frozen',
            'probe': 'a training-only StandardScaler and a balanced L2 logistic regression, C=1, liblinear, maximum '
                     '2,000 iterations and the 0.5 decision rule, the same for both representations; no hyperparameter '
                     'search, change to the encoder’s weights, LoRA or fine-tuning',
            'sealing': 'all eight folds sealed before separate scoring',
        },
        'uncertainty': {**ORTH_UNCERTAINTY,
                        'paired': 'the paired interval resamples matched per-person differences, not the gap between '
                                  'two separate intervals'},
        'reading': 'Frozen EEGPT with the fixed supervised probe is slightly below the matched 58-channel classical '
                   'features on balanced accuracy, and the paired interval spans zero. This pilot establishes no '
                   'advantage for either arm, and neither equivalence nor a general inferiority of EEG foundation '
                   'models.',
        'limitations': [
            'One short-window supervised transfer setup on eight people: the frozen encoder feeds a probe trained on '
            'the other seven people’s labels. Not zero-shot and not a verified unseen-dataset test.',
            'The 64-channel classical scores were seen before this comparison was frozen: a prospective diagnostic, not '
            'a blind confirmatory comparison.',
            'Montage, filtering, reference, scaling, population and the half-second, two-patch context differ from '
            'EEGPT’s pretraining; running it natively does not establish that the transfer suits it.',
            'Overlap between this dataset and EEGPT’s pretraining data has not been excluded.',
            'The labels are recorded injected device events; movement, muscle and device artifacts may contribute. '
            'There is no subjective-recognition, isolated-neural, online, clinical or population claim.',
            'The response-clean subset (5 standard events, 446 errors) stays out of the comparison.',
            'Audit scope: the independent audit recomputed all 720 metric rows, 270 aggregate and interval rows and '
            'both paired intervals, and 24 source-only refits reproduced the sealed probabilities exactly; it did not '
            're-extract the encoder features or refit every permutation probe.',
        ],
        'release_limits': export['limitations'],
        'claims_not_supported': [
            'no advantage for either arm, and not equivalence',
            'not zero-shot transfer and not a verified unseen-dataset test',
            'not evidence about EEG foundation models in general',
            'no online, clinical or isolated neural decoding claim',
            'not new dataset or person coverage',
        ],
        'independent_audit': {
            'status': 'pass', 'people': audit['people'], 'metric_rows_recomputed': audit['all_metric_rows_recomputed'],
            'aggregate_rows_recomputed': audit['all_aggregates_recomputed'],
            'source_only_refits': audit['source_only_refits'],
            'largest_refit_difference': audit['maximum_refit_probability_difference'],
            'not_checked': 'the encoder features were not re-extracted and the permutation probes were not all refitted',
        },
    }
    written_from(result, (addendum, decision_doc, json.dumps(export)), label)
    return result, export


# ---------------------------------------------------------------------------- BINGO
BINGO_DIRS = (('train_gr_test_gr', 'Greek → Greek', 'Greek', 'Greek', 'within-language'),
              ('train_gr_test_eng', 'Greek → English', 'Greek', 'English', 'cross-language'),
              ('train_eng_test_eng', 'English → English', 'English', 'English', 'within-language'),
              ('train_eng_test_gr', 'English → Greek', 'English', 'Greek', 'cross-language'))
BINGO_FIELDS, BINGO_TRIALS, BINGO_CLASSES = 17, 5100, 15
TOP3_TOLERANCE = 0.02   # the reading "close to its 20% prior": every top-3 mean within two points of it


def bingo(src, record):
    label = BINGO
    export, export_sha = pinned(src['export'], f'{label} export')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    final, _ = pinned(src['finalization'], f'{label} finalization')
    qa, qa_sha = pinned(src['payloadQa'], f'{label} payload QA')
    audit, audit_sha = pinned(src['resultAudit'], f'{label} result audit')
    prov, prov_sha = pinned(src['provenanceDecision'], f'{label} provenance decision')
    docs = record['sourceDocuments']
    v2 = flat(pinned_text(docs['datasetDocumentation']['text'], f'{label} D3.1 version 2.0'))
    v3 = flat(pinned_text(docs['consentDocument']['text'], f'{label} D3.1 version 3.0'))

    require(final['status'] == 'approved_aggregate_only' and final['approved_export_sha256'] == export_sha
            and final['approved_export'] == in_batch(src['export']) and final['internal_handoff_sha256']
            == src['handoff']['sha256'] and final['independent_payload_review_sha256'] == qa_sha
            and final['independent_result_audit_sha256'] == audit_sha and final['numerical_payload_unchanged_from_qa'] is True
            and final['no_website_edits_or_cross_session_contact'] is True, f'{label}: the finalization does not bind these bytes')
    rf = qa['reviewed_files']
    require(qa['status'] == 'approved_for_parent_finalization' and qa['unresolved_issues'] == []
            and rf[in_batch(src['resultAudit'])] == audit_sha and rf[in_batch(src['provenanceDecision'])] == prov_sha
            and rf['review/bingo-dimensionless-transfer-v1-aggregate-candidate.json']
            == export['reproducibility']['aggregate_candidate_sha256'] and qa['website_edited'] is False,
            f'{label}: the payload QA did not pass these bytes')
    require(audit['status'] == 'pass_independent_derived_result_audit' and audit['source_defined_fields'] == BINGO_FIELDS
            and audit['retained_trials'] == BINGO_TRIALS and audit['independent_main_control_refits'] == 102
            and audit['independent_permutation_refits'] == 0 and audit['max_refit_abs_error'] == 0.0
            and audit['max_stored_model_abs_error'] == 0.0 and audit['all_metric_bootstrap_checks'] is True,
            f'{label}: the result audit did not pass')
    require(export['release_status'] == 'approved_aggregate_only' and export['release_review_sha256'] == qa_sha
            and export['reproducibility']['independent_audit_receipt_sha256'] == audit_sha,
            f'{label}: the export names another QA or audit')
    require(prov['source_url'] == export['source_url'] == record['source'] and prov['raw_redistribution'] is False,
            f'{label}: another source page')
    require(export['source_defined_subject_fields'] == BINGO_FIELDS and export['retained_trials'] == BINGO_TRIALS
            and export['classes'] == BINGO_CLASSES and len(export['canonical_order']) == BINGO_CLASSES
            and export['channel_count'] == 19 and export['sample_rate_hz'] == 300
            and export['nominal_window_seconds'] == [0, 1.5] and export['features'] == 76
            and export['trained_encoder'] is False, f'{label}: another design')
    prior = export['class_prior_balanced_accuracy']
    close(prior, 1 / BINGO_CLASSES, f'{label}: the class prior', 1e-15)
    other = export['other']
    require(len(other) == 4 * 24, f'{label}: the control entries are not four directions of 24')

    def m(entry, where, hi=1.0):
        return {'mean': entry['mean'], 'interval_95': bounded(entry['mean'], entry['percentile_2_5_97_5'], where, 0.0, hi)}

    directions, conf = [], qa['confirmed_display_values']
    for key, name, train, test, kind in BINGO_DIRS:
        where = f'{label}/{key}'
        main = m(export['main'][key], where)
        top3 = m(other[f'{key}/main/top3_accuracy'], f'{where}/top3')
        order = m(other[f'{key}/order/balanced_accuracy'], f'{where}/order')
        art = m(other[f'{key}/artifact/balanced_accuracy'], f'{where}/high-frequency')
        pri = other[f'{key}/prior/balanced_accuracy']
        require(pri['mean'] == prior and pri['percentile_2_5_97_5'] == [prior, prior], f'{where}: the prior is not 1/15')
        shuffles = [other[f'{key}/permutation_{i:02d}/balanced_accuracy']['mean'] for i in range(20)]
        shuf = replicate_summary(shuffles, f'{where} shuffles', 20)
        require(main['interval_95'][0] <= prior <= main['interval_95'][1],
                f'{where}: the interval no longer holds the prior; the reading must be reviewed')
        require(abs(top3['mean'] - 3 / BINGO_CLASSES) < TOP3_TOLERANCE, f'{where}: top-3 is no longer near its prior')
        c = conf[key]
        require(c['balanced_accuracy_percent'] == round(100 * main['mean'], 2) and c['top3_percent']
                == round(100 * top3['mean'], 2) and c['order_percent'] == round(100 * order['mean'], 2)
                and c['artifact_percent'] == round(100 * art['mean'], 2)
                and c['shuffle_mean_percent'] == round(100 * shuf['balanced_accuracy_mean'], 2)
                and c['shuffle_range_percent'] == [round(100 * v, 2) for v in shuf['observed_range']],
                f'{where}: the QA’s confirmed values are not these')
        stated(handoff, f'| {name} | {pct(main["mean"])}% | {pct(main["interval_95"][0])}–{pct(main["interval_95"][1])}% '
                        f'| {pct(top3["mean"])}% |', where)
        stated(handoff, f'| {name} | {pct(order["mean"])}% | {pct(art["mean"])}% | {pct(shuf["balanced_accuracy_mean"])}% '
                        f'| {pct(shuf["observed_range"][0])}–{pct(shuf["observed_range"][1])}% |', where)
        directions.append({
            'id': key, 'label': name, 'train_language': train, 'test_language': test, 'kind': kind,
            'balanced_accuracy': main, 'top3_accuracy': top3,
            'controls': {
                'order_only': {'label': 'Order-only control', 'balanced_accuracy': order},
                'high_frequency_ratio': {'label': 'High-frequency ratio control', 'balanced_accuracy': art},
                'class_prior': {'label': 'Class prior', 'balanced_accuracy': {'mean': pri['mean']}},
                'label_shuffle': {'label': 'Training-label shuffles', 'balanced_accuracy': shuf},
            },
        })
    by = {d['id']: d['balanced_accuracy']['mean'] for d in directions}
    ct = export['contrasts']
    close(ct['gr_cross_minus_within']['mean'], by['train_gr_test_eng'] - by['train_gr_test_gr'], f'{label}: Greek contrast')
    close(ct['eng_cross_minus_within']['mean'], by['train_eng_test_gr'] - by['train_eng_test_eng'], f'{label}: English contrast')
    close(ct['transfer_minus_within']['mean'],
          (ct['gr_cross_minus_within']['mean'] + ct['eng_cross_minus_within']['mean']) / 2, f'{label}: the contrast')
    contrast = {k: {'mean': ct[k]['mean'], 'interval_95': bounded(ct[k]['mean'], ct[k]['percentile_2_5_97_5'],
                                                                  f'{label}/{k}', -1.0, 1.0)}
                for k in ('transfer_minus_within', 'gr_cross_minus_within', 'eng_cross_minus_within')}
    civ = contrast['transfer_minus_within']['interval_95']
    require(civ[0] < 0 < civ[1], f'{label}: the contrast interval no longer spans zero; the reading must be reviewed')
    require(conf['transfer_minus_within_percentage_points'] == round(100 * ct['transfer_minus_within']['mean'], 2)
            and conf['contrast_interval_percentage_points'] == [round(100 * v, 2) for v in civ],
            f'{label}: the QA’s contrast is not this')
    stated(handoff, f'**{100 * ct["transfer_minus_within"]["mean"]:+.2f} percentage points**, with a descriptive interval '
                    f'of **{100 * civ[0]:.2f} to {100 * civ[1]:+.2f} points**', label)
    for phrase in ('Seventeen complete source-defined subject fields contribute 5,100 trials.',
                   'Each held-out field supplies 150 Greek and 150 English trials, with ten trials per noun and language.',
                   'Training uses only one language from the other sixteen fields (2,400 rows).',
                   'produce 34 main models, 68 order/high-frequency controls, 680 shuffled-label fits and 34 unfitted '
                   'class-prior predictions. All 816 prediction checkpoints were sealed before any scoring.',
                   'reconstructed all 782 fitted-model predictions and independently refitted all 102 main/control models',
                   'Python samples 749:1199, exactly 450 samples', 'producing 76 features'):
        stated(handoff, phrase, label)
    require(audit['sealed_model_checkpoints'] == 816, f'{label}: another checkpoint count')

    # The source's own documents: the protocol and the delivered preprocessing (D3.1 version 2.0), and the project's
    # own subject-independent result on its other dataset (D3.1 version 3.0).
    for phrase in ('t = -2.5 s: A randomly selected lexical item is presented on the screen', 't = -1 s: The lexical item '
                   'is removed from the screen', 'A countdown takes place', 't = 0 s: A fixation cross (“+”) appears',
                   't = 1.5 s: The fixation cross disappears, marking the end of the trial',
                   'Each participant completes ten (10) repetitions per lexical item, with trial order fully randomized',
                   'we identified 15 words in English and Greek', 'Bandpass Filtering (1–145 Hz)',
                   'Notch Filtering at 50 Hz and Harmonics', 'Artifact Subspace Reconstruction (ASR)',
                   'FORCe-Based Artifact Removal', 'to remove ocular (e.g., eye blinks and saccades) and muscle-related (EMG) '
                   'activity', 'Trial-Based Segmentation', 'Both EEG datasets underwent the following preprocessing steps'):
        stated(v2, phrase, f'{label} D3.1 version 2.0')
    reported = re.search(r'EEGNet achieves an overall mean accuracy of ([\d.]+)%, indicating performance at chance level '
                         r'when evaluated on unseen subjects', v3)
    require(reported is not None and 'LOSO-CV (26-class)' in v3 and 'EEG data were collected from 20 participants over '
            'three sessions, using a 26-word vocabulary' in v3, f'{label}: D3.1 version 3.0 no longer reports it')

    v2_url, v3_url = docs['datasetDocumentation']['url'], docs['consentDocument']['url']
    result = {
        'id': BINGO, 'dataset': 'bingo-imagined-speech', 'pilot': 'bingo',
        'title': 'Inner speech in Greek and English: across people and across languages',
        'question': 'Can a fixed spectral baseline trained on other people decode which of 15 nouns someone imagined '
                    'saying, and does training in one language carry over to the other?',
        'kind': 'negative result', 'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'leaderboard': False,
        'task': '15-class classification of inner speech of 15 matched nouns in Greek and in English, from the 0–1.5 '
                'second inner-speech window that starts when the fixation cross appears; each source field is held out '
                'whole, both of its languages excluded from every fitted operation',
        'cohort': {
            'source_fields': export['source_defined_subject_fields'], 'trials': export['retained_trials'],
            'trials_per_held_out_field': {'greek': 150, 'english': 150}, 'trials_per_noun_and_language': 10,
            'training_rows': 2400,
            'counting_unit': 'source-defined subject fields: the operational groups; biological identity and cross-day '
                             'grouping were not independently certified',
            'incomplete_field': 'one incomplete field excluded by the prospective complete-record rule; no exclusion '
                                'depended on a score',
        },
        'signal': {'channels': export['channel_count'], 'sampling_hz': export['sample_rate_hz'],
                   'window_seconds': export['nominal_window_seconds'], 'window_samples': 450,
                   'values_per_trial': export['features']},
        'classes': export['classes'],
        'chance': {'balanced_accuracy': prior, 'top3_accuracy': 3 / BINGO_CLASSES,
                   'note': 'balanced 15-class prior; top-3 prior is three in fifteen'},
        'metric': 'balanced_accuracy', 'secondary_metrics': ['top3_accuracy'],
        'weighting': 'field-equal: the mean over the 17 held-out fields',
        'directions': directions,
        'contrast': {
            'comparison': 'cross-language minus within-language balanced accuracy, the mean over the two training '
                          'languages; the same held-out fields',
            'balanced_accuracy_difference': contrast['transfer_minus_within'],
            'interval_excludes_zero': civ[0] > 0 or civ[1] < 0,
            'by_training_language': {
                'greek': {'comparison': 'trained on Greek: tested on English minus tested on Greek',
                          'balanced_accuracy_difference': contrast['gr_cross_minus_within']},
                'english': {'comparison': 'trained on English: tested on Greek minus tested on English',
                            'balanced_accuracy_difference': contrast['eng_cross_minus_within']},
            },
        },
        'fits': {'main_models': 34, 'order_and_high_frequency_controls': 68, 'shuffled_label_fits': 680,
                 'class_prior_outputs': 34, 'sealed_checkpoints': audit['sealed_model_checkpoints']},
        'method': {
            'window': 'the stored time vectors verify the half-open 0–1.5 second action window at 300 Hz',
            'inputs': 'per trial and channel, max-absolute scaling and demeaning, then Hann periodograms; four relative '
                      'bands partition 1–30 Hz across 19 source-order channels; no guessed voltage calibration, '
                      'montage interpolation or re-referencing',
            'model': 'a source-only StandardScaler and RidgeClassifier with fixed alpha 1 and the Cholesky solver; no '
                     'tuning against held-out scores; ties broken by a fixed noun order',
            'controls': 'an order-only control, a high-frequency ratio control, the class prior and 20 training-label '
                        'shuffles per direction',
            'sealing': 'all 816 checkpoints sealed before any scoring',
        },
        'uncertainty': {
            'kind': 'approximate descriptive 2.5–97.5% intervals from 10,000 field bootstrap draws',
            'conditional_on': 'fixed predictions from overlapping leave-one-field-out fits: training refit variability '
                              'is omitted, and they are not calibrated population confidence intervals',
        },
        'protocol': {
            'nouns': 15, 'languages': ['Greek', 'English'],
            'timeline_seconds': {'word_shown': -2.5, 'word_removed_countdown': -1.0, 'fixation_inner_speech_onset': 0.0,
                                 'end': 1.5},
            'repetitions_per_noun': 10, 'order': 'fully randomized across the session',
            'source': f'BINGO deliverable D3.1, version 2.0, the cross-linguistic protocol ({v2_url})',
        },
        'delivered_signal': {
            'statement': 'The project documents the same preprocessing for both of its released datasets: band-pass '
                         'filtering from 1 to 145 Hz, notch filtering at 50 Hz and its harmonics, Artifact Subspace '
                         'Reconstruction (ASR), FORCe removal of ocular and muscle artifacts, and then segmentation '
                         'into trials. The signals analysed here were therefore artifact-cleaned on the continuous '
                         'recordings before any trial was cut.',
            'source': f'BINGO deliverable D3.1, version 2.0, pre-processing and denoising ({v2_url}), read '
                      f'{record["reviewedAt"]}',
            'verified_against_file': False,
            'note': 'as the project states it; not re-verified against the delivered file',
        },
        'project_reported': {
            'kind': 'reported by the BINGO project on its other dataset; not run here and not comparable with the '
                    'results above',
            'dataset': 'the project’s NATO-alphabet inner-speech dataset: 20 participants, 26 words, three sessions',
            'evaluation': 'EEGNet, leave-one-subject-out, 26 classes',
            'mean_accuracy_percent': float(reported.group(1)), 'classes': 26,
            'chance_level': 1 / 26,
            'reading': 'the deliverable reports performance at chance level for people the model was not trained on',
            'source': f'BINGO deliverable D3.1, version 3.0, section 4 ({v3_url})',
        },
        'reading': 'Every direction is close to the 15-class prior of 6.67%, with each interval holding it, and top-3 '
                   'accuracy is close to its 20% prior. The cross-language-minus-within-language contrast is small and '
                   'its interval spans zero. A negative result for this baseline in this setting: it does not show '
                   'that inner speech cannot be decoded by other methods.',
        'limitations': [
            'One fixed spectral baseline: no EEG foundation model, PEFT or deep model was evaluated.',
            'Source-defined subject fields are the operational groups; biological identity and cross-day grouping '
            'were not independently certified.',
            'The delivered signals were already cleaned by the project (ASR and FORCe on the continuous recordings, by '
            'its own account); physical amplitude units, the named montage and the measured display latency are not '
            'established.',
            'The nominal window was verified against the stored time vectors; that does not certify causal or online '
            'processing, brain-only signal origin, full BINGO coverage or cross-day performance.',
            'The intervals are approximate and descriptive: fixed overlapping leave-one-field-out fits, no refit '
            'variability, not calibrated population confidence intervals. The shuffles measure sensitivity to the '
            'training labels and are not a calibrated randomization test.',
            'The contrast is not superiority, equivalence, a significance test or a reliable transfer gain.',
        ],
        'release_limits': export['limits'],
        'claims_not_supported': [
            'not evidence that inner speech cannot be decoded',
            'no superiority or equivalence between languages, and no significance test',
            'no online, real-time or brain-only decoding claim',
            'not a foundation-model ranking, and no medical or diagnostic claim',
        ],
        'independent_audit': {
            'status': 'pass', 'source_fields': audit['source_defined_fields'],
            'refitted_models': audit['independent_main_control_refits'], 'reconstructed_models': 782,
            'refitted_shuffle_models': audit['independent_permutation_refits'],
            'largest_refit_difference': audit['max_refit_abs_error'],
            'not_checked': 'the 680 shuffle models were reconstructed, not refitted, and the raw file was not '
                           're-extracted: the audit used cached features and verified lineage receipts',
        },
    }
    written_from(result, (handoff, json.dumps(export), v2, v3, json.dumps(docs)), label)
    return result, export


# ---------------------------------------------------------------------------- handwriting
HAND_ARMS = {
    'relative_eeg': ('Mask-aware relative EEG', 'EEG',
                     '295 channel-major relative Welch band-power slots from the available channels, zero where a '
                     'channel is unavailable'),
    'mask_only': ('Missingness mask only', 'control', '59 availability bits plus the available-channel fraction'),
    'time_only': ('Elapsed time / trial order', 'control', 'onset, log1p(onset), trial rank and rank over count'),
    'mask_plus_time': ('Mask + time', 'control', 'the mask and time controls together'),
    'majority': ('Training-majority control', 'control', 'the most frequent class of the four training people'),
}
HAND_CONTRASTS = {
    'relative_eeg_minus_mask_only': ('mask_only', 'Relative EEG minus missingness mask only'),
    'relative_eeg_minus_time_only': ('time_only', 'Relative EEG minus elapsed time / trial order'),
    'relative_eeg_minus_mask_plus_time': ('mask_plus_time', 'Relative EEG minus mask + time'),
}
HAND_SHUFFLED = ('relative_eeg', 'mask_only', 'time_only', 'mask_plus_time')
HAND_PEOPLE, HAND_SESSIONS, HAND_EVENTS, HAND_TRIALS, HAND_CHANNELS = 5, 45, 1620, 1618, 59


def handwriting(src):
    label = HAND
    export, export_sha = pinned(src['export'], f'{label} export')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    final, _ = pinned(src['finalization'], f'{label} finalization')
    qa, qa_sha = pinned(src['payloadQa'], f'{label} payload QA')
    audit, audit_sha = pinned(src['resultAudit'], f'{label} result audit')
    earlier, earlier_sha = pinned(src['earlierExport'], f'{label} earlier export')
    earlier_handoff = pinned_text(src['earlierHandoff'], f'{label} earlier handoff')
    earlier_check, _ = pinned(src['earlierCheck'], f'{label} earlier check')
    earlier_audit, earlier_audit_sha = pinned(src['earlierAudit'], f'{label} earlier audit')

    require(final['status'] == 'approved_aggregate_diagnostic_only' and final['result_audit']['sha256'] == audit_sha
            and final['independent_payload_qa']['sha256'] == qa_sha
            and final['final_output_hashes'] == {in_batch(src['export']): export_sha,
                                                 Path(src['handoff']['path']).name: src['handoff']['sha256']}
            and final['numerical_results_unchanged'] is True and final['no_official_test_signals_or_labels_used'] is True
            and final['exact_allowed_changes_only'] is True, f'{label}: the finalization does not bind these bytes')
    require(qa['verdict'] == 'pass' and qa['issues'] == [] and qa['input_sha256'][in_batch(src['resultAudit'])]
            == audit_sha, f'{label}: the payload QA did not pass')
    require(audit['status'] == 'pass_independent_derived_result_audit' and audit['people'] == HAND_PEOPLE
            and audit['eligible_trials'] == HAND_TRIALS and audit['quarantine_rows'] == 2 and audit['sealed_checkpoints'] == 125
            and audit['reconstructed_models'] == 120 and audit['independent_true_label_refits'] == 20
            and audit['independent_permutation_refits'] == 0 and audit['max_refit_abs_error'] == 0.0
            and audit['max_stored_model_abs_error'] == 0.0 and audit['all_metric_bootstrap_checks'] is True,
            f'{label}: the result audit did not pass')
    require(export['status'] == 'approved_for_aggregate_diagnostic_website_handoff' and export['release_qa']['sha256'] == qa_sha
            and export['publication']['public_leaderboard_eligible'] is False and export['publication']['aggregate_only'] is True
            and export['publication']['participant_rows_included'] is False, f'{label}: not the approved export')
    s = export['source']
    require(s['revision'] == '4036680b5fb0015472d55589da2f34c5a87a3c10' and s['declared_license'] == 'cc-by-nc-sa-4.0',
            f'{label}: another revision or licence')
    co = export['cohort']
    require(co['development_people'] == HAND_PEOPLE and co['sessions'] == HAND_SESSIONS and co['original_events']
            == HAND_EVENTS and co['eligible_trials'] == HAND_TRIALS and co['preserved_quarantines'] == 2
            and co['classes'] == 4, f'{label}: another cohort')
    me = export['method']
    require(me['fit_count'] == 120 and me['sealed_checkpoints'] == 125, f'{label}: other fit counts')
    ec = earlier_check['evidence_hashes']
    require(earlier_check['status'] == 'approved' and ec['handoff_sha256'] == src['earlierHandoff']['sha256']
            and ec['public_export_sha256'] == earlier_sha and ec['result_audit_sha256'] == earlier_audit_sha
            and earlier_audit['public_export'] == in_batch(src['earlierExport']), f'{label}: the earlier analysis chain')

    r = export['results']['primary_and_contrasts']
    arms = {}
    for a, (name, kind, desc) in HAND_ARMS.items():
        e = r['arms'][a]
        arms[a] = {'label': name, 'kind': kind, 'description': desc,
                   'balanced_accuracy': {'mean': e['mean'], 'interval_95': bounded(e['mean'], e['percentile_2_5_97_5'],
                                                                                    f'{label}/{a}', 0.0, 1.0)}}
    require(set(r['arms']) == set(HAND_ARMS) and arms['majority']['balanced_accuracy']['mean'] == 0.25
            and arms['majority']['balanced_accuracy']['interval_95'] == [0.25, 0.25], f'{label}: other arms or majority')
    contrasts = {}
    for k, (other, name) in HAND_CONTRASTS.items():
        e = r['contrasts'][k]
        close(e['mean'], arms['relative_eeg']['balanced_accuracy']['mean'] - arms[other]['balanced_accuracy']['mean'],
              f'{label}/{k}: the paired mean')
        iv = bounded(e['mean'], e['percentile_2_5_97_5'], f'{label}/{k}', -1.0, 1.0)
        contrasts[k] = {'label': name, 'balanced_accuracy_difference': {'mean': e['mean'], 'interval_95': iv},
                        'interval_excludes_zero': iv[0] > 0 or iv[1] < 0}
    require(contrasts['relative_eeg_minus_mask_only']['interval_excludes_zero']
            and contrasts['relative_eeg_minus_mask_plus_time']['interval_excludes_zero']
            and not contrasts['relative_eeg_minus_time_only']['interval_excludes_zero']
            and arms['relative_eeg']['balanced_accuracy']['interval_95'][0] > 0.25,
            f'{label}: the contrasts changed sides; the reading must be reviewed')
    pm = export['results']['permutation_person_macro_ba']
    shuffles = {}
    for a in HAND_SHUFFLED:
        vals = [pm[f'{a}/seed{20261012 + i}'] for i in range(5)]
        shuffles[a] = replicate_summary(vals, f'{label}/{a} shuffles', 5)
    require(len(pm) == 20, f'{label}: not five shuffles per representation')
    raw, fin = export['results']['raw_mask_distribution'], export['results']['final_mask_distribution']
    require(raw == fin and sum(fin.values()) == HAND_TRIALS, f'{label}: the availability histograms differ')
    counts = sorted((int(k), v) for k, v in fin.items())
    rc = export['results']['reason_counts']
    require(rc['upper_rail'] == rc['nonfinite'] == rc['denominator_invalid'] == 0, f'{label}: other flags')

    pct2 = lambda x: f'{100 * x:+.2f}'
    for a, (name, _, _) in HAND_ARMS.items():
        b = arms[a]['balanced_accuracy']
        stated(handoff, f'| {name} | {pct(b["mean"])}% | {pct(b["interval_95"][0])}–{pct(b["interval_95"][1])}% |', label)
    for k, c in contrasts.items():
        d = c['balanced_accuracy_difference']
        stated(handoff, f'| {c["label"]} | {pct2(d["mean"])} pp | {pct2(d["interval_95"][0])} to {pct2(d["interval_95"][1])} '
                        'pp |', label)
    for a in HAND_SHUFFLED:
        sh = shuffles[a]
        stated(handoff, f'| {HAND_ARMS[a][0]} | {pct(sh["balanced_accuracy_mean"])}% | {pct(sh["observed_range"][0])}–'
                        f'{pct(sh["observed_range"][1])}% |', label)
    hist = ', '.join(f'{v:,} retain {k}' if i else f'{v:,} trials retain {k} channels' for i, (k, v) in enumerate(counts[:-1]))
    stated(handoff, f'{hist} and {counts[-1][1]} retain {counts[-1][0]}', label)
    stated(handoff, f'Across {HAND_TRIALS * HAND_CHANNELS:,} channel-trials, {rc["constant"]:,} trigger the constant flag '
                    f'and {rc["lower_rail"]:,} the lower-rail flag.', label)
    stated(handoff, 'The unchanged development cohort contains five people, 45 sessions and 1,618 eligible trials from '
                    '1,620 events.', label)

    # The earlier analysis: context, the same cohort.
    ea = {a['arm']: a for a in earlier['aggregate']}
    require(earlier['people'] == HAND_PEOPLE and earlier['sessions'] == HAND_SESSIONS
            and earlier['eligible_trials'] == HAND_TRIALS and earlier['release']['leaderboard_eligible'] is False,
            f'{label}: the earlier analysis is another cohort')
    earlier_arms = {}
    for a, name in (('logistic', 'EEG spectral logistic regression'), ('shrinkage_lda', 'EEG spectral shrinkage LDA')):
        mean = ea[a]['person_mean']['balanced_accuracy']
        iv = bounded(mean, ea[a]['person_bootstrap_95ci']['balanced_accuracy'], f'{label} earlier/{a}', 0.0, 1.0)
        earlier_arms[a] = {'label': name, 'balanced_accuracy': {'mean': mean, 'interval_95': iv}}
        stated(earlier_handoff, f'| {name} | {pct(mean)}% | {pct(iv[0])}–{pct(iv[1])}% |', label)
    q, bq = earlier['quality_flags'], earlier['bounded_posthoc_quality']
    require(q['digital_rail']['epochs'] == q['digital_rail']['total_eligible_epochs'] == HAND_TRIALS,
            f'{label}: the earlier rail flag')
    stated(earlier_handoff, f'All {HAND_TRIALS:,} scored windows contain at least one selected-channel sample at a '
                            f'header-declared digital rail. Separately, {q["ptp_greater_than_500uV"]["epochs"]} windows', label)
    stated(earlier_handoff, f'Of {bq["total_channel_windows"]} channel-windows, {bq["rail_flat_channel_windows"]} were flat',
           label)
    # Five people. No per-person value is in the export, and the pooled block is not published; but a percentile of
    # resampled five-person means is one person's score where the scores tie, and the mask-only control's scores sit so
    # close to 25% that its bounds would show individual people's scores. Its interval is withheld, and its bounds are
    # checked absent from the file. (The majority control scores chance for every person by construction.)
    secret = [v for v in arms['mask_only']['balanced_accuracy']['interval_95'] if v != 0.25]
    arms['mask_only']['balanced_accuracy']['interval_95'] = None
    arms['mask_only']['interval_note'] = ('not published: with five people, this control’s bootstrap bounds would show '
                                          'individual people’s scores')

    result = {
        'id': HAND, 'dataset': 'eeg-fnirs-handwriting', 'pilot': 'handwriting',
        'title': 'Mask-aware EEG: a five-person development diagnostic',
        'question': 'When channels that sit flat at a digital rail are masked, what is left, and does it predict four '
                    'released labels better than the masks and the clock do?',
        'kind': 'data-quality and methods case study', 'model_family': 'classical', 'foundation_model': False,
        'fine_tuning': False, 'leaderboard': False,
        'task': 'four released coded labels, 0 to 3 (events 200 to 203), from a fixed window 0.5–4.5 seconds after the '
                'released EEG-relative onset; glyph identity and continuous trajectories are not established, so this '
                'is not handwriting recognition',
        'cohort': {
            'people': co['development_people'], 'sessions': co['sessions'], 'events': co['original_events'],
            'trials': co['eligible_trials'], 'quarantined_events': co['preserved_quarantines'], 'classes': co['classes'],
            'reuse': 'a reused development cohort: the same five training people as the earlier analysis, whose scores '
                     'were seen before this design; not a new or independent cohort',
            'split': 'five leave-one-person-out folds; every session of the held-out person excluded from fitting',
            'official_test': 'the official ten-person test signals and reference labels were not used; earlier intake '
                             'inspected unlabeled test metadata, and this analysis made no further test access',
        },
        'metric': 'balanced_accuracy', 'chance_level': 0.25,
        'weighting': 'the unweighted mean of the five held-out people’s balanced accuracy',
        'arms': arms,
        'contrasts': contrasts,
        'label_shuffle': {
            'representations': {a: shuffles[a] for a in HAND_SHUFFLED},
            'design': 'five fixed training-label shuffles per representation, preserving source person and session; '
                      'sensitivity controls, not a full permutation significance test'},
        'availability': {
            'channels_recorded': HAND_CHANNELS,
            'available_channels_per_trial': {'fewest': counts[0][0], 'most': counts[-1][0]},
            'trials_by_available_channels': [{'channels': k, 'trials': v} for k, v in counts],
            'channel_trials': HAND_TRIALS * HAND_CHANNELS,
            'flags': {'constant': rc['constant'], 'lower_rail': rc['lower_rail'], 'upper_rail': rc['upper_rail'],
                      'nonfinite': rc['nonfinite'], 'invalid_denominator': rc['denominator_invalid']},
            'flags_note': 'the constant and lower-rail flags overlap and must not be summed',
            'available_means': 'nonconstant, not touching either header-declared digital rail and numerically valid '
                               'under a fixed rule: not certified clean physiological EEG',
            'scope': 'counts for the selected cohort only, not the whole source dataset',
        },
        'earlier_analysis': {
            'relation': 'the same five people, sessions and trials, analysed earlier with all-channel common-average '
                        'referencing and log band power: context, not a second cohort',
            'arms': earlier_arms,
            'quality_findings': {
                'windows': HAND_TRIALS, 'windows_with_a_rail_sample': q['digital_rail']['epochs'],
                'windows_over_500_microvolts': q['ptp_greater_than_500uV']['epochs'],
                'inspected_windows': bq['windows'], 'channel_windows': bq['total_channel_windows'],
                'rail_flat_channel_windows': bq['rail_flat_channel_windows'],
            },
            'not_attributable': 'masking, referencing and the spectral representation changed together, so the '
                                'difference between the two analyses cannot be attributed to masking, and no best '
                                'model is selected from them',
        },
        'method': {
            'window': '0.5–4.5 seconds after the released EEG-relative onset: 4,000 samples at 1,000 Hz; only the 59 '
                      'header-identified EEG channels read',
            'masking': 'constant, rail-touching or nonfinite channel-windows masked before any transform; available '
                       'channels demeaned individually; no common-average reference and no interpolation',
            'inputs': 'Welch estimates (1,000-sample Hann window, 500 overlap); five half-open bands from 1 to 45 Hz, '
                      'each divided by the sum of the five',
            'model': 'source-only standardization and balanced multinomial logistic regression, C=1, lbfgs, max_iter '
                     '2000, tolerance 1e-4, seed 20261012',
            'sealing': 'all 125 checkpoints sealed before the separate scorer opened held-out truth',
        },
        'uncertainty': {
            'kind': 'descriptive 2.5–97.5% intervals from 10,000 fixed-seed person-bootstrap draws over five people',
            'conditional_on': 'the already fitted overlapping folds: not calibrated population confidence intervals or '
                              'evidence of superiority',
        },
        'reading': 'Mask-aware relative EEG is slightly above the 25% majority control, and above the missingness-only '
                   'and mask-plus-time controls with paired intervals above zero; against the elapsed-time control the '
                   'paired interval crosses zero. Five people and four coded labels: a data-quality and methods case '
                   'study, not handwriting recognition.',
        'limitations': [
            'Five reused development people whose earlier scores were seen before this design: no independent '
            'confirmation and no population inference.',
            'Four released coded labels: glyph identity and trajectories are not established, so this is not '
            'handwriting recognition.',
            'Availability is a numerical rule, not certified clean EEG; why other channels sit flat at a digital rail '
            'is unknown.',
            'Masking, referencing and the spectral representation changed together, so no difference from the earlier '
            'analysis can be attributed to masking.',
            'The contrast with the elapsed-time control crosses zero.',
            'Optical species, units and the clock between modalities are unresolved, so no fNIRS or fusion conclusion '
            'follows; no online, physiological-origin, competition-standing or medical claim.',
            'Audit scope: all 120 stored models reconstructed and the 20 true-label models refitted independently, '
            'with no discrepancy; the shuffle models were not refitted, and the audit used cached derived artifacts, '
            'not fresh raw-feature extraction.',
        ],
        'claims_not_supported': [
            'not handwriting recognition and not glyph or trajectory decoding',
            'no superiority over the elapsed-time control',
            'no fNIRS, fusion, online, competition-standing or medical claim',
            'not a leaderboard entry or a model recommendation',
        ],
        'independent_audit': {
            'status': 'pass', 'people': audit['people'], 'reconstructed_models': audit['reconstructed_models'],
            'refitted_models': audit['independent_true_label_refits'],
            'refitted_shuffle_models': audit['independent_permutation_refits'],
            'largest_refit_difference': audit['max_refit_abs_error'],
            'not_checked': 'the raw samples were not reread and the features were not re-extracted',
        },
    }
    written_from(result, (handoff, json.dumps(export), earlier_handoff, json.dumps(earlier)), label)
    return result, (export, earlier), secret


# ---------------------------------------------------------------------------- REFED
REFED_CONDITIONS = (
    ('shared_stimulus_person_holdout', 'shared_videos_held_folder', 'Shared videos, held folder',
     'two folds: train on all 15 clips of one folder and predict the other folder; familiar stimuli can support '
     'prediction through stimulus identity'),
    ('joint_person_video_holdout', 'held_folder_and_videos', 'Jointly held folder and video IDs',
     'ten folds: each folder held out with one of five fixed three-video groups, training on the other folder’s 12 '
     'remaining videos'),
)
REFED_ARMS = {
    'eeg_ridge': ('EEG Ridge', 'EEG', '320 relative Welch band powers per clip (five bands at each of 64 channel '
                                     'positions), source-only standardization, Ridge with alpha 1'),
    'source_global_mean': ('Source global mean', 'control', 'the training clips’ mean target'),
    'source_video_lookup': ('Source video lookup', 'control', 'the training target of the same video ID, falling back '
                                                              'to the source global mean when the video is absent'),
    'duration_video_id_ridge': ('Duration / numeric-video-ID Ridge', 'control',
                                'Ridge on stored duration and the numeric video ID, a key-index proxy and not '
                                'established presentation order'),
}


def refed(src):
    label = REFED
    export, export_sha = pinned(src['export'], f'{label} export')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    check, _ = pinned(src['approval'], f'{label} handoff check')
    audit, audit_sha = pinned(src['resultAudit'], f'{label} result audit')

    require(check['status'] == 'approved' and check['handoff_sha256'] == src['handoff']['sha256']
            and check['public_export_sha256'] == export_sha and check['public_export'] == in_batch(src['export'])
            and check['result_audit_sha256'] == audit_sha and check['checks_count'] == len(check['checks']) == 15,
            f'{label}: the handoff check does not bind these bytes')
    all_true(check['checks'], f'{label} handoff check')
    require('satisfies the immutable export parent_handoff_approval_required gate' in check['integration_condition'],
            f'{label}: the check no longer resolves the export’s pending approval')
    rel = export['release']
    require(export['status'].endswith('pending_parent_handoff_approval') and rel['parent_handoff_approval_required'] is True
            and rel['aggregate_diagnostic_eligible'] is True and rel['leaderboard_eligible'] is False
            and rel['physiological_benchmark_eligible'] is False and rel['population_generalization_eligible'] is False
            and rel['crossday_eligible'] is False and rel['raw_redistribution_in_scope'] is False,
            f'{label}: not the approved diagnostic export')
    require(audit['safe_export']['sha256'] == export_sha and audit['numerical_verification']
            ['all_private_perperson_and_fold_metrics_verified'] is True and audit['checks']['assertions_passed'] == 2838
            and audit['checks']['unique_categories'] == 58 and audit['counts']['clips'] == 30
            and audit['counts']['channels_audited'] == 1920, f'{label}: the result audit did not pass these bytes')
    sm = export['sample']
    require(sm['nominal_participant_groups'] == 2 and sm['unique_shared_video_ids'] == 15 and sm['stored_clips'] == 30
            and sm['scored_clips_per_arm_per_condition'] == 30 and sm['target_axes'] == ['valence', 'arousal'],
            f'{label}: another sample')
    mt = export['metrics']
    require(mt['confidence_intervals'] is None and mt['significance_tests'] is False and mt['axis_order']
            == ['valence', 'arousal'], f'{label}: intervals or tests appeared; the result must be reviewed')
    qu = export['quality']
    require(qu['stored_clips_audited'] == 30 and qu['channel_clip_rows_audited'] == 1920 and qu['clips_or_channels_removed']
            == 0 and qu['full30_prefit_eligibility_passed'] is True and qu['physical_units_established'] is False,
            f'{label}: other quality counts')
    me = export['method']
    require(me['feature_dimensions'] == 320 and me['channel_positions'] == 64 and me['optimizer_fits'] == 24
            and me['two_axis_prediction_vectors'] == 240 and me['prediction_postprocessing'] is None,
            f'{label}: another method')

    conditions, secret = [], []
    for key, cid, name, design in REFED_CONDITIONS:
        pooled, rec, sc = mt['pooled'][key], audit['independently_recomputed_pooled_metrics'][key], me['split_conditions'][key]
        cov = mt['source_video_lookup_coverage'][key]
        arms = {}
        for a, (aname, kind, _) in REFED_ARMS.items():
            p = pooled[a]
            require(p['clips'] == 30, f'{label}/{key}/{a}: not 30 clips')
            close(p['equal_axis_mean_MAE'], sum(p['MAE_by_axis']) / 2, f'{label}/{key}/{a}: the equal-axis mean')
            close(p['equal_axis_mean_MAE'], rec[a]['equal_axis_mean_MAE'], f'{label}/{key}/{a}: the audit', 1e-9)
            require(p['equal_axis_mean_MAE'] >= 0, f'{label}/{key}/{a}: a negative error')
            arms[a] = {'label': aname, 'kind': kind, 'equal_axis_mae': p['equal_axis_mean_MAE']}
            secret += [*p['MAE_by_axis'], *p['RMSE_by_axis'], p['combined_RMSE']]
        eeg = arms['eeg_ridge']['equal_axis_mae']
        require(all(eeg > arms[a]['equal_axis_mae'] for a in REFED_ARMS if a != 'eeg_ridge'),
                f'{label}/{key}: EEG Ridge is no longer worse than every control; the reading must be reviewed')
        conditions.append({'id': cid, 'label': name, 'design': design, 'folds': sc['folds'],
                           'training_clips_per_fold': sc['training_clips_per_fold'],
                           'held_clips_per_fold': sc['held_clips_per_fold'], 'clips_scored': cov['held_clips'],
                           'lookup_matched_videos': cov['matched_source_video_ids'], 'arms': arms})
    shared, joint = conditions
    require(joint['arms']['source_video_lookup']['equal_axis_mae'] == joint['arms']['source_global_mean']['equal_axis_mae']
            and joint['lookup_matched_videos'] == 0 and shared['lookup_matched_videos'] == 30
            and min(shared['arms'], key=lambda a: shared['arms'][a]['equal_axis_mae']) == 'source_video_lookup',
            f'{label}: the lookup lesson no longer holds; the reading must be reviewed')
    for a, (aname, _, _) in REFED_ARMS.items():
        stated(handoff, f'| {aname} | {shared["arms"][a]["equal_axis_mae"]:.6f} | {joint["arms"][a]["equal_axis_mae"]:.6f} |',
               label)
    stated(handoff, 'The independent audit passed 2,838 assertions across 58 categories', label)

    result = {
        'id': REFED, 'dataset': 'refed', 'pilot': 'refed',
        'title': 'REFED: a stored-clip computational diagnostic',
        'question': 'Can whole-clip EEG band power predict a clip’s mean self-reported valence and arousal better than '
                    'simple source-only controls?',
        'kind': 'computational diagnostic', 'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'leaderboard': False,
        'cohort': {'nominal_folders': sm['nominal_participant_groups'], 'videos': sm['unique_shared_video_ids'],
                   'clips': sm['stored_clips'],
                   'note': 'two source-declared nominal participant folders with the same 15 videos; folder identity is '
                           'the grouping unit, the 30 clips are not 30 independent people, and two folders support no '
                           'population claim'},
        'target': {'axes': sm['target_axes'],
                   'scale': 'the published raw self-report scale from 1 to 255',
                   'definition': 'per axis, the mean of each clip’s complete stored label array',
                   'meaning': 'descriptive self-report means: not SAM scores and not calibrated physical or clinical '
                              'distances'},
        'metric': {'id': 'equal_axis_mae', 'name': 'Equal-axis mean absolute error',
                   'unit': 'raw label units on the 1–255 scale', 'lower_is_better': True,
                   'aggregation': 'the mean of the valence and arousal absolute errors, the 30 clips weighted equally'},
        'arms': {a: {'label': n, 'kind': k, 'description': d} for a, (n, k, d) in REFED_ARMS.items()},
        'conditions': conditions,
        'controls_lesson': 'With shared videos, the lookup of the same video’s training target has the smallest error: '
                           'familiar stimuli can carry the prediction through stimulus identity, which is why that '
                           'control is there. When folder and video are held out together the lookup has no matching '
                           'video and falls back to the global mean, so the two are equal. This illustrates the '
                           'confound; it does not establish a mechanism.',
        'quality': {'clips_checked': qu['stored_clips_audited'], 'channel_clip_rows': qu['channel_clip_rows_audited'],
                    'clips_or_channels_removed': qu['clips_or_channels_removed'],
                    'note': 'finite, nonconstant values and valid spectral denominators in every clip: numerical '
                            'eligibility only, not acquisition quality, physical units or physiological specificity'},
        'uncertainty': {'kind': 'none: no confidence interval or significance test, because two nominal folders support '
                                'no population inference'},
        'method': {
            'inputs': 'five relative Welch band powers, [1,4), [4,8), [8,13), [13,30) and [30,45) Hz, each divided by '
                      'that channel’s [1,45) Hz total, for each of the 64 original channel positions: 320 per clip; '
                      'Welch at the nominal 1,000 Hz with one-second Hann windows and 50% overlap',
            'model': 'source-only standardization and Ridge with fixed alpha 1, no tuning; predictions finite but '
                     'unclipped, no calibration after the fact',
            'channels': 'no channel selection, common-average reference, cross-channel mixing or invented trim',
            'sealing': 'all fold predictions and fitted parameters sealed before separate scoring',
        },
        'reading': 'EEG Ridge has a larger error than every source-only control in both conditions. With shared '
                   'videos, the same-video lookup has the smallest error; when folder and video are held out together, '
                   'the lookup has no matching video and equals the global mean. No physiological or population claim '
                   'follows.',
        'limitations': [
            'Two nominal folders and 15 shared video keys: a descriptive computational diagnostic, not a population, '
            'cross-day or leaderboard result.',
            'Stored EEG units, calibration and sensor validity, the precise EEG-to-label clock and the annotation '
            'polling are unresolved; relative band power removes a constant channel gain, which is a property of the '
            'representation only.',
            'Published video durations exceed the stored arrays by two seconds and the crop end points are unknown: '
            'pairing whole arrays establishes no precise physiological alignment.',
            'The numeric video ID is a key-index proxy, not established presentation order, and the shared-video '
            'condition carries familiar-stimulus confounding.',
            'The label vectors had been inspected, all 30 means computed privately and two arrays quality-checked '
            'before this design: these are not untouched targets.',
            'No confidence interval, significance test, clinical affect, neural specificity or population claim.',
        ],
        'release_limits': export['limitations'],
        'claims_not_supported': [
            'no physiological or neural decoding claim',
            'not a population, cross-day or leaderboard result',
            'no causal mechanism for the lookup’s advantage',
            'no fNIRS or fusion result',
        ],
        'independent_audit': {
            'status': 'pass', 'assertions': audit['checks']['assertions_passed'],
            'categories': audit['checks']['unique_categories'],
            'largest_metric_difference': audit['numerical_verification']['maximum_metric_absolute_error'],
            'checked': 'sealed predictions reconstructed exactly and every metric recomputed independently; all 30 '
                       'preparation records verified',
            'not_checked': 'no raw signal or original annotation was reread and no model was refitted or tuned',
        },
    }
    written_from(result, (handoff, json.dumps(export), json.dumps(audit)), label)
    return result, export, secret


# ---------------------------------------------------------------------------- boundary
def range_allowed(trail):
    """A permutation or label-shuffle control's observed range, and nothing else, may carry the key observed_range."""
    return re.search(r'\.(?:permutation_control|label_shuffle)(?:\.[a-z0-9_]+)*\.observed_range$', trail) is not None


def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            if k == 'observed_range':
                require(range_allowed(here), f'refused field in export: {here}')
                require(isinstance(v, list) and len(v) == 2 and all(number(x) for x in v), f'{here}: not a range')
                continue
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not SOURCE_IDS.search(value), f'source file or participant identifier in export: {trail}')
        require(not PRIVATE_TOKENS.search(value), f'private host or path in export: {trail}')
        if trail not in ('$.schema_version', '$.release_id'):   # identifiers, kept as they are
            require(not VERSION_LABEL.search(value), f'a version label in export text: {trail}')
            require(not UPDATE_MARKER.search(value), f'an update marker in export text: {trail}')
        require('jev' not in value.lower(), f'{trail}: Jev is not part of these pilots')


def sentences(text):
    return re.split(r'(?<=[.;:])\s+', text)


def claims_negated(payload):
    """A claim these results do not support appears only in a sentence that negates it."""
    for trail, text in strings(payload):
        if any(trail.startswith(p) for p in ('$.datasets', '$.provenance')):
            continue
        for sentence in sentences(text):
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def weights_not_apache(payload):
    """Apache-2.0 is the EEGPT repository code's licence: never the weights'."""
    for trail, text in strings(payload):
        if trail.endswith('.model.code_licence'):   # the field itself says whose licence it is
            continue
        for sentence in sentences(text):
            if 'apache' in sentence.lower():
                require(re.search(r'\bcode\b', sentence, re.I) and not re.search(r'weights? (?:are|is) apache', sentence, re.I),
                        f'{trail}: Apache-2.0 not tied to the code: {sentence!r}')
                if re.search(r'\bweights?\b|checkpoint', sentence, re.I):
                    require(NEGATION.search(sentence), f'{trail}: Apache-2.0 beside the weights, unnegated: {sentence!r}')
    m = payload['results'].get(ORTH_FM, {}).get('model')
    if m:
        require(m['weights_licence'] is None and m['code_licence'] == 'Apache-2.0' and m['weights_distributed'] is False
                and 'unresolved' in m['weights_licence_status'], 'the EEGPT weights’ licence must stay unresolved')


def figure_free(entries, what):
    """A hold or a status-only item says that no figure exists and why; it carries none, not even a numeral."""
    for h in entries:
        require(set(h) == {'id', 'statement', 'reason', 'scope'}, f'{what} {h.get("id")}: unexpected fields')
        require(all(isinstance(v, str) and v and not re.search(r'\d', v) for v in h.values()),
                f'{what} {h["id"]}: carries a figure')
    return entries


# What each pilot is, in the order of PILOTS, for the scope line: published and held pilots named apart, so the
# switches (sources[...].publication) decide which list a pilot is in and no held pilot reads as a result.
SCOPE_ITEMS = {'orthosis': 'one Orthosis cohort in three configurations, counted once',
               'bingo': 'a cross-person, cross-language inner-speech baseline on BINGO',
               'handwriting': 'a mask-aware EEG analysis of a handwriting dataset',
               'refed': 'a stored-clip computational diagnostic on REFED'}


def scope(pub):
    def listed(items):
        return items[0] if len(items) == 1 else '; '.join(items[:-1]) + '; and ' + items[-1]
    state = {pid: pub[DATASETS[d][0]] for pid, d, _ in PILOTS}
    released = [SCOPE_ITEMS[p] for p, _, _ in PILOTS if state[p] == 'released']
    held = [SCOPE_ITEMS[p] for p, _, _ in PILOTS if state[p] == 'status_only']
    require(released, 'no pilot is released')
    text = ('Small pilots on four sources, all kept outside every leaderboard and model ranking. Published, each from '
            f'its own approved aggregate export: {listed(released)}.')
    if held:
        text += (f' Held for {"its rights review" if len(held) == 1 else "their rights reviews"}, run and audited but '
                 f'with no figure, and listed under holds: {listed(held)}.')
    return text + ' No dataset, cohort, species, task or metric is pooled, and the results share no ranking.'


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require([d['id'] for d in manifest['datasets']] == list(DATASETS), 'the manifest names other datasets')
    require(tuple(s['id'] for s in manifest['sources']) == SOURCE_ORDER, 'the manifest names other sources')
    for s in manifest['sources']:
        require(s['decision'] == 'aggregate_preview', f'{s["id"]}: no other decision has an extractor')
        require(s['id'] in DATASETS[s['dataset']], f'{s["id"]}: filed under another dataset')
        require(s['publication'] in PUBLICATION, f'{s["id"]}: publication must be released or status_only')
    pinned_text(manifest['handoffIndex'], 'handoff index')
    gates, _ = pinned(manifest['remainingGates'], 'remaining gates')
    require(gates['currently_executable_new_training_jobs'] == [], 'the batch has queued work')
    src = {s['id']: s for s in manifest['sources']}
    pub = {s['id']: s['publication'] for s in manifest['sources']}
    for d, ids in DATASETS.items():
        require(len({pub[i] for i in ids}) == 1, f'{d}: its results must be released or held together')

    built, secret, held_values = {}, [], []
    r64, e64, s64 = orthosis_64(src[ORTH64])
    r58, e58 = orthosis_58(src[ORTH58])
    rfm, efm = orthosis_fm(src[ORTH_FM], e58, src[ORTH58]['export']['sha256'])
    built.update({ORTH64: (r64, [e64]), ORTH58: (r58, [e58]), ORTH_FM: (rfm, [efm])})
    secret += s64
    records = {d['id']: d for d in manifest['datasets']}
    rb, eb = bingo(src[BINGO], records['bingo-imagined-speech'])
    built[BINGO] = (rb, [eb])
    rh, eh, sh = handwriting(src[HAND])
    built[HAND] = (rh, list(eh))
    secret += sh
    rr, er, sr = refed(src[REFED])
    built[REFED] = (rr, [er])
    secret += sr

    results, holds = {}, []
    for sid in SOURCE_ORDER:
        result, exports = built[sid]
        if pub[sid] == 'released':
            results[sid] = result
        else:   # every figure the held result would have printed
            held_values += list(numbers(result))
    datasets = {}
    for d, ids in DATASETS.items():
        state = pub[ids[0]]
        datasets[d] = {**dataset_rights(records[d], state), 'results': [i for i in ids if i in results]}
        if state == 'status_only':
            holds.append({'id': f'{ids[0]}-rights',
                          'statement': 'Run and independently audited; no figure is published.',
                          'reason': records[d]['heldStatement'].removeprefix('Nothing is published from this source. '),
                          'scope': f'{records[d]["name"].split(" (")[0]} · {built[ids[0]][0]["title"].split(":")[0]}'})
    pilots = [{'id': pid, 'dataset': d, 'label': name, 'publication': pub[DATASETS[d][0]],
               'results': [i for i in DATASETS[d] if i in results],
               **({'hold': f'{DATASETS[d][0]}-rights'} if pub[DATASETS[d][0]] == 'status_only' else {})}
              for pid, d, name in PILOTS]

    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'title': TITLE,
        'question': QUESTION,
        'placement': 'small pilots outside every leaderboard and model ranking',
        'metric_units': 'balanced accuracy, AUROC, average precision, top-3 accuracy, shares and chance levels are '
                        'proportions in [0,1]; differences of these are differences of proportions; the REFED error is '
                        'a mean absolute error in raw label units on the published 1–255 scale (lower is better); '
                        'counts of people, fields, folders, clips, runs, events, trials and channels are whole numbers; '
                        'null means not computed or not stated, never zero',
        'scope': scope(pub),
        'pilots': pilots,
        'results': results,
        'datasets': datasets,
        'status_only': figure_free(manifest['statusOnly'], 'status-only item'),
        'holds': figure_free(holds, 'hold'),
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': list(results),
                       'holds': [h['id'] for h in holds],
                       'held_sources': [s for s in SOURCE_ORDER if pub[s] == 'status_only'],
                       'source_export_sha256': {s: src[s]['export']['sha256'] for s in results}},
    }
    scrub_check(payload)
    claims_negated(payload)
    weights_not_apache(payload)
    validate_public(payload)
    published = set(numbers(payload))
    trivial = {0.0, 0.25, 0.5, 1.0}   # chance levels and constant controls, shared by many blocks by construction
    leaked = [v for v in secret if v not in trivial and v in published]
    require(not leaked, f'a per-person value reached the export: {leaked[:3]}')
    leaked = [v for v in held_values if v not in trivial and v in published]
    require(not leaked, f'a held source’s figure reached the export: {leaked[:3]}')
    return payload


def input_refs(manifest):
    refs = [manifest['handoffIndex'], manifest['remainingGates']]

    def walk(v):
        if isinstance(v, dict):
            if 'path' in v and 'sha256' in v:
                refs.append(v)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(manifest['datasets'])
    walk(manifest['sources'])
    return refs


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest))


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_pilot_studies_export
    return audit_pilot_studies_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
