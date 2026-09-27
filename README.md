# Haus Zu-Pi — DXF aus den Bauantragszeichnungen

DXF-Dateien, erzeugt aus `bauantragszeichnungen.pdf` (19 Seiten, Architekt
Dipl.-Ing. Stefan Fleischmann, gezeichnet 22.05.2022).

Das PDF ist eine echte Vektorzeichnung, kein Scan. Die Linien wurden deshalb
nicht nachgezeichnet oder nachgebaut, sondern die im PDF vorhandene Geometrie
wurde direkt übernommen und maßstäblich umgerechnet.

## Was in den Dateien steckt

| Eigenschaft | Wert |
|---|---|
| Einheit | Millimeter (`$INSUNITS = 4`), 1 Zeichnungseinheit = 1 mm |
| Maßstab | Realmaß 1:1 — der Plan 1:100 ist auf wahre Größe hochgerechnet |
| DXF-Version | `dxf/` = AC1032 (AutoCAD 2018), `dxf-r2000/` = AC1015 (AutoCAD 2000) |
| Nullpunkt | linke untere Ecke des DIN-A3-Blatts |

**Alle Geschosse liegen im selben Koordinatensystem.** Die Grundrisse lassen
sich direkt übereinanderlegen: die linke Gebäudekante sitzt in Keller-, Erd-,
1. und 2. Obergeschoss jeweils millimetergenau an derselben Stelle.

## Zwei Fassungen

Der Ordner `dxf/` enthält DXF 2018. Das lesen ArchiCAD, Vectorworks,
BricsCAD, Rhino und AutoCAD problemlos.

Der Ordner `dxf-r2000/` enthält dieselben 19 Zeichnungen als DXF 2000 —
das älteste Format, das alles Nötige kann, und damit das verträglichste.
Für QCAD, LibreCAD und andere freie Programme diese Fassung nehmen.

Die Geometrie ist in beiden Fassungen bis auf die letzte Nachkommastelle
identisch. Ein Unterschied: DXF 2000 kennt keine Transparenz, deshalb ist
dort der Layer `11_Sonstiges` mit der rosa Planungsfläche ab Werk
ausgeschaltet — eingeschaltet würde die Fläche deckend über allem liegen.
Auch die Layerbeschreibungen fehlen in DXF 2000, die Layernamen bleiben.

## Dateien

### Geschossgrundrisse

| Datei | Inhalt | PDF-Seite |
|---|---|---|
| `04_Kellergeschoss.dxf` | Kellergeschoss | 4 |
| `01_Erdgeschoss.dxf` | Erdgeschoss | 1 |
| `02_1-Obergeschoss.dxf` | 1. Obergeschoss | 2 |
| `03_2-Obergeschoss.dxf` | 2. Obergeschoss | 3 |
| `05_3-Obergeschoss.dxf` | 3. Obergeschoss | 5 |
| `13_Staffelgeschoss.dxf` | Staffelgeschoss | 13 |

### Dieselben Geschosse mit Entwässerungsplanung

`06_Erdgeschoss_Entwaesserung.dxf`, `07_1-Obergeschoss_Entwaesserung.dxf`,
`08_2-Obergeschoss_Entwaesserung.dxf`, `09_Kellergeschoss_Entwaesserung.dxf`,
`10_3-Obergeschoss_Entwaesserung.dxf`, `11_Staffelgeschoss_Entwaesserung.dxf`,
`12_Schnitt-A-A_Entwaesserung.dxf` (PDF-Seiten 6–12)

### Schnitte und Ansichten

`14_Schnitt-A-A.dxf`, `16_Schnitt-B-B.dxf`, `15_Ansicht-Suedwesten.dxf`,
`17_Ansicht-Nordosten.dxf`, `18_Ansicht-Suedosten.dxf`,
`19_Ansicht-Nordwesten.dxf` (PDF-Seiten 14–19)

## Layer

| Layer | Farbe | Inhalt |
|---|---|---|
| `00_Wand_Bestand` | schwarz | Bestehendes Mauerwerk und Betondecken, schwarz gefüllt |
| `01_Daemmung_neu` | hellgrau | Wärmedämmung neu |
| `02_Grundstuecksgrenze` | grau | Grundstücksgrenze, Nachbarbebauung |
| `03_Sanitaer` | blau | Sanitärobjekte, blau hinterlegte Einbauten |
| `04_Schraffur` | cyan | Schraffuren (Schließung von Öffnungen, Dachflächen) |
| `05_Linien_stark` | schwarz | Kräftige Feder: Neubauteile, Wandkanten, Umrisse |
| `06_Linien_fein` | grün | Feine Feder: Möblierung, Einbauten, Details |
| `07_Bemassung` | magenta | Maßlinien, Maßhilfslinien, Maßstriche, Maßzahlen |
| `08_Schnittlinie` | rot | Schnittverlauf A-A / B-B |
| `09_Weissflaechen` | grau | Weiße Deckflächen aus dem PDF — **standardmäßig ausgeschaltet** |
| `10_Text` | schwarz | Raumnamen, Höhenkoten, Hinweistexte |
| `11_Sonstiges` | orange | Farbige Tonflächen (rosa Planungszone), Restgeometrie |
| `12_Plankopf` | blaugrün | Schriftfeld und Legende am rechten Planrand |

