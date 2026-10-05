# Decision log

## 2026-10-03 — Design image phase frozen

The current approved logo, technical turnaround, technical parts/lookdev sheet and selected beauty views are sufficient to begin 3D blockout.

New general concept images are no longer created by default.

## 2026-10-03 — Perched V1

Owli V1 sits on a modern cylindrical tech perch. Flight is deferred.

## 2026-10-03 — Organic tech character

Owli is modeled as a living stylized owl with integrated digital motifs, not as a metallic robot owl.

## 2026-10-03 — Foot anatomy

Each foot has exactly 4 toes/claws: 3 forward and 1 rear.

## 2026-10-03 — Feather strategy

Use clean body/wing volumes plus major stylized feather groups. Do not build full realistic feather simulation for V1.

## 2026-10-03 — Animation-first topology

Eyes, beak, wing roots, neck and feet must be designed with future avatar deformation in mind from the beginning.

## 2026-10-03 — Fixed validation studio (issue #12)

Camera locations/targets, 0.58 m orthographic scale and the 65 mm 3/4 lens from
the original renderer remain unchanged. Camera/light/render/reference parameters
now live in validation/reference_views.json. Five fixed neutral white area lights,
an explicit neutral world and Standard color management replace the unlit default.
Light power was reduced after visual review found clipped white fixture surfaces.
The saved studio uses 1024px renders, zero exposure compensation and no automatic
fitting. Object bounds must keep a 2% margin; invalid image/depth framing fails.

The validation Blend uses only existing coarse volumes and exactly 3+1 toe guides
as a technical fixture. No anatomy, material-design or silhouette decisions are
introduced. Geometry identity and four exact pixel comparisons after save/reload
are checked. The production scene is not created or overwritten by setup-review.

Front/profile/back use labeled technical turnaround panels. The 3/4 board shows
both the original beauty reference (style, rank 4) and technical 3/4 panel (geometry,
rank 2). The technical 3/4 panel depicts the opposite lateral side to the preserved
+X/+Y camera; it is not mirrored and is not interpreted as a metric alignment.
The back panel's drawn cyan crown motif does not authorize a second rear symbol;
the logo and written specification require a centered forehead motif. Visual
ambiguity in claw drawings cannot overrule the explicit 3+1 foot specification.

The coarse fixture still lacks the approved brow/ear silhouette, cream mask,
layered eyes, tech motif and real gripping toes. Its proportions, tail and beak
remain provisional. These existing modeling limitations are assigned to #13/#14
and later production goals; this setup review grants no silhouette approval.

## 2026-10-03 — Parameterized coarse blockout (issue #13)

All authored dimensions now live in design/proportions.json. Values are meters at
reference_height_m=0.45; character_spec.production_scale applies uniformly to every
character and perch vertex. Ring rows are [z, center_x, center_y, radius_x, radius_y].
Lofts represent primary head/body, folded wings, compact centered tail, mask bridge,
chest, hooked beak and one broad swept tuft on each side. Two spherical eyes remain
separate; iris/pupil caps are positioning guides. Deterministic sphere construction
avoids Blender operator polygon-order variation on repeated builds.

The logo controls face/color identity; technical turnaround 07 controls compact
perched volume and side/back interpretation; parts sheet 08 controls the hooked
beak and gripping foot intent. A broad navy brow and cream cheek/bridge volumes
reserve the feather mass without modeling individual feathers. The reference's
layered crest is represented by one editable volume per side. No conflicting old
concept proportions were averaged in. Fixed #12 camera and light parameters are
unchanged; the opposite-side technical 3/4 panel remains unmirrored.

Perch bar length is 0.37 m rather than the former 0.43 m, radius is 0.0185 m.
The ear tips reach 0.53 m above the base; the nominal 0.45 m character scale is a
provisional recipe scale, not a strict foot-to-crown metrology guarantee. The
body tapers into the seat; visible leg/pad guides connect it to the bar. Each foot
has exactly three forward curves and one rear curve around the bar, with tips
below its center. Rear centers remain strictly behind the bar. Dark toe tips are
part of each guide mesh; they are not additional anatomical toes or final claws.
Final foot topology and grip articulation belong to #5.

