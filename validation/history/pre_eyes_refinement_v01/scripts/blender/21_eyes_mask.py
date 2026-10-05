"""Apply #16 after approved #15, preserving all unrelated primary/deferred geometry."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from face_geometry import build
from blockout_geometry import save
build(Path.cwd())
save(Path.cwd())
print('FACE GEOMETRY BUILT: layered eyes, aim pivots, perforated mask and spherical lids. Final rig/lookdev follows.')
