# Repo-Karte für die Fortsetzung

Einstieg und aktueller Status: [Agent-Übergabe](agent-handoff.md).
Die Tabelle beschreibt die Zuständigkeit; Existenz einer Datei beweist nicht,
dass ihr Produktionsgoal abgeschlossen ist.

| Pfad | Funktion |
|---|---|
| `AGENTS.md`, `DESIGN_FREEZE.md`, `CHARACTER.md` | Auftrag, Referenzautorität, Anatomie, Iterationsvertrag |
| `design/reference_hierarchy.json`, `references/manifest.json` | Referenzränge, Dateien, Abmessungen und Hashes |
| `references/approved/` | neun tatsächlich vorhandene freigegebene PNGs |
| `design/character_spec.json`, `materials.json`, `rig_spec.json` | Zielmaß, Anatomie, Material-/Rig-Anforderungen |
| `design/proportions.json` | eingefrorene grobe Maße und Ringschemata |
| `design/silhouette_freeze.json` | manuelle grobe Vieransichtenentscheidung mit Quellenbindungen |
| `design/head_body.json`, `face.json`, `beak.json`, `feet.json` | implementierte Meilensteinparameter |
| `blender/scene/` | LFS-Szenen; aktueller #19-Stand `owli_eyes_v01.blend`; #18-Materialszene bleibt historische Baseline; #6/#37 und frühere Szenen bleiben historische Baselines |
| `validation/reference_views.json`, `checklist.json` | Studio und unveränderte Pflichtansichten / visuelle Checks |
| `validation/reviews/<milestone>/` | dauerhafte Szenen-/Quellen-/Rendernachweise und separate manuelle Entscheidung |
| `validation/history/pre_feet_v01/` | bytegenaue Original-Metadaten und geprüfte historische Quellenumbindung |
| `docs/decisions.md` | zeitlicher Verlauf von Geometrieentscheidungen, Konflikten und Grenzen |
| `scripts/project.py`, `validate_project.py` | CLI, Doctor, strikte Assetvalidierung und isolierter Gesamtsmoke |
| `scripts/setup_review.py`, `silhouette_review.py` | Studio-/Blockout-Runner, Bildmetriken, Vergleichstafeln und Freeze-Validierer |
| `scripts/head_body_review.py`, `face_review.py`, `beak_review.py`, `feet_review.py` | isolierte Build-/Fresh-Reload-Übergaben mit aktuellen Artefaktvalidierern |
| `scripts/history_bindings.py` | historischer Version-1-Helfer; bytegleich als #5-Quellbeleg erhalten |
| `scripts/delivery_gates.py`, `delivery_shapes.py`, `evidence_contracts.py`, `history_gate.py` | aktuelle Version-2-Abnahme: komplette Inventare/Reloadschemas und im echten Vorgänger verankerte History |
| `scripts/review_fixes_review.py`, `review_fixes_gate.py`, `review_fixes_contracts.py` | expliziter #37-Runner, eigene Artefaktabnahme und geschützte historische Git/LFS-Inventare |
| `scripts/blender/review_fixes_geometry.py`, `review_fixes_checks.py`, `review_fixes_evidence.py` | parametrisierte Gesichtskorrektur, adjazente/coplanare Prüfungen und Blender-Worker |
| `scripts/blender/blockout_geometry.py`, `primary_geometry.py` | gemeinsame Mesh-/Material-/Skalierungs-/BVH- und Quad-Cap-Helfer; bereits hashgebunden |
| `scripts/blender/00_scene_setup.py`, `10_blockout.py`, `20_head_body.py`, `21_eyes_mask.py`, `22_beak.py` | implementierte Stufen bis #4 |
| `scripts/blender/40_feet_perch.py`, `feet_geometry.py`, `verify_feet.py`, `feet_probe.py`, `feet_evidence.py` | #5 Produktion, echte Mesh-/Kontaktprüfungen und isolierte Evidenzerzeugung |
| `design/wings_feathers.json`, `scripts/blender/30_wings_feathers.py`, `feathers_geometry.py` | #6: tatsächliche Primärflügel und 48 parametrisierte geschlossene Federgruppen, gemeinsame Gestenprobe |
| `scripts/blender/feathers_checks.py`, `feathers_evidence.py` | tatsächliche Root-/Mesh-/Funktionsprüfung und vier isolierte Blender-Worker |
| `scripts/feathers_review.py`, `feathers_gate.py`, `feathers_contracts.py` | eigener #6-Producer, strikte vollständige Abnahme, 462 geschützte Vorgängeranker |
| `validation/reviews/feathers_v01/` | aktueller Federbericht, 40 Evidenzbilder, vier Pflichtansichten, separate Entscheidung und unabhängige Berichte |
| `scripts/blender/legacy/30_wings_feathers.py`, `validation/history/pre_feathers_v01/` | byte-exakte archivierte Metadatenstufe aus Git966b7f0 |
| `design/materials_lookdev.json`, `scripts/blender/50_materials.py`, `materials_geometry.py` | #18: echte Nicht-Augen-Zuweisung, Brust-F01, sitzendes Stirnmotiv und Stangenringe |
| `scripts/blender/materials_checks.py`, `materials_evidence.py` | tatsächliche Shader-/Erhaltungs-/Tech-/Bewegungsprüfung in vier Blender-Prozessen |
| `scripts/materials_review.py`, `materials_gate.py`, `materials_contracts.py` | isolierter Producer, strikte Abnahme und 548 Vorgängeranker |
| `validation/reviews/materials_v01/` | aktueller Bericht, Brustvergleich, 40 Evidenzbilder, vier feste Ansichten und unabhängige Berichte |
| `scripts/blender/legacy/50_materials.py`, `validation/history/pre_materials_v01/` | bytegenaue Stage50-Sicherung aus Git a863493 |
| `design/eyes_lookdev.json`, `scripts/blender/eyes_geometry.py` | #19: getrennte Shader, Pupille, Irisnetzwerk, begrenzte Augentiefe und Lid-/Brückenintegration |
| `scripts/blender/eyes_checks.py`, `eyes_evidence.py` | Vollzustand/UV/Attribute/lokale Augenformen/Corner-Normalen, optische Geometrie und vier echte Worker |
| `scripts/eyes_contracts.py`, `eyes_gate.py`, `eyes_review.py` | #19-Producer/Gate, 626 Vorgängeranker und 145 Bindungen des früheren lokalen Kandidaten |
| `validation/reviews/eyes_v01/` | Aktuelle vier Ansichten, Augendetails, Bewegungsbelege und unabhängige Reviews |
| `validation/history/pre_eyes_refinement_v01/` | Unveränderte Szene, Quellen und Reviews des verworfenen lokalen Augenstands; keine aktuelle Freigabe |
| `scripts/blender/60_rig.py` | ungewichtetes Gerüst; keine finale Rig-Deformation |
| `scripts/blender/90_validation.py`, `validation_setup.py`, `verify_validation_setup.py` | feste Kameras/Lichter, Framing, Rendering und Studio-Prüfung |
| `scripts/blender/legacy/40_feet_perch.py` | ursprünglicher Guide-Code, unverändert für ältere Blockout-Rezepte |
| `scripts/legacy/project.py` | historische CLI-Quellensicherung; nicht als aktuellen Runner verwenden |
| `tests/`, `.github/workflows/validate.yml`, `requirements.txt`, `.gitattributes` | Negative und positive Gate-Tests, Windows/Ubuntu-CI, Python-Abhängigkeiten, LF-/LFS-Regeln |

