"""Create initial stylized material library from design/materials.json."""
from pathlib import Path
import bpy, json

ROOT=Path.cwd()
cfg=json.loads((ROOT/"design"/"materials.json").read_text())
palette=cfg["sampled_logo_colors"]

def rgb(hexv):
    h=hexv.lstrip("#")
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(1,)

def mat(name,color,roughness=0.5,metallic=0.0,emission=None,emission_strength=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=rgb(color)
    bsdf.inputs["Roughness"].default_value=roughness
    bsdf.inputs["Metallic"].default_value=metallic
    if emission:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value=rgb(emission)
            bsdf.inputs["Emission Strength"].default_value=emission_strength
    return m

mat("Owli_Feather_Navy",palette["deep_navy"],0.58,0.0)
mat("Owli_Feather_Blue",palette["mid_blue"],0.52,0.0)
mat("Owli_Feather_Cyan",palette["cyan_reference"],0.48,0.0)
mat("Owli_Face_Cream",palette["cream"],0.64,0.0)
mat("Owli_Beak_Orange",palette["orange_reference"],0.32,0.0)
mat("Owli_Claw_Dark","#111522",0.28,0.0)
mat("Owli_Eye_Gloss","#06163B",0.06,0.0)
mat("Owli_Tech_Emission","#55F7FF",0.22,0.0,"#55F7FF",2.5)
mat("Owli_Perch_Metal","#AEB8C5",0.3,0.85)

for material in bpy.data.materials:
    if material.name.startswith("Owli_"):
        material.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"blender"/"scene"/"owli.blend"))
print("Created and saved Owli V1 material library.")