Simple rough, nonmetallic debug swatches use the unchanged existing logo palette
with explicit sRGB-to-linear conversion. These provide mask/eye/beak readability;
they do not replace the material specification. Glossy layered eyes, orange chest
feather accents, cyan plumage layers, forehead network geometry/emission and metal
perch finishing remain in #6/#16/#18/#19 and later production steps. The forehead
motif is not inferred on the back from turnaround 07's ambiguous crown drawing.
No new concepts, flight geometry, rig or fine feathers were added.

Four fixed views were inspected against their approved reference panels. The
blockout establishes the required anatomy and primary masses, but the mask/brow
transitions are separate overlapping volumes; ear tips remain broad, neck seams
and chest/tail ends pinch, and the cyan eye guides lack eyelids, cornea and final
iris depth. These are explicit coarse-stage limitations. Relative head/body,
beak, tail and wing proportions still require the separate #14 silhouette review.
This milestone grants no silhouette freeze or production-readiness approval.

The neutral setup evidence is refreshed using the current coarse anatomy with
material slots cleared. Its cameras/lights are identical to #12; the colored
blockout evidence and saved milestone are delivered separately. Integration
checks repeat builds without object/mesh/material leaks, probe eye spacing/depth,
beak/wing/tail edits and uniform scale, restore the baseline, render four views,
then reopen and rerender in a fresh Blender process. Controlled parameter probes
are tests, not new design iterations or alternate approved character designs.

## 2026-10-04 — Four-view coarse silhouette freeze (#14)

The #13 baseline was reviewed simultaneously against logo 00 (face/brand/color),
technical turnaround 07 (volume/profile/back), and parts 08 (beak/feet). It showed
undersized eye read, an oversized shield-like cream chest, exposed leg columns,
and a tail terminating too high in the back. Parameters now cover more of the
legs with the lower body, shorten the cream chest into a tapered V, add two broad
orange chest masses, enlarge eyes from 0.086 to 0.098 m diameter, move their centers
from Y=0.096 to Y=0.074, widen/shorten the coarse beak projection, lower wing tips,
and extend the centered tail below the perch bar. Tufts now sweep inward at their
tips, and the brow tilt is reduced from 0.20 to 0.08 rad after a stern-expression
finding. Mask lobes are narrowed to avoid broad cream side protrusions in back.

Iterations are retained under validation/reviews/blockout_v01/iterations/:
13_baseline, 14_iteration_01 and 14_iteration_02. Each includes four original
renders and reference boards, parameters and verification. Iteration 01 was
rejected for excessive eye projection; iteration 02 for stern brows and broad
cream temple edges. The final iteration resolves these coarse placement blockers.
Tiny cream temple seams remain a topology/feather integration task, not a large
volume error. Overlapping component joins and smooth bulb-like primary masses
are intentionally coarse; later topology must preserve the frozen outer envelope.

Two orange chest masses are color/volume guides, not individual detailed feathers.
A single sparse cyan graph reserves the forehead motif's position from logo/parts
references. It is a matte geometry guide, not the finished emissive tech asset.
Upper points can be visible above the head from back/profile; there is no second
rear symbol. Final feather integration, emission and node styling belong to #18.
No new design art, flight geometry, fine feather layers or rig was introduced.

The coarse silhouette and face arrangement are frozen to the explicit hashes and
12 reasoned checklist results in design/silhouette_freeze.json, with visible
findings in validation/reviews/blockout_v01/report.md. This freezes the large
head/body/wing/tail/beak envelope, seated pose and eye/mask placement. It does not
approve production topology, deformation, final materials, eyelids, cornea,
individual feather groups, final claw mechanics or animation. Those goals must
respect this envelope; a later substantial silhouette change requires a new
four-view review and an updated freeze decision, rather than changing cameras.

