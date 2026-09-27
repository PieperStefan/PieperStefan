#!/usr/bin/env python3
"""
pdf2dxf.py -- Vektor-PDF (CAD-Plot) -> massstaebliches DXF.

Ausgelegt auf Bauantragsplaene, die als Vektor-PDF vorliegen. Das PDF wird
nicht nachgezeichnet: die vorhandene Vektorgeometrie wird uebernommen und in
Millimeter Realmass umgerechnet (1 PDF-Punkt = 25,4/72 mm Papier * Massstab).

Zwei Eigenheiten dieses Plantyps werden gesondert behandelt:

1. Viele Linien liegen im PDF nicht als Stroke vor, sondern als even-odd
   gefuellter Ring (Aussenkontur minus Innenkontur). Solche Ringe werden
   erkannt und auf ihre Mittellinie zurueckgerechnet, damit im CAD eine
   einzelne fangbare Linie entsteht statt zweier Konturen.

2. Bemassung traegt im PDF keine eigene Farbe. Sie wird ueber ihre Massmarken
   gefunden: die gefuellten Massstriche und die gleich grossen Masspunkt-
   kreise. Linien, die durch mindestens zwei solche Marken laufen, sind
   Mass- oder Masshilfslinien.

Aufruf:
    python3 pdf2dxf.py plan.pdf --pages 1,2 --scale 100 --outdir dxf/
"""

from __future__ import annotations

import argparse
import math
import os
import re
from dataclasses import dataclass

import ezdxf
import pymupdf

PT_TO_MM = 25.4 / 72.0          # 1 PDF-Punkt in mm Papier
FLATTEN_TOL_PT = 0.02           # Sehnentoleranz beim Zerlegen von Bezierkurven
WELD_TOL_PT = 1e-4              # Toleranz fuer "gleicher Punkt"
RING_UNIFORM_TOL = 0.45         # max. Streuung des Ringabstands, sonst kein Ring
CIRCLE_TOL = 0.06               # max. Radiusabweichung fuer Kreiserkennung
MARK_RADIUS_PT = 2.5            # bis hierhin gilt ein Kreis als Masspunkt
MARK_LINE_TOL_PT = 1.3          # Abstand Marke <-> Linie fuer "liegt darauf"
PLANKOPF_MARGIN_PT = 10.0       # Sicherheitsabstand links des Schriftfelds

TITLE_ANCHORS = ("Legende", "Baugrundstück", "Bauherr", "Bauantrag",
                 "Architekt Dipl.-Ing.")
NUMBER_RE = re.compile(r"^[\d.,]{1,8}$")


# ---------------------------------------------------------------- Layerplan

@dataclass(frozen=True)
class LayerDef:
    name: str
    aci: int
    description: str


LAYERS = [
    LayerDef("00_Wand_Bestand",         7, "Bestehendes Mauerwerk / Betondecken, schwarz gefuellt"),
    LayerDef("01_Daemmung_neu",         9, "Waermedaemmung neu, hellgraue Flaeche"),
    LayerDef("02_Grundstuecksgrenze",   8, "Grundstuecksgrenze / Nachbarbebauung, graue Flaeche"),
    LayerDef("03_Sanitaer",             5, "Sanitaerobjekte und blau hinterlegte Einbauten"),
    LayerDef("04_Schraffur",            4, "Schraffuren: Schliessung von Oeffnungen, Dachflaechen"),
    LayerDef("05_Linien_stark",         7, "Kraeftige Feder: Neubauteile, Wandkanten, Umrisse"),
    LayerDef("06_Linien_fein",          3, "Feine Feder: Moeblierung, Einbauten, Details"),
    LayerDef("07_Bemassung",            6, "Masslinien, Masshilfslinien, Massstriche, Masszahlen"),
    LayerDef("08_Schnittlinie",         1, "Schnittverlauf A-A / B-B, Strichpunktlinien"),
    LayerDef("09_Weissflaechen",        8, "Weisse Deckflaechen aus dem PDF, standardmaessig aus"),
    LayerDef("10_Text",                 7, "Beschriftung: Raumnamen, Hoehenkoten, Hinweise"),
    LayerDef("11_Sonstiges",           30, "Farbige Tonflaechen (rosa Planungszone) und Restgeometrie"),
    LayerDef("12_Plankopf",           140, "Schriftfeld und Legende am rechten Planrand"),
]

