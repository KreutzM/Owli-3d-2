"""Current v2 admission gates; byte-exact historical validators remain v1 evidence.

Reject omissions before calling v1. New milestones must declare their own complete
source/reference/reload contracts and may reuse validate_inventory, never .items()
as a substitute for required coverage. This module does not regenerate approvals.
"""
import json
import math
from pathlib import Path

from evidence_contracts import DELIVERY_INVENTORIES, GATE_VERSION
from delivery_shapes import RELOAD_SHAPES
from face_review import validate_delivery as historical_face
from beak_review import validate_beak_delivery as historical_beak
from feet_review import validate_feet_delivery as historical_feet
from history_gate import validate_history

ROOT = Path(__file__).resolve().parents[1]


def validate_inventory(proof, contract):
    errors = []
    if not isinstance(proof, dict):
        return ['Proof must be an object']
    for field, required in contract.items():
        table = proof.get(field)
        if not isinstance(table, dict):
            errors.append(f'{field}: required object missing or invalid')
            continue
        missing, extra = set(required) - table.keys(), table.keys() - set(required)
        if missing:
            errors.append(f'{field}: missing required keys: ' + ', '.join(sorted(missing)))
        if extra:
            errors.append(f'{field}: unexpected keys: ' + ', '.join(sorted(extra)))
        if field.endswith('_sha256'):
            for name, digest in table.items():
                if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                    errors.append(f'{field}: invalid SHA-256 for {name}')
    return errors


def validate_shape(value, schema, path):
    """Require concrete nested data of the reviewed shape, never matched nulls."""
    if isinstance(schema, str):
        if type(value).__name__ != schema:
            return [f'{path}: expected {schema}, got {type(value).__name__}']
        if schema == 'str' and not value.strip():
            return [f'{path}: empty comparison string']
        if schema == 'str' and any(field in path.split('/') for field in ('geometry_sha256', 'unchanged_part_sha256')):
            if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                return [f'{path}: invalid geometry comparison digest']
        if schema == 'float' and not math.isfinite(value):
            return [f'{path}: non-finite comparison number']
        return []
    if 'dict' in schema or 'keys' in schema:
        if not isinstance(value, dict):
            return [f'{path}: expected object']
        required = schema['dict'] if 'dict' in schema else {k: schema['values'] for k in schema['keys']}
        if set(value) != set(required):
            return [f'{path}: incomplete or unexpected comparison fields']
        return [e for key, child in required.items() for e in validate_shape(value[key], child, path+'/'+key)]
    if not isinstance(value, list) or len(value) != schema['list']:
        return [f'{path}: incomplete comparison sequence']
    items = schema['items']
    return [e for i, item in enumerate(value)
            for e in validate_shape(item, items[0] if len(items) == 1 else items[i], path+'/'+str(i))]


def validate_milestone(name, root=ROOT, proof=None, decision=None):
    """Check exact table coverage, reload equality, then all existing milestone gates."""
    root = Path(root)
    folder = root / 'validation/reviews' / name
    try:
        if proof is None:
            proof = json.loads((folder / 'verification.json').read_text(encoding='utf-8'))
        if decision is None:
            decision = json.loads((folder / 'review.json').read_text(encoding='utf-8'))
        errors = validate_inventory(proof, DELIVERY_INVENTORIES[name])
        if errors:
            return errors
        build = proof.get('build')
        if not isinstance(build, dict):
            return ['Build proof must be an object']
        for key in DELIVERY_INVENTORIES[name]['reloaded']:
            shape_errors = []
            for label, table in (('build', build), ('reloaded', proof['reloaded'])):
                shape_errors.extend(validate_shape(table.get(key), RELOAD_SHAPES[name][key], label+'/'+key))
            if shape_errors:
                return errors + shape_errors
            if key not in build or build[key] != proof['reloaded'][key]:
                errors.append('Reopened scene differs or build field missing: ' + key)
        if name == 'face_v01':
            return errors + historical_face(root, decision, proof)
        if name == 'beak_v01':
            return errors + historical_beak(root, proof, decision)
        return errors + historical_feet(root, proof, decision) + validate_history(root)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return [f'{name}: malformed or missing delivery evidence: {exc}']


def validate_delivery(root=ROOT, decision=None, proof=None):
    return validate_milestone('face_v01', root, proof, decision)


def validate_beak_delivery(root=ROOT, proof=None, decision=None):
    return validate_milestone('beak_v01', root, proof, decision)


def validate_feet_delivery(root=ROOT, proof=None, decision=None):
    return validate_milestone('feet_v01', root, proof, decision)


def validate_all(root=ROOT):
    return [f'{name}: {error}' for name in DELIVERY_INVENTORIES for error in validate_milestone(name, root)]