The fixed studio remains unchanged. Technical verification never grants visual
approval automatically: its design_approval=false refers to the automated check.
The separately authored silhouette_freeze.json is the visual decision. It binds
current parameters, checklist, camera recipe, reference hierarchy, source images,
saved Blend and four final images. CI rejects missing checklist entries, blocking
findings, wrong reference ranks or changed/stale freeze artifacts. The neutral
setup fixture is refreshed separately from the same current primary volumes.

## 2026-10-04 — Editable primary head/neck/torso topology (#15)

The #14 outer envelopes remain authoritative. Stage 20 samples evaluated head and
torso envelopes and replaces both closed overlapping coarse objects with one
closed, continuous quad shell. Horizontal circumferential loops pass through
the neck; there are no hidden head-bottom/body-top caps inside this shell.
Distributed quad-disk caps avoid high-valence polar fans. Brow and swept ear-tuft
masses become separate closed quad primary volumes, mirrored in X. Their deliberate
closed attachment roots still overlap the head, as the design calls for feather
groups; joining those feather roots is separate from eliminating torso/head
internal surfaces. Face mask, lids, eyes, beak, wings, chest guides, tail and 3+1
feet are preserved byte-for-byte at mesh/matrix level for their own goals.

Reference authority remains logo 00 for face/color identity, turnaround 07 for
outer volumes and parts 08 for construction intent. No camera, illumination,
reference crop, material palette, anatomy or perched/no-flight decision changed.
The small shape adjustment from replacing coarse subdivision caps and smoothing
the envelope junction is measured against the old evaluated surfaces and checked
in full and isolated-primary silhouettes. This is topology refinement within the
existing freeze, not a new general design or concept-art phase.

Numerical ray/quad tessellation noise in the coarse source is not interpreted as
an asymmetric design. Paired torso rings are symmetrized, and the right tuft is
constructed from the left by reflection and reversed winding. Sampling occurs
at reference scale and the completed cage is uniformly scaled afterward, avoiding
scale-dependent BVH tessellation. Additional end loops prevent subdivision pulling
the seated lower-body envelope inward; small insets at the extrema avoid microscopic
sliver caps. Early diagnostic builds exposed symmetry, cap and scale problems;
these were fixed before accepting or publishing the milestone.

Body/head weights partition unity with a broad soft transition from Z=0.265 to
0.385 m; the neck pivot is Z=0.325 m. Independent left/right wing-root masks provide
soft attachment regions rather than cut-out sockets or a rigid shell. Head tilt
15 degrees, turn 20 degrees and each wing-root displacement 12 mm are exercised
on the actual cage and subdivided result. Weights are preparation, not final rig
approval: facial/tuft attachments, wing deformation, final bone layout and volume
preservation still require their subsequent production goals. Rigging should reuse
the editable cage/loops and refine these initial weights in combined pose tests.

The full avatar retains intentional coarse face/chest/wing overlaps. Neck/body
continuity is delivered here; face-mask/eyelid construction belongs to #16, beak
articulation to #17, feathers to #6 and final surface/tech treatment to #18/#19.
The navy/blue boundary is a debug material assignment, not a seam in the new mesh.
Do not mistake the matte diagnostic palette or four-view topology acceptance for
completion of the production character. The LFS milestone, fresh-open verification,
fixed-view reference comparisons and limits are documented in its review report.

## 2026-10-04 — #16 layered eyes, perforated mask and spherical blink

Reference authority remains logo 00 for friendly face language and cream/cyan
identity, turnaround 07 for frozen head/profile placement, and parts 08 for
separate volumetric eye construction. No new concept image was generated. Frozen
eye centers (+/-0.064, 0.074, 0.409 m) and globe radius 0.049 m are unchanged.
The coarse closed mask lobes are replaced with thick annular cream cheek surfaces
and a narrow central bridge, retaining the frozen outer X/Z envelope. Eyes now
have separately named globe, iris, pupil and cornea meshes with globe-center aim
pivots and +Y forward. This resolves geometry hidden behind the old flat guides.