LINE_LAYERS = {"05_Linien_stark", "06_Linien_fein", "11_Sonstiges"}


# ---------------------------------------------------------------- Geometrie

def near(a, b, tol=WELD_TOL_PT):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def flatten_bezier(p0, p1, p2, p3, tol=FLATTEN_TOL_PT):
    """Kubische Bezierkurve in Polygonzug zerlegen (adaptiv ueber Sehnenfehler)."""
    chord = math.dist(p0, p3)
    poly = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
    if poly <= 1e-9:
        return [p3]
    n = max(2, min(48, int(math.ceil(math.sqrt((poly - chord) / max(tol, 1e-9)) * 3))))
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1.0 - t
        out.append((
            u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
            u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
        ))
    return out


def items_to_subpaths(items):
    """PyMuPDF-Items in getrennte Konturen (Polygonzuege) zerlegen."""
    subs, cur = [], []

    def flush():
        nonlocal cur
        if len(cur) >= 2:
            subs.append(cur)
        cur = []

    for it in items:
        kind = it[0]
        if kind == "re":
            flush()
            r = it[1]
            subs.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
        elif kind == "qu":
            flush()
            q = it[1]
            subs.append([(q.ul.x, q.ul.y), (q.ur.x, q.ur.y),
                         (q.lr.x, q.lr.y), (q.ll.x, q.ll.y), (q.ul.x, q.ul.y)])
        elif kind == "l":
            a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
            if cur and near(cur[-1], a):
                cur.append(b)
            else:
                flush()
                cur = [a, b]
        elif kind == "c":
            a = (it[1].x, it[1].y)
            c1, c2 = (it[2].x, it[2].y), (it[3].x, it[3].y)
            b = (it[4].x, it[4].y)
            if not (cur and near(cur[-1], a)):
                flush()
                cur = [a]
            cur.extend(flatten_bezier(a, c1, c2, b))
    flush()

    cleaned = []
    for s in subs:
        out = [s[0]]
        for p in s[1:]:
            if not near(out[-1], p):
                out.append(p)
        if len(out) >= 2:
            cleaned.append(out)
    return cleaned


def _extent(sub):
    xs = [p[0] for p in sub]
    ys = [p[1] for p in sub]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def centroid(sub):
    return (sum(p[0] for p in sub) / len(sub), sum(p[1] for p in sub) / len(sub))


def is_closed(sub):
    return len(sub) >= 4 and near(sub[0], sub[-1], 1e-3)


def poly_area(sub):
    a = 0.0
    for i in range(len(sub) - 1):
        a += sub[i][0] * sub[i + 1][1] - sub[i + 1][0] * sub[i][1]
    return abs(a) / 2.0


def corner_points(sub):
    """Kontur auf ihre Eckpunkte reduzieren (kollineare Punkte entfernen)."""
    pts = sub[:-1] if near(sub[0], sub[-1], 1e-3) else sub[:]
    if len(pts) < 3:
        return pts
    keep = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        d = math.dist(a, b) * math.dist(b, c)
        if d < 1e-12 or abs(cross) / d > 1e-3:
            keep.append(b)
    return keep if len(keep) >= 3 else pts


