# Unterlagen für Sweet Home 3D

Sweet Home 3D kann keine DXF-Zeichnung als Grundriss öffnen. Als Vorlage zum
Nachzeichnen nimmt es ein **Bild** (BMP, GIF, JPG, PNG) über
*Plan → Hintergrundbild importieren*.

Genau dafür sind diese sechs PNG-Dateien gedacht.

## Maßstab

| | |
|---|---|
| Auflösung | **100 Pixel je Meter** — 1 Pixel = 1 cm |
| Bildgröße | 3295 × 2045 Pixel = 32,95 × 20,45 m |
| Maßstabsbalken | unten links, rote Marken, **exakt 10,00 m** |

Der Balken wurde nachgemessen: zwischen den Mitten der beiden roten Endstriche
liegen in jeder der sechs Dateien exakt 1000,0 Pixel.

## Alle Geschosse passen übereinander

Alle sechs Bilder benutzen denselben Bildausschnitt. Wenn Sie in jedem
Geschoss dieselben zwei Punkte für den Maßstab anklicken und denselben
Ursprung setzen, liegen die Grundrisse deckungsgleich übereinander.

## So geht es in Sweet Home 3D

1. *Plan → Hintergrundbild importieren*, Datei wählen
2. Im Assistenten die **Mitte des linken roten Endstrichs** und die
   **Mitte des rechten** anklicken, als Länge **1000 cm** eingeben
3. Ursprung setzen — am einfachsten die linke untere Gebäudeecke, in allen
   Geschossen dieselbe
4. Wände mit dem Wandwerkzeug über die schwarzen Mauern ziehen

## Was auf den Bildern zu sehen ist

Bemaßung, Schnittlinien, Nachbarbebauung und Plankopf sind ausgeblendet —
übrig bleibt die Bauzeichnung mit Raumnamen und Höhenkoten. Das Mauerwerk
ist schwarz gefüllt, sodass die Wandstärken beim Nachzeichnen gut zu treffen
sind.

Neu erzeugen: `python3 tools/dxf2sweethome3d.py` (erwartet die DXF-Dateien
im Ordner `alle/`).