All eye components are rigid local meshes under the two aim pivots; mask/lids stay
in head/world space until the later rig attachment goal. Lids use offset spherical
quad patches and a deterministic nonlinear open/closed reconstruction, not linear
shape-key interpolation. Their back surface clears the cornea. The final rig must
preserve this spherical constraint when connecting blink_L/blink_R controls.
The probe API supports unilateral blinks, but no finished facial controller,
speech synchronization, or animation system is introduced by this geometry goal.

An early downward-curved meeting edge folded the upper lid near its canthi at
95% closure. The actual mesh self-intersection audit rejected it; a straight
shared meeting edge fixes the Jacobian reversal and maintains a finite canthus
strip. A dedicated negative probe preserves that rejected case as a regression
check. The initial 31 mm mask ridge looked like a hard tube, so it was softened
to 14 mm; a dangling bridge below the beak was removed. Neutral and blink states
are compared through the unchanged front, left, back and 3/4 cameras. These
changes refine the facial construction inside the frozen placement/envelope.

The cream mask/lid outer junction is an intentional attachment overlap; the
upper/lower closed lid seam is exact shared contact between separate meshes.
Mask surfaces must not intersect any eye layer or the coarse orange beak. The
beak remains unchanged for #17. Matte palette and completely transparent cornea
inspection treatment are temporary diagnostic materials. Gloss, network iris
motifs, feather layering and final material tuning remain #6/#18/#19 work.
The neutral mask is smooth primary geometry, with visible lid canthi and no
individual feather detailing. The current flat closure line is a geometric
minimum; expression-specific shaping requires later combined rig/pose review.
Body, primary head, wings, tail, tech, perch and exact 3+1 toe anatomy are preserved.

## 2026-10-04 — #17 hooked upper beak and hinged lower jaw

Logo 00 governs the orange face landmark, turnaround 07 the frozen front/profile
projection, and parts 08 the hooked beak construction. The accepted #16 face is
the starting scene. No new concept art or unrelated head/eye adjustment is needed.
The evaluated frozen beak envelope is divided by a tilted plane into two closed
rigid meshes, rather than replacing the approved outer shape with new proportions.
The upper hooked tip remains fixed. The smaller posterior lower jaw rotates
downward behind it, matching the anatomy implied by the profile/parts references.

The split is specified at (0, 0.105, 0.386) m with normal (0, 1.2, 1). Opposed
planar interior caps leave a 0.4 mm closed seam. The hinge is (0, 0.095, 0.398) m,
on the extended split plane and behind every boundary vertex, with negative local
X rotation opening the jaw. An earlier forward hinge swung rear jaw vertices
into the upper beak; the actual BVH opening test rejected it. Moving the hinge
behind the complete separation boundary fixes that collision rather than hiding
it through the camera. A too-small lower piece looked like a sliver; the revised
division retains a volumetric lower jaw while leaving the distal hook uppermost.

`design/beak.json` and `beak_geometry.set_open` document a 0–18 degree probe range.
Opening is rigid articulation, so the planar interior caps intentionally need no
deforming quad lattice. Exterior polygons are clipped from the accepted evaluated
surface; all generated vertices lie on that old envelope in the closed state.
Geometry is sampled/split at reference scale and scaled afterward, avoiding
scale-dependent clipping/vertex ordering. Interior faces use the existing deep
navy diagnostic swatch to expose a dark mouth opening; exterior keratin remains
orange. No teeth, tongue, speech synchronization or finished rig controls are added.

The unchanged #16 eyes/mask/lids, head, wings, feet, tech and perch are verified by
mesh/matrix/material/weight/modifier hashes. Four unchanged cameras expose closed,
half-open and fully open states. Full character and isolated beak alpha silhouettes
are compared to #16; the narrow physical seam may remove a small interior stripe
but must not redesign the exterior envelope. No camera or light changes hide the
open jaw. Final shader tuning and combined avatar rig/pose validation remain later
work; the geometry probe pivot is prepared for the future `beak_open` control.

