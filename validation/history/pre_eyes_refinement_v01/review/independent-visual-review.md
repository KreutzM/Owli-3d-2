# Unabhängiger visueller Finalreview — #19 / F-03

Reviewer: `/root/goal19_visual_review`, 2026-10-05. **Visuelle Empfehlung: #19 und F-03 akzeptieren; keine offenen visuellen Blocker in diesem Umfang.** Hauptagent übernimmt die gemeinsame Abnahme. Eigene Zuständigkeit: unabhängige visuelle Bewertung, Scratch und dieser Bericht; keine Produktionsgeometrie/-shader/-parameter bearbeitet.

## Verbindlicher Stand und tatsächliche unabhängige Prüfung

Ausgang: #18/main `e04afa99302fbed620309fadd3bef396e075d4e8`, Materialszene SHA256 `ca5522b3948e2d3501eb47c0b0f3099a7ca9d7e596e8e9af5b9f6128353acaa3`. Finale Lieferung: `blender/scene/owli_eyes_v01.blend`, **2.241.341 Bytes**, SHA256 `88d10dd7fba31ecec7116002c2ec40934d5c0e820c77dd6aecc79d34b4e093cc`.

Acht AGENTS-Pflichtquellen in vorgeschriebener Reihenfolge gelesen, danach Übergabe, Startplan19, Repo-Karte, Entscheidungen, Materialbericht und tatsächliche GitHub-Issues19/40. Tatsächliche Referenzen00,07,08 und alle vier Vorgängeransichten angesehen. Preview01/03/05 unabhängig beurteilt;05 zusätzlich selbst frisch geöffnet/rendered. Für die finale Empfehlung erneut die exakte gelieferte Szene in eigene Scratchkopie übernommen und mit Blender5.2.1 LTS frisch geöffnet. Alle vier vorhandenen Kameras unverändert gerendert; eigene Front/Links/Rücken/3Q tatsächlich angesehen. Studio-Snapshot vor/nach Rendering exakt gleich; keine Kameras, Licht/World, Shader oder Geometrie zum Rendern verändert. Die vier eigenen RGBA-Puffer stimmen pixelgenau mit den gelieferten kanonischen Bildern überein: **0 unterschiedliche Pixel pro Ansicht**. Unterschiedliche PNG-Metadaten werden nicht als Pixelabweichung ausgegeben.

[Vorher/Nachher-Augentafel](eyes_before_after.png) und tatsächliche finalen Details zusätzlich betrachtet. Alle20 tatsächlichen Endposebilder aus run01 (voller Blink, Schnabelöffnung, GesteL/R/beide × vier Ansichten) unabhängig angesehen; die20 finalen gelieferten Endpose-Pixel anschließend mit diesen geprüften Bildern verglichen, überall exakt gleich. Geschlossene Lider verdecken Augen/Leuchtmotiv vollständig; Schnabel-/Gestenbilder zeigen stabile Gesichtslesbarkeit. Zusätzlich auf einer zweiten eigenen Kopie der **exakten finalen Szene** ±12° umX/Z tatsächlich angewendet, Front und3Q je Zustand selbst gerendert und Augen-Crops betrachtet. Acht Gaze-Bilder reproduzieren die bereits angesehenen run01-Gaze-Pixel exakt; neutrale Rotationen danach wiederhergestellt. Blickrichtungen bleiben klar; Netzwerk folgt der Iris, echte Lampenreflexe folgen Blick-/Oberflächenrelation.

Scratchbelege: `tmp/goal19/visual/final-own/own-open-render.json`, `final-binding-audit.json`, `final-gaze/gaze-open-render.json`, `gaze-pixel-recheck.json`, `gaze-details.png`; eigene Renderer `render_final.py`/`render_final_gaze.py`. Scratch ist keine Produktionslieferung. Dieser Bericht bindet die dauerhaften Produktionsdateien nachfolgend unabhängig durch tatsächliche Byte-/Pixelvergleiche. Vollständige Geometrie-/41-Zustands-Trajektorien und626 historische Git/LFS-Anker gehören zum separaten technischen Review; hier wird keine eigene technische Vollprüfung behauptet.

## Referenzentscheidungen und F-03-Ergebnis

00 kontrolliert Gesicht/Farbidentität;07 kontrolliert erhaltenes Kopf-/Körpervolumen und Profil/Rücken;08 unterstützt Augenschichtung, Glanz und Netzwerk. Der große dunkelblaue Bereich der Illustration ist als beschattete Iris interpretiert, nicht als riesige physische Pupille. Deshalb ist die alte projizierte Pupillen-/Irisquote etwa.744 durch **.2518543321** ersetzt:11.144mm Pupillenradius gegenüber44.248mm Irisradius. Kleine klar dunkle zentrale Pupille bleibt neutral symmetrisch; illustrierte scheinbare Offsets wurden nicht als metrischer Augenanordnungsauftrag übernommen. Die vier Iris-/Pupillen-Cages ändern sich gezielt; Globe/Cornea/Lider/Maske und EyeAim-Zentren bleiben erhalten. Wölbung/Projektion wurden ausdrücklich in Links/3Q geprüft: optisch runde separate Dome, keine alten harten cyanfarbenen Zylinderbänder; kein zusätzlicher Geometrieeingriff nötig.

