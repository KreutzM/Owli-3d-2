# Next goal — #40 chest color distribution and paired recessed nostrils

The renewed user findings are documented in
[the analysis](reviews/user-findings-2026-10-05.md) and
[Issue #40](https://github.com/KreutzM/Owli-3d/issues/40).
F-01 chest refinement and F-02 nostrils remain open. F-03 eye refinement belongs
to #19; inspect its actual delivered proof, separate acceptance and merged PR
before starting. The archived first eye candidate is not a current approval.

Read AGENTS and its eight required files in order, then current handoff, actual
GitHub #40/#11 and this plan. Start from delivered #19 owli_eyes_v01.blend.
Its exact SHA/size/source/render proof is in eyes_v01/verification.json.
Inspect actual 00 > 07 > 08; use 00 for color/identity and 08 for feather/beak details.

## F-01: chest

#18 removed much of the broad orange impression, but the remaining smooth narrow
diagonal trims still differ from the broader fanned gold/orange/cream feather
zones. The renewed user feedback reopens visual acceptance. Do not assume an
actual closed circumferential belt exists: the analysis distinguishes the visible
impression from geometry. Compare and adjust color distribution and feather-group
read in all four fixed views, preserving the readable cream center and controlled
warm accents. Prefer designed broad groups over hundreds of individual feathers.
Record every justified geometry/material exception.

## F-02: beak

Implement two small elongated editable depressions in the upper lateral beak,
with actual depth, rim and closed clean wall/bottom surfaces. Black surface dots
alone do not satisfy F-02. Parametrize location/width/length/depth; compare 08
across Front/Left/Back/3Q. Preserve the accepted hook/envelope, lower hinge/pivot
and 0–18° opening. Both recesses must be present, even when one is occluded.

## Delivery and combined checks

Use new helpers/JSON, an own new LFS scene and review folder. Older beak/face/
material/eye sources are hash-bound and must not be casually edited. Preserve
the complete accepted #19 eye state: pupil ratio, iris network/variation,
reflection recipe, lid custom normals, local globe/cornea envelopes, mask and
bridge integration. Use eyes_geometry.configure_lids(root) before inherited
movement probes and eyes_geometry.set_blink(root, value) for actual animated
geometry and normal updates. Opening the Blend must not reconstruct it.

Protect all 626 predecessor anchors, all 145 eye-candidate archive bindings and
the full new #19 delivery/source chain. Bind actual UV/attributes/material graphs
and corner normals, not just cage hashes. One writer per scene; independent
visual and technical reviewers inspect final artifacts themselves.

Re-run 41 blink states/164 triangle clearances, ±12° gaze, 41 beak states, wing
gestures and all new nostril collision targets. Verify exactly 3 forward+1 rear
toes/claws and eight contacts. Add common chest/beak/eye detail boards, fixed
four-view reference comparison, repeat build/full fresh-open data and canonical
pixel evidence. Gate sources/references/manual review separately. Run existing
gates, tests, Compileall and full Blender smoke. Own reviewed green PR; close
#40 only after all three Finding IDs pass on the final common scene.
Then #20 → #21–23 → #9 → #24. No finished V1/rig/animation claim.

```powershell
python scripts/project.py validate
python scripts/feathers_gate.py
python scripts/materials_gate.py
python scripts/eyes_gate.py
python -m unittest discover -s tests -v
```
