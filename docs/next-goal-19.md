# Startplan für Goal #19 — Augenlookdev und F-03

**Aktueller Zusatzauftrag:** Erneute Nutzer-Rückmeldung zu Brust/Schnabel/Augen;
[Analyse](reviews/user-findings-2026-10-05.md) und aktualisiertes #40 beachten.
Die erste lokale Augenabnahme wurde dadurch überholt und unverändert archiviert.
Die neue Verfeinerung umfasst Reflexe, Irisvariation, Netzwerk und Lidintegration.
Aktuelle Lieferung und separate Freigabe stehen in `eyes_v01/verification.json`
und `review.json`; tatsächlichen PR-/Issue-Status in GitHub prüfen. F-01 benötigt
weitere Brustnacharbeit in #40. Eine frühere Abnahme ersetzt die neue Prüfung nicht.

Auftrag: [Issue #19](https://github.com/KreutzM/Owli-3d/issues/19), Parent #7,
Epic #11. Erst auf der gelieferten Materialszene aus #18 starten. AGENTS und
die acht Pflichtquellen in Reihenfolge, danach aktuelle Übergabe und das echte
GitHub-Issue lesen. 00 > 07 > 08 tatsächlich ansehen.

## Ausgang und vollständiger Umfang

Aktuelle Szene: `blender/scene/owli_materials_v01.blend`; ihr verbindlicher Hash,
Größe und Produktionscommit stehen in `validation/reviews/materials_v01/verification.json`
und dem #18-PR. [Materialbericht](../validation/reviews/materials_v01/report.md).
Vor Fortsetzung `materials_gate.py` und die historischen Gates prüfen; keine
älteren Meilensteine regenerieren. Eigene Szene/eigenen Reviewordner anlegen.

Die acht `FAC_Globe/Iris/Pupil/Cornea_L/R`-Meshes besitzen weiterhin unveränderte
Diagnosematerialien. #18 bewahrt diese Geometrie, Slots und Nodegraphs bytegenau
als Laufzeit-Digests. Die existierende physische Schichtung ist noch kein
fertiges optisches Lookdev. Sichtbar sind matte große Navy-Scheiben und harte
Blue/Cyan-Ringe; F-03 aus [#40](https://github.com/KreutzM/Owli-3d/issues/40) ist offen.

- Glossy Cornea, tiefe Blue→Cyan-Iris mit hellerer unterer Zone, dunkle lesbare
  Pupille, kontrollierte Catchlights und dezentes Iris-Netzwerk tatsächlich
  implementieren und zuweisen. Warme untere Referenzakzente aus 00 bewerten.
- Pupillen-/Irisverhältnis, Cornea-Wölbung/Projektion und sichtbare Randringe
  ausdrücklich mit 00/08 vergleichen. Shader nicht ungeprüft als vollständige
  Lösung voraussetzen. Nötige Geometrieänderungen dokumentieren und in vier
  festen Ansichten neu prüfen; Augenanordnung und Maskenlesbarkeit erhalten.
- Blink 41 Zustände, Gaze ±12°, Schnabelöffnung, Flügelgesten und 3+1-Griff
  tatsächlich auf der neuen gemeinsamen Szene ausführen. Neue Motifgeometrie
  ebenfalls als Kollisionsziel berücksichtigen. Lid-/Cornea-Abstände prüfen.
- Vorher/Nachher-Augendetails ergänzen die vier Pflichtansichten; Kamera,
  Licht und World nicht zum Kaschieren verändern. Wenige breite Federgruppen
  bleiben die geometrische Ausgangsbasis; keine neue allgemeine Konzeptkunst.

## Reproduktion und Schutz

```powershell
git status --short --branch
python scripts/project.py validate
python scripts/feathers_gate.py
python scripts/materials_gate.py
python -m unittest discover -s tests -v
```

Quellenbindung in `materials_contracts.py` beachten: Vorgänger und aktuelle
Materialquellen sind Teil der historischen Kette. Neue Augenhelfer/-parameter
bevorzugen; gemeinsam gebundene Skripte nicht beiläufig ändern oder alte
Freigaben auf neue Hashes umschreiben. `50_materials.py` speichert beim
Gerüst-Smoke nach `owli.blend`; die Produktion verwendet explizite Arbeitskopien.
Der generische Renderbefehl kann die geladene Szene speichern.

Separate visuelle/technische Sub-Agents auf die endgültige Szene binden, ein
Schreiber pro Produktionsdatei. Eigener grüner PR, LFS-Szene, vier frische
Blender-Worker oder gleichwertiger tatsächlicher Build/Reload-Nachweis,
kanonische Pixelvergleiche und vollständige Quellen-/Referenz-/Beleginventare.
Relevante Gates, Tests, Compileall und Blender-Smoke ausführen. Issue #19 erst
mit tatsächlicher Lieferung schließen und dann Container #7 bewerten.

Die F-01-Teilverbesserung aus #18 ist historisch nachgewiesen; die erneute
Brust-Rückmeldung bleibt offen. **F-02 Nasenlöcher bleibt ein zusätzlicher
Geometrieauftrag in #40** und muss vor #20 erledigt werden. #40 erst nach allen
drei Findings am gemeinsamen Stand schließen. Vollständige Topologie/Rig/
Animation und finaler V1-Avatar bleiben #20–#24.

## Historischer lokaler Kandidat — 2026-10-05

Der erste lokale `owli_eyes_v01.blend`-Kandidat besaß vier Actual-Worker und
unabhängige Reviews. Er wurde nicht gemergt. Die neue Nutzer-Rückmeldung hält
F-03 offen; seine frühere Abnahme ist keine finale Freigabe. Unveränderte Szene,
Quellen und Belege sind unter `validation/history/pre_eyes_refinement_v01/`
archiviert. Aktuelle optische/Formproben liegen ausschließlich in `tmp/goal19/`.
Der neue reproduzierbare Ansatz verschiebt beide EyeAim-Pivots um −6 mm in Y,
tapered die vier Lid-Cages zur unveränderten Außenkontur und verwendet explizite
radiale Stylized-Corner-Normalen mit getrennten Kappen. Die vorhandene #37-Brücke
wird nur in X verbreitert, um die mediale Lücke zu schließen; beide Masken bleiben
exakt. Vier Iris/Pupil-Cages ändern sich weiter. Exakt 90 vollständige Nicht-Augen-
Zustände, drei übrige Pivots und lokale Globe/Cornea-Formen samt Normalen bleiben
erhalten. Keine globale Lockerung der Erhaltungsprüfung oder Kameraveränderung.
13 separate visuelle Kriterien und tatsächliche 41 Blink-Normalenzustände ergänzen
die vollständigen ursprünglichen Funktions-/Reproduktionsanforderungen.
Nach tatsächlicher F-03-Lieferung folgt #40/F-01 und F-02, anschließend #20.