def ring_midline(outer, inner):
    """Mittellinie zwischen zwei parallelen Konturen; None wenn kein sauberer Ring."""
    o, i = corner_points(outer), corner_points(inner)
    if len(o) != len(i) or len(o) < 3:
        return None, None
    n = len(o)
    best = None
    for rev in (False, True):
        cand = i[::-1] if rev else i
        for shift in range(n):
            rot = cand[shift:] + cand[:shift]
            d = [math.dist(o[k], rot[k]) for k in range(n)]
            spread = (max(d) - min(d)) / max(max(d), 1e-9)
            score = sum(d) / n
            if spread <= RING_UNIFORM_TOL and (best is None or score < best[0]):
                best = (score, rot, d)
    if best is None:
        return None, None
    _, rot, d = best
    mid = [((o[k][0] + rot[k][0]) / 2.0, (o[k][1] + rot[k][1]) / 2.0) for k in range(n)]
    mid.append(mid[0])
    return mid, 2.0 * (sum(d) / n) / math.sqrt(2.0)


def as_circle(sub):
    """Kontur als Kreis (Mittelpunkt, Radius) erkennen, sonst None."""
    pts = sub[:-1] if near(sub[0], sub[-1], 1e-3) else sub
    if len(pts) < 8:
        return None
    c = centroid(pts)
    rs = [math.dist(p, c) for p in pts]
    rm = sum(rs) / len(rs)
    if rm < 1e-6 or (max(rs) - min(rs)) / rm > CIRCLE_TOL:
        return None
    return c, rm


def split_ring(path, subs):
    """(aussen, innen) liefern, wenn der Pfad eine als Flaeche gezeichnete Kontur ist."""
    if not (path.get("even_odd") and len(subs) == 2):
        return None
    if not (is_closed(subs[0]) and is_closed(subs[1])):
        return None
    a, b = subs
    return (a, b) if poly_area(a) >= poly_area(b) else (b, a)


def is_tick_bundle(subs):
    """Sammelpfad aus vielen winzigen gefuellten Konturen = Massstriche."""
    return len(subs) > 12 and sum(1 for s in subs if _extent(s) < 3.0) > 0.8 * len(subs)


def is_hatch_bundle(subs):
    """Sammelpfad aus vielen losen Einzelstrichen = Schraffurfeld."""
    return len(subs) > 12 and sum(1 for s in subs if len(s) == 2) > 0.8 * len(subs)


# ---------------------------------------------------------------- Massmarken

