# 🧱 Gehäuse zum 3D-Drucken

Zweiteiliges Gehäuse für das LilyGO T-Display (52 × 26 × 6 mm) mit einem 1100-mAh-LiPo-Akku (47 × 29 × 8 mm) darunter.

| Datei | Teil | Maße (L × B × H) |
|---|---|---|
| [`gehaeuse_unterteil.stl`](gehaeuse_unterteil.stl) | Unterteil für Akku und Platine, Öffnung für USB-C | 57,3 × 32,8 × 16,3 mm |
| [`gehaeuse_deckel.stl`](gehaeuse_deckel.stl) | Schnappdeckel mit Displayfenster und zwei federnden Tasten | 57,3 × 32,8 × 6,4 mm |

## Aufbau

```
   ┌──────────── Deckel: Fenster · Tasten GPIO0/GPIO35 ────────────┐
   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ Display ▓▓▓▓▓▓▓▓▓▓▓▓▓▓       ▲ ▲              │
   │ ═══════════════════ T-Display ═══════════════════════         │ ← USB-C
   │      ░░ ESP32-Modul / Akkustecker (Rückseite) ░░              │
   │      ▒ Schaumstoff-Pad ▒                                      │
   │  Freiraum  ┌─────────────────────── LiPo-Akku ─────────────────┤
   └────────────┴───────────────────────────────────────────────────┘
```

- Der Akku ist breiter als die Platine. Das Unterteil richtet sich nach dem Akku; **Führungsleisten am Deckel** halten die Platine seitlich mittig (0,15 mm Spiel je Seite, `FRAME_CLR`) und drücken sie am Rand nach unten. Sie laufen bis zur Stirnwand durch und reichen 1,5 mm unter die Platine (`GUIDE_DEPTH`). Auf der USB-Seite halten zwei **Anschläge** links und rechts der Buchse die Platinenkante, am anderen Ende eine Querleiste. Für sie ist der Innenraum dort 1,5 mm länger (`END_STOP`). Die Platine ist damit eingefasst und sitzt auch im losen Deckel fest: seitlich mit 0,15 mm Spiel (`FRAME_CLR`), an den Enden mit 0,6 mm (`STOP_CLR`; mit 0,15 mm passte sie der Länge nach nicht hinein, 0,6 mm ist knapp, passt aber). Lässt sie sich nicht einlegen, `FRAME_CLR` bzw. `STOP_CLR` erhöhen.
- Die **USB-C-Buchse** steckt in einer Aussparung der Platine: Sie reicht unten bis zur Platinenunterseite, oben 1,2 mm über die Platinenoberseite und steht 2 mm über die Platinenkante hinaus. Die Taster sind mit ca. 1,8 mm noch etwas höher. Auf den letzten `USB_LEN` + 0,5 mm zur USB-Seite drückt der Deckel deshalb **nicht** auf die Platine und ist innen bis zu 0,6 mm ausgespart; gehalten wird die Platine dort von der Buchse in der Wandöffnung. Über der Buchse selbst ist der Deckel 10 mm breit **ganz ausgeschnitten**, genau so breit wie die Wandöffnung im Unterteil (`USB_W`). So kann die Buchse den Deckel nicht anheben, er liegt plan auf dem Display, und Deckel und Unterteil schließen an der Öffnung bündig ab.
- Auf der Unterseite steht der Projektname **N.I.N.A. Pocket Companion** mit „© 2026 by Kai Linde“, 0,5 mm tief eingraviert und so gespiegelt, dass er nach dem Umdrehen um die Längsachse lesbar ist. Text, Größe und Tiefe stehen in `LABEL`, `LABEL_SIZE` und `LABEL_DEPTH`. Die Schrift kommt aus `matplotlib`; ohne das Paket entsteht das Gehäuse ohne Schriftzug.
- Die **Tasten** sind federnde Zungen im Deckel (14 × 4,5 mm, `BTN_TONGUE_L`/`BTN_TONGUE_W`; das freie Ende reicht `BTN_TONGUE_TIP` = 4,5 mm über die Tastermitte hinaus), die von unten auf 1,0 mm (`BTN_TONGUE_T`) ausgedünnt sind. Je länger und dünner die Zunge, desto leichter lässt sich die Taste drücken. Unter jeder Zunge sitzt ein **Kissen** (Ø 3 mm), das bis auf `BTN_GAP` = 0,15 mm an den Taster heranreicht und so den Leerweg bis zum Klick kurz hält. Wie genau das passt, hängt an `BTN_H`. Kleine Mulden auf der Oberseite machen die Tasten ertastbar.
- Der Deckel **rastet** über zwei 24 mm lange Wülste in eine Nut an den Längsseiten ein. Sie greifen 0,4 mm in die Wand (`SNAP_DEPTH`); hält der Deckel zu fest oder zu locker, diesen Wert in 0,1-mm-Schritten ändern.
- Der Akku ist 5 mm kürzer als die Platine mit Buchse. Dieser **Freiraum** nimmt das Akkukabel auf, das zum Stecker auf der Rückseite der Platine hochgeführt wird.
- Ein 1 mm dickes **Schaumstoff-Pad** zwischen Akku und Platinenrückseite federt den Stapel ab und schützt den Akku.

## Maße

Gemessen sind Platine (52 × 26 × 6 mm, die 52 mm **mit** USB-Buchse), Akku (47 × 29 × 8 mm), die USB-C-Buchse und die Lage der Taster. `FRONT_H`, `BACK_H`, `WIN_CX` und `BTN_H` sind noch **angenommen oder aus Fotos geschätzt**. Ein Probedruck mit den aktuellen Werten passt; wer ein anderes Board oder einen anderen Akku verwendet, sollte sie trotzdem mit dem Messschieber prüfen. Alle Werte stehen oben in [`gehaeuse.py`](gehaeuse.py).

