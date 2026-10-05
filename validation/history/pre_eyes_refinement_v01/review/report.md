# Goal #19 — Blue/Cyan eye lookdev and F-03

Scene `blender/scene/owli_eyes_v01.blend`, 2,241,341 bytes,
SHA256 `88d10dd7fba31ecec7116002c2ec40934d5c0e820c77dd6aecc79d34b4e093cc`. Predecessor: main `e04afa99302fbed620309fadd3bef396e075d4e8`,
`owli_materials_v01.blend`, SHA256
`ca5522b3948e2d3501eb47c0b0f3099a7ca9d7e596e8e9af5b9f6128353acaa3`.
117 objects/103 meshes/five pivots/four fixed cameras/five area lights;
14 assigned materials = ten non-eye roles plus four optical eye roles.
No Armature/Actions/final rig. This closes the bounded eye lookdev; final V1
topology, rig and animation remain #20–#24, nostrils remain #40/F-02.

## Actual appearance and reference decisions

00 > 07 > 08 was inspected directly. The broad dark illustrated eye is mostly
shaded iris, not the literal black pupil. The old measured pupil/iris radius
ratio .74858 becomes 0.251854332: pupil 11.144 mm, iris 44.248 mm. Neutral pupils
remain centered for coherent gaze rather than copying an illustrated off-axis dot.
Only four Iris/Pupil cages change. Eye arrangement, 49-mm globes, 50.8-mm outer
cornea, mask/lids and fixed studio remain exact. Iris uses 192 angular/32 radial
segments; the smaller pupil 96/8. An over-resolved 192/32 pupil triggered the
unchanged adjacent/coplanar near-plane audit; the simpler cage passes without
relaxing tolerances. Optically separate layers have real measurable spacing.

Four actual assigned shaders supply deep upper navy, blue/cyan depth, curved
pale lower iris crescent, dark readable pupil, soft deep limbus and a restricted
gold lower peripheral accent from the logo. No homogeneous orange eye ring.
The subtle lower-inner network has nine analytic links and ten nodes (.22-mm
stroke half-width/.65-mm node radius) in actual local object coordinates. It
follows each eye pivot, leaves the pupil clear and adds no collision geometry.
`eyes_before_after.png` compares equal fixed-camera crops against 00/08.

Metallic=0; iris roughness .09, pupil .065, globe .10, cornea .04; IOR 1.376.
Real studio lights create view-dependent smooth catchlights on the curved shell.
Cornea uses a single front-facing Fresnel transparent/glossy coating. BLENDED
transparency removes stochastic speckle. For the unchanged low-energy Eevee
studio, ShaderToRGB applies an explicit artistic reflection gain 6 to the real
glossy light response; this is not an energy-conserving raytraced refraction
shader. Iris emission .40 plus up to .65 in the lower crescent supports the
branded luminous color. These stylized departures are parameterized and justified,
not hidden lighting edits. Three broad actual-area catchlights and the stronger
profile rim differ from the painted reference highlights; they remain controlled
and were explicitly accepted within this fixed-studio goal.

## Iterations and independent review

Preview01–05 each rendered the same Front/Left/Back/3Q cameras. V19-01 (flat
horizontal color horizon) became a curved peripheral lower crescent; V19-02
(grainy then gray flat reflections) became smooth actual-light cornea highlights;
V19-03 (invisible network nodes) was corrected with .65-mm nodes. All are closed.
Front/3Q remain friendly, profile retains a convex dome, back preserves the
accepted non-eye silhouette. No new concept art, anatomy, flight or camera edits.
Primary and independent visual reviewer inspected actual references and all four
final views; the reviewer also opened/rendered the delivered scene independently.
See the separate final visual/technical reports and bound companion evidence.

## Measured preservation, function and reproducibility

All 95 non-eye meshes retain complete cages, slots, full graphs, polygon indices,
actual UVs, rest/mesh attributes and shape keys. Five pivots and all studio/render
settings remain unchanged. Four globe/cornea cages are exact; only four iris/pupil
cages change. 626 real predecessor Git/LFS anchors, 75 source files and nine
reference files are bound. Historical scenes, scripts, images and approvals were
neither regenerated nor rebound. No shared source-bound helper was edited.

Four actual Blender workers prove build/repeat/save and fresh saved-build/two
reloads. Repeat comparison includes all eye material slots and complete graphs;
no object/mesh/material leaks. All 25 canonical runtime fields agree, and all four
saved-build/reload RGBA buffers are exactly identical. Live Eevee cache images
remain separately identified. New eye surfaces pass closed/connected/outward,
nondegenerate, duplicate and adjacent/coplanar triangle audits.

Actual probes include 41 nonlinear blinks/164 triangle minima, 10,034 closure
rays, ±12° gaze, 41 beak states, six wing gestures, all 51 FTH/17 TECH targets,
exact 3+1 toes/claws and eight claw/bar contacts. New actual-cornea-radius minimum
clearance is 1.024824882 mm; all 1,312 lid/eight-eye pairs and four times 72
eye/mask/lid/beak gaze pairs are explicit. Every individual minimum and its
aggregate is validated. Neutral restoration is exact. The independent technical
reviewer additionally checks five mixed states/3,080 eye-target pairs and negative
gate cases; actual scope/counts/results are in its own bound evidence.

## Reproduction and acceptance

```powershell
python scripts/eyes_review.py --work tmp/goal19/new_unique_run --output validation/reviews/eyes_v01 --scene-output blender/scene/owli_eyes_v01.blend
python scripts/project.py doctor
python scripts/project.py validate
python scripts/feathers_gate.py
python scripts/materials_gate.py
python scripts/eyes_gate.py
python -m unittest discover -s tests -v
python -m compileall -q scripts
python scripts/project.py smoke
```

The separate `review.json` records nine reasoned criteria, four views and zero
blocking findings; automated `design_approval=false` does not grant that review.
Strict gates, all 102 tests (89.913 seconds), Compileall, Doctor/validate and the
isolated Blender smoke passed locally. Eleven independent full-delivery mutation
fixtures were rejected; restored positive controls passed and every production
byte remained unchanged. The smoke remains the older stage-chain fixture; the four actual
eye workers and independent fresh-open probes validate this production scene.
Windows/Ubuntu CI must pass on the exact PR head before integration; GitHub records
the actual runs, merge and issue closure without circularly embedding future commit
hashes into these bound artifacts. Few broad feather groups remain the accepted
abstraction; full physical raytracing, topology/deformation rig and animation are
future work. F-01 from #18 is preserved; F-03 is fulfilled here. F-02 remains open.
