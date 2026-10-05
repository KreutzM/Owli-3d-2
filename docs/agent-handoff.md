# Current agent handoff

Current eye milestone: [#19](https://github.com/KreutzM/Owli-3d/issues/19),
including renewed F-03 eye/lid refinement from the 2026-10-05 user feedback.
The actual current artifact is blender/scene/owli_eyes_v01.blend. Its exact SHA,
size, source bindings and four-worker evidence are in
[verification.json](../validation/reviews/eyes_v01/verification.json);
separate manual acceptance is [review.json](../validation/reviews/eyes_v01/review.json).
Read the [eye report](../validation/reviews/eyes_v01/report.md) and both independent
reviews. Check the actual #19 PR merge and CI in GitHub before further production;
this source-bound handoff does not substitute for an actual integration check.

**Next: [#40](https://github.com/KreutzM/Owli-3d/issues/40), renewed F-01 chest color
and F-02 paired recessed nostrils, before #20.**
[User analysis](reviews/user-findings-2026-10-05.md),
[eye scope](next-goal-19.md), [next production plan](next-goal-40.md).
The first unmerged eye candidate and its earlier PASS decisions were superseded,
not rewritten. They remain byte-exact in validation/history/pre_eyes_refinement_v01/.
A finished V1 avatar, rig or animation set is not delivered at this milestone.

## Required entry

AGENTS and eight mandatory sources in exact order; then this handoff, next-goal-40,
actual GitHub #40/#11, repo map, decisions and current eye report.
Inspect references 00 > 07 > 08. Do not regenerate completed historical milestones.
Check current branch/worktree; secure own changes before switching branches.
An LFS pointer is not an actual working Blend. Fetch/LFS pull within authorized scope.

```powershell
git status --short --branch
git fetch origin
git lfs pull
python scripts/project.py doctor
python scripts/project.py validate
python scripts/feathers_gate.py
python scripts/materials_gate.py
python scripts/eyes_gate.py
python -m unittest discover -s tests -v
python -m compileall -q scripts
python scripts/project.py smoke
```

## Production content and deliberate eye changes

117 objects/103 meshes, five Empty pivots, four fixed cameras, five lights,
14 materials = ten assigned non-eye roles plus four eye roles. No Armature/Actions.
Meters, Z up, +Y forward, character left −X. Contiguous head/neck/torso,
prepared body/head/wing groups; no final rig. 51 FTH meshes/48 closed broad layers,
0–12° folded-wing gestures, fixed roots/45-mm shoulder blend. Per foot exactly
three front+one rear toes/claws; eight actual claw/bar contacts. Upper/lower beak
with 0–18° opening; **nostrils still missing**.

Seven seated forehead nodes/six links and four thin perch rings remain #18.
Feathers satin/matte, keratin semigloss, brushed metal and restrained tech emission.
The #18 cream chest and local warm diagonals are preserved in #19. Renewed F-01
is open: narrow smooth trims still differ from the fanned reference zones.
Few broad feather groups do not reproduce every feather in the illustration.

Each eye has separate Globe/Iris/Pupil/Cornea under its aim pivot. Four editable
actual eye shaders; projected pupil/iris ratio 0.251854332; varied blue/cyan iris,
bright curved lower crescent, restricted warm lower arc, subtle branched network
and compact actual view-dependent catchlights. Cornea IOR1.376/roughness.04,
transparent/glossy BLENDED shell with capped front Fresnel. Fixed Eevee uses
explicit artistic gain32, directional reflection kernel power384, radiance
threshold .65–1.60 and lower-iris emission .4+.65. This is a documented stylized
reflection response, not energy-conserving raytraced refraction. Studio unchanged.

Nine local cages change: four Iris/Pupil, four Lids and the existing FAC_MaskBridge.
Both EyeAim pivots move −6 mm in Y; X/Z arrangement is preserved. The lid depth
falls off quadratically to the exact outer boundary. Authored radial front/back
corner normals with separate endcaps integrate the cream lids without the former
inflated ring appearance. These are intentional stylized shading normals, not
mathematical surface normals of the tapered cage. They update at each nonlinear
blink. The actual #37 41×21 bridge rows widen only in X with bounded fades
z=.377–.388/.433–.448 m and target half-width16.5mm. Both masks stay exact.
90 non-eye full states, three other pivots, local Globe/Cornea cages and their
actual corner normals remain exact. No blanket exemption or relaxed .3-mm clearance.

## Evidence and following sequence

Four isolated actual Blender workers: repeated build, saved-build, reload_a,
reload_b. Complete current slots/graphs/UV/attributes/local-eye shapes/normal
hashes and audits; exact common runtime data and saved/two-reload RGBA arrays.
41 nonlinear blink states/164 triangle minima, 1,312 lid/eye collision checks,
10,034 closure rays, ±12° gaze, 41 beak states, six wing states, all51FTH/17TECH
and all8eyes. The refined reproduced minimum eye clearance is 1.777607436 mm; the canonical
reload_b checks give 1.7776074357634466 mm; use the current datasets.
Actual 41×4 pose-normal hashes and exact neutral restoration are part of proof.
13 manual criteria include the renewed reflection/iris/network/lid findings.
Independent final reviewers must open/render/probe the actual delivered scene.
CI validates artifacts/tests on Windows/Ubuntu; it does not install Blender.

| Order | Goal |
|---|---|
| Next | #40/F-01 chest distribution and F-02 nostrils; all three findings checked on common scene |
| Then | #20 combined topology/deformation preparation after lookdev and #40 |
| Then | #21 → #22 → #23 body/head → face → wings/feet rig; container #8 |
| Then | #9 animations, #24 owli_v1.blend/final QA/docs/handoff.md; Epic #11 |

#18 is merged. Actual #19 closure must follow delivered acceptance and integration.
#7 remains open for the renewed chest-material acceptance F-01 in #40, even after
its eye child #19 is delivered. #40 stays open for F-01/F-02. Existing rig/animation follow-up
[QA contract](review-fixes-qa-followup.md) remains #20–24.

## Historical chain and APIs

#18 main e04afa99302fbed620309fadd3bef396e075d4e8, materials scene SHA
ca5522b3948e2d3501eb47c0b0f3099a7ca9d7e596e8e9af5b9f6128353acaa3,1793740bytes.
#6/PR39 a8634936494512d64e311149f20ed4e24ea492ac, feathers scene SHA
76ee3f1c0f8b4314aee40585445c14e3b2d193b7aa04c7e2c86e6f810f576b0a,1385718bytes.
#37 commit966b7f02489ebad4890ba17a6c64f4c03adc2803, scene SHA
8685fc054428ec848f20a922c995487f9ac4a2797cbe3713eaeb5e364b02e8fb.
Archived unmerged candidate SHA88d10dd7fba31ecec7116002c2ec40934d5c0e820c77dd6aecc79d34b4e093cc
is superseded and kept byte-exact in validation/history/pre_eyes_refinement_v01/.
Delivered #19 scene SHA 8c1bcd9474281cc8c0509c50606016973db582f94771df25bdc30f505b76bc9b,
2245164 bytes (regenerated in the canonical Owli-3d-2 worktree; the Blend is
working-directory dependent, so its embedded scratch path changes the hash). eyes_contracts.py fixes626 predecessor Git/LFS anchors,
145 archive bindings and all current source/reference/evidence bindings. Future
work must additionally protect the entire new #19 delivery. Shared historical
helpers, design/materials.json/project.py and old approvals remain exact.
Own helper/JSON/scene/review folder per goal; one writer per production file.
Separate independent reviewers and scratch scenes. tmp/ is ignored scratch.

Full eyes_checks.mesh_state binds slots/graphs/UV/color/attributes/shape keys;
actual ordered corner normals have their own hash/audit. shape_hashes is geometry.
For saved-scene probes call eyes_geometry.configure_lids(root) before inherited
movement checks; it installs the current recipe without modifying loaded cages.
Use eyes_geometry.set_blink(root,value) for nonlinear lid reconstruction plus
actual custom-normal updates. Linear interpolated keys can cut cornea.
The old inherited helper alone does not update custom normals. Preserve this API
through rigging and evaluate geometry AND normals at intermediate states.

Old verifiers can expect replaced diagnostic guides; reuse generic audit/function
APIs explicitly and include new geometry as collision targets. TECH tori Euler0;
GRP_ reserved for feet/perch. Some render commands save loaded scenes: use scratch
copies. Stage50 smoke writes generic scratch owli.blend; Stage60 is an unweighted
scaffold. Eye production is explicitly scripts/eyes_review.py, not scaffold smoke.
Fresh reproduction uses a new work directory, for example:

```powershell
python scripts/eyes_review.py --work tmp/goal19/reproduce_new --output validation/reviews/eyes_v01 --scene-output blender/scene/owli_eyes_v01.blend
```

This overwrites only the named current #19 delivery; future goals should write
new named artifacts. UTF-8/LF and read_bytes hashes preserve cross-platform sources.
Python3.11.9/Pillow12.2.0/Git2.53/LFS3.7.1/Blender5.2.1LTS;
Blender path C:/Program Files/Blender Foundation/Blender 5.2/blender.exe.
SSH push/GitHub connector work; older gh token invalid. Git writes require sandbox
escalation in this environment; never version credentials.