## 2026-10-04 — #5 connected feet and opposed perch grip

Turnaround 07 defines the compact perched pose; parts/lookdev 08 defines thick
orange toes and separate dark hooked keratin claws. Each foot now has one editable
quad skin joining the pad, ankle and exactly three front branches plus one rear
branch. The pad uses a cube-to-ellipsoid quad lattice with four open toe ports and
an ankle port. Swept rings reuse those boundaries; there are no disconnected toe
roots, hidden internal root caps or voxel/remesh surfaces. Separate closed claw
meshes meet the distal toe caps and continue the opposing hooks below the bar.

The grip follows the real 128-sided bar surface. Contact samples use the same
angular intervals as the bar faces, so a polygon chord cannot accidentally sink
through a mathematically circular guide. `verify_feet.py` checks closed connected
surfaces, consistent outward normals, self intersections, each branch's actual
mesh adjacency, signed halfspaces of the actual bar and triangle clipping against
its interior. Contact requires a nearest-surface distance below 0.2 micrometers;
that tolerance accommodates Blender float precision rather than a visible gap.

The bar, stem and base keep their original outside dimensions and gain rounded
ends and quad caps. Their structural intersections are intended joints. The ankle
extends into the body for the later foot/leg rig. `design/feet.json` permits a
16–22 mm bar radius and 50–62 mm foot half spacing. Increasing the radius raises
the pad correspondingly to preserve support contact at the bar crown. Changes within these
ranges still require a new four-view visual review. The nominal values match the
approved coarse bar dimensions and foot spacing. The pad is lowered 1.5 mm from
the old guide position so its underside actually supports weight at the crown.
The dark claw starts at 101.25 degrees and continues to 157.5 degrees, making its
hooked shape distinct from the orange skin. A neutral gray perch inspection shader
separates the claws visually from the bar. Final brushed metal, cyan accents and
keratin shaders remain the separately planned #18 lookdev goal.

The development gates preserve all 37 unrelated predecessor meshes, repeat builds
identically, exercise half/double global scale and both permitted parameter limits,
and reject deliberately floating, penetrating and incorrectly placed rear claws.
The production entry point is `40_feet_perch.py`; scenes before #4 retain the
byte-exact archived coarse stage. The historical dependency relocation is audited
under `validation/history/pre_feet_v01/` without changing prior scene bytes,
pixels, criteria or approval decisions. The new saved scene is
`blender/scene/owli_feet_v01.blend`; permanent four-view comparisons and the
separate foot geometry decision are under `validation/reviews/feet_v01/`.
Two fresh Blender reloads reproduce identical geometry and pixels in all four
fixed cameras. The profile exposes the rear hook; the full 3/4 view shows its base
while the bar naturally occludes the lowest tip. The explicitly isolated toe
view resolves that anatomy without changing the camera. No blocking geometry
finding remains for this milestone; final avatar controls follow in the rig goals.

## 2026-10-04 — #37 organic face and complete admission gates

IR-01 is a primary form correction: logo 00 controls friendly organic face
language, 07 the head/profile and 08 the broad cream facial feather intent. The
old ring-mask envelope and horizontal brow bars were a weaker interpretation.
New parameterized discs fit their broad cheek border to the actual unchanged
head, reduce the annular ridge, connect below the beak through a smooth widened
bridge and raise/taper the brows toward the ear tufts. Exactly five meshes change;
45 others, all three pivots and the full fixed studio remain exact. New four-view
decision at `validation/reviews/review_fixes_v01/review.json` reassesses these
primary volumes; the original silhouette freeze, approval reasons, scenes and
pixels stay immutable. No concepts generated, no reference averaging.

Current editable scene is `owli_review_fixes_v01.blend`, SHA256
`8685fc054428ec848f20a922c995487f9ac4a2797cbe3713eaeb5e364b02e8fb`,
1,068,211 bytes. Blue/cyan separate eye layers, nonlinear full blink, ±12-degree
aim, 0–18-degree beak opening and actual 3+1 opposed grip remain verified.
Outer cream boundary and cheek/bridge feather flow are explicitly assigned to
large facial feather groups in #6, alongside its full wing/body/tail production.
Final eye shaders and network detailing remain #18/#19. This is primary form
acceptance, not completed V1 beauty/rig acceptance.

