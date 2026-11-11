# 🧱 Gehäuse zum 3D-Drucken

Zweiteiliges Gehäuse für das LilyGO T-Display (52 × 26 × 6 mm) mit einem 1100-mAh-LiPo-Akku (47 × 29 × 8 mm) darunter.

| Datei | Teil | Maße (L × B × H) |
|---|---|---|
| [`gehaeuse_unterteil.stl`](gehaeuse_unterteil.stl) | Unterteil für Akku und Platine, Öffnung für USB-C | 55,8 × 32,8 × 16,3 mm |
| [`gehaeuse_deckel.stl`](gehaeuse_deckel.stl) | Schnappdeckel mit Displayfenster und zwei federnden Tasten | 55,8 × 32,8 × 4,6 mm |

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

- Der Akku ist breiter als die Platine. Das Unterteil richtet sich nach dem Akku; **Führungsleisten am Deckel** halten die Platine seitlich mittig (±0,3 mm Spiel) und drücken sie am Rand nach unten.
- Die **Tasten** sind federnde Zungen im Deckel mit einem Stößel auf der Unterseite. Kleine Mulden auf der Oberseite machen sie ertastbar.
- Der Deckel **rastet** über zwei Nasen in eine Nut an den Längsseiten ein.
- Der Akku ist 5 mm kürzer als die Platine. Dieser **Freiraum** nimmt das Akkukabel auf, das zum Stecker auf der Rückseite der Platine hochgeführt wird.
- Ein 1 mm dickes **Schaumstoff-Pad** zwischen Akku und Platinenrückseite federt den Stapel ab und schützt den Akku.

## Maße

Gemessen sind Platine (52 × 26 × 6 mm) und Akku (47 × 29 × 8 mm). Diese Werte sind noch **angenommen** und sollten vor dem Druck geprüft werden; sie stehen oben in [`gehaeuse.py`](gehaeuse.py):

| Parameter | Annahme | Was messen |
|---|---|---|
| `FRONT_H` | 1,8 mm | Displayoberfläche über der Platinenoberseite |
| `BACK_H` | 2,6 mm | höchstes Bauteil auf der Rückseite (ergibt mit 1,6 mm Platine und `FRONT_H` die 6 mm) |
| `WIN_CX` | 21,0 mm | Mitte des sichtbaren Displays, gemessen vom Platinenende **ohne** USB |
| `BTN_FROM_USB`, `BTN_FROM_SIDE` | 4,5 / 4,0 mm | Mitte der Taster, gemessen von USB-Kante bzw. Längskante |
| `BTN_H` | 1,5 mm | Oberkante der Taster über der Platine |

Danach neu erzeugen:

```bash
pip install manifold3d numpy
python3 hardware/gehaeuse/gehaeuse.py
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

- Das T-Display hat **keinen Ein/Aus-Schalter**, der Akku wird also ständig entladen. Ein Schiebeschalter im Akkukabel hilft. Mit `SWITCH = True` bekommt das Unterteil dafür eine Öffnung in der Längswand; Lage und Größe sind Parameter.
- LiPo-Akkus nicht quetschen: Wenn der Deckel nur schwer schließt, lieber `BAT_T` oder `GAP` erhöhen.
