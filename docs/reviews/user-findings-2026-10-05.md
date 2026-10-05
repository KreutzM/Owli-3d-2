# Erneute Nutzer-Findings: Brust, Schnabel und Augen

Auftrag: Brustfarbverteilung ("orangener Gürtel"), fehlende Nasenlöcher und
Augen-Referenztreue analysieren und das bestehende [Issue #40](https://github.com/KreutzM/Owli-3d/issues/40)
ergänzen. Diese Analyse korrigiert den aktuellen Abschlussstatus, ohne historische
Szenen oder gebundene Reviews umzuschreiben. Die früheren technischen Ergebnisse
bleiben nachvollziehbar; sie ersetzen die erneute visuelle Nacharbeit nicht.

## Tatsächlich geprüfte Stände

- #6 / PR #39: Federstand, Commit `a8634936494512d64e311149f20ed4e24ea492ac`.
- Aktuelles main: #18 / PR #41, Commit `e04afa99302fbed620309fadd3bef396e075d4e8`;
  `owli_materials_v01.blend`, SHA256
  `ca5522b3948e2d3501eb47c0b0f3099a7ca9d7e596e8e9af5b9f6128353acaa3`.
- Lokaler, noch nicht committeter oder gemergter #19-Kandidat:
  `owli_eyes_v01.blend`, SHA256
  `88d10dd7fba31ecec7116002c2ec40934d5c0e820c77dd6aecc79d34b4e093cc`.

Alle drei tatsächlichen Kontaktbögen mit Front/Linksprofil/Rücken/3/4, beide
Brust-/Augen-Vergleichsbilder sowie die Originalreferenzen 00 > 07 > 08 wurden
angesehen. JSON und Produktionsquellen wurden gelesen; die beiden aktuellen
Szenenhashes und main wurden erneut geprüft. Separate visuelle und technische
Reviewer ergänzen diese Analyse. Für die Triage wurde kein neuer Blenderlauf
durchgeführt; vorhandene Produktions-/Funktionsbelege bleiben separat bezeichnet.

## F-01: Brustfarben und Federfluss

#6 hatte zwei große homogene Orangeflächen neben einer schmalen Cream-Mitte.
#18 reduziert diesen Eindruck mit einer breiteren Cream-Mitte und lokalen
Warmverläufen; derselbe Brustzustand bleibt im #19-Kandidaten erhalten.
Die Akzente erscheinen jedoch weiter als zwei schmale, glatte diagonale Streifen,
die eine Reihe abgesetzter Cream-Lagen einfassen. Logo 00 und Brustdetail 08
zeigen breitere aufgefächerte Orange-/Goldzonen mit einem fließenden Cream-V
und Übergängen in benachbarte Cyan-/Navy-Federgruppen. Die Nutzerwahrnehmung eines
aufgesetzten Bands bleibt deshalb ein konkreter visueller Nacharbeitsbedarf.
Ein geschlossener orangefarbener Gürtel wurde auch jetzt nicht nachgewiesen.

Ursache/Ansatz: zwei `FTH_Orange_L/R`-Gruppen und ein gleichmäßiger UV-Warmverlauf
(`WarmDiagonal`, `WarmTaper`, `IntegratedWarmAccent`) in `materials_geometry.py`;
Lage/Breite in `materials_lookdev.json/chest_overrides`. Verteilung und Kontur
gemeinsam gegen 00/08 überarbeiten, nicht nur den Orange-Hexwert ändern.
Orange als Markenakzent erhalten; kein neuer durchgehender Ring.

**F-01 in #40 wieder offen:** Die historische #18-Teilverbesserung bleibt belegt,
ist jedoch kein Abschluss dieser erneuten Nutzer-Rückmeldung.

## F-02: Nasenlöcher

In allen drei Ständen ist der Oberschnabel glatt. `beak.json` und
`beak_geometry.py` enthalten keine Nasenlochparameter oder Muldenkonstruktion.
08 zeigt zwei längliche dunkle Öffnungen an den oberen seitlichen Flächen.
Parametrisierte bearbeitbare Vertiefungen mit sichtbarer Tiefe/Rand und sauberen
geschlossenen Wand-/Bodenflächen ergänzen. Schwarze aufgeklebte Punkte reichen
nicht. Haken, Pivot und volle 0–18° Schnabelöffnung erhalten und erneut prüfen.
F-02 bleibt offen und muss vor #20 umgesetzt werden.

## F-03: Augen

Auf main/#18 bestehen weiterhin matte Diagnoseaugen mit großer dunkler Scheibe
und harten Blue/Cyan-Ringen. Der lokale #19-Kandidat ergänzt tatsächliche
optische Shader, kleinere Pupillen, einen unteren Cyanbogen und ein Irisnetzwerk.
Er ist eine nachgewiesene Verbesserung, aber noch keine veröffentlichte Lieferung.

Verbleibende Unterschiede zu 00/08: drei breite grau-weiße Reflexflächen in Front,
eine sehr helle Corneakante im Profil, regelmäßige sichtbare Randringe sowie ein
glatter, symmetrischer unterer Irisverlauf mit dünner, wenig verzweigter Netzwerkkette.
Die Vorlage zeigt differenziertere Iriszonen und ein variableres Netzwerk; 08
zeigt kompaktere dominante Reflexe. Logo 00 besitzt wiederum eigene gemalte
Reflex-/Netzwerkformen; Unterschiede der Referenzen nach ihrer Autorität bewerten.
Gemalte Reflexpositionen nicht blind als feste Geometrie kopieren.

Ursache/Ansatz: tatsächliche Studioreflexe mit Eevee-Verstärkung 6 und Fresnelcoat,
radial/vertikal berechneter Irisbogen und neun Links/zehn gleich große Nodes.
Reflexgröße/-dominanz, Randwirkung, lokale Farbvariation und Motifverteilung
gezielt verbessern. Kameras/Lichter bleiben unverändert. Pupille/Blicklesbarkeit,
Schichtung und Lidabstände erhalten; erforderliche Geometrieänderungen begründen.
Die vorher akzeptierten festen Studiogrenzen sind für diese Nutzer-Rückmeldung
erneut zu bewerten. **F-03 und #19 bleiben offen; kein Abschluss allein aufgrund
der bisherigen lokalen PASS-Berichte.**

## Gemeinsame Abnahme

Neue Vorher/Nachher-Details plus vier feste Pflichtansichten gegen 00 > 07 > 08.
Finale gemeinsame Szene mit tatsächlichen Blink-/Gaze-/Schnabel-/Flügel-/Griffproben,
3+1-Anatomie, Fresh-Open-/Reproduktionsnachweisen und unabhängigen visuellen sowie
technischen Reviews prüfen. Historische Dateien/Quellen/Reviews bewahren; neue
Helfer/Szenenkopien für Nacharbeit verwenden. #40 erst nach allen drei Findings
schließen; #7 bleibt bis zum tatsächlichen #19-Abschluss offen. Kein fertiges V1.