Die Iris hat dunklen Navy-Oberbereich, räumlichen Blue→Cyan-Verlauf und eine **gekrümmte helle äußere Unterzone** statt horizontalem Verlauf oder gleichförmigen Farbringen. Dünner lokaler warmer Unterrand respektiert00, bleibt deutlich untergeordnet und bildet keinen vollständigen dominanten Orange-Ring. Dunkler weicher Limbus rahmt das Auge, ohne die alte mehrfache harte Ringästhetik. Schwarze Pupille bleibt getrennt bearbeitbar und gut lesbar. Cornea und Iris zeigen unterschiedliche Tiefen-/Reflexanteile. Die wenigen dünnen cyanfarbenen Links/Knoten liegen im dunkleren unteren Irisbereich, sind im Detail lesbar und verdecken Pupille/Blickrichtung nicht.

Vieransichtenentscheidung:

| Ansicht | Tatsächlicher visueller Befund | Empfehlung |
|---|---|---|
| Front | Freundliche symmetrische Augen; kleine dunkle Pupillen, tiefe obere Navy-Iris, helle Cyan-Unterbögen, dezente warme Kante. Cream-Maske deutlich lesbar. | pass |
| Linksprofil | Convexer Cornea-/Globe-Aufbau innerhalb vorhandener Platzierung; harte Diagnosebänder weg. Heller Reflexrand ist stärker als die Illustration und unten begrenzt. | pass mit dokumentierter Glanzgrenze |
| Rücken | Bestehender Kopf/Feder-/Flügel-/Sitzaufbau bleibt visuell erhalten; kein zusätzliches Augen-Gerät oder rückwärtiges Motiv. | pass |
|3Q | Beide Augen räumlich gerundet, freundlicher klarer Blick, getrennte Iris/Pupille/Cornea optisch nachvollziehbar; Netzwerk bleibt sekundär. | pass |

## Konkrete Findings und Materialgrenzen

- **V19-01 erledigt:** Preview01 zeigte flachen horizontalen Farbhorizont. Parametrisierter radialer Unterbogen und dunklere innere Iris stellen gekrümmte Referenzlesbarkeit her.
- **V19-02 erledigt:** Preview01 hatte körnige große Reflexflächen;03 glatte, aber matt graublaue Flecken. BLENDED-Cornea und tatsächliche lichtabhängige Reflexantwort liefern jetzt glatte helle Catchlights/konvexen Glanz ohne Speckle.
- **V19-03 erledigt:** Anfangs waren Netzwerkknoten kaum lesbar. Selektiv.65mm Knoten bei weiterhin dünnen.22mm Links sind im finalen Detail subtil sichtbar; keine dichte leuchtende Schaltung.

Roughness Cornea.04/Iris.09/Pupille.065/Globe.10 liegt in der Augen-Vorgabe. IOR1.376; Nicht-Augen-Materialien unverändert. Fünf unveränderte echte Studiolampen ergeben drei breite reflektierte Flächen, keine zwei aufgemalten Weißpunkte. Das ist eine dokumentierte reale Studiointerpretation der illustrierten Catchlights. Die Frontspots bleiben breiter/grauweißer als08;3Q liest heller. Der Profilrand ist stärker. Diese Unterschiede sind sichtbare Grenzen, kein weiterer #19-Blocker.

Die Cornea nutzt eine **Eevee-spezifische stilisierte Reflexverstärkung6** aus der tatsächlichen Glossy-Light-Antwort via ShaderToRGB/Fresnel. Positionen werden nicht gemalt, UV-gebunden oder durch verschobene Lampen konstruiert. Dies ist ausdrücklich keine energieerhaltende physikalische Raytracing-Cornea; in Cycles oder anderer Beleuchtung ist ein eigener optischer Materialabgleich nötig. Iris-Emission.40 plus lokaler Unterbogen.65 ist begründete Marken-Lookdev-Stilisierung unter dem eingefrorenen Studio. Bei Aufwärtsgaze wird der dunklere Globe unter der endlichen Iris sichtbar; bei seitlichem Extremblick können echte Reflexflächen den Pupillenrand teilweise überlagern, ohne die Blickrichtung zu verdecken. Das ist in den eigenen Gaze-Details nachvollziehbar.