Draufsicht auf das USB-Ende (Display oben, schematisch, nicht maßstäblich). `[+]` ist die **Mitte** eines Tasters, gemessen wird parallel zur Längskante:

```
  TTGO-Ende                              USB-Seite
  ┌─────────────────────────────────────────┐
  │                       Taster [+]        │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ┌───────────────┴─────┐
  │  ▓▓▓▓▓▓ Display ▓▓▓▓▓▓  │        USB-C-Buchse │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  └───────────────┬─────┘
  │                       Taster [+]        │
  └─────────────────────────────────────────┘
                            ┊     ┊         ┊     ┊
                                  ├───────────────┤ BTN_FROM_USB 7,0
                                            ├─────┤ USB_OUT 2,0
                            ├───────────────┤ USB_LEN 7,0
```

- **Buchsenspitze** ist die Stirnfläche der USB-C-Buchse, in die das Kabel gesteckt wird.
- `BTN_FROM_USB` geht von dort bis zur Mitte des Tasters, nicht bis zu seiner Kante. Leichter zu messen: von der Buchsenspitze bis zur fernen Kante des Tasters, davon die halbe Tasterbreite abziehen.
- Probe: `BTN_FROM_USB` − `USB_OUT` ist der Abstand der Tastermitte von der Platinenkante.

| Parameter | Wert | Herkunft | Was messen |
|---|---|---|---|
| `PCB_L` | 50,0 mm | 52 − `USB_OUT` | Platinenlänge **ohne** die überstehende Buchse |
| `USB_OUT` | 2,0 mm | Messung | wie weit die Buchse über die Platinenkante hinausragt |
| `USB_LEN` | 7,0 mm | Messung | wie weit die Buchse von der Platinenkante in die Platine hineinreicht |
| `USB_TOP` | 1,2 mm | Messung | Oberkante der Buchse über der Platinenoberseite |
| `FRONT_H` | 1,8 mm | Annahme | Displayoberfläche über der Platinenoberseite |
| `BACK_H` | 2,6 mm | Annahme | höchstes Bauteil auf der Rückseite (ergibt mit 1,6 mm Platine und `FRONT_H` die 6 mm) |
| `WIN_CX` | 19,5 mm | Foto | Mitte des sichtbaren Displays, gemessen vom Platinenende **ohne** USB (TTGO-Ende) |
| `WIN_W`, `WIN_L` | 16 × 27 mm | – | Fensterausschnitt; sichtbare Fläche ca. 14,9 × 24,9 mm, der Rest ist Spielraum |
| `BTN_FROM_USB` | 7,0 mm | Messung | Mitte der Taster, gemessen von der **Spitze der USB-Buchse** |
| `BTN_FROM_SIDE` | 4,0 mm | Messung | Mitte der Taster, gemessen von der Längskante |
| `BTN_H` | 1,8 mm | Foto | Oberkante der Taster über der Platinenoberseite |

Ist die Buchse oder sind die Taster höher, als der Deckel aufnehmen kann, bricht das Skript mit einer Meldung ab, statt ein unpassendes Gehäuse zu erzeugen.

Danach neu erzeugen:

```bash
pip install manifold3d numpy matplotlib
python3 hardware/gehaeuse/gehaeuse.py
```

Für sehr neue Python-Versionen gibt es oft noch kein fertiges `manifold3d`-Paket, und der Build aus dem Quellcode scheitert (z. B. an fehlendem `tbb`). Dann mit einem älteren Python eine eigene Umgebung anlegen, z. B. mit dem System-Python von macOS:

```bash
/usr/bin/python3 -m venv .venv-gehaeuse
.venv-gehaeuse/bin/pip install --only-binary=:all: manifold3d numpy matplotlib
.venv-gehaeuse/bin/python hardware/gehaeuse/gehaeuse.py
```

> [!TIP]
> Erst nur den Deckel drucken (ca. 15 min) und auf die Platine legen: Sitzen Fenster und Tasten richtig, passt der Rest auch.

## Druckeinstellungen

| | Empfehlung |
|---|---|
| Material | PETG oder PLA (PETG federt bei den Tasten besser) |
| Schichthöhe | 0,2 mm (Deckel gern 0,12–0,16 mm) |
| Wände | 3 Perimeter |
| Füllung | 20 % |
| Stützstrukturen | keine nötig |
| Ausrichtung | Unterteil mit dem Boden aufs Bett. Der Deckel liegt in der STL schon richtig: Oberseite aufs Bett. |

## Montage

1. Akku mit doppelseitigem Klebeband auf den Boden kleben, an die Wand mit der USB-Öffnung geschoben. Das Kabel zeigt zum anderen Ende, wo 5 mm frei bleiben.
2. Ein ca. 1 mm dickes Schaumstoff-Pad auf den Akku legen, das Kabel im Freiraum nach oben führen und an der Platinenrückseite einstecken.
3. Platine mit dem Display nach oben einlegen, USB-C in die Öffnung.
4. Deckel aufdrücken, bis er einrastet.

## Hinweise

- Das T-Display hat **keinen Ein/Aus-Schalter**. Die Firmware schickt es nach 10 Minuten ohne Tastendruck oder per langem Druck auf die rechte Taste in den Deep Sleep, ganz stromlos ist es aber auch dann nicht. Für längere Pausen hilft ein Schiebeschalter im Akkukabel. Mit `SWITCH = True` bekommt das Unterteil dafür eine Öffnung in der Längswand; Lage und Größe sind Parameter.
- LiPo-Akkus nicht quetschen: Wenn der Deckel nur schwer schließt, lieber `BAT_T` oder `GAP` erhöhen.
