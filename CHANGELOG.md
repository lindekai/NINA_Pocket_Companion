# Changelog

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