IR-02/03 are corrected by new gate version 2, not by rewriting historical source
or approval hashes. Old face/beak/feet/history producers remain byte-exact v1
evidence. Current `delivery_gates` and recursive `delivery_shapes` require every
source/reference/reload key, concrete nonempty typed comparison data and valid
geometry digests. `history_gate` walks an external code-owned inventory anchored
in real predecessor Git bytes and permits only known top-level dependency maps.
Empty/short maps, missing snapshots, altered archives/criteria and matched null
reload claims fail. Fourteen pre-feet anchors and 384 protected review files
were independently compared against actual Git/LFS bytes.

IR-04 adds focused cage/evaluated triangle-interior checks, adjacency included,
and a projected coplanar area test because BVH alone misses planar overlaps.
Four actual malformed fixtures reject. Small features below the documented
inset/area/plane tolerances remain a stated limit; a vertex pad contact does not
claim pressure physics. The complete future combined avatar QA has concrete
owners #20–#24 in `docs/review-fixes-qa-followup.md` and corresponding issues.

IR-05 uses an explicit new scratch work directory and only the named new output
milestone. Accepted inputs and historical artifacts are checked unchanged before
and after. In-process Eevee live images exhibit small RGB cache differences even
with exact cages; the saved-build renderer and two additional fresh processes
give exact canonical RGBA pixels. Live images are retained, not relabeled as
identical. Both the unchanged complete numerical-stage smoke and the additional
#5-to-#37 production path run; #6 starts from a copy of the delivered #37 scene.

## 2026-10-05 — #6 accepted broad feather geometry

Logo00 retains brand/cream face authority; turnaround07 determines folded side,
back and compact tail; parts08 determines broad directional layering. The new
stage30 replaces six coarse wing/tail/chest guides with clean primary wings,
a tail foundation and 48 broad closed quad feather groups. The actual new meshes
are parameterized in `design/wings_feathers.json` and reflected, rather than
independently tessellating each side. Historical #37 mask/brows, eyes, lids,
beak, feet/perch and tech guides remain unchanged geometry in the candidate.

Wing primary and visible layers use the same nonlinear12-degree deformation
field and durable neutral `fth_rest` coordinates under separate root empties.
The shoulder blends over 45mm; vertices above 335mm stay fixed in the neutral root
seat, while distal geometry follows the mirrored outward lift. This is a
geometric gesture probe, not a finished avatar rig. Root embedding and neighboring
feather overlap are intentional attachments, not pressure/simulation physics.

Early builds exposed real folds from projecting a thick cream shell through
discontinuous mask/head normals, asymmetric independently sampled left-wing
indices, and a narrow wing-tip wall crossing. Smooth authored face depth spines,
exact reflection and constant-Z radial wing thickness address those cases.
Expanded all-new-mesh gaze checks also rejected an outer cream strip entering
the globe; its bow now runs outside that volume. No gate was weakened to admit
those candidates. Four real workers now pass repeated build, save and fresh reload;
all canonical RGBA pixels and complete runtime datasets match. Separate visual and
technical agents accepted the exact final run12 scene after reviewing the actual
artifacts. V6-01–03 and G6-TECH-01 are closed through changed geometry.

Face/tail roots now anchor to actual supporting ray hits; all 48 leaves have
measured front/back seats. Worst front-root distance 0.780121mm; least embedded
back sample 0.131826mm. Narrow recessed HeadCenter/BodyCenter/ChestCenter leaves
close central gaps while preserving visible paired tier tips. Inward middle
back tips establish overlap. Primary surfaces deliberately remain visible between
few broad groups, rather than reproducing dense illustrated individual plumage.