## Nachweise lesen, ohne sie neu zu erzeugen

```powershell
python scripts/project.py validate
python scripts/feathers_gate.py
python scripts/materials_gate.py
python scripts/eyes_gate.py
python -m unittest discover -s tests -v
python -c "import sys; sys.path.insert(0,'scripts'); from delivery_gates import validate_feet_delivery; from review_fixes_gate import validate_review_fixes; print(validate_feet_delivery()); print(validate_review_fixes())"
```

Eine leere Fehlerliste bedeutet, dass die gespeicherten Liefernachweise zu den
aktuellen Dateien passen. Sie ersetzt weder die visuelle Prüfung eines neuen
Modells noch einen tatsächlichen Blender-Test nach einer Modelländerung.

## Neue Übergabe strukturieren

Die tatsächliche #6-Lieferung nutzt `design/wings_feathers.json`,
`scripts/feathers_review.py`, `blender/scene/owli_feathers_v01.blend` und
`validation/reviews/feathers_v01/`. Die aktuelle #18-Lieferung liegt separat in `owli_materials_v01.blend` und
`materials_v01/`. Die neue aktuelle #19-Lieferung liegt in `owli_eyes_v01.blend` und `eyes_v01/`.
Den tatsächlichen Integrationsstatus von #19 über seinen GitHub-PR prüfen.
Als Nächstes die verbleibende [Brust-/Schnabel-Nacharbeit](reviews/user-findings-2026-10-05.md) in #40 und
[Fortsetzungsplan #40](next-goal-40.md) vor #20. F-01/F-02 bleiben offen;
F-03 nur anhand der aktuellen Szene und ihrer separaten Abnahme beurteilen.
Historische Artefakte und frühere Teilnachweise erhalten.
