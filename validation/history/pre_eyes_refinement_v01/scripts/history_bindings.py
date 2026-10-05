"""Audit byte-exact legacy sources and metadata-only historical dependency relocation."""
import hashlib
import json
from pathlib import Path


def validate_history(root):
    root=Path(root)
    manifest=json.loads((root/'validation/history/pre_feet_v01/manifest.json').read_text())
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    errors=[]
    keys={old:item['path'] for old,item in manifest['source_relocations'].items()}
    keys['40_feet_perch.py']='legacy/40_feet_perch.py'
    hashes={item['before_sha256']:item['after_sha256'] for item in manifest['metadata_relocations'].values()}
    def transform(value):
        if isinstance(value,dict):return {keys.get(k,k):transform(v) for k,v in value.items()}
        if isinstance(value,list):return [transform(v) for v in value]
        return hashes.get(value,value) if isinstance(value,str) else value
    for old,item in manifest['source_relocations'].items():
        if digest(root/item['path'])!=item['sha256']:errors.append('Historical source changed: '+old)
    for name,item in manifest['metadata_relocations'].items():
        old,current=root/item['snapshot'],root/name
        if digest(old)!=item['before_sha256']:errors.append('Historical metadata snapshot changed: '+name)
        if digest(current)!=item['after_sha256']:errors.append('Relocated historical metadata changed: '+name)
        if transform(json.loads(old.read_bytes()))!=json.loads(current.read_bytes()):
            errors.append('Migration changed more than dependency paths and hashes: '+name)
    return errors
