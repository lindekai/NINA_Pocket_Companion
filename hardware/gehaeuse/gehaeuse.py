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
# Flexure buttons in the lid: tongue hinged towards the display, pad underneath
BTN_TONGUE_L, BTN_TONGUE_W = 14.0, 4.5  # longer = softer; the hinge must stay clear of the window
BTN_TONGUE_TIP = 4.5  # how far the free end reaches past the button centre towards USB
BTN_TONGUE_T = 1.0  # tongue thickness, thinned from the underside (lid: LID_T); thinner = softer
BTN_PAD_R = 1.5     # pad under the tongue that presses the button
BTN_GAP = 0.15      # air between pad and button top - less travel before the click
# USB-C socket: mid-mount, sits in a notch of the board and reaches down to the PCB bottom
USB_TOP = 1.2       # top of the socket above the PCB top - measured
USB_OUT = 2.0       # how far the socket sticks out beyond the board edge - measured
USB_LEN = 7.0       # how far the socket reaches into the board from the board edge - measured
# USB-C opening in the end wall, centred on the socket; open towards the lid if it reaches the rim.
# The lid has a notch of the same width right through it over the socket (socket ~9 mm wide),
# so the opening, the notch and the gap between the lid's end stops line up.
USB_W, USB_H = 10.0, 6.0
# Battery 1100 mAh LiPo (measured); wider than the board, shorter than it
BAT_L, BAT_W, BAT_T = 47.0, 29.0, 8.0
GAP = 1.0           # foam pad between battery and the parts on the board's back
GUIDE_DEPTH = 1.5   # lid guides beside the board reach this far below the PCB bottom
CABLE_BAY = 0.0     # extra length for the battery cable (battery is shorter than the board)
END_STOP = 1.5      # room for a stop of the lid at the board end opposite the USB socket
# Case
CLR = 0.3           # clearance board <-> wall
FRAME_CLR = 0.15    # clearance board <-> guides and stops of the lid (snug, so the board cannot shift)
STOP_CLR = 0.6      # clearance board <-> the stops at both board ends (lengthwise; 0.15 was too tight)
WALL, FLOOR, LID_T = 1.6, 1.2, 1.4
R_OUT = 3.0         # outer corner radius
FIT = 0.15          # lid skirt clearance per side
SKIRT_T = 1.2
SNAP_DEPTH = 0.4    # how far the lid's snap beads reach into the grooves of the shell
# Optional cut-out for a slide switch in the battery lead (long side wall, far end)
SWITCH = False
SWITCH_W, SWITCH_H, SWITCH_X = 9.0, 4.0, 10.0
# Project name engraved into the underside (font via matplotlib; skipped if it is missing)
LABEL = ("N.I.N.A.", "Pocket Companion", "\u00a9 2026 by Kai Linde")
LABEL_SIZE = (8.0, 5.0, 3.5)  # font size per line
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
IN_L = CABLE_BAY + END_STOP + max(PCB_L + USB_OUT, BAT_L) + 2 * CLR
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
SNAP_R = FIT + SNAP_DEPTH                  # bead centred on the skirt face
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
        s -= cyl_x(xm - SNAP_LEN / 2 - 1, xm + SNAP_LEN / 2 + 1, y, SNAP_Z, SNAP_R + 0.1)
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
    guide_bot = Z_PCB_BOT - GUIDE_DEPTH
    assert guide_bot > FLOOR + BAT_T + GAP + 0.3, "lid guides reach down to the battery - reduce GUIDE_DEPTH"
    for g in (box(sk_x0, sk_y0, guide_bot, sk_x1, py0 - FRAME_CLR, z0),
              box(sk_x0, py1 + FRAME_CLR, guide_bot, sk_x1, sk_y1, z0),
              box(sk_x0, sk_y0, guide_bot, px0 - STOP_CLR, sk_y1, z0)):  # end stop, see END_STOP
        bb = g.bounding_box()
        if min(bb[3] - bb[0], bb[4] - bb[1]) >= 0.8:
            skirt += g
    # snap bumps
    xm = OUT_L / 2
    bumps = cyl_x(xm - SNAP_LEN / 2, xm + SNAP_LEN / 2, sk_y0, SNAP_Z, SNAP_R) + \
        cyl_x(xm - SNAP_LEN / 2, xm + SNAP_LEN / 2, sk_y1, SNAP_Z, SNAP_R)
    part = plate + skirt + bumps
    # clearance above the board at the USB end (buttons); the guides beside the board
    # run on to the end wall so the lid stays held there
    part -= box(px1 - END_ZONE, py0 - FRAME_CLR, guide_bot - 1, OUT_L + 1, py1 + FRAME_CLR, END_CLEAR)
    # end stops beyond the board edge on the USB side, left and right of the socket
    ny0, ny1 = PCB_Y0 + PCB_W / 2 - USB_W / 2, PCB_Y0 + PCB_W / 2 + USB_W / 2
    for y0, y1 in ((sk_y0, ny0), (ny1, sk_y1)):
        part += box(px1 + STOP_CLR, y0, guide_bot, sk_x1, y1, z0 + 0.01)
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
    # flexure buttons: U-shaped slot, thinned tongue hinged towards the display, pad underneath
    slot = 0.8
    tx0, tx1 = BTN_X + BTN_TONGUE_TIP - BTN_TONGUE_L, BTN_X + BTN_TONGUE_TIP
    assert tx1 <= px1, "button tongue reaches past the board edge - reduce BTN_TONGUE_TIP"
    assert tx0 >= wx0 + WIN_L + c + 1.0, "button tongue reaches into the display window - shorten BTN_TONGUE_L"
    for by in BTN_YS:
        ty0, ty1 = by - BTN_TONGUE_W / 2, by + BTN_TONGUE_W / 2
        u = box(tx0, ty0 - slot, z0 - 1, tx1 + slot, ty1 + slot, z0 + LID_T + 1)
        u -= box(tx0 - 1, ty0, z0 - 2, tx1, ty1, z0 + LID_T + 2)
        part -= u
        underside = z0 + LID_T - BTN_TONGUE_T
        part -= box(tx0 - 0.01, ty0, z0 - 3, tx1 + 0.01, ty1, underside)
        pad_bot = Z_PCB_TOP + BTN_H + BTN_GAP
        if pad_bot < underside:
            part += cyl_z(BTN_X, by, pad_bot, underside + 0.01, BTN_PAD_R)
        # small dimple on top so the buttons can be found by touch
        part -= Manifold.sphere(1.6, SEG).translate((BTN_X, by, z0 + LID_T + 1.2))
    # notch right through the lid over the USB-C socket so it can never lift the lid
    # off the display
    assert ny0 - (BTN_YS[0] + BTN_TONGUE_W / 2 + slot) >= 0.8, "USB notch too close to the button tongues"
    part -= box(px1 - END_ZONE, ny0, guide_bot - 1, OUT_L + 1, ny1, z0 + LID_T + 1)
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
