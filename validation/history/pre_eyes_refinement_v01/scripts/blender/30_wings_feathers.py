"""Build actual broad feather groups on a working copy; smoke runs before40."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from feathers_geometry import build
from blockout_geometry import save
ROOT = Path.cwd()
parts = build(ROOT)
save(ROOT)
print('FEATHERS BUILT:',len(parts),'editable components, symmetric layers and soft wing roots.')
