"""Feather strategy scaffold.

V1 uses large stylized feather groups over clean wing/body volumes. This script intentionally avoids
literal full-feather simulation.
"""
import bpy

if "WINGS" not in bpy.data.collections or "FEATHERS" not in bpy.data.collections:
    raise RuntimeError("Run scene setup first.")

for side in ("L","R"):
    wing=bpy.data.objects.get(f"BLK_Wing_{side}")
    if wing:
        wing["feather_strategy"]="large layered groups; keep wing root deformable"
        wing["gesture_requirement"]="must support restrained explanatory gesture"

print("Wing/feather policy attached. Build a small number of readable layers, not hundreds of feathers.")
