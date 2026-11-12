# Changelog

## v0.2 – November 2026

### Akku
- Akkuanzeige: Spannung über den Spannungsteiler des T-Display (GPIO34, freigeschaltet über GPIO14), geglättet.
- Akkusymbol mit Füllstand in der Kopfzeile, Spannung und geschätzter Ladestand auf der Seite **Info**; `USB`, wenn USB angesteckt ist.
- Abschaltbar mit `BATTERY_MONITOR = false`.

### Display-Timeout
- Display geht nach `DISPLAY_TIMEOUT_MIN` Minuten ohne Tastendruck aus (Standard 5, `0` = immer an); Hintergrundbeleuchtung aus, Displaycontroller im Schlafmodus.
- Der erste Tastendruck weckt nur das Display.
- Bei ausgeschaltetem Display wird seltener abgefragt (`POLL_MS_DISPLAY_OFF`, Standard 30 s).
- `WAKE_ON_EVENTS`: Display schaltet sich bei Sequenzende (→ Session), Verbindungsverlust (→ Systemstatus) und Akku ≤ 10 % (→ Info) selbst ein.

### Sonstiges
- Seite **Info** neu aufgeteilt (Akku, Display-Timeout).
- Seitentitel auf 8 Zeichen begrenzt, damit das Akkusymbol Platz hat.

### Getestet
- Auf dem T-Display bestätigt: plausible Akkuspannung ohne USB, Anzeige `USB` bei angestecktem Kabel, Display-Timeout und Aufwecken per Tastendruck ohne Weiterblättern.

## v0.1 – November 2026

### Anzeige
- Bild um 180° gedreht: USB-C und Tasten unten.
- Werte und Seitentitel in doppelter Schriftgröße; längere Texte klein, aber vollständig (bis 21 Zeichen).
- Flackerfreier Bildaufbau über einen Bildpuffer im Speicher.
- Fußzeile mit den Tastenfunktionen `WEITER` / `MENU`.
- Zuletzt bekannte Werte bleiben bei Verbindungsverlust sichtbar und sind mit `ALT` markiert.
- Umlaute aus N.I.N.A. werden für die Display-Schrift umschrieben (ü → ue).
- Zu lange Texte, die am Rand umgebrochen wären, gekürzt.

### N.I.N.A.-Daten
- Sequenzstatus aus dem Sequenzbaum der Advanced API v2: Status, aktuelles Ziel, laufender Schritt, Belichtungszeit und Frames.
- JSON-Verschachtelungstiefe auf 40 Ebenen erhöht – der Sequenzbaum war für die Standardgrenze (10) zu tief.
- Kamera: Soll-Temperatur (`TargetTemp` / `TemperatureSetPoint`) und Kühlleistung.
- Guider: RMS aus `RMSError.Total.Arcseconds` und Guider-Status; RMS nur während des Guidings.
- Antworten werden ohne Chunked Encoding angefordert (`HTTP/1.0`), damit ArduinoJson sie direkt lesen kann.

### Netzwerk
- Auto-Discovery: Ist `NINA_HOST` leer, wird der N.I.N.A.-PC im eigenen /24-Netz gesucht, per `GET /v2/api/version` bestätigt und im Flash gespeichert.
- Verbindungs-Timeout 1,5 s; ist N.I.N.A. nicht erreichbar, werden die übrigen Abfragen der Runde übersprungen.
- Beim Start wird bis zu 10 s auf das WLAN gewartet; nach einem Reconnect wird sofort abgefragt.

### Konfiguration
- WLAN-Zugangsdaten und Standort in `secrets.h` ausgelagert (in `.gitignore`), Vorlage `secrets_example.h`.

### Projekt
- Projektseite mit pixelgenauen Mockups (`tools/render_mockups.py`).
- 3D-druckbares Gehäuse für T-Display und 1100-mAh-Akku (`hardware/gehaeuse`).
- MIT-Lizenz.
