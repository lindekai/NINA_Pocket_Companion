# Nachtmodus und Helligkeitssteuerung (v0.3) – Design

Datum: 2026-11-12
Status: freigegeben

## Ziel

Am Teleskop soll das Display die Dunkeladaption der Augen nicht stören. Dafür gibt es:

1. einen **Nachtmodus**: rote Darstellung auf Schwarz mit eigener, niedriger Helligkeit, umschaltbar über beide Tasten gleichzeitig
2. eine **Helligkeitssteuerung** in 5 Stufen, getrennt für Tag- und Nachtmodus, am Gerät einstellbar und dauerhaft gespeichert

## Bedienung

| Geste | Wirkung |
|---|---|
| kurz links (`BTN_NEXT`, GPIO0) | wie bisher: WEITER (Menücursor bzw. nächste Seite) |
| kurz rechts (`BTN_PAGE`, GPIO35) | wie bisher: MENU (Seite öffnen bzw. zurück zum Hauptmenü) |
| beide gleichzeitig | Nachtmodus an/aus |
| links lang (≥ 800 ms) | Helligkeit des aktiven Modus eine Stufe weiter: 1→2→3→4→5→1 |
| beliebige Geste bei ausgeschaltetem Display | weckt nur das Display, keine weitere Wirkung |

Jede Geste setzt `lastActivity` zurück (Display-Timeout).

### Gestenerkennung

Bisher löst eine Taste beim Drücken aus. Neu: eine Zustandsmaschine über beide Tasten, die bei jedem `loop()` den entprellten Zustand beider Tasten auswertet (Entprellung wie bisher: 40 ms).

- **Gestenbeginn:** Die erste Taste wird gedrückt, während keine gedrückt ist. Der Zeitpunkt wird gemerkt.
- **Beide:** Sind beide Tasten gleichzeitig gedrückt und die Geste ist noch nicht ausgelöst, wird sofort der Nachtmodus umgeschaltet und die Geste als *ausgelöst* markiert.
- **Lang links:** Ist nur die linke Taste seit ≥ `LONG_PRESS_MS` (800) gedrückt und die Geste noch nicht ausgelöst, wird die Helligkeit umgestellt und die Geste als *ausgelöst* markiert.
- **Kurz:** Werden alle Tasten losgelassen und die Geste wurde nicht ausgelöst, zählt sie als kurzer Druck der Taste, die die Geste begonnen hat.
- **Gestenende:** Sind beide Tasten losgelassen, wird der Zustand zurückgesetzt. Loslassen nach einer ausgelösten Geste bewirkt nichts.
- **Display aus:** Der Gestenbeginn weckt das Display (`wakeDisplay()`), und die Geste wird als *ausgelöst* markiert. Dadurch hat sie keine weitere Wirkung.

Folge: Kurzes Drücken wirkt erst beim Loslassen. Das ist bewusst so, denn nur dann ist eine Unterscheidung von „beide“ und „lang“ möglich.

`processButton()` wird durch diese Logik ersetzt (z. B. `readButtons()` + `handleGesture()`). Die Navigationslogik (Cursor/Seite) bleibt unverändert und wandert in eine eigene Funktion `shortPress(bool nextButton)`.

## Helligkeit

- Hintergrundbeleuchtung GPIO4 (`TFT_BL`) per `analogWrite()` (PWM). Das funktioniert mit ESP32-Arduino-Core 2.x und 3.x. Die PWM-Frequenz ist der Core-Standard.
- Stufentabellen (Werte 0–255):
  - Tag: `{20, 50, 100, 170, 255}`, Standard Stufe 5
  - Nacht: `{1, 3, 6, 12, 24}`, Standard Stufe 2
- Neue Funktion `applyBacklight()` schreibt den Wert der aktiven Stufe (bzw. 0, wenn das Display aus ist). `sleepDisplay()`, `wakeDisplay()` und `setup()` verwenden sie statt `digitalWrite(TFT_BL, …)`. In `wakeDisplay()` bleibt die Reihenfolge erhalten: zuerst rendern, dann Beleuchtung an.
- **Rückmeldung:** Nach dem Verstellen erscheint für 1,5 s in der Fußzeile anstelle der Tastenbeschriftung `HELL` mit 5 Kästchen, davon so viele gefüllt wie die aktuelle Stufe. Umgesetzt wird das über `overlayUntil` (millis). `footer()` zeichnet den Balken, solange die Zeit nicht abgelaufen ist. `loop()` rendert nach Ablauf einmal neu.

## Nachtmodus