Delivered scene SHA256 `76ee3f1c0f8b4314aee40585445c14e3b2d193b7aa04c7e2c86e6f810f576b0a`,
1,385,718 bytes, 109 objects/95 meshes/51 new meshes. All 44 retained #37 meshes
and original pivots/studio remain exact. All 51 new surfaces pass cage/evaluated
adjacent/coplanar audits. Full blink/gaze/beak are rechecked against new geometry;
six gestures and exact 3+1/eight claw contacts pass. Final acceptance/report and
independent evidence are under `validation/reviews/feathers_v01/`.

The old30 metadata stage is archived byte-exact from Git966b7f0. Bound historical
CLI/validators remain unchanged; current #6 adds `feathers_gate.py` and an explicit
CI invocation alongside the prior validation. Final shader assignment/tech
integration remain #18/#19, combined final topology/rig/animation QA #20–#24.

## 2026-10-05 — #18 assigned non-eye lookdev and chest F-01

The original palette remains exact; actual shader values use IEC sRGB-to-linear
conversion. Nonmetal satin feather ramps, soft cream, orange/dark keratin and
fine directional brushed metal are assigned to all 95 non-eye meshes.
Eight F-01 cream/warm groups intentionally change shape: a wider cream center
and root-out/tip-in diagonal warm gradients replace separate homogeneous
orange patches. Authority 00 > 07 > 08 remains unchanged. The few broad groups
remain an abstraction of the illustrated feather layering.

A seated cyan forehead graph replaces nine old guides. The hub is lower and
more domed after an independent visual finding; crown foreshortening in
profile/3Q is documented. Four slim perch accents remain secondary. A real
11-micrometer symmetry rejection led to exact reflection of authored right
TECH surfaces; audit tolerance was preserved. Torus rings correctly use Euler 0.
G18-TECH-01 exposed contradictory individual blink clearances admitted by the
gate; per-sample/global-min checks and focused negative tests close that gap.

Scene SHA256 `ca5522b3948e2d3501eb47c0b0f3099a7ca9d7e596e8e9af5b9f6128353acaa3`, 1,793,740 bytes,
117 objects/103 meshes, 14 stored materials, no armature/actions. 78 old cages
and eight complete eye states remain exact. Four actual Blender workers and
independent fresh opens verify slots/nodes/UVs/geometry, full movement trajectories
and 3+1 contact; canonical RGBA pixels are exact. All 548 predecessor Git/LFS
byte anchors remain fixed; stage50 is archived from a863493.
The live build's 17 material datablocks include three unused old materials
omitted on reopening; stored scenes retain ten owned roles plus four eye diagnostics.
A 19-nanometer variation in old BVH shoulder metrics with exact cages uses a
2e-7-meter measurement tolerance; current worker datasets remain mutually exact.

F-01 is resolved in #18; F-02 nostrils stays #40 and F-03 eyes stays #19. #40
remains open until all three pass on a common current scene; nostril geometry
must precede #20. Final rig binding/combined QA remain #20–24. No V1 approval.

## 2026-10-05 — #19 optical eye finish and F-03

00 > 07 > 08 was inspected. The large illustrated dark region is shaded iris,
not the literal black pupil: measured projected ratio .74858 becomes 0.251854332.
Neutral pupils stay centered for coherent aim; only four iris/pupil cages change.
49-mm globes, 50.8-mm cornea, eye placement, lids/mask, all 95 non-eye full states and
studio remain exact. Iris 192×32; smaller pupil 96×8 passes the unchanged adjacent/
coplanar audit after an over-resolved tiny 192×32 pupil was rejected. No audit
tolerance relaxation. All four fixed views evaluated each geometry iteration.

Deep upper navy and curved bright blue/cyan lower crescent replace hard rings;
a thin restricted lower warm arc follows logo 00 rather than adding an orange
ring. Nine analytic local-space links/ten .65-mm nodes remain subtle and leave
pupils clear. Four actually assigned separate shaders remain editable. Cornea
IOR 1.376/roughness .04, BLENDED single Fresnel coating; its real area reflections
receive explicit artistic Eevee ShaderToRGB gain 6. Iris lower emission .4+.65.
These are documented fixed-studio stylizations, not energy-conserving raytraced
refraction. Three broad area catches/stronger profile rim were assessed and
accepted; no camera/light changes. V19-01/02/03 resolved through actual renders.

