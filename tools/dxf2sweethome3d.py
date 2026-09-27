"""Geschossgrundrisse als massstaebliche PNG-Unterlagen fuer Sweet Home 3D.

Aufloesung exakt 100 Pixel je Meter (1 Pixel = 1 cm). Alle Geschosse teilen
denselben Bildausschnitt, liegen also deckungsgleich uebereinander.
"""
import ezdxf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, LineweightPolicy
from ezdxf.addons.drawing.properties import LayoutProperties

FLOORS = [('04_Kellergeschoss','Kellergeschoss'), ('01_Erdgeschoss','Erdgeschoss'),
          ('02_1-Obergeschoss','1. Obergeschoss'), ('03_2-Obergeschoss','2. Obergeschoss'),
          ('05_3-Obergeschoss','3. Obergeschoss'), ('13_Staffelgeschoss','Staffelgeschoss')]
OFF = {'07_Bemassung', '12_Plankopf', '09_Weissflaechen', '11_Sonstiges',
       '02_Grundstuecksgrenze', '08_Schnittlinie'}
PX_PER_M = 100          # 1 Pixel = 1 cm
MARGIN = 1500           # mm Rand um die Bebauung
BAR_M = 10              # Laenge des Massstabsbalkens in Metern

def structure_bbox(paths):
    """Huelle ueber das Bestandsmauerwerk aller Geschosse; das ist das Gebaeude
    selbst, ohne Nachbarbebauung, Masshilfslinien und Verweislinien."""
    keep = {'00_Wand_Bestand'}
    xs, ys = [], []
    for p in paths:
        for e in ezdxf.readfile(p).modelspace():
            if e.dxf.layer not in keep:
                continue
            if e.dxftype() == 'LWPOLYLINE':   pts = [q[:2] for q in e.get_points()]
            elif e.dxftype() == 'LINE':       pts = [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]
            elif e.dxftype() == 'HATCH':      pts = [q[:2] for pa in e.paths for q in pa.vertices]
            else: continue
            for q in pts: xs.append(q[0]); ys.append(q[1])
    return min(xs), min(ys), max(xs), max(ys)

box = structure_bbox([f'alle/{f}.dxf' for f, _ in FLOORS])
x0, y0, x1, y1 = box[0]-MARGIN, box[1]-MARGIN-2200, box[2]+MARGIN, box[3]+MARGIN
px_w = round((x1-x0)/1000*PX_PER_M); px_h = round((y1-y0)/1000*PX_PER_M)
x1 = x0 + px_w/PX_PER_M*1000; y1 = y0 + px_h/PX_PER_M*1000      # exakt aufs Raster
print(f'Ausschnitt {(x1-x0)/1000:.2f} x {(y1-y0)/1000:.2f} m  ->  {px_w} x {px_h} px')

for fname, label in FLOORS:
    doc = ezdxf.readfile(f'alle/{fname}.dxf'); msp = doc.modelspace()
    for lay in doc.layers:
        if lay.dxf.name in OFF: lay.off()
    fig = plt.figure(figsize=(px_w/100, px_h/100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ctx = RenderContext(doc)
    lp = LayoutProperties.from_layout(msp); lp.set_colors("#FFFFFF")
    cfg = Configuration(lineweight_policy=LineweightPolicy.ABSOLUTE, lineweight_scaling=2.2)
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(
        msp, finalize=False, layout_properties=lp)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')

    # Massstabsbalken: exakt BAR_M Meter zwischen den beiden Endstrichen
    bx, by, L = x0 + 700, y0 + 900, BAR_M * 1000
    ax.plot([bx, bx+L], [by, by], color='#D40000', lw=5, solid_capstyle='butt', zorder=99)
    for xx in (bx, bx+L):
        ax.plot([xx, xx], [by-300, by+300], color='#D40000', lw=5, zorder=99)
    ax.text(bx+L/2, by+420, f'{BAR_M},00 m', color='#D40000', fontsize=22,
            ha='center', va='bottom', weight='bold', zorder=99)
    ax.text(bx + L + 900, by, label, color='#444444', fontsize=26, ha='left', va='center', zorder=99)

    out = f'sh3d/{fname}.png'
    fig.savefig(out, facecolor='white', dpi=100)
    plt.close(fig)
    print('  ', out)
