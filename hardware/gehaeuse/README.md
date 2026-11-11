# 🧱 Gehäuse zum 3D-Drucken

Zweiteiliges Gehäuse für das LilyGO T-Display mit einem LiPo-Akku gleicher Grundfläche (z. B. 1100 mAh, ca. 50 × 25 × 10 mm) darunter.

| Datei | Teil | Maße (L × B × H) |
|---|---|---|
| [`gehaeuse_unterteil.stl`](gehaeuse_unterteil.stl) | Unterteil für Akku und Platine, Öffnung für USB-C | 57,8 × 28,8 × 19,8 mm |
| [`gehaeuse_deckel.stl`](gehaeuse_deckel.stl) | Schnappdeckel mit Displayfenster und zwei federnden Tasten | 57,8 × 28,8 × 5,9 mm |

## Aufbau

```
   ┌──────────── Deckel: Fenster · Tasten GPIO0/GPIO35 ────────────┐
   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ Display ▓▓▓▓▓▓▓▓▓▓▓▓▓▓       ▲ ▲              │
   │ ═══════════════════ T-Display ═══════════════════════         │ ← USB-C
   │      ░░ ESP32-Modul / Akkustecker (Rückseite) ░░              │
   │ ┌──────────────────── LiPo-Akku ────────────────────┐         │
   └─┴───────────────────────────────────────────────────┴─────────┘
     ↑ Kabelfach
```

- Der **Deckel** drückt die Platine am Rand nach unten. Ein Anschlag am hinteren Ende hält sie an der USB-Seite.
- Die **Tasten** sind federnde Zungen im Deckel mit einem Stößel auf der Unterseite. Kleine Mulden auf der Oberseite machen sie ertastbar.
- Der Deckel **rastet** über zwei Nasen in eine Nut an den Längsseiten ein.
- Das **Kabelfach** am hinteren Ende nimmt das Akkukabel auf, das zum Stecker auf der Rückseite der Platine hochgeführt wird.

## ⚠️ Vor dem Drucken nachmessen

Ich habe typische Maße angenommen. Bitte mit dem Messschieber prüfen und oben in [`gehaeuse.py`](gehaeuse.py) anpassen:

| Parameter | Annahme | Was messen |
|---|---|---|
| `PCB_L`, `PCB_W` | 51,5 × 25,0 mm | Platine außen |
| `BACK_H` | 3,5 mm | höchstes Bauteil auf der Rückseite (ESP32-Modul, Akkustecker) |
| `FRONT_H` | 3,0 mm | Displayoberfläche über der Platinenoberseite |
| `WIN_CX` | 21,0 mm | Mitte des sichtbaren Displays, gemessen vom Platinenende **ohne** USB |
| `BTN_FROM_USB`, `BTN_FROM_SIDE` | 4,5 / 4,0 mm | Mitte der Taster, gemessen von USB-Kante bzw. Längskante |
| `BTN_H` | 1,8 mm | Oberkante der Taster über der Platine |
| `BAT_L`, `BAT_W`, `BAT_T` | 50 × 25 × 10 mm | Akku inkl. Schutzschaltung |

Danach neu erzeugen:

```bash
pip install manifold3d numpy
python3 hardware/gehaeuse/gehaeuse.py
```

> [!TIP]
> Erst nur den Deckel drucken (ca. 20 min) und auf die Platine legen: Sitzen Fenster und Tasten richtig, passt der Rest auch.

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

1. Akku mit doppelseitigem Schaumklebeband auf den Boden kleben. Das Kabel zeigt zum Ende **ohne** USB-Öffnung.
2. Kabel im Kabelfach nach oben führen und an der Platinenrückseite einstecken.
3. Platine mit dem Display nach oben einlegen, USB-C in die Öffnung.
4. Deckel aufdrücken, bis er einrastet.

## Hinweise

- Das T-Display hat **keinen Ein/Aus-Schalter**, der Akku wird also ständig entladen. Ein Schiebeschalter im Akkukabel hilft. Mit `SWITCH = True` bekommt das Unterteil dafür eine Öffnung in der Längswand; Lage und Größe sind Parameter.
- LiPo-Akkus nicht quetschen: Wenn der Deckel nur schwer schließt, lieber `BAT_T` oder `GAP` erhöhen.