Four independent Blender build/reload workers and separate final visual/technical
reviews bind the delivered scene `8c1bcd9474281cc8c0509c50606016973db582f94771df25bdc30f505b76bc9b` and its sources/evidence.
41 blink states, 164 actual-radius minima with 1.7776074357634466 mm minimum, ±12° aim,
41 beak states, six gestures, 3+1 feet and eight contacts pass; all eight new eyes,
51 FTH and 17 TECH meshes are explicit targets. 626 real historical Git/LFS anchors
and 75 sources remain protected. F-01 preserved, F-03 fulfilled; F-02 nostrils
remains #40 before #20. #7's #18/#19 lookdev is complete; full topology, rig,
animation and final avatar remain #20–24.

## 2026-10-05 — Renewed user findings supersede planned visual closure

The user again reports chest color/belt appearance, absent nostrils and eye
reference mismatch. Actual 00/07/08, all three four-view contact sheets and
chest/eye details were rechecked, with separate visual/technical analyses.
Main remains #18/e04afa9; #19 scene 8c1bcd94 is the delivered canonical-worktree stand; the earlier 88d10dd7 candidate is archived.
The earlier F-01/F-03 partial improvements and bound reviews remain intact,
but they do not resolve this renewed feedback. F-01 is reopened in #40;
F-02/F-03 remain open. Refine smooth narrow chest strips and eye reflections,
rims, iris variation/network; add actual paired nostril recesses before #20.
#19/#7/#40 remain open. No merge or final V1 acceptance is implied by the
earlier planned delivery text. See reviews/user-findings-2026-10-05.md and #40.

## 2026-10-05 — Revised F-03 optical and lid integration recipe

The first unmerged candidate and its sources/reviews are retained byte-exact in
pre_eyes_refinement_v01, with 145 code-owned bindings. Its broad gray reflections,
uniform crescent/network and inflated cream rim did not close renewed feedback.
New fixed-studio optical response concentrates actual reflected area radiance via
real reflection directions and a documented stylized power384 kernel/gain32,
radiance threshold .65–1.60 and front Fresnel cap .10. Local iris angle variation
and a branched 13-node/10-link network replace the uniform/chain-like treatment.
No synthetic catchlight texture, new studio or new material role is introduced.

Depth/profile comparison against 07/08 justified moving both eyes −6 mm in Y,
with a quadratic matching lid taper to unchanged outer bounds. Four lid cages
retain topology; authored radial corner normals (back reversed, endcaps separate)
remove misleading shaded ring edges. These are intentional shading normals,
not exact geometric normals after taper. All41 blink states recompute them;
actual ordered hashes/audits and neutral restoration are now independently bound.

Mask experiments and an initial bridge probe incorrectly assumed obsolete #16
cage layouts. All were rejected, none was applied to production. The accepted
method derives the actual #37 41×21 front/back bridge rows from review_fixes.json,
widening X alone toward16.5mm over z=.377–.448 with smooth lower11mm/upper15mm fades.
The too-wide alternative collided during ±12° gaze and was rejected under the
unchanged tolerance. Both actual masks remain exact; targeted bridge5 closes the
medial navy gap without that collision. Independent candidate/reproduction visual
reviews cover all four fixed views; actual reproduced arrays match bridge5.

Exactly nine local cages and two depth pivots are explicit bounded changes;
90 complete non-eye states, three other pivots and local Globe/Cornea envelopes
and normals remain exact. The original optical/function/CI/delivery requirements
remain; added F-03 criteria and 41×4 normal-state checks strengthen acceptance.
Canonical four-worker publication and independent final artifact-bound reviews
must precede integration and #19 closure. F-01 chest colors and F-02 nostrils
remain #40, with common-scene confirmation before #20. No V1 acceptance.
