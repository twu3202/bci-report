"""Opaque, stable row ids for the open register.

Every register row gets an id that says nothing about the row: ``r-hf-0412``, ``r-moabb-0031``,
``r-corpus-seed``, ``r-model-popt``, ``r-site-beta``. Numbered ids (Hugging Face uploads and families,
MOABB record groups) are kept in a persisted map, ``register-ids.json``, keyed by the row's identity
(an HF repo id, an uploader series, a MOABB record DOI). A key that has an id keeps it in every later
register version; a new key gets the next free number; a key that leaves the population is moved to
``retired`` and its number is never reused. Slug ids (corpus families, models, site rows) are derived
from a fixed slug and are recorded in the same map so that one file lists every id ever issued.

The map is a research file. It is never served: its keys hold repo ids and uploader names, which the
served register shows only in row bodies, never in an id, URL or anchor.

    from register_ids import IdMap
    ids = IdMap.load(path)            # or IdMap.fresh(path) before the first release
    rid = ids.numbered('hf', 'hf:some/repo')
    ids.save()
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA = 'bci-report-register-ids-v1'
PREFIX = {'hf': 'r-hf-', 'moabb': 'r-moabb-'}
WIDTH = 4
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
ID = re.compile(r'^r-(?:hf-\d{4}|moabb-\d{4}|corpus-[a-z0-9-]+|model-[a-z0-9-]+|site-[a-z0-9.-]+)$')


class IdMap:
    def __init__(self, path: Path, data: dict | None = None):
        self.path = Path(path)
        self.data = data or {'schema_version': SCHEMA, 'assigned': {}, 'retired': {}, 'next': {k: 1 for k in PREFIX}}
        self.seen: set[str] = set()
        self.issued_this_run: list[str] = []

    @classmethod
    def load(cls, path: Path) -> 'IdMap':
        path = Path(path)
        if not path.exists():
            return cls(path)
        data = json.loads(path.read_text())
        if data.get('schema_version') != SCHEMA:
            raise ValueError(f'{path}: unknown id map schema {data.get("schema_version")!r}')
        for k in PREFIX:
            data['next'].setdefault(k, 1)
        return cls(path, data)

    @classmethod
    def fresh(cls, path: Path) -> 'IdMap':
        return cls(Path(path))

    # ---------------------------------------------------------------- issuing
    def numbered(self, kind: str, key: str) -> str:
        """The id for ``key`` in a numbered series (``hf`` or ``moabb``); issue the next number if new."""
        if kind not in PREFIX:
            raise ValueError(f'unknown numbered id kind {kind!r}')
        full = f'{kind}|{key}'
        self.seen.add(full)
        assigned = self.data['assigned']
        if full in assigned:
            return assigned[full]
        if full in self.data['retired']:
            # A key that comes back keeps its old number.
            rid = self.data['retired'].pop(full)
            assigned[full] = rid
            return rid
        n = self.data['next'][kind]
        rid = f'{PREFIX[kind]}{n:0{WIDTH}d}'
        if n >= 10 ** WIDTH:
            raise ValueError(f'{kind} ids exhausted at {rid}')
        self.data['next'][kind] = n + 1
        assigned[full] = rid
        self.issued_this_run.append(rid)
        return rid

    def slug(self, kind: str, slug: str) -> str:
        """``r-corpus-<slug>``, ``r-model-<slug>`` or ``r-site-<slug>``, recorded in the map."""
        if kind not in ('corpus', 'model', 'site'):
            raise ValueError(f'unknown slug id kind {kind!r}')
        if kind != 'site' and not SLUG.match(slug):
            raise ValueError(f'bad {kind} slug {slug!r}')
        rid = f'r-{kind}-{slug}'
        full = f'{kind}|{slug}'
        self.seen.add(full)
        self.data['retired'].pop(full, None)
        self.data['assigned'][full] = rid
        return rid

    # ---------------------------------------------------------------- closing
    def retire_unseen(self, kinds: tuple[str, ...]) -> list[str]:
        """Move keys of the given kinds that this run did not use to ``retired`` (numbers stay reserved)."""
        moved = []
        for full in sorted(self.data['assigned']):
            kind = full.split('|', 1)[0]
            if kind in kinds and full not in self.seen:
                self.data['retired'][full] = self.data['assigned'].pop(full)
                moved.append(full)
        return moved

    def redact_retired(self, predicate) -> list[str]:
        """Replace each retired key for which ``predicate(key)`` is true by a digest key, ``<kind>|sha256:<hex>``.

        Its number stays reserved and is never reused; the key's text (a repo id that looks like a participant
        id) leaves the map. Such a repo only ever appears inside a family row, so it never needs its old number back.
        """
        import hashlib
        moved = []
        for full in sorted(self.data['retired']):
            if full.split('|', 1)[1].startswith('sha256:') or not predicate(full):
                continue
            kind = full.split('|', 1)[0]
            digest = f'{kind}|sha256:' + hashlib.sha256(full.encode()).hexdigest()[:32]
            self.data['retired'][digest] = self.data['retired'].pop(full)
            moved.append(digest)
        return moved

    def check(self) -> None:
        ids = list(self.data['assigned'].values()) + list(self.data['retired'].values())
        if len(ids) != len(set(ids)):
            raise ValueError('register-ids.json issues one id to two keys')
        for rid in ids:
            if not ID.match(rid):
                raise ValueError(f'malformed register id {rid!r}')

    def dumps(self) -> str:
        self.check()
        out = {'schema_version': SCHEMA,
               'note': 'Opaque register row ids by identity key. Research file; never served.',
               'assigned': dict(sorted(self.data['assigned'].items())),
               'retired': dict(sorted(self.data['retired'].items())),
               'next': dict(sorted(self.data['next'].items()))}
        return json.dumps(out, ensure_ascii=False, indent=1) + '\n'

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.dumps())
