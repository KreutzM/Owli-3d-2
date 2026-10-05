"""v2: code-owned predecessor inventories and typed dependency-only relocation.

Anchors were compared with Git 84bee42 during #37. Validation needs no network or
deep clone: it checks SHA-256 of those exact bytes, independent of manifest claims.
The old history_bindings.py stays byte-exact because #5 binds its original source.
"""
import copy
import hashlib
import json
from pathlib import Path

from evidence_contracts import HISTORY_CONTRACT, HISTORY_PREDECESSOR, PREDECESSOR_SHA256

DEPENDENCY_FIELDS = ('source_sha256', 'evidence_sha256', 'recipe_sources', 'fixture_sources')


def relocated_metadata(value):
    """Only top-level typed dependency maps may change; criteria/prose remain exact."""
    result = copy.deepcopy(value)
    paths = {old: item['path'] for old, item in HISTORY_CONTRACT['source_relocations'].items()}
    paths['40_feet_perch.py'] = 'legacy/40_feet_perch.py'
    digests = {item['before_sha256']: item['after_sha256'] for item in HISTORY_CONTRACT['metadata_relocations'].values()}
    for field in DEPENDENCY_FIELDS:
        if field not in result:
            continue
        table = result[field]
        if not isinstance(table, dict) or any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 for k, v in table.items()):
            raise ValueError('Invalid historical dependency map: ' + field)
        result[field] = {paths.get(k, k): digests.get(v, v) for k, v in table.items()}
    return result


def validate_history(root):
    root = Path(root)
    errors = []

    def read(path):
        try:
            return (root / path).read_bytes()
        except OSError as exc:
            errors.append(f'Missing historical evidence: {path}: {exc}')
            return None

    raw = read('validation/history/pre_feet_v01/manifest.json')
    try:
        manifest = json.loads(raw) if raw is not None else None
    except (ValueError, TypeError):
        manifest = None
    if manifest != HISTORY_CONTRACT:
        errors.append('Historical manifest differs from code-owned complete predecessor contract ' + HISTORY_PREDECESSOR)
    # Always walk the external inventory, even when the submitted manifest is empty.
    for old, record in HISTORY_CONTRACT['source_relocations'].items():
        archived = read(record['path'])
        if archived is not None and hashlib.sha256(archived).hexdigest() != PREDECESSOR_SHA256[old]:
            errors.append('Historical source differs from predecessor Git bytes: ' + old)
    for name, record in HISTORY_CONTRACT['metadata_relocations'].items():
        before, after = read(record['snapshot']), read(name)
        if before is None or after is None:
            continue
        if hashlib.sha256(before).hexdigest() != PREDECESSOR_SHA256[name]:
            errors.append('Historical snapshot differs from predecessor Git bytes: ' + name)
        if hashlib.sha256(after).hexdigest() != record['after_sha256']:
            errors.append('Relocated historical bytes changed: ' + name)
        try:
            if relocated_metadata(json.loads(before)) != json.loads(after):
                errors.append('Migration changed non-dependency fields: ' + name)
        except (ValueError, TypeError, AttributeError) as exc:
            errors.append(f'Invalid historical metadata: {name}: {exc}')
    return errors
