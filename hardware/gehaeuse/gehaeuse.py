#!/usr/bin/env python3
"""
Parametric 3D-printable case for the N.I.N.A. Pocket Companion:
LilyGO T-Display (ESP32) stacked on a 1100 mAh LiPo (47 x 29 x 8 mm).

Two parts:
  gehaeuse_unterteil.stl  shell holding battery + board, USB-C opening
  gehaeuse_deckel.stl     snap-on lid with display window and two
                          flexure buttons for GPIO0 / GPIO35

All dimensions in mm. Measure your board and battery and adjust the
values in the PARAMETERS block, then run:

  pip install manifold3d numpy matplotlib
  python3 hardware/gehaeuse/gehaeuse.py

Coordinates: x along the board (0 = end without USB, + towards USB-C),
y across the board, z up (display facing up).

Copyright (c) 2026 Kai Linde - MIT License, see LICENSE.
"""
import struct
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold

# ------------------------------ PARAMETERS ------------------------------
# T-Display board: measured 52 x 26 x 6 mm overall (52 incl. the USB-C socket,
# 6 = BACK_H + PCB_T + FRONT_H)
PCB_L, PCB_W, PCB_T = 50.0, 26.0, 1.6   # PCB_L: board only, without the protruding socket
BACK_H = 2.6        # tallest part on the back side (ESP32 module, JST plug) - assumed
FRONT_H = 1.8       # display glass surface above the PCB top - assumed
# Display window (active area ~14.9 x 24.9 mm), centre measured from the PCB end without USB
WIN_W, WIN_L, WIN_CX = 16.0, 27.0, 19.5  # WIN_CX estimated from a photo
WIN_CHAMFER = 1.0
# Buttons GPIO0 / GPIO35, measured from the tip of the USB-C socket and from each long edge
BTN_FROM_USB, BTN_FROM_SIDE = 7.0, 4.0
BTN_H = 1.8         # top of the push button above the PCB top - estimated from a photo
# USB-C socket: mid-mount, sits in a notch of the board and reaches down to the PCB bottom
USB_TOP = 1.2       # top of the socket above the PCB top - measured
USB_OUT = 2.0       # how far the socket sticks out beyond the board edge - measured
USB_LEN = 7.0       # how far the socket reaches into the board from the board edge - measured
# USB-C opening in the end wall, centred on the socket; open towards the lid if it reaches the rim
USB_W, USB_H = 12.0, 6.0
# Battery 1100 mAh LiPo (measured); wider than the board, shorter than it
BAT_L, BAT_W, BAT_T = 47.0, 29.0, 8.0
GAP = 1.0           # foam pad between battery and the parts on the board's back
CABLE_BAY = 0.0     # extra length for the battery cable (battery is shorter than the board)
# Case
CLR = 0.3           # clearance board <-> wall
WALL, FLOOR, LID_T = 1.6, 1.2, 1.4
R_OUT = 3.0         # outer corner radius
FIT = 0.15          # lid skirt clearance per side
SKIRT_T = 1.2
# Optional cut-out for a slide switch in the battery lead (long side wall, far end)
SWITCH = False
SWITCH_W, SWITCH_H, SWITCH_X = 9.0, 4.0, 10.0
# Project name engraved into the underside (font via matplotlib; skipped if it is missing)
LABEL = ("N.I.N.A.", "Pocket Companion")
LABEL_SIZE = (8.0, 5.0)  # font size per line
LABEL_MAX_W = 44.0       # lines wider than this are scaled down
LABEL_GAP = 2.5          # space between the lines
LABEL_DEPTH = 0.5        # of the 1.2 mm floor
# ------------------------------------------------------------------------

OUT = Path(__file__).resolve().parent
SEG = 48


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def rounded(x0, y0, x1, y1, r, z0, z1):
    cs = CrossSection.square((x1 - x0 - 2 * r, y1 - y0 - 2 * r)).translate((x0 + r, y0 + r))
    cs = cs.offset(r, JoinType.Round, circular_segments=SEG)
    return Manifold.extrude(cs, z1 - z0).translate((0, 0, z0))


def cyl_x(x0, x1, y, z, r):
    return Manifold.cylinder(x1 - x0, r, r, SEG).rotate((0, 90, 0)).translate((x0, y, z))


def cyl_z(x, y, z0, z1, r):
    return Manifold.cylinder(z1 - z0, r, r, SEG).translate((x, y, z0))


