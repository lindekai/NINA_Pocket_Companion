#!/usr/bin/env python3
"""
Renders pixel-accurate mockups of the N.I.N.A. Pocket Companion screens.

The drawing code of the sketch is mirrored 1:1 (coordinates, colors, the
classic 5x7 Adafruit GFX font incl. line wrapping) with demo data, so the
images show what the 135x240 display actually looks like.

Usage:
  python3 tools/render_mockups.py [path/to/glcdfont.c]

The font is read from the installed Adafruit GFX Library
(default: ~/Documents/Arduino/libraries/Adafruit_GFX_Library/glcdfont.c).
Requires Pillow. Output goes to docs/images/.

Copyright (c) 2026 Kai Linde - MIT License, see LICENSE.
"""
import math
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
W, H = 135, 240


def rgb565(c):
    r, g, b = (c >> 11) & 0x1F, (c >> 5) & 0x3F, c & 0x1F
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31)


BG, PANEL, CYAN, GREEN = 0x0006, 0x084D, 0x07FF, 0x07E0
YELLOW, WHITE, GRAY, RED = 0xFFE0, 0xFFFF, 0xA514, 0xF800
LINE, GRID = 0x19CA, 0x18E3
DEG = "\xf7"  # degree sign in the classic GFX font (char 247)


def load_font(path):
    src = Path(path).expanduser().read_text()
    body = src[src.index("font[]"):]
    body = body[body.index("{") + 1:body.index("};")]
    body = re.sub(r"//.*", "", body)
    return [int(v, 16) for v in re.findall(r"0x[0-9A-Fa-f]{2}", body)]


