# Goal #19 — Eyes V01

Current production scene: `blender/scene/owli_eyes_v01.blend`.
[Report](report.md), [manual decision](review.json), [machine evidence](verification.json),
[visual review](independent-visual-review.md), [technical review](independent-technical-review.md).
Four canonical fixed-camera renders, comparison boards and `eyes_before_after.png`
show actual reference comparison. `evidence/` includes neutral/baseline and actual
blink, beak and wing endpoint renders. Four worker JSONs/logs bind reproducibility.

Read-only verification: `python scripts/eyes_gate.py`.
Reproduction needs a new explicit scratch directory and the named own milestone
outputs; historical deliveries must never be regenerated. See the report command.
F-03 is addressed here; F-02 nostrils remain #40 before #20. This is not final V1.
