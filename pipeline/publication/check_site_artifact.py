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
        assert not any(term in content for term in forbidden), path
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