class Screen:
    """Minimal Adafruit_GFX subset with identical rasterization."""

    def __init__(self, font):
        self.font = font
        self.img = Image.new("RGB", (W, H))
        self.px = self.img.load()
        self.cx = self.cy = 0
        self.size = 1
        self.fg = self.bg = WHITE

    def pixel(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[x, y] = rgb565(c)

    def fill_rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.pixel(xx, yy, c)

    def fill_screen(self, c):
        self.fill_rect(0, 0, W, H, c)

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill_rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0, x1, y1 = y0, x0, y1, x1
        if x0 > x1:
            x0, x1, y0, y1 = x1, x0, y1, y0
        dx, dy = x1 - x0, abs(y1 - y0)
        err, ystep = dx // 2, 1 if y0 < y1 else -1
        while x0 <= x1:
            self.pixel(y0, x0, c) if steep else self.pixel(x0, y0, c)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    def _circle_helper(self, x0, y0, r, corners, delta, c):
        f, ddx, ddy, x, y = 1 - r, 1, -2 * r, 0, r
        px, py = x, y
        delta += 1
        while x < y:
            if f >= 0:
                y -= 1
                ddy += 2
                f += ddy
            x += 1
            ddx += 2
            f += ddx
            if x < y + 1:
                if corners & 1:
                    self.vline(x0 + x, y0 - y, 2 * y + delta, c)
                if corners & 2:
                    self.vline(x0 - x, y0 - y, 2 * y + delta, c)
            if y != py:
                if corners & 1:
                    self.vline(x0 + py, y0 - px, 2 * px + delta, c)
                if corners & 2:
                    self.vline(x0 - py, y0 - px, 2 * px + delta, c)
                py = y
            px = x

    def fill_circle(self, x0, y0, r, c):
        self.vline(x0, y0 - r, 2 * r + 1, c)
        self._circle_helper(x0, y0, r, 3, 0, c)

    def fill_round_rect(self, x, y, w, h, r, c):
        r = min(r, min(w, h) // 2)
        self.fill_rect(x + r, y, w - 2 * r, h, c)
        self._circle_helper(x + w - r - 1, y + r, r, 1, h - 2 * r - 1, c)
        self._circle_helper(x + r, y + r, r, 2, h - 2 * r - 1, c)

    def draw_char(self, x, y, ch, fg, bg, s):
        code = ord(ch)
        if code >= 176:  # Adafruit GFX default (non-CP437) glyph offset
            code += 1
        base = code * 5
        for i in range(6):
            bits = self.font[base + i] if i < 5 else 0
            for j in range(8):
                c = fg if bits & 1 else bg
                self.fill_rect(x + i * s, y + j * s, s, s, c)
                bits >>= 1

    def print(self, text):
        for ch in text:
            if ch == "\n":
                self.cx, self.cy = 0, self.cy + 8 * self.size
                continue
            if self.cx + 6 * self.size > W:  # Adafruit GFX wraps at the right edge
                self.cx, self.cy = 0, self.cy + 8 * self.size
            self.draw_char(self.cx, self.cy, ch, self.fg, self.bg, self.size)
            self.cx += 6 * self.size


# ---- demo data (same as demoData() in the sketch) ----
D = dict(api=True, camera=True, mount=True, guider=True, wheel=True, focuser=True,
         running=True, parked=False, temp=-9.8, target_temp=-10.0, rms=0.52,
         alt=62.3, az=314.8, ra=23.345, dec=61.216, filter="Ha 7nm",
         target="NGC 7635", sequence="Bubble Nebula Ha", camera_name="ToupTek",
         completed=42, total=120, exposure=300)
SITE_LAT, SITE_LON = 52.52, 13.40
WIFI_IP, NINA_IP = "192.168.1.42", "192.168.1.20"


def cut(s, n):
    return s[:n - 2] + ".." if len(s) > n else s


def yes_no(v):
    return "OK" if v else "AUS"


class Pages:
    def __init__(self, scr):
        self.s = scr

    def text(self, x, y, s, c=WHITE, size=1, bg=BG):
        self.s.fg, self.s.bg, self.s.size = c, bg, size
        self.s.cx, self.s.cy = x, y
        self.s.print(s)

    def sep(self, y):
        self.s.hline(5, y, 125, LINE)

    def header(self, title):
        self.s.fill_screen(BG)
        self.s.fill_rect(0, 0, W, 23, PANEL)
        self.text(5, 4, cut(title, 9), CYAN, 2, PANEL)
        self.s.fill_circle(126, 11, 3, GREEN)
        self.sep(24)

    def footer(self, left="WEITER", right="MENU"):
        self.sep(216)
        self.text(6, 224, left, GRAY)
        self.text(77, 224, right, GRAY)

    def kv(self, y, label, value, c=WHITE):
        self.text(6, y, cut(label, 20), GRAY)
        self.text(6, y + 11, cut(value, 10), c, 2)
        self.sep(y + 30)

    def row(self, y, label, val, c=WHITE):
        val = cut(val, 6)
        self.text(6, y + 5, cut(label, 12), GRAY)
        self.text(129 - 12 * len(val), y + 1, val, c, 2)
        self.sep(y + 19)

    def home(self, cursor=0):
        self.header("N.I.N.A.")
        names = ["System", "Session", "Kamera", "Guiding", "Filter", "Objekt", "Hoehe", "Info"]
        for i, n in enumerate(names):
            y = 29 + i * 20
            sel = i == cursor
            if sel:
                self.s.fill_round_rect(3, y - 2, 129, 19, 4, PANEL)
            self.text(10, y, n, YELLOW if sel else WHITE, 2, PANEL if sel else BG)
        self.text(6, 195, "N.I.N.A. ONLINE", GREEN)
        self.footer("WEITER", "OEFFNEN")

    def system(self):
        self.header("SYSTEM")
        self.text(6, 30, "ONLINE", GREEN, 2)
        self.text(6, 50, "Session: AKTIV", YELLOW)
        self.sep(63)
        self.row(66, "Kamera", "OK", GREEN)
        self.row(87, "Montierung", "OK")
        self.row(108, "Guiding", "OK", GREEN)
        self.row(129, "Filterrad", "OK", GREEN)
        self.row(150, "Fokussierer", "OK", GREEN)
        self.row(171, "Filter", D["filter"], CYAN)
        self.row(192, "Temp", f"{D['temp']:.1f}{DEG}", CYAN)
        self.footer()

    def session(self):
        self.header("SESSION")
        self.text(6, 30, "AKTIV", GREEN, 2)
        self.kv(52, "Objekt", D["target"], CYAN)
        self.kv(85, "Sequenz", D["sequence"])
        self.kv(118, "Frames", f"{D['completed']}/{D['total']}")
        self.kv(151, "Belichtung", f"{D['exposure']} s")
        self.footer()

    def camera(self):
        self.header("KAMERA")
        self.text(6, 30, cut(D["camera_name"], 21), CYAN)
        self.kv(44, "Verbindung", "OK", GREEN)
        self.kv(77, "Ist-Temperatur", f"{D['temp']:.1f}{DEG}C", CYAN)
        self.kv(110, "Soll-Temperatur", f"{D['target_temp']:.1f}{DEG}C")
        self.footer()

    def guiding(self):
        self.header("GUIDING")
        self.kv(32, "Guider", "OK", GREEN)
        self.kv(65, "RMS gesamt", f"{D['rms']:.2f}\"", GREEN)
        self.text(6, 110, "Nur N.I.N.A. Daten", GRAY)
        self.footer()

    def filter(self):
        self.header("FILTER")
        self.kv(32, "Verbindung", "OK", GREEN)
        self.kv(65, "Aktiver Filter", D["filter"], CYAN)
        self.text(6, 110, "Nur Anzeige", GRAY)
        self.footer()

    def object(self):
        self.header("OBJEKT")
        self.kv(30, "Ziel", D["target"], CYAN)
        self.kv(63, "Hoehe (Montierung)", f"{D['alt']:.1f}{DEG}")
        self.kv(96, "Azimut", f"{D['az']:.1f}{DEG}")
        self.kv(129, "RA", f"{D['ra']:.2f} h")
        self.kv(162, "Dec", f"{D['dec']:.1f}{DEG}")
        self.footer()

    def altitude(self, now):
        self.header("HOEHE")
        self.text(6, 28, cut(D["target"], 10), CYAN, 2)
        cur = altitude_at(now, D["ra"], D["dec"])
        self.text(6, 46, f"{cur:.1f}{DEG}", GREEN, 2)
        self.text(76, 51, "aktuell", GRAY)
        x0, x1, y0, y1 = 18, 130, 76, 184
        s = self.s
        s.line(x0, y0, x0, y1, GRAY)
        s.line(x0, y1, x1, y1, GRAY)
        for a in range(0, 91, 30):
            y = y1 - (a * (y1 - y0)) // 90
            s.hline(x0, y, x1 - x0, GRID)
            self.text(0, y - 4, str(a), GRAY)
        start = now - 4 * 3600
        old_x = old_y = transit_x = -1
        prev_ha = 0.0
        for px in range(x0, x1 + 1):
            t = start + int((px - x0) * 8.0 * 3600.0 / (x1 - x0))
            alt = altitude_at(t, D["ra"], D["dec"])
            yy = y1 - max(0, min(90, round(alt))) * (y1 - y0) // 90
            if old_x >= 0:
                s.line(old_x, old_y, px, yy, CYAN)
            ha = hour_angle(t, D["ra"])
            if old_x >= 0 and prev_ha < 0 <= ha:
                transit_x = px
            prev_ha, old_x, old_y = ha, px, yy
        if transit_x >= 0:
            for y in range(y0, y1 + 1, 5):
                s.line(transit_x, y, transit_x, y + 2, YELLOW)
            self.text(max(x0, min(transit_x - 9, W - 18)), 67, "MER", YELLOW)
        cx = (x0 + x1) // 2
        cy = y1 - max(0, min(90, round(cur))) * (y1 - y0) // 90
        s.fill_circle(cx, cy, 3, GREEN)
        s.vline(cx, y0, y1 - y0, GREEN)
        self.text(7, 193, "-4h", GRAY)
        self.text(60, 193, "JETZT", GREEN)
        self.text(108, 193, "+4h", GRAY)
        self.text(5, 205, "MER=Transit,kein Flip", YELLOW)
        self.footer("WEITER", "MENU")

    def about(self):
        self.header("INFO")
        self.text(6, 30, "N.I.N.A. POCKET", CYAN)
        self.text(6, 43, "Companion v0.1", WHITE)
        self.text(6, 64, "READ-ONLY", GREEN, 2)
        self.text(6, 99, "WiFi:", GRAY)
        self.text(6, 112, WIFI_IP)
        self.text(6, 137, "N.I.N.A. PC (auto):", GRAY)
        self.text(6, 150, NINA_IP)
        self.text(6, 171, "Port: 1888")
        self.text(6, 190, "LIVE", GREEN, 2)
        self.footer()


def hour_angle(u, ra_hours):
    jd = u / 86400.0 + 2440587.5
    t = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t - t ** 3 / 38710000.0
    ha = (gmst + SITE_LON - ra_hours * 15.0) % 360.0
    return ha - 360.0 if ha > 180.0 else ha


def altitude_at(u, ra_hours, dec_deg):
    r = math.pi / 180
    ha, lat, dec = hour_angle(u, ra_hours) * r, SITE_LAT * r, dec_deg * r
    v = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(ha)
    return math.asin(max(-1.0, min(1.0, v))) / r


def demo_time():
    """An autumn evening ~1.5 h before the target crosses the meridian."""
    t = int(datetime(2026, 10, 15, 18, 0, tzinfo=timezone.utc).timestamp())
    while not (hour_angle(t, D["ra"]) < 0 <= hour_angle(t + 60, D["ra"])):
        t += 60
    return t - 90 * 60


# ---------------- presentation graphics ----------------
def font(size, bold=False):
    for path, idx in (("/System/Library/Fonts/Avenir Next.ttc", 2 if bold else 0),
                      ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0)):
        try:
            return ImageFont.truetype(path, size, index=idx)
        except OSError:
            pass
    return ImageFont.load_default(size)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return m


def device(screen, scale=3):
    """Stylized LilyGO T-Display (portrait) with the rendered screen."""
    sw, sh = W * scale, H * scale
    glass = 22 * scale // 3
    pcb_side, pcb_top, pcb_bottom = 26 * scale // 3, 30 * scale // 3, 78 * scale // 3
    gw, gh = sw + 2 * glass, sh + 2 * glass + 18 * scale // 3
    bw, bh = gw + 2 * pcb_side, gh + pcb_top + pcb_bottom
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # PCB
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), 18 * scale // 3, fill=(22, 24, 30), outline=(52, 56, 66), width=2)
    for hx in (14 * scale // 3, bw - 14 * scale // 3):
        d.ellipse((hx - 6, 14 * scale // 3 - 6, hx + 6, 14 * scale // 3 + 6), fill=(8, 9, 12), outline=(150, 128, 70), width=2)
    # display module with glass
    gx, gy = pcb_side, pcb_top
    d.rounded_rectangle((gx, gy, gx + gw, gy + gh), 6 * scale // 3, fill=(6, 7, 10), outline=(40, 44, 52), width=2)
    sx, sy = gx + glass, gy + glass
    img.paste(screen.resize((sw, sh), Image.NEAREST), (sx, sy))
    # glass reflection
    sheen = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).polygon([(0, 0), (gw * 0.55, 0), (0, gh * 0.42)], fill=(255, 255, 255, 14))
    img.alpha_composite(sheen, (gx, gy))
    # buttons and USB-C
    by = gy + gh + 22 * scale // 3
    small = font(9 * scale // 3, bold=True)
    for bx, label in ((bw // 4, "GPIO0"), (bw * 3 // 4, "GPIO35")):
        d.rounded_rectangle((bx - 18 * scale // 3, by, bx + 18 * scale // 3, by + 16 * scale // 3), 4,
                            fill=(190, 192, 198), outline=(110, 112, 120), width=2)
        d.rounded_rectangle((bx - 10 * scale // 3, by + 4 * scale // 3, bx + 10 * scale // 3, by + 12 * scale // 3), 3,
                            fill=(30, 30, 34))
        d.text((bx, by + 30 * scale // 3), label, font=small, fill=(200, 204, 214), anchor="mm")
    ux = bw // 2
    d.rounded_rectangle((ux - 14 * scale // 3, bh - 9 * scale // 3, ux + 14 * scale // 3, bh + 4), 5,
                        fill=(170, 172, 180), outline=(90, 92, 100), width=2)
    return img


def with_shadow(img, blur=28, offset=(0, 26), alpha=150):
    pad = blur * 3
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, alpha))
    sh.putalpha(Image.eval(img.getchannel("A"), lambda a: a * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


def night_sky(size, seed=7):
    w, h = size
    rnd = random.Random(seed)
    sky = Image.new("RGB", size)
    d = ImageDraw.Draw(sky)
    top, bottom = (4, 8, 22), (14, 22, 48)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    # faint milky way band
    band = Image.new("L", size, 0)
    bd = ImageDraw.Draw(band)
    for _ in range(900):
        x = rnd.uniform(-0.1, 1.1) * w
        y = h * 0.95 - x * 0.55 + rnd.gauss(0, h * 0.09)
        r = rnd.uniform(10, 60)
        bd.ellipse((x - r, y - r, x + r, y + r), fill=rnd.randint(4, 12))
    band = band.filter(ImageFilter.GaussianBlur(40))
    glow = Image.new("RGB", size, (120, 140, 200))
    sky = Image.composite(glow, sky, band.point(lambda v: min(255, v * 3)))
    d = ImageDraw.Draw(sky)
    for _ in range(int(w * h / 900)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        b = int(rnd.random() ** 3 * 220) + 25
        tint = rnd.choice([(1, 1, 1), (0.85, 0.92, 1), (1, 0.95, 0.85)])
        c = tuple(int(b * t) for t in tint)
        if rnd.random() < 0.015:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=c)
        else:
            d.point((x, y), fill=c)
    return sky.convert("RGBA")


def hero(screens, author):
    w, h = 2000, 1040
    img = night_sky((w, h))
    d = ImageDraw.Draw(img)
    x = 110
    d.text((x, 210), "N.I.N.A.", font=font(64, True), fill=(92, 225, 255))
    d.text((x, 285), "Pocket Companion", font=font(84, True), fill=(245, 247, 252))
    d.text((x, 400), "Der Status deines Astro-Setups –", font=font(36), fill=(190, 200, 220))
    d.text((x, 446), "immer im Blick, in der Hosentasche.", font=font(36), fill=(190, 200, 220))
    chips = ["ESP32 · T-Display", "Read-only", "Auto-Discovery", "Höhenkurve", "Arduino IDE"]
    cy, cx = 545, x
    cf = font(26, True)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for c in chips:
        tw = d.textlength(c, font=cf)
        if cx + tw + 40 > 780:
            cx, cy = x, cy + 66
        od.rounded_rectangle((cx, cy, cx + tw + 40, cy + 50), 25, fill=(92, 225, 255, 26),
                             outline=(92, 225, 255, 200), width=2)
        od.text((cx + 20, cy + 25), c, font=cf, fill=(220, 240, 255, 255), anchor="lm")
        cx += tw + 56
    img.alpha_composite(overlay)
    d.text((x, h - 110), f"von {author}", font=font(26), fill=(150, 160, 185))

    # side devices first, the centre one is drawn on top
    layout = [("session", -8, 1180, 170), ("system", 8, 1800, 170), ("altitude", 0, 1490, 70)]
    for name, angle, cxm, top in layout:
        dev = device(screens[name])
        if name != "altitude":
            dev = dev.resize((int(dev.width * 0.8), int(dev.height * 0.8)), Image.LANCZOS)
        dev = dev.rotate(angle, resample=Image.BICUBIC, expand=True)
        dev = with_shadow(dev)
        img.alpha_composite(dev, (cxm - dev.width // 2, top - 80))
    return img.convert("RGB")


def gallery_tile(screen, label):
    scale = 2
    pad, label_h = 24, 56
    w, h = W * scale + 2 * pad, H * scale + 2 * pad + label_h
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=(13, 16, 26), outline=(44, 52, 72), width=2)
    scr = screen.resize((W * scale, H * scale), Image.NEAREST).convert("RGBA")
    scr.putalpha(rounded_mask(scr.size, 6))
    tile.alpha_composite(scr, (pad, pad))
    d.text((w // 2, h - label_h // 2 - 6), label, font=font(24, True), fill=(225, 232, 245), anchor="mm")
    return tile


def main():
    font_path = sys.argv[1] if len(sys.argv) > 1 else \
        "~/Documents/Arduino/libraries/Adafruit_GFX_Library/glcdfont.c"
    glyphs = load_font(font_path)
    now = demo_time()
    pages = [("home", "Hauptmenü", lambda p: p.home()),
             ("system", "Systemstatus", lambda p: p.system()),
             ("session", "Session", lambda p: p.session()),
             ("camera", "Kamera", lambda p: p.camera()),
             ("guiding", "Guiding", lambda p: p.guiding()),
             ("filter", "Filterrad", lambda p: p.filter()),
             ("object", "Objekt", lambda p: p.object()),
             ("altitude", "Höhenverlauf", lambda p: p.altitude(now)),
             ("about", "Info", lambda p: p.about())]
    (OUT / "screens").mkdir(parents=True, exist_ok=True)
    screens = {}
    for key, label, draw in pages:
        scr = Screen(glyphs)
        draw(Pages(scr))
        screens[key] = scr.img
        gallery_tile(scr.img, label).save(OUT / "screens" / f"{key}.png", optimize=True)
        print("screen", key)
    author = sys.argv[2] if len(sys.argv) > 2 else "Kai Linde"
    hero(screens, author).save(OUT / "hero.png", optimize=True)
    with_shadow(device(screens["home"])).save(OUT / "device-home.png", optimize=True)
    print("hero.png, device-home.png")


if __name__ == "__main__":
    main()
