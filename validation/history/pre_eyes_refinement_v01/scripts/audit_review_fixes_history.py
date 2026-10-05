"""Independently compare v2 anchors against actual predecessor Git/LFS bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from evidence_contracts import HISTORY_PREDECESSOR, HISTORY_CONTRACT, PREDECESSOR_SHA256
from review_fixes_contracts import PROTECTED_SHA256

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args = parser.parse_args()
sha = lambda data:hashlib.sha256(data).hexdigest()
def git_bytes(commit,name):
    return subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT)
result = {'pre_feet_commit':HISTORY_PREDECESSOR,'review_baseline_commit':'473f8726d32ac7852ef93884b3010b52b8836521',
          'pre_feet_anchors':{},'protected_review_files':{}}
for name,digest in PREDECESSOR_SHA256.items():
    actual = git_bytes(HISTORY_PREDECESSOR,name)
    record = HISTORY_CONTRACT['source_relocations'].get(name) or HISTORY_CONTRACT['metadata_relocations'][name]
    saved = (ROOT/(record.get('path') or record['snapshot'])).read_bytes()
    assert sha(actual)==digest and actual==saved,name
    result['pre_feet_anchors'][name] = dict(git_sha256=sha(actual),saved_sha256=sha(saved),byte_exact=True)
for name,digest in PROTECTED_SHA256.items():
    actual = git_bytes(result['review_baseline_commit'],name)
    saved = (ROOT/name).read_bytes()
    if actual.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        lines = actual.decode().splitlines()
        oid = next(line.split(':')[1] for line in lines if line.startswith('oid sha256:'))
        size = int(next(line.split()[1] for line in lines if line.startswith('size ')))
        assert sha(saved)==oid==digest and len(saved)==size,name
        result['protected_review_files'][name] = dict(lfs_oid=oid,bytes=size,unchanged=True)
    else:
        assert actual==saved and sha(saved)==digest,name
        result['protected_review_files'][name] = dict(git_sha256=sha(actual),bytes=len(saved),unchanged=True)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print('ACTUAL GIT/LFS HISTORY PASS:',len(result['pre_feet_anchors']),'pre-feet anchors;',len(result['protected_review_files']),'protected review files')
