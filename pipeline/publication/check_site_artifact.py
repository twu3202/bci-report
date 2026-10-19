"""Inspect the built site, including invisible downloadable assets.

Run before every deploy. With a previous audit record present this also fails on
drift: the record used to be overwritten with whatever was on disk, so a hand-
edited `dist/` re-recorded itself as a pass. Pass `--accept` to adopt a new build.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from export_snapshot import validate_public
from export_deployment_topics import serialized_export, EXPORT_AUDIT, OUTPUTS
import export_evidence_update as evidence
import export_clinical_update as clinical
import export_context_update as context
import export_adaptation_update as adaptation
import export_extension_update as extension
import export_large_source_update as large_source
import export_reliable_decisions_update as reliable_decisions
import export_foundation_models_update as foundation_models
import export_shared_representation_update as shared_representation
import export_later_sessions_update as later_sessions
import audit_later_sessions_export as later_sessions_audit
import export_questions_in_language_update as questions_in_language
import audit_questions_in_language_export as questions_in_language_audit
import export_beyond_scalp_update as beyond_scalp
import audit_beyond_scalp_export as beyond_scalp_audit
import export_pilot_studies_update as pilot_studies
import audit_pilot_studies_export as pilot_studies_audit
import export_eegpt_core_update as eegpt_core
import audit_eegpt_core_export as eegpt_core_audit

PROJECT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT/'research/publication_review_20260920/build-release-audit.json'

# Text is scanned for leaks; binary is inventoried and hashed only.
# .md: the Markdown copy of every page (site/scripts/build-agent-files.mjs), scanned like the page.
TEXT_SUFFIXES = {'.html', '.css', '.js', '.json', '.csv', '.svg', '.txt', '.xml', '.md'}
BINARY_SUFFIXES = {'.ico', '.png', '.jpg', '.webp', '.woff2'}
# Host control files. They carry no extension, are parsed by Cloudflare rather
# than served, and still go through the same text scan as everything else —
# a header or redirect rule can leak a hostname just as easily as a page can.
CONTROL_FILES = {'_headers', '_redirects'}


def check(root):
    snapshot = json.loads((root/'data/experiments.json').read_text())
    expected = {'experiments.json'} | {t['id']+suffix for t in snapshot['tracks']
                                       for suffix in ('-results.csv','-protocol.json')}
    topic_payload = serialized_export()
    topic_snapshot = json.loads(topic_payload)
    topic_audit = json.loads(EXPORT_AUDIT.read_text())
    assert topic_audit['status'] == 'pass', 'Topic export review did not pass'
    assert hashlib.sha256(topic_payload).hexdigest() == topic_audit['export_sha256'], 'Stale topic export audit'
    assert (root/'data/deployment-topics.json').read_bytes() == topic_payload, 'Unreviewed topic download'
    assert all(p.read_bytes() == topic_payload for p in OUTPUTS), 'Topic source/download drift'
    expected.add('deployment-topics.json')
    # The 2026-09-22 batch has its own boundary and its own audit; it is held to
    # the same standard as the topic export, not folded into it.
    # Re-derived where the private research inputs exist; elsewhere (a clone)
    # the published bytes are held to the committed audit hash alone.
    evidence_rederived = evidence.inputs_available()
    evidence_payload = (evidence.serialized_export() if evidence_rederived
                        else (root/'data/evidence-update.json').read_bytes())
    evidence_audit = json.loads(evidence.EXPORT_AUDIT.read_text())
    assert evidence_audit['status'] == 'pass', 'Evidence export review did not pass'
    assert hashlib.sha256(evidence_payload).hexdigest() == evidence_audit['export_sha256'], 'Stale evidence export audit'
    assert (root/'data/evidence-update.json').read_bytes() == evidence_payload, 'Unreviewed evidence download'
    assert all(p.read_bytes() == evidence_payload for p in evidence.OUTPUTS), 'Evidence source/download drift'
    expected.add('evidence-update.json')

    # Same gate for the 2026-09-23 clinical export: re-derived where the pinned
    # research inputs exist, hash-checked against its own audit everywhere else.
    clinical_rederived = clinical.inputs_available()
    clinical_payload = (clinical.serialized_export() if clinical_rederived
                        else (root/'data/clinical-update.json').read_bytes())
    clinical_audit = json.loads(clinical.EXPORT_AUDIT.read_text())
    assert clinical_audit['status'] == 'pass', 'Clinical export review did not pass'
    assert hashlib.sha256(clinical_payload).hexdigest() == clinical_audit['export_sha256'], 'Stale clinical export audit'
    assert (root/'data/clinical-update.json').read_bytes() == clinical_payload, 'Unreviewed clinical download'
    assert all(p.read_bytes() == clinical_payload for p in clinical.OUTPUTS), 'Clinical source/download drift'
    expected.add('clinical-update.json')

    # And the 2026-09-27 context export.
    context_rederived = context.inputs_available()
    context_payload = (context.serialized_export() if context_rederived
                       else (root/'data/context-update.json').read_bytes())
    context_audit = json.loads(context.EXPORT_AUDIT.read_text())
    assert context_audit['status'] == 'pass', 'Context export review did not pass'
    assert hashlib.sha256(context_payload).hexdigest() == context_audit['export_sha256'], 'Stale context export audit'
    assert (root/'data/context-update.json').read_bytes() == context_payload, 'Unreviewed context download'
    assert all(p.read_bytes() == context_payload for p in context.OUTPUTS), 'Context source/download drift'
    expected.add('context-update.json')

    # And the 2026-10-01 adaptation export.
    adaptation_rederived = adaptation.inputs_available()
    adaptation_payload = (adaptation.serialized_export() if adaptation_rederived
                          else (root/'data/adaptation-update.json').read_bytes())
    adaptation_audit = json.loads(adaptation.EXPORT_AUDIT.read_text())
    assert adaptation_audit['status'] == 'pass', 'Adaptation export review did not pass'
    assert hashlib.sha256(adaptation_payload).hexdigest() == adaptation_audit['export_sha256'], 'Stale adaptation export audit'
    assert (root/'data/adaptation-update.json').read_bytes() == adaptation_payload, 'Unreviewed adaptation download'
    assert all(p.read_bytes() == adaptation_payload for p in adaptation.OUTPUTS), 'Adaptation source/download drift'
    expected.add('adaptation-update.json')

    # And the 2026-10-02 extension export (YSU twenty-person extension, LTRSVP).
    extension_rederived = extension.inputs_available()
    extension_payload = (extension.serialized_export() if extension_rederived
                         else (root/'data/extension-update.json').read_bytes())
    extension_audit = json.loads(extension.EXPORT_AUDIT.read_text())
    assert extension_audit['status'] == 'pass', 'Extension export review did not pass'
    assert hashlib.sha256(extension_payload).hexdigest() == extension_audit['export_sha256'], 'Stale extension export audit'
    assert (root/'data/extension-update.json').read_bytes() == extension_payload, 'Unreviewed extension download'
    assert all(p.read_bytes() == extension_payload for p in extension.OUTPUTS), 'Extension source/download drift'
    expected.add('extension-update.json')

    # And the 2026-10-03 large-source export (Dreem sleep baselines, OpenBMI calibration).
    large_source_rederived = large_source.inputs_available()
    large_source_payload = (large_source.serialized_export() if large_source_rederived
                            else (root/'data/large-source-update.json').read_bytes())
    large_source_audit = json.loads(large_source.EXPORT_AUDIT.read_text())
    assert large_source_audit['status'] == 'pass', 'Large-source export review did not pass'
    assert hashlib.sha256(large_source_payload).hexdigest() == large_source_audit['export_sha256'], 'Stale large-source export audit'
    assert (root/'data/large-source-update.json').read_bytes() == large_source_payload, 'Unreviewed large-source download'
    assert all(p.read_bytes() == large_source_payload for p in large_source.OUTPUTS), 'Large-source source/download drift'
    expected.add('large-source-update.json')

    # And the 2026-10-04 route-1 export (reliable decisions: rejection and probability calibration).
    reliable_rederived = reliable_decisions.inputs_available()
    reliable_payload = (reliable_decisions.serialized_export() if reliable_rederived
                        else (root/'data/reliable-decisions-update.json').read_bytes())
    reliable_audit = json.loads(reliable_decisions.EXPORT_AUDIT.read_text())
    assert reliable_audit['status'] == 'pass', 'Reliable-decisions export review did not pass'
    assert hashlib.sha256(reliable_payload).hexdigest() == reliable_audit['export_sha256'], 'Stale reliable-decisions export audit'
    assert (root/'data/reliable-decisions-update.json').read_bytes() == reliable_payload, 'Unreviewed reliable-decisions download'
    assert all(p.read_bytes() == reliable_payload for p in reliable_decisions.OUTPUTS), 'Reliable-decisions source/download drift'
    expected.add('reliable-decisions-update.json')

    # And the 2026-10-04 v9 foundation-model export: one JSON and a CSV per protocol, all held to one audit.
    foundation_rederived = foundation_models.inputs_available()
    if foundation_rederived:
        foundation_payload, foundation_csvs = foundation_models.serialized_export()
    else:
        foundation_payload = (root/'data/foundation-models-update.json').read_bytes()
        foundation_csvs = {name: (root/'data'/name).read_bytes()
                           for name in json.loads(foundation_models.EXPORT_AUDIT.read_text())['csv_sha256']}
    foundation_audit = json.loads(foundation_models.EXPORT_AUDIT.read_text())
    assert foundation_audit['status'] == 'pass', 'Foundation-model export review did not pass'
    assert hashlib.sha256(foundation_payload).hexdigest() == foundation_audit['export_sha256'], 'Stale foundation-model export audit'
    assert {n: hashlib.sha256(b).hexdigest() for n, b in foundation_csvs.items()} == foundation_audit['csv_sha256'], \
        'Stale foundation-model CSV audit'
    assert (root/'data/foundation-models-update.json').read_bytes() == foundation_payload, 'Unreviewed foundation-model download'
    assert all(p.read_bytes() == foundation_payload for p in foundation_models.OUTPUTS), 'Foundation-model source/download drift'
    for name, body in foundation_csvs.items():
        assert (root/'data'/name).read_bytes() == body, f'Unreviewed foundation-model CSV: {name}'
        assert (foundation_models.CSV_DIR/name).read_bytes() == body, f'Foundation-model CSV source/download drift: {name}'
    expected |= {'foundation-models-update.json', *foundation_csvs}

    # And the 2026-10-07 route-2 export (one representation, several questions; BOAS under its stated gaps).
    shared_rederived = shared_representation.inputs_available()
    shared_payload = (shared_representation.serialized_export() if shared_rederived
                      else (root/'data/shared-representation-update.json').read_bytes())
    shared_audit = json.loads(shared_representation.EXPORT_AUDIT.read_text())
    assert shared_audit['status'] == 'pass', 'Shared-representation export review did not pass'
    assert hashlib.sha256(shared_payload).hexdigest() == shared_audit['export_sha256'], 'Stale shared-representation export audit'
    assert (root/'data/shared-representation-update.json').read_bytes() == shared_payload, 'Unreviewed shared-representation download'
    assert all(p.read_bytes() == shared_payload for p in shared_representation.OUTPUTS), 'Shared-representation source/download drift'
    expected.add('shared-representation-update.json')

    # And the large-source batch's later-session results (WBCIC-SHU, longitudinal RSVP, Forenzo): re-derived from
    # its own manifest where the pinned inputs exist, and its independent audit re-run on the same bytes.
    later_rederived = later_sessions.inputs_available()
    later_payload = (later_sessions.serialized_export() if later_rederived
                     else (root/'data/later-sessions-update.json').read_bytes())
    later_audit = json.loads(later_sessions.EXPORT_AUDIT.read_text())
    assert later_audit['status'] == 'pass', 'Later-sessions export review did not pass'
    assert hashlib.sha256(later_payload).hexdigest() == later_audit['export_sha256'], 'Stale later-sessions export audit'
    assert (root/'data/later-sessions-update.json').read_bytes() == later_payload, 'Unreviewed later-sessions download'
    assert all(p.read_bytes() == later_payload for p in later_sessions.OUTPUTS), 'Later-sessions source/download drift'
    if later_rederived:
        assert later_sessions_audit.audit() == later_audit, 'Later-sessions independent audit no longer reproduces'
    expected.add('later-sessions-update.json')

    # And route 3 of the decision-research roadmap, questions in language: two served files (the results, and the
    # wording lists with the partition and derangements), re-derived from their own manifest where the pinned inputs
    # exist, and the independent audit re-run on the same bytes.
    qil_rederived = questions_in_language.inputs_available()
    if qil_rederived:
        qil_payload, qil_wordings = questions_in_language.serialized_export()
    else:
        qil_payload = (root/'data/questions-in-language-update.json').read_bytes()
        qil_wordings = (root/'data/questions-in-language-wordings.json').read_bytes()
    qil_audit = json.loads(questions_in_language.EXPORT_AUDIT.read_text())
    assert qil_audit['status'] == 'pass', 'Questions-in-language export review did not pass'
    assert hashlib.sha256(qil_payload).hexdigest() == qil_audit['export_sha256'], 'Stale questions-in-language export audit'
    assert hashlib.sha256(qil_wordings).hexdigest() == qil_audit['wordings_sha256'], 'Stale questions-in-language wordings audit'
    assert (root/'data/questions-in-language-update.json').read_bytes() == qil_payload, 'Unreviewed questions-in-language download'
    assert (root/'data/questions-in-language-wordings.json').read_bytes() == qil_wordings, 'Unreviewed questions-in-language wordings download'
    assert all(p.read_bytes() == qil_payload for p in questions_in_language.OUTPUTS), 'Questions-in-language source/download drift'
    assert all(p.read_bytes() == qil_wordings for p in questions_in_language.WORDING_OUTPUTS), 'Questions-in-language wordings source/download drift'
    if qil_rederived:
        assert questions_in_language_audit.audit() == qil_audit, 'Questions-in-language independent audit no longer reproduces'
    expected |= {'questions-in-language-update.json', 'questions-in-language-wordings.json'}

    # And the two batches of one site version (owner decisions, 2026-10-12): the results beyond scalp EEG (human
    # fNIRS, macaque intracortical spiking, an fNIRS coverage check) and the pilot studies (Orthosis in three
    # configurations of one cohort, BINGO, the handwriting analysis, REFED). Each is re-derived from its own
    # manifest where the pinned inputs exist, and its independent audit re-run on the same bytes.
    beyond_rederived = beyond_scalp.inputs_available()
    beyond_payload = (beyond_scalp.serialized_export() if beyond_rederived
                      else (root/'data/beyond-scalp-update.json').read_bytes())
    beyond_audit = json.loads(beyond_scalp.EXPORT_AUDIT.read_text())
    assert beyond_audit['status'] == 'pass', 'Beyond-scalp export review did not pass'
    assert hashlib.sha256(beyond_payload).hexdigest() == beyond_audit['export_sha256'], 'Stale beyond-scalp export audit'
    assert hashlib.sha256(beyond_scalp.MANIFEST.read_bytes()).hexdigest() == beyond_audit['manifest_sha256'], 'Beyond-scalp manifest is not the audited one'
    assert (root/'data/beyond-scalp-update.json').read_bytes() == beyond_payload, 'Unreviewed beyond-scalp download'
    assert all(p.read_bytes() == beyond_payload for p in beyond_scalp.OUTPUTS), 'Beyond-scalp source/download drift'
    if beyond_rederived:
        assert beyond_scalp_audit.audit() == beyond_audit, 'Beyond-scalp independent audit no longer reproduces'
    expected.add('beyond-scalp-update.json')

    pilot_rederived = pilot_studies.inputs_available()
    pilot_payload = (pilot_studies.serialized_export() if pilot_rederived
                     else (root/'data/pilot-studies-update.json').read_bytes())
    pilot_audit = json.loads(pilot_studies.EXPORT_AUDIT.read_text())
    assert pilot_audit['status'] == 'pass', 'Pilot-studies export review did not pass'
    assert hashlib.sha256(pilot_payload).hexdigest() == pilot_audit['export_sha256'], 'Stale pilot-studies export audit'
    assert hashlib.sha256(pilot_studies.MANIFEST.read_bytes()).hexdigest() == pilot_audit['manifest_sha256'], 'Pilot-studies manifest is not the audited one'
    assert (root/'data/pilot-studies-update.json').read_bytes() == pilot_payload, 'Unreviewed pilot-studies download'
    assert all(p.read_bytes() == pilot_payload for p in pilot_studies.OUTPUTS), 'Pilot-studies source/download drift'
    if pilot_rederived:
        assert pilot_studies_audit.audit() == pilot_audit, 'Pilot-studies independent audit no longer reproduces'
    expected.add('pilot-studies-update.json')

    # EEGPT's eight core-matrix cells and its pretraining-attribution rows (owner decisions, 2026-10-12 and
    # 2026-10-13): a frozen row beside the core matrix, from the same runs as the published LaBraM rows (and, except
    # on idle, CBraMod's), re-derived from its own manifest where the pinned run records exist, and its independent
    # audit re-run on the same bytes.
    eegpt_rederived = eegpt_core.inputs_available()
    eegpt_payload = (eegpt_core.serialized_export() if eegpt_rederived
                     else (root/'data/eegpt-core-update.json').read_bytes())
    eegpt_audit = json.loads(eegpt_core.EXPORT_AUDIT.read_text())
    assert eegpt_audit['status'] == 'pass', 'EEGPT core export review did not pass'
    assert hashlib.sha256(eegpt_payload).hexdigest() == eegpt_audit['export_sha256'], 'Stale EEGPT core export audit'
    assert hashlib.sha256(eegpt_core.MANIFEST.read_bytes()).hexdigest() == eegpt_audit['manifest_sha256'], 'EEGPT core manifest is not the audited one'
    assert (root/'data/eegpt-core-update.json').read_bytes() == eegpt_payload, 'Unreviewed EEGPT core download'
    assert all(p.read_bytes() == eegpt_payload for p in eegpt_core.OUTPUTS), 'EEGPT core source/download drift'
    if eegpt_rederived:
        assert eegpt_core_audit.audit() == eegpt_audit, 'EEGPT core independent audit no longer reproduces'
    expected.add('eegpt-core-update.json')
    # The 2026-10-20 release: four result exports and the open register, each served exactly as its audit bound it.
    review_0420 = PROJECT/'research/publication_review_20261020'
    for served, audit_path, manifest_path in (
            ('new-ssvep-frequencies-update.json', 'new-ssvep-frequencies-export-audit.json', 'new-ssvep-frequencies-release-manifest.json'),
            ('data-quality-update.json', 'data-quality-export-audit.json', 'data-quality-release-manifest.json'),
            ('clinical-iesseeg-update.json', 'clinical-iesseeg-export-audit.json', 'clinical-iesseeg-release-manifest.json'),
            ('neurolm-eegmat-update.json', 'neurolm-eegmat-export-audit.json', 'neurolm-eegmat-release-manifest.json'),
            ('open-register-20261020.json', 'register/open-register-export-audit.json', 'register/open-register-release-manifest.json')):
        audit = json.loads((review_0420/audit_path).read_text())
        payload = (root/'data'/served).read_bytes()
        assert audit['status'] == 'pass', f'{served}: its audit did not pass'
        assert hashlib.sha256(payload).hexdigest() == audit['export_sha256'], f'Unreviewed download {served}'
        assert hashlib.sha256((review_0420/manifest_path).read_bytes()).hexdigest() == audit['manifest_sha256'], f'{served}: manifest is not the audited one'
        assert (PROJECT/'site/src/data'/served).read_bytes() == payload, f'{served}: source/download drift'
        expected.add(served)
    reg_audit = json.loads((review_0420/'register/open-register-export-audit.json').read_text())
    assert hashlib.sha256((root/'data/open-register-20261020.csv').read_bytes()).hexdigest() == reg_audit['csv_sha256'], 'Unreviewed register CSV'
    expected.add('open-register-20261020.csv')
    assert {p.name for p in (root/'data').iterdir()} == expected, 'Unexpected download route'
    files = sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: str(p))
    # Path roots, not one machine's spellings. The list used to name this
    # operator's home directory and external volume, which made the check both
    # narrower than it should be and a leak of the thing it exists to catch.
    # `dist/` carries no absolute path of any kind, so the broad form has room.
    forbidden = ['subjectResults','/Users/','/Volumes/','/home/','C:\\',
                 'train_subjects','test_subjects','y_true','y_pred']
    for path in files:
        assert path.suffix in TEXT_SUFFIXES | BINARY_SUFFIXES or path.name in CONTROL_FILES, path
        assert not path.is_symlink(), f'symlink in payload: {path}'
        if path.suffix in BINARY_SUFFIXES:
            continue
        content = path.read_text()
        # A web address is not a filesystem path: the SEED terms page lives at bcmi.sjtu.edu.cn/home/seed/ (2026-10-20).
        assert not any(term in re.sub(r'https?://[^\s"\'<>]+', '', content) for term in forbidden), path
        assert not re.search(r'\bsub-\d{2,}\b',content), path
        if path.suffix=='.json': validate_public(json.loads(content))
    for path in root.rglob('*.html'):
        for href in re.findall(r'href="(/[^"#]*)', path.read_text()):
            target = root/href.lstrip('/')
            assert target.exists() or target.with_suffix('.html').exists() or (target/'index.html').exists(), (path,href)
    assert json.loads((PROJECT/'site/src/data/mvp.json').read_text()) == snapshot
    return {
        'status':'pass', 'releaseId':snapshot['releaseId'], 'files':len(files),
        'downloadFiles':len(expected), 'comparisons':snapshot['coverage']['displayedComparisons'],
        'protocols':len(snapshot['tracks']),
        'deploymentTopics':topic_snapshot['coverage'],
        'checks':['explicit download inventory','cohort-only JSON schema','no participant IDs or local paths in built assets',
                  'local links resolve','source snapshot equals download snapshot','no waveform or model files',
                  'topic payload reproduced from pinned reviewed inputs and matches page/download copies',
                  ('evidence-update payload reproduced from its own manifest and audit' if evidence_rederived
                   else 'evidence-update payload matched to its audit hash (private inputs not present)'),
                  ('clinical-update payload reproduced from its own manifest and audit' if clinical_rederived
                   else 'clinical-update payload matched to its audit hash (private inputs not present)'),
                  ('context-update payload reproduced from its own manifest and audit' if context_rederived
                   else 'context-update payload matched to its audit hash (private inputs not present)'),
                  ('adaptation-update payload reproduced from its own manifest and audit' if adaptation_rederived
                   else 'adaptation-update payload matched to its audit hash (private inputs not present)'),
                  ('extension-update payload reproduced from its own manifest and audit' if extension_rederived
                   else 'extension-update payload matched to its audit hash (private inputs not present)'),
                  ('large-source-update payload reproduced from its own manifest and audit' if large_source_rederived
                   else 'large-source-update payload matched to its audit hash (private inputs not present)'),
                  ('reliable-decisions-update payload reproduced from its own manifest and audit' if reliable_rederived
                   else 'reliable-decisions-update payload matched to its audit hash (private inputs not present)'),
                  ('foundation-models-update payload and CSVs reproduced from their own manifest and audit' if foundation_rederived
                   else 'foundation-models-update payload and CSVs matched to their audit hashes (private inputs not present)'),
                  ('shared-representation-update payload reproduced from its own manifest and audit' if shared_rederived
                   else 'shared-representation-update payload matched to its audit hash (private inputs not present)'),
                  ('later-sessions-update payload reproduced from its own manifest, and its independent audit re-run'
                   if later_rederived
                   else 'later-sessions-update payload matched to its audit hash (private inputs not present)'),
                  ('questions-in-language-update payload and wordings reproduced from their own manifest, and their '
                   'independent audit re-run' if qil_rederived
                   else 'questions-in-language-update payload and wordings matched to their audit hashes (private inputs not present)'),
                  ('beyond-scalp-update payload reproduced from its own manifest, and its independent audit re-run'
                   if beyond_rederived
                   else 'beyond-scalp-update payload matched to its audit hash (private inputs not present)'),
                  ('pilot-studies-update payload reproduced from its own manifest, and its independent audit re-run'
                   if pilot_rederived
                   else 'pilot-studies-update payload matched to its audit hash (private inputs not present)'),
                  ('eegpt-core-update payload reproduced from its own manifest, and its independent audit re-run'
                   if eegpt_rederived
                   else 'eegpt-core-update payload matched to its audit hash (private inputs not present)'),
                  'no symlinks in payload','hashes compared against the previous audit record'],
        'built_artifact_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }


def compare_with_previous(result):
    """Report how the payload differs from the recorded build, if there is one."""
    if not AUDIT.exists():
        return None
    previous = json.loads(AUDIT.read_text()).get('built_artifact_sha256', {})
    current = result['built_artifact_sha256']
    return {
        'added': sorted(set(current) - set(previous)),
        'removed': sorted(set(previous) - set(current)),
        'changed': sorted(k for k in set(current) & set(previous) if current[k] != previous[k]),
    }


if __name__=='__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--accept', action='store_true',
                    help='adopt the current build as the recorded one after an intended change')
    args = ap.parse_args()

    result = check(PROJECT/'site/dist')
    drift = compare_with_previous(result)
    if drift and any(drift.values()) and not args.accept:
        print(json.dumps({'status':'drift','drift':drift}, indent=2))
        raise SystemExit(
            'Built payload differs from the recorded build. Review the difference above, '
            'then re-run with --accept to adopt it.')
    AUDIT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='built_artifact_sha256'}))