# ---- derived geometry ----
IN_L = CABLE_BAY + max(PCB_L + USB_OUT, BAT_L) + 2 * CLR
IN_W = max(PCB_W, BAT_W) + 2 * CLR
OUT_L, OUT_W = IN_L + 2 * WALL, IN_W + 2 * WALL
Z_PCB_BOT = FLOOR + BAT_T + GAP + BACK_H
Z_PCB_TOP = Z_PCB_BOT + PCB_T
Z_RIM = Z_PCB_TOP + FRONT_H + 0.1          # lid sits on the rim just above the glass
PCB_X0 = WALL + IN_L - CLR - USB_OUT - PCB_L  # PCB end without USB (socket tip at the USB wall)
PCB_Y0 = WALL + (IN_W - PCB_W) / 2         # board centred across the (wider) cavity
PRESS = 1.0                                # how far the lid rim overlaps the PCB edge
SNAP_Z = Z_PCB_TOP - 0.3
SNAP_LEN = 24.0
BTN_X = PCB_X0 + PCB_L + USB_OUT - BTN_FROM_USB
# Near the USB end the socket and the buttons stand up to the display height: the lid
# keeps clear of the board there and may cut up to 0.6 mm into its plate.
END_ZONE = USB_LEN + 0.5                   # measured from the board edge on the USB side
END_CLEAR = Z_PCB_TOP + max(USB_TOP, BTN_H) + 0.3
assert END_CLEAR <= Z_RIM + 0.6, "socket/buttons higher than the lid allows - check USB_TOP, BTN_H, FRONT_H"
BTN_YS = (PCB_Y0 + BTN_FROM_SIDE, PCB_Y0 + PCB_W - BTN_FROM_SIDE)


def shell():
    s = rounded(0, 0, OUT_L, OUT_W, R_OUT, 0, Z_RIM)
    s -= rounded(WALL, WALL, WALL + IN_L, WALL + IN_W, 0.6, FLOOR, Z_RIM + 1)
    # USB-C opening, centred on the socket (PCB bottom up to USB_TOP)
    zc = (Z_PCB_BOT + Z_PCB_TOP + USB_TOP) / 2
    yc = OUT_W / 2
    s -= box(OUT_L - WALL - 1, yc - USB_W / 2, zc - USB_H / 2, OUT_L + 1, yc + USB_W / 2, zc + USB_H / 2)
    # snap grooves on both long inner walls
    xm = OUT_L / 2
    for y in (WALL, WALL + IN_W):
        s -= cyl_x(xm - SNAP_LEN / 2 - 1, xm + SNAP_LEN / 2 + 1, y, SNAP_Z, 0.6)
    if SWITCH:
        zc = FLOOR + BAT_T / 2 + 2
        s -= box(SWITCH_X, -1, zc - SWITCH_H / 2, SWITCH_X + SWITCH_W, WALL + 1, zc + SWITCH_H / 2)
    text = label()
    if text is not None:
        s -= Manifold.extrude(text, LABEL_DEPTH + 1).translate((0, 0, -1))
    return s


def label():
    """LABEL as a cross-section centred on the floor, mirrored so that it reads
    correctly when the case is turned over about its long axis."""
    try:
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextPath
    except ImportError:
        print("matplotlib not installed - building the case without the label")
        return None
    prop = FontProperties(family="DejaVu Sans", weight="bold")
    lines = []
    for text, size in zip(LABEL, LABEL_SIZE):
        path = TextPath((0, 0), text, size=size, prop=prop)
        cs = CrossSection([np.asarray(p, float) for p in path.to_polygons()], FillRule.EvenOdd)
        x0, y0, x1, y1 = cs.bounds()
        if x1 - x0 > LABEL_MAX_W:
            cs = cs.scale((LABEL_MAX_W / (x1 - x0),) * 2)
            x0, y0, x1, y1 = cs.bounds()
        lines.append(cs.translate((-(x0 + x1) / 2, -y1)))  # centred, top edge at y = 0
    text, y = CrossSection(), 0.0
    for cs in lines:
        x0, y0, x1, y1 = cs.bounds()
        text += cs.translate((0, y))
        y += y0 - LABEL_GAP
    x0, y0, x1, y1 = text.bounds()
    text = text.translate((0, -(y0 + y1) / 2)).scale((1, -1))
    return text.translate((OUT_L / 2, OUT_W / 2))