F-03 ist hier visuell erledigt. F-01-Brustlook bleibt am gemeinsamen Augenstand erhalten. F-02-Nasenlöcher ist weiterhin #40 vor#20; #40 darf nicht aufgrund dieser Augenabnahme geschlossen werden. Wenige breite Federgruppen bleiben die angenommene Stilabstraktion; kombinierte Topologie, finales Rig, Animation und V1-Abnahme bleiben #20–24. Keine neue Konzeptkunst, keine Flugkomplexität; perch und3+1-Anatomie bleiben die sichtbare gemeinsame Ausgangsbasis.

## Unabhängig geprüfte finale Bindungen

`verification.json` tatsächlicher SHA256: `ea9ee7ed4161744a51cf3432c45fd5c1dfb3914a39537b5e39ac123185cd5fa4`. Alle **75 Quellen**, **9 Referenzen** und **58 Producer-Belege** aus seinen vollständigen Inventaren gegen tatsächlich gelesene Dateien geprüft: keine Byteabweichung. Manifestdigest ist SHA256 über UTF-8 JSON mit sortierten Schlüsseln, kompakten Separatoren und ensure_ascii=false; er bindet die vollständigen Pfad→SHA256-Maps im oben gehashten dauerhaften Proof.

- 75 Quellen: `03539cdad8702d0f580b8a249544e0fa2706431285fb558d10f21bbd58fcc900`.
- 9 Referenzen: `3944e881a1ba05a5345d3352a79aca9c08e550338e63aebe222d8e034d176978`.
- 58 Belege: `8dcf5e344a97f9e2b01c871e8c2470aec179fda41c6eb5bdc3bf20e60cef0a07`.

Kernquellen tatsächlich gelesen/geprüft:

- `design/eyes_lookdev.json`: `b3cd077b8d4bf0821d90d9306becde346ace5cff1ff646bc7f9370d7b1812503`.
- `scripts/blender/eyes_geometry.py`: `362c193cd6e1957b7938529205c9d0ecd7068c28af1385f19bc532127f8d81fc`.
- `scripts/blender/eyes_checks.py`: `f11b596ba176dcbea692a24c3a0efb9309bbd57c5696e746f54158e92bd4cb15`.
- `validation/reference_views.json`: `b54fc4aa5b6bdf0ba07d7a96006ca207791b397f2374a465ede581855cb9d89f`.

Tatsächlich angesehene autoritative Referenzen:

- `00_original_logo.png`: `d97c36505ae64d3d70b04f55b055cba84de1bfa7326daa91a556b87dae3d0c2e`.
- `07_turnaround_technical.png`: `b15a961ceadc50c9b226aefb981464461c5e049d0a18de5e969f454fc90259a1`.
- `08_parts_lookdev_technical.png`: `6438c5a11db515e6d73f72a9617d511839b407e1e6c7022b80aa475b2a362488`.

| Finale kanonische Ansicht | Tatsächlicher PNG-SHA256 | Eigener identischer RGBA-SHA256 | Unterschiedliche Pixel |
|---|---|---|---|
| VAL_FRONT | `701c585519439248f930aba20cd031c610063c8e91c9c7e67a4543b21f76a058` | `185227fc60cd13017048e70abf0011f6bcf036a1b8f6c4a4987eca051f876abb` |0 |
| VAL_LEFT | `410d90a5f4e974960b30637b1362992773e5850acac4001761ac58e35add1cfc` | `38a7c132a807de327520a24af276a4c3d4b227b7cd84e1cbabf5f5e217dd5fee` |0 |
| VAL_BACK | `bc25256bb2cecac7eaeca921b81c2db87866f3759ebbd46158e7c978fc2cf6a8` | `82c858ecebed19a8cf1a115f1de2d8b64c6c634aee94395b8a6d510edda622ad` |0 |
| VAL_3Q | `2222a4add8b100327ced25818d118b60e4c4cf49d9b9c9e23240514e566742c4` | `32e91333808bfd628accc19159d11d8557981d33c7715d5190302cb173e93188` |0 |

`eyes_before_after.png` SHA256: `d59cf7808fcdab40b9133beb35d5b1b17a8a2ee40e92fe58fbb480c0058b0fa2`. Alle20 Endposesets sind in der vollständigen58-Belegmap gebunden; eigene SHA/Pixelrecheckmap für genau diese20 Bilder Digest `0ae910d297219183c5cfa49616d6465e097c4d232b34a68f0012a2efec1b0b25`, jeweils0 geänderte Pixel gegenüber den tatsächlich inspizierten run01-Bildern.

Eigener Final-Gaze-Nachweis, finale Szenenbindung und acht tatsächliche Bilder: `tmp/goal19/visual/final-gaze/gaze-open-render.json` SHA256 `d1883eccab8d0f000297c2ba78ed5aed9474ed644b777ad8e926a32edf707672`. Eigener vollständiger Quellen-/Referenz-/Bildbindungsaudit SHA256 `cd11fa879ae1d5a65413bf276f322c3affe1645028084cd82efaa4c57bb09f2d`. Keine Probe schreibt die gelieferte Blend-Datei.