class DimMarks:
    """Raster ueber alle Massmarken, um Linien darauf zu pruefen."""

    CELL = 8.0

    def __init__(self, pts):
        self.pts = pts
        self.grid = {}
        for p in pts:
            self.grid.setdefault((int(p[0] // self.CELL), int(p[1] // self.CELL)), []).append(p)

    def _around(self, x, y):
        cx, cy = int(x // self.CELL), int(y // self.CELL)
        out = []
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                out.extend(self.grid.get((cx + i, cy + j), ()))
        return out

    def on_segment(self, a, b, tol=MARK_LINE_TOL_PT):
        """Anzahl Massmarken, die auf der Strecke a-b liegen."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            return 0
        ux, uy = dx / L, dy / L
        seen, n = set(), 0
        steps = max(2, int(L / self.CELL) + 2)
        cands = []
        for k in range(steps + 1):
            t = L * k / steps
            cands.extend(self._around(a[0] + ux * t, a[1] + uy * t))
        for q in cands:
            if q in seen:
                continue
            seen.add(q)
            t = (q[0] - a[0]) * ux + (q[1] - a[1]) * uy
            if -1.5 < t < L + 1.5 and abs(-(q[0] - a[0]) * uy + (q[1] - a[1]) * ux) < tol:
                n += 1
        return n

    def near_point(self, p, r):
        return any(math.dist(p, q) <= r for q in self._around(*p))

    # -- zweite Stufe: erkannte Masslinien als Bezug fuer Masshilfslinien

    def set_dim_lines(self, segments):
        """Bereits erkannte Masslinien fuer den Anschlusstest hinterlegen."""
        self.dim_grid = {}
        for a, b in segments:
            L = math.dist(a, b)
            steps = max(1, int(L / self.CELL) + 1)
            for k in range(steps + 1):
                t = k / steps
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                self.dim_grid.setdefault(
                    (int(x // self.CELL), int(y // self.CELL)), []).append((a, b))

    def on_dim_line(self, p, tol=2.0):
        """Liegt der Punkt auf einer bereits erkannten Masslinie?"""
        cx, cy = int(p[0] // self.CELL), int(p[1] // self.CELL)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for a, b in getattr(self, "dim_grid", {}).get((cx + i, cy + j), ()):
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    L = math.hypot(dx, dy)
                    if L < 1e-9:
                        continue
                    ux, uy = dx / L, dy / L
                    t = (p[0] - a[0]) * ux + (p[1] - a[1]) * uy
                    if -tol < t < L + tol and \
                            abs(-(p[0] - a[0]) * uy + (p[1] - a[1]) * ux) < tol:
                        return True
        return False

    def segment_is_dimension(self, a, b, second_pass):
        """Masslinie: mindestens zwei Marken darauf.
        Masshilfslinie: eine Marke darauf und ein Ende auf einer Masslinie."""
        n = self.on_segment(a, b)
        if n >= 2:
            return True
        if second_pass and n >= 1 and math.dist(a, b) < 160.0:
            return self.on_dim_line(a) or self.on_dim_line(b)
        return False

    def is_dimension_polyline(self, sub, second_pass=True):
        """Polygonzug gilt als Massgeometrie, wenn die Mehrheit seiner
        Teilstrecken zur Bemassung gehoert."""
        good = total = 0
        for i in range(len(sub) - 1):
            if math.dist(sub[i], sub[i + 1]) < 2.0:
                continue
            total += 1
            if self.segment_is_dimension(sub[i], sub[i + 1], second_pass):
                good += 1
        return total > 0 and good >= max(1, 0.6 * total)

    def collect_dim_segments(self, sub):
        """Teilstrecken mit mindestens zwei Marken (= sichere Masslinien)."""
        out = []
        for i in range(len(sub) - 1):
            if math.dist(sub[i], sub[i + 1]) >= 2.0 and self.on_segment(sub[i], sub[i + 1]) >= 2:
                out.append((sub[i], sub[i + 1]))
        return out


def collect_marks(page):
    """Massstriche und Masspunktkreise einsammeln."""
    marks = []
    for path in page.get_drawings():
        subs = items_to_subpaths(path["items"])
        if not subs:
            continue
        if is_tick_bundle(subs) and not is_hatch_bundle(subs):
            marks.extend(centroid(s) for s in subs)
            continue
        ring = split_ring(path, subs)
        if ring:
            co, ci = as_circle(ring[0]), as_circle(ring[1])
            if co and ci and (co[1] + ci[1]) / 2.0 <= MARK_RADIUS_PT:
                marks.append(co[0])
    return marks


def find_plankopf_x(page):
    """Linke Kante des Schriftfelds ueber feste Beschriftungen bestimmen."""
    xs = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span.get("text", "").strip() in TITLE_ANCHORS:
                    xs.append(span["bbox"][0])
    return min(xs) - PLANKOPF_MARGIN_PT if xs else None


# ---------------------------------------------------------------- Stil -> Layer

def parse_dashes(s):
    if not s:
        return []
    txt = str(s)
    if "[" in txt and "]" in txt:
        txt = txt[txt.find("[") + 1: txt.find("]")]
    return [float(x) for x in re.findall(r"[\d.]+", txt) if float(x) > 0]


def grey(c):
    return c is not None and abs(c[0] - c[1]) < 0.06 and abs(c[1] - c[2]) < 0.06


def classify(path, is_ring=False, ring_width_pt=None):
    """Grafikeigenschaften eines PDF-Pfades auf einen Layer abbilden."""
    fill = path.get("fill")
    stroke = path.get("color")
    width = path.get("width") or 0.0
    size = max(path["rect"].width, path["rect"].height)
    dashes = parse_dashes(path.get("dashes"))
    col = stroke if stroke is not None else fill
    blueish = col is not None and not grey(col) and col[2] > col[0] + 0.15

    if is_ring:
        if blueish:
            return "03_Sanitaer"
        if size <= 2 * MARK_RADIUS_PT:
            return "07_Bemassung"
        w = ring_width_pt if ring_width_pt else width
        return "05_Linien_stark" if w >= 0.35 else "06_Linien_fein"

    if fill is not None and path["type"] in ("f", "fs"):
        if grey(fill):
            v = fill[0]
            if v > 0.97:
                return "09_Weissflaechen"
            if v > 0.68:
                return "01_Daemmung_neu"
            if v > 0.30:
                return "02_Grundstuecksgrenze"
            return "00_Wand_Bestand" if size >= 2.0 else "07_Bemassung"
        if blueish:
            return "03_Sanitaer"
        return "11_Sonstiges"

    if dashes:
        return "08_Schnittlinie" if width >= 0.5 else "06_Linien_fein"
    if blueish:
        return "03_Sanitaer"
    return "05_Linien_stark" if width >= 0.35 else "06_Linien_fein"


def lineweight(width_pt):
    """PDF-Strichstaerke (pt) -> DXF-Lineweight (1/100 mm, genormte Stufe)."""
    if not width_pt:
        return -1
    std = [0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80,
           90, 100, 106, 120, 140, 158, 200, 211]
    return min(std, key=lambda v: abs(v - width_pt * PT_TO_MM * 100))


# ---------------------------------------------------------------- Konvertierung

class Converter:
    def __init__(self, page, scale_denom, dxfversion="R2018"):
        self.page = page
        self.dxfversion = dxfversion
        self.S = PT_TO_MM * scale_denom          # pt -> mm Realmass
        self.H = page.rect.height
        self.W = page.rect.width
        self.marks = DimMarks(collect_marks(page))
        self.marks.set_dim_lines(self._prescan_dim_lines())
        self.plankopf_x = find_plankopf_x(page)
        self.doc = ezdxf.new(self.dxfversion, setup=True)
        self.msp = self.doc.modelspace()
        self.stats = {}
        self._ltypes = set()
        self._hatches = []
        self._setup_doc()

    def _setup_doc(self):
        d = self.doc
        d.units = ezdxf.units.MM
        d.header["$INSUNITS"] = 4        # Millimeter
        d.header["$MEASUREMENT"] = 1     # metrisch
        d.header["$LUNITS"] = 2
        d.header["$LUPREC"] = 2
        d.header["$LTSCALE"] = 50.0
        for ld in LAYERS:
            lay = d.layers.add(ld.name, color=ld.aci)
            if d.dxfversion > "AC1015":
                lay.description = ld.description
            if ld.name == "09_Weissflaechen":
                lay.off()
            # Ohne Transparenz (vor R2004) wuerden die Tonflaechen alles zudecken
            if ld.name == "11_Sonstiges" and d.dxfversion <= "AC1015":
                lay.off()
        d.styles.add("PLAN", font="arial.ttf")

    def _prescan_dim_lines(self):
        """Erster Durchgang: sichere Masslinien finden (>= 2 Massmarken)."""
        segs = []
        for path in self.page.get_drawings():
            subs = items_to_subpaths(path["items"])
            if len(subs) > 12:
                continue
            for sub in subs:
                segs.extend(self.marks.collect_dim_segments(sub))
        return segs

    # ---- Koordinaten und Attribute

    def xy(self, p):
        return (p[0] * self.S, (self.H - p[1]) * self.S)

    def bump(self, layer, n=1):
        self.stats[layer] = self.stats.get(layer, 0) + n

    def in_plankopf(self, pts):
        return (self.plankopf_x is not None
                and all(p[0] >= self.plankopf_x for p in pts))

    def ltype_for(self, dashes):
        if not dashes:
            return "CONTINUOUS"
        pat = tuple(round(v * self.S, 1) for v in dashes[:6])
        name = ("PDF_" + "_".join(str(v).replace(".", "-") for v in pat))[:30]
        if name not in self._ltypes:
            elems = [v if k % 2 == 0 else -v for k, v in enumerate(pat)]
            if len(elems) % 2:
                elems.append(-pat[0])
            try:
                self.doc.linetypes.add(
                    name, pattern=[sum(abs(e) for e in elems)] + elems,
                    description="aus PDF uebernommen")
            except Exception:
                return "DASHED"
            self._ltypes.add(name)
        return name

    def attribs(self, layer, path, width_pt=None):
        a = {"layer": layer, "color": 256}
        w = width_pt if width_pt is not None else (path.get("width") or 0.0)
        lw = lineweight(w)
        if lw > 0:
            a["lineweight"] = lw
        lt = self.ltype_for(parse_dashes(path.get("dashes")))
        if lt != "CONTINUOUS":
            a["linetype"] = lt
        return a

    # ---- Ausgabe

    def emit(self, sub, layer, attr, force_closed=False):
        if self.in_plankopf(sub):
            layer = "12_Plankopf"
        elif layer in LINE_LAYERS and self.marks.is_dimension_polyline(sub):
            layer = "07_Bemassung"
        attr = dict(attr, layer=layer)

        circ = as_circle(sub) if (is_closed(sub) or force_closed) else None
        if circ:
            self.msp.add_circle(self.xy(circ[0]), circ[1] * self.S, dxfattribs=attr)
            self.bump(layer)
            return
        pts = [self.xy(p) for p in sub]
        closed = near(sub[0], sub[-1], 1e-3)
        if closed:
            pts = pts[:-1]
        if len(pts) == 2:
            self.msp.add_line(pts[0], pts[1], dxfattribs=attr)
        elif len(pts) > 2:
            self.msp.add_lwpolyline(pts, close=closed or force_closed, dxfattribs=attr)
        else:
            return
        self.bump(layer)

    def emit_circle(self, center, radius, layer, attr):
        if self.in_plankopf([center]):
            layer = "12_Plankopf"
        self.msp.add_circle(self.xy(center), radius * self.S,
                            dxfattribs=dict(attr, layer=layer))
        self.bump(layer)

    def emit_hatch(self, subs, layer, opacity=1.0):
        for s in subs:
            if len(s) < 3:
                continue
            lay = "12_Plankopf" if self.in_plankopf(s) else layer
            h = self.msp.add_hatch(dxfattribs={"layer": lay, "color": 256})
            h.set_solid_fill()
            h.dxf.hatch_style = 0
            if opacity < 0.9 and self.doc.dxfversion > "AC1015":
                h.transparency = round(1.0 - opacity, 2)
            self._hatches.append(h)
            pts = [self.xy(p) for p in s]
            if pts[0] == pts[-1]:
                pts = pts[:-1]
            h.paths.add_polyline_path(pts, is_closed=True)
            self.bump(lay)

    # ---- Pfade

    def run_paths(self):
        for path in self.page.get_drawings():
            try:
                self.one_path(path)
            except Exception as exc:
                print(f"   ! Pfad uebersprungen: {exc}")

    def one_path(self, path):
        subs = items_to_subpaths(path["items"])
        if not subs:
            return
        filled = path["type"] in ("f", "fs") and path.get("fill") is not None

        if len(subs) > 12:
            if is_hatch_bundle(subs):
                attr = self.attribs("04_Schraffur", path, width_pt=path.get("width") or 0.13)
                for s in subs:
                    self.emit(s, "04_Schraffur", attr)
                return
            if is_tick_bundle(subs):
                attr = self.attribs("07_Bemassung", path, width_pt=0.0)
                for s in subs:
                    self.emit(s, "07_Bemassung", attr)
                return

        ring = split_ring(path, subs) if filled else None
        if ring:
            outer, inner = ring
            co, ci = as_circle(outer), as_circle(inner)
            if co and ci:                                    # Kreisring
                w = max(co[1] - ci[1], 0.0)
                layer = classify(path, is_ring=True, ring_width_pt=w)
                self.emit_circle(co[0], (co[1] + ci[1]) / 2.0, layer,
                                 self.attribs(layer, path, width_pt=w))
                return
            mid, w = ring_midline(outer, inner)
            if mid is not None:
                layer = classify(path, is_ring=True, ring_width_pt=w)
                self.emit(mid, layer, self.attribs(layer, path, width_pt=w),
                          force_closed=True)
                return
            layer = classify(path, is_ring=True, ring_width_pt=0.2)
            attr = self.attribs(layer, path, width_pt=0.0)
            for s in (outer, inner):
                self.emit(s, layer, attr)
            return

        layer = classify(path)
        if filled:
            closed = [s for s in subs if is_closed(s) and poly_area(s) > 1e-6]
            if closed and layer != "09_Weissflaechen":
                self.emit_hatch(closed, layer, path.get("fill_opacity") or 1.0)
            attr = self.attribs(layer, path, width_pt=0.0)
        else:
            attr = self.attribs(layer, path)
        for s in subs:
            self.emit(s, layer, attr)

    # ---- Text

    def run_text(self):
        for block in self.page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                dx, dy = line.get("dir", (1.0, 0.0))
                rot = math.degrees(math.atan2(-dy, dx)) % 360.0
                for span in line.get("spans", []):
                    self.one_span(span, rot)

    def one_span(self, span, rot):
        txt = span.get("text", "")
        if not txt.strip():
            return
        h = span["size"] * self.S * 0.72          # Schriftgroesse -> Versalhoehe
        if h <= 0:
            return
        x0, y0, x1, y1 = span["bbox"]
        if self.plankopf_x is not None and x0 >= self.plankopf_x:
            layer = "12_Plankopf"
        elif NUMBER_RE.match(txt.strip()) and (
                self.marks.near_point(((x0 + x1) / 2.0, (y0 + y1) / 2.0), 18.0)
                or self.marks.on_dim_line(((x0 + x1) / 2.0, (y0 + y1) / 2.0), 16.0)):
            layer = "07_Bemassung"                # Masszahl
        else:
            layer = "10_Text"
        e = self.msp.add_text(txt, height=h, rotation=rot,
                              dxfattribs={"layer": layer, "style": "PLAN", "color": 256})
        e.set_placement(self.xy(span["origin"]))
        self.bump(layer)

    def finish(self, out):
        if self._hatches:                       # Flaechen hinter die Linien legen
            back = [h.dxf.handle for h in self._hatches]
            rest = [e.dxf.handle for e in self.msp if e.dxftype() != "HATCH"]
            self.msp.set_redraw_order({h: f"{i:08X}" for i, h in enumerate(back + rest)})
        self.doc.header["$EXTMIN"] = (0.0, 0.0, 0.0)
        self.doc.header["$EXTMAX"] = (self.W * self.S, self.H * self.S, 0.0)
        self.doc.saveas(out)


def convert(pdf_path, page_no, scale_denom, outdir, name, dxfversion="R2018"):
    doc = pymupdf.open(pdf_path)
    conv = Converter(doc[page_no - 1], scale_denom, dxfversion)
    conv.run_paths()
    conv.run_text()
    out = os.path.join(outdir, f"{name}.dxf")
    conv.finish(out)
    return out, conv.stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="1")
    ap.add_argument("--scale", type=float, default=100.0, help="Nenner des Planmassstabs")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--names", default="", help="Dateinamen je Seite, kommagetrennt")
    ap.add_argument("--dxfversion", default="R2018",
                    help="DXF-Version, z.B. R2018 (Standard) oder R2000 fuer aeltere Programme")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    pages = [int(x) for x in args.pages.split(",")]
    names = [n.strip() for n in args.names.split(",")] if args.names else []

    for k, pno in enumerate(pages):
        name = names[k] if k < len(names) and names[k] else f"Seite_{pno:02d}"
        out, stats = convert(args.pdf, pno, args.scale, args.outdir, name, args.dxfversion)
        print(f"\n{out}")
        for lay in sorted(stats):
            print(f"   {lay:<24} {stats[lay]:>6}")


if __name__ == "__main__":
    main()
