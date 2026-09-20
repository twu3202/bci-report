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

PROJECT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT/'research/publication_review_20260920/build-release-audit.json'

# Text is scanned for leaks; binary is inventoried and hashed only.
TEXT_SUFFIXES = {'.html', '.css', '.js', '.json', '.csv', '.svg', '.txt', '.xml'}
BINARY_SUFFIXES = {'.ico', '.png', '.jpg', '.webp', '.woff2'}


def check(root):
    snapshot = json.loads((root/'data/experiments.json').read_text())
    expected = {'experiments.json'} | {t['id']+suffix for t in snapshot['tracks']
                                       for suffix in ('-results.csv','-protocol.json')}
    assert {p.name for p in (root/'data').iterdir()} == expected, 'Unexpected download route'
    files = sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: str(p))
    forbidden = ['subjectResults','<home>/','<evidence-root>/','<workstation-home>/',
                 'train_subjects','test_subjects','y_true','y_pred']
    for path in files:
        assert path.suffix in TEXT_SUFFIXES | BINARY_SUFFIXES, path
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
        'checks':['explicit download inventory','cohort-only JSON schema','no participant IDs or local paths in built assets',
                  'local links resolve','source snapshot equals download snapshot','no waveform or model files',
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
