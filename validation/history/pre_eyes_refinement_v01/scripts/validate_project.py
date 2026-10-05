#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, sys
from validation_config import validate_studio

ROOT=Path(__file__).resolve().parents[1]
errors=[]
warnings=[]

def load(path):
    try:
        return json.loads((ROOT/path).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return {}

spec=load("design/character_spec.json")
rig=load("design/rig_spec.json")
hier=load("design/reference_hierarchy.json")
materials=load("design/materials.json")
manifest=load("references/manifest.json")
views=load("validation/reference_views.json")
checklist=load("validation/checklist.json")
errors.extend(validate_studio(views, manifest, hier))

feet=spec.get("anatomy",{}).get("feet",{})
if feet.get("toes_per_foot") != 4 or feet.get("forward_toes") != 3 or feet.get("rear_toes") != 1:
    errors.append("character_spec foot anatomy must be exactly 3 forward + 1 rear toe per foot")

rfeet=rig.get("foot_rule",{})
if rfeet != {"toes_per_foot":4,"forward":3,"rear":1}:
    errors.append("rig_spec foot rule must be exactly 3+1")

if spec.get("flight_required") is not False:
    errors.append("V1 must keep flight_required=false")

refs=manifest.get("references",[])
names=[r.get("file") for r in refs]
if len(names)!=len(set(names)):
    errors.append("reference manifest contains duplicate filenames")

for required in ("00_original_logo.png","07_turnaround_technical.png","08_parts_lookdev_technical.png"):
    if required not in names:
        errors.append(f"missing core reference manifest entry: {required}")

ranked=[]
for item in hier.get("hierarchy",[]):
    ranked.extend(([item["file"]] if "file" in item else item.get("files",[])))
for required in ("00_original_logo.png","07_turnaround_technical.png","08_parts_lookdev_technical.png"):
    if required not in ranked:
        errors.append(f"reference hierarchy does not include {required}")

for key in ("feather_navy","feather_blue_cyan","face_cream"):
    if materials.get("materials",{}).get(key,{}).get("metallic",1) != 0.0:
        errors.append(f"{key} must remain non-metallic")

if len(views.get("views",[])) < 4:
    errors.append("at least four validation views are required")

if {v.get("name") for v in views.get("views", [])} != {"VAL_FRONT", "VAL_LEFT", "VAL_BACK", "VAL_3Q"}:
    errors.append("validation views must include front, left profile, back and 3/4 front")

if hier.get("conflict_rule") != "higher_rank_wins":
    errors.append("reference conflicts must use higher_rank_wins")
for rank, filename in enumerate(("00_original_logo.png", "07_turnaround_technical.png", "08_parts_lookdev_technical.png"), 1):
    if not any(item.get("rank") == rank and item.get("file") == filename for item in hier.get("hierarchy", [])):
        errors.append(f"reference hierarchy rank {rank} must be {filename}")

if len(checklist.get("checks",[])) < 8:
    errors.append("validation checklist unexpectedly short")

ap=argparse.ArgumentParser()
ap.add_argument("--strict-assets",action="store_true")
args=ap.parse_args()

approved=ROOT/"references"/"approved"
try:
    from PIL import Image
except Exception:
    Image=None
    errors.append("Pillow is required for reference dimension validation; install requirements.txt")

for rec in refs:
    p=approved/rec["file"]
    if not p.exists():
        msg=f"reference asset not present yet: {p.relative_to(ROOT)}"
        if args.strict_assets and rec.get("required"):
            errors.append(msg)
        else:
            warnings.append(msg)
        continue
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if digest != rec.get("sha256"):
        errors.append(f"{rec['file']}: SHA-256 mismatch")
    if Image:
        try:
            with Image.open(p) as im:
                if im.size != (rec.get("width"),rec.get("height")):
                    errors.append(f"{rec['file']}: dimensions {im.size} != expected {(rec.get('width'),rec.get('height'))}")
        except Exception as exc:
            errors.append(f"{rec['file']}: cannot read image: {exc}")

for w in warnings:
    print("WARNING:",w)

# Current admission gates supplement the byte-exact historical v1 validators.
# This entry point is not bound by previous milestone source inventories.
if not errors:
    from delivery_gates import validate_all
    errors.extend(validate_all(ROOT))
    from review_fixes_gate import validate_review_fixes
    errors.extend(validate_review_fixes(ROOT))

if errors:
    print("VALIDATION FAILED")
    for e in errors:
        print(" -",e)
    sys.exit(1)

print(f"VALIDATION OK: {len(refs)} reference records; 3+1 foot rule locked; V1 flight disabled.")