- Zustand `nightMode` (bool).
- **Rotfärbung:** In `render()` wird vor `tft.drawRGBBitmap()` jeder Pixel des Canvas-Puffers umgerechnet, sofern der Nachtmodus aktiv ist:
  - RGB565 → r5, g6, b5 → Helligkeit `l = (r5*2*77 + g6*150 + b5*2*29) >> 8` (Bereich 0–63)
  - neuer Pixel: nur Rotkanal, `r = l >> 1` (0–31), Grün und Blau 0
  - Die Umrechnung erfolgt direkt im Puffer. Das ist zulässig, weil jede Seite beim nächsten `render()` vollständig neu gezeichnet wird (`header()` → `fillScreen`).
- Der Hintergrund `BG` (0x0006) wird dadurch nahezu schwarz. Gewollt ist das.
- Gibt es keinen Canvas (Notfallpfad, direkte Zeichnung auf das TFT), entfällt die Rotfärbung. Der Nachtmodus dimmt dann nur.
- Beim Umschalten: `applyBacklight()`, `dirty = true`, speichern.
- Ein Aufwecken durch Ereignisse (`WAKE_ON_EVENTS`) verwendet den aktiven Modus und dessen Helligkeit.

## Speichern

- Vorhandenes `Preferences prefs`, Namespace `"nina"`. Schlüssel: `"night"` (bool), `"briDay"` (uint8, 1–5), `"briNight"` (uint8, 1–5).
- `prefs.begin("nina", false)` wird an den Anfang von `setup()` verschoben, also vor das Lesen der Einstellungen. Bisher wurde es nur im Auto-Discovery-Pfad aufgerufen. Der doppelte Aufruf dort entfällt.
- Ungültige gespeicherte Werte (außerhalb 1–5) werden durch den Standard ersetzt.
- Geschrieben wird nur bei Änderungen durch eine Geste.
- `setup()` setzt nach dem Laden die Beleuchtung über `applyBacklight()` (statt `HIGH`), damit der Startbildschirm im Nachtmodus nicht voll hell aufleuchtet. Die Rotfärbung gilt erst ab dem ersten `render()`, wenn der Canvas aktiv ist. Die Textzeilen beim Start zeichnet `setup()` direkt auf das TFT, sie bleiben daher farbig, aber gedimmt.

## Seite Info

Unter „Display aus“ (y = 167/179) kommen zwei Zeilen hinzu, Schriftgröße 1:

- y = 194: `Hell: Tag 3/5 Nacht 2/5`
- y = 204: `Nachtmodus: an` / `Nachtmodus: aus`

Bezeichnungen in `GRAY`, Werte in `WHITE`, passend zum bestehenden Stil. Beide Zeilen müssen oberhalb der Fußzeilenlinie (y = 216) bleiben.

## Doku

- Version 0.2 → 0.3: Info-Seite (`N.I.N.A. POCKET v0.3`), README-Badge
- `CHANGELOG.md`: neuer Abschnitt v0.3
- README: Tastenbelegung (kurz / beide / lang) und Nachtmodus in den Highlights
- `tools/render_mockups.py`: Info-Seite um die zwei Zeilen ergänzen, `docs/images/screens/about.png` neu rendern

## Nicht im Umfang

- keine Helligkeitsautomatik und keine zeitgesteuerte Nachtmodus-Umschaltung
- keine eigene Einstellungsseite
- kein Mockup für den Nachtmodus

## Prüfung

- Kompilieren und Flashen übernimmt der Nutzer später in der Arduino IDE. Während der Umsetzung wird nicht kompiliert. Deshalb sorgfältig auf Syntax und Typen achten, z. B. Prototypen für Funktionen mit Default-Argumenten.
- Die Pixel-Umrechnung wird vorab in Python an den Projektfarben geprüft (BG → nahezu schwarz, WHITE → volles Rot, GRAY → mittleres Rot).
- Am Gerät:
  1. Kurz links/rechts blättert wie bisher (beim Loslassen).
  2. Beide Tasten schalten den Nachtmodus um, ohne dabei zu blättern.
  3. Links lang ändert die Helligkeit, der Balken erscheint und verschwindet nach ~1,5 s, und es wird nicht geblättert.
  4. Tag- und Nachtstufe sind unabhängig voneinander. Nach einem Neustart bleiben Modus und Stufen erhalten.
  5. Bei dunklem Display weckt jede Geste nur das Display.
  6. Die niedrigste Nachtstufe ist noch lesbar und flackert nicht. Sonst werden die Tabellenwerte angepasst.
  7. Display-Timeout und Aufwecken durch Ereignisse funktionieren im Nachtmodus mit gedimmter Beleuchtung.