Zum Arbeiten am Gebäude reicht es meist, `07_Bemassung`, `10_Text` und
`12_Plankopf` auszuschalten — dann bleibt die reine Bauzeichnung übrig.

Alle Objekte liegen auf Farbe BYLAYER, die Strichstärken sind aus dem PDF
übernommen. Flächen liegen in der Zeichenreihenfolge hinter den Linien.

## Genauigkeit

Die Geometrie stammt unverändert aus dem PDF, umgerechnet mit dem exakten
Faktor 1 PDF-Punkt = 35,2778 mm (25,4/72 × 100). Der Maßstab wurde zusätzlich
aus der Zeichnung selbst überprüft: die gemessenen Wandstärken treffen das
10-mm-Raster (15, 22, 24, 25, 30 cm), und ein freier Fit über alle Wandstärken
liefert 35,276 mm/pt — 0,005 % neben dem theoretischen Wert.

Ein Abgleich von 96 Maßkettenintervallen gegen die eingetragenen Maßzahlen
ergibt eine mittlere Abweichung von rund 7 mm bei einer Streuung von etwa
4 cm. Das entspricht der Genauigkeit, die eine 1:100-Zeichnung überhaupt
hergibt: eine Linie von 0,4 mm Strichstärke ist im Realmaß bereits 4 cm breit.

**Für Ausführungsmaße bleibt das Aufmaß am Bau maßgeblich, nicht diese Datei.**

## Grenzen der Umsetzung

* Es sind **keine Volumenkörper und keine Wandobjekte** entstanden, sondern
  2D-Linien, Polylinien, Kreise, Flächen und Text. Das Architekturprogramm
  kennt also keine „Wand“ — die Zeichnung eignet sich als maßhaltige
  Grundlage, auf der Bauteile nachgezogen werden.
* Die Zuordnung `05_Linien_stark` / `06_Linien_fein` folgt der Feder, mit der
  im PDF gezeichnet wurde, nicht der Bedeutung des Bauteils. Das PDF enthält
  diese Information nicht. `00_Wand_Bestand`, `01_Daemmung_neu`,
  `02_Grundstuecksgrenze` und `04_Schraffur` sind dagegen inhaltlich sicher,
  weil der Plan sie über Füllung und Farbe eindeutig unterscheidet.
* Die Bemaßung wurde über ihre Maßstriche und Maßpunktkreise erkannt. Ein
  paar kurze Maßhilfslinien bleiben auf den Linienlayern liegen.
* Maßzahlen sind **Text, keine assoziativen DXF-Bemaßungen**. Wenn Geometrie
  verschoben wird, ändern sich die Zahlen nicht mit.
* Auf den Ansichten enthält das PDF Staffage als Pixelbilder (Personen, Auto,
  Oberflächentexturen). Pixelbilder lassen sich nicht in DXF-Vektoren
  überführen und fehlen deshalb. Die Bauzeichnung selbst ist vollständig.

## Sweet Home 3D

Sweet Home 3D öffnet keine DXF-Zeichnungen, sondern nimmt als Vorlage ein
Bild. Der Ordner `sweethome3d/` enthält die sechs Geschosse als PNG mit
exakt 100 Pixel je Meter und einem eingezeichneten 10-Meter-Maßstabsbalken.
Einzelheiten in `sweethome3d/LIESMICH.md`.

## Kontrollansichten

`vorschau/erdgeschoss.png` zeigt das fertige DXF komplett,
`vorschau/erdgeschoss_ohne_bemassung.png` dasselbe mit ausgeschalteten
Layern `07_Bemassung`, `10_Text` und `12_Plankopf`.

## Neu erzeugen

```bash
pip install pymupdf ezdxf
python3 tools/pdf2dxf.py bauantragszeichnungen.pdf \
    --pages 1,2,3 --scale 100 --outdir dxf/ --names EG,OG1,OG2
```

`--scale` ist der Nenner des Planmaßstabs (100 für 1:100, 50 für 1:50).
Mit `--dxfversion R2000` entsteht die verträglichere Fassung für ältere
Programme, ohne die Angabe wird DXF 2018 geschrieben.