def lid():
    """Modelled in assembly position; flipped for printing in main()."""
    z0 = Z_RIM
    plate = rounded(0, 0, OUT_L, OUT_W, R_OUT, z0, z0 + LID_T)
    # skirt that slides into the shell and presses the PCB edges down
    sk_x0, sk_y0 = WALL + FIT, WALL + FIT
    sk_x1, sk_y1 = WALL + IN_L - FIT, WALL + IN_W - FIT
    px0, py0, px1, py1 = PCB_X0, PCB_Y0, PCB_X0 + PCB_L, PCB_Y0 + PCB_W
    skirt_bot = Z_PCB_TOP + 0.05
    inner = (max(px0 + PRESS, sk_x0 + SKIRT_T), max(py0 + PRESS, sk_y0 + SKIRT_T),
             min(px1 - PRESS, sk_x1 - SKIRT_T), min(py1 - PRESS, sk_y1 - SKIRT_T))
    skirt = rounded(sk_x0, sk_y0, sk_x1, sk_y1, 0.5, skirt_bot, z0)
    skirt -= rounded(*inner, 0.3, skirt_bot - 1, z0 + 1)
    # guides beside the board where the cavity is wider/longer than the PCB
    guide_bot = Z_PCB_BOT + 0.3
    for g in (box(sk_x0, sk_y0, guide_bot, sk_x1, py0 - CLR, z0),
              box(sk_x0, py1 + CLR, guide_bot, sk_x1, sk_y1, z0),
              box(sk_x0, sk_y0, guide_bot, px0 - CLR, sk_y1, z0)):
        bb = g.bounding_box()
        if min(bb[3] - bb[0], bb[4] - bb[1]) >= 0.8:
            skirt += g
    # snap bumps
    xm = OUT_L / 2
    bumps = cyl_x(xm - SNAP_LEN / 2, xm + SNAP_LEN / 2, sk_y0 + 0.15, SNAP_Z, 0.45) + \
        cyl_x(xm - SNAP_LEN / 2, xm + SNAP_LEN / 2, sk_y1 - 0.15, SNAP_Z, 0.45)
    part = plate + skirt + bumps
    # clearance above USB-C socket and buttons; reaches below the guides so no thin
    # sliver of them is left hanging in the air
    part -= box(px1 - END_ZONE, sk_y0 - 1, guide_bot - 1, OUT_L + 1, sk_y1 + 1, END_CLEAR)
    # display window with chamfer on the top face
    wx0 = PCB_X0 + WIN_CX - WIN_L / 2
    wy0 = PCB_Y0 + PCB_W / 2 - WIN_W / 2
    win = box(wx0, wy0, z0 - 5, wx0 + WIN_L, wy0 + WIN_W, z0 + LID_T + 1)
    c = WIN_CHAMFER
    chamfer = Manifold.batch_hull([
        box(wx0, wy0, z0 + LID_T - c, wx0 + WIN_L, wy0 + WIN_W, z0 + LID_T - c + 0.01),
        box(wx0 - c, wy0 - c, z0 + LID_T, wx0 + WIN_L + c, wy0 + WIN_W + c, z0 + LID_T + 0.01),
    ])
    part -= win + chamfer
    # flexure buttons: U-shaped slot, tongue hinged towards the display, nub underneath
    tongue_w, tongue_l, slot = 5.0, 9.0, 0.8
    for by in BTN_YS:
        tx0, tx1 = BTN_X - tongue_l + 2.5, BTN_X + 2.5
        ty0, ty1 = by - tongue_w / 2, by + tongue_w / 2
        u = box(tx0, ty0 - slot, z0 - 1, tx1 + slot, ty1 + slot, z0 + LID_T + 1)
        u -= box(tx0 - 1, ty0, z0 - 2, tx1, ty1, z0 + LID_T + 2)
        part -= u
        nub_bot = Z_PCB_TOP + BTN_H + 0.2
        underside = END_CLEAR if BTN_X > px1 - END_ZONE else z0
        if nub_bot < underside:
            part += cyl_z(BTN_X, by, nub_bot, underside + 0.01, 1.2)
        # small dimple on top so the buttons can be found by touch
        part -= Manifold.sphere(1.6, SEG).translate((BTN_X, by, z0 + LID_T + 1.2))
    return part


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    with open(path, "wb") as f:
        f.write(b"N.I.N.A. Pocket Companion case".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        for i in range(len(t)):
            f.write(struct.pack("<12fH", *n[i], *a[i], *b[i], *c[i], 0))


def main():
    s = shell()
    # lid: flip upside down so the top face lies on the print bed
    l = lid().rotate((180, 0, 0))
    bb = l.bounding_box()
    l = l.translate((-bb[0], -bb[1], -bb[2]))
    for name, part in (("gehaeuse_unterteil", s), ("gehaeuse_deckel", l)):
        assert part.status().name == "NoError", part.status()
        write_stl(part, OUT / f"{name}.stl")
        bb = part.bounding_box()
        print(f"{name}.stl  {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
              f"{part.volume()/1000:.1f} cm3")


if __name__ == "__main__":
    main()
