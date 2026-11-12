# Nachtmodus und Helligkeitssteuerung (v0.3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nachtmodus (rot + gedimmt, beide Tasten) und 5-stufige Helligkeit (links lang), dauerhaft gespeichert.

**Architecture:** Reine Logik ohne Arduino-Abhängigkeit (Entprellen, Gestenerkennung, Rot-Umrechnung, Stufen) kommt in den neuen Header `NINA_Pocket_Companion/companion_logic.h` und wird auf dem Mac mit clang getestet. Die Sketch-Datei verdrahtet diese Logik mit Pins, PWM, `Preferences` und Zeichnung.

**Tech Stack:** Arduino C++ (ESP32-Core 3.3.12, LilyGO T-Display), Adafruit GFX/ST7789, `Preferences`. Host-Tests mit Apple clang (`c++ -std=c++17`). Mockups mit Python/Pillow.

**Spec:** `docs/superpowers/specs/2026-11-12-nachtmodus-helligkeit-design.md`

## Global Constraints

- Der Sketch wird **nicht** kompiliert (macht der Nutzer später in der Arduino IDE). Nur `companion_logic.h` wird über den Host-Test übersetzt. Deshalb sauber auf Syntax achten.
- Arduino-IDE-Falle: Die IDE erzeugt Prototypen für Funktionen im `.ino` und setzt sie vor die erste Funktion. Funktionen im `.ino` dürfen daher **keine Parameter mit selbst definierten struct-Typen** haben, die im `.ino` definiert sind. Structs gehören in `companion_logic.h`. Funktionen mit Default-Argumenten brauchen einen manuellen Prototyp (siehe `wakeDisplay`).
- Code-Stil wie im Sketch: kompakt, 1 Leerzeichen Einrückung, englische Kommentare, sparsam kommentiert.
- `LONG_PRESS_MS` = 800, Entprellung 40 ms, Overlay 1500 ms.
- Stufen Tag `{20, 50, 100, 170, 255}` (Standard 5), Nacht `{1, 3, 6, 12, 24}` (Standard 2).
- Preferences-Namespace `"nina"`, Schlüssel `"night"`, `"briDay"`, `"briNight"`.
- Info-Zeilen höchstens 21 Zeichen (6-px-Schrift, Rand 6 px).
- Commits enden mit `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Dateien

- Create: `NINA_Pocket_Companion/companion_logic.h` – `Debounce`, `GestureDetector`, `Gesture`, `nightPixel()`, `nextLevel()`, `validLevel()`
- Create: `tools/test_companion_logic.cpp` – Host-Tests dafür
- Modify: `NINA_Pocket_Companion/NINA_Pocket_Companion.ino` – Konfiguration, Hintergrundbeleuchtung, Einstellungen, Tasten, Rendern, Info-Seite
- Modify: `tools/render_mockups.py` – Info-Seite
- Modify: `README.md`, `CHANGELOG.md`, `docs/superpowers/specs/2026-11-12-nachtmodus-helligkeit-design.md`

Test-Befehl (wird in mehreren Tasks verwendet), aus dem Repo-Wurzelverzeichnis:

```bash
c++ -std=c++17 -Wall -Wextra -Werror -I NINA_Pocket_Companion tools/test_companion_logic.cpp -o "${TMPDIR:-/tmp}/test_companion_logic" && "${TMPDIR:-/tmp}/test_companion_logic"
```

---

### Task 1: Reine Logik in `companion_logic.h` mit Host-Tests

**Files:**
- Create: `NINA_Pocket_Companion/companion_logic.h`
- Test: `tools/test_companion_logic.cpp`

**Interfaces:**
- Produces:
  - `enum Gesture : uint8_t { G_NONE, G_SHORT_NEXT, G_SHORT_PAGE, G_BOTH, G_LONG_NEXT, G_WAKE };`
  - `const uint32_t LONG_PRESS_MS = 800;`
  - `struct Debounce { bool state; uint32_t changed; bool update(bool raw, uint32_t now); };`
  - `struct GestureDetector { Gesture update(bool next, bool pageKey, uint32_t now, bool displayOn); };`
  - `uint16_t nightPixel(uint16_t c);`
  - `uint8_t nextLevel(uint8_t level);` (1–5, zyklisch)
  - `uint8_t validLevel(uint8_t level, uint8_t fallback);`

- [ ] **Step 1: Test schreiben**

`tools/test_companion_logic.cpp`:

```cpp
// Host tests for the pure firmware logic. Run from the repo root:
// c++ -std=c++17 -Wall -Wextra -Werror -I NINA_Pocket_Companion tools/test_companion_logic.cpp -o /tmp/t && /tmp/t
#include <cstdio>
#include "companion_logic.h"

static int failures=0;
#define CHECK(cond) do{ if(!(cond)){ std::printf("FAIL %s:%d  %s\n",__FILE__,__LINE__,#cond); failures++; } }while(0)

static void testDebounce(){
 Debounce d;
 CHECK(d.update(true,100)==true);    // first change after >40 ms is taken
 CHECK(d.update(false,120)==true);   // bounce within 40 ms ignored
 CHECK(d.update(false,141)==false);  // stable change taken
}
static void testShortPresses(){
 GestureDetector g;
 CHECK(g.update(true,false,0,true)==G_NONE);
 CHECK(g.update(false,false,100,true)==G_SHORT_NEXT);
 CHECK(g.update(false,true,200,true)==G_NONE);
 CHECK(g.update(false,false,300,true)==G_SHORT_PAGE);
}
static void testBoth(){
 GestureDetector g;
 CHECK(g.update(true,false,0,true)==G_NONE);
 CHECK(g.update(true,true,50,true)==G_BOTH);
 CHECK(g.update(true,true,900,true)==G_NONE);    // no long press after "both"
 CHECK(g.update(true,false,950,true)==G_NONE);
 CHECK(g.update(false,false,1000,true)==G_NONE); // release does nothing
 // both in the same frame
 CHECK(g.update(true,true,2000,true)==G_BOTH);
 CHECK(g.update(false,false,2100,true)==G_NONE);
 // started with the right key
 CHECK(g.update(false,true,3000,true)==G_NONE);
 CHECK(g.update(true,true,3100,true)==G_BOTH);
 CHECK(g.update(false,false,3200,true)==G_NONE);
}
static void testLongNext(){
 GestureDetector g;
 CHECK(g.update(true,false,0,true)==G_NONE);
 CHECK(g.update(true,false,799,true)==G_NONE);
 CHECK(g.update(true,false,800,true)==G_LONG_NEXT);
 CHECK(g.update(true,false,2000,true)==G_NONE);  // fires once
 CHECK(g.update(true,true,2100,true)==G_NONE);   // already fired
 CHECK(g.update(false,false,2200,true)==G_NONE);
 // right key held long is still a short press
 CHECK(g.update(false,true,3000,true)==G_NONE);
 CHECK(g.update(false,true,5000,true)==G_NONE);
 CHECK(g.update(false,false,5100,true)==G_SHORT_PAGE);
}
static void testWake(){
 GestureDetector g;
 CHECK(g.update(true,false,0,false)==G_WAKE);
 CHECK(g.update(true,false,900,true)==G_NONE);   // no long press after waking
 CHECK(g.update(false,false,1000,true)==G_NONE);
 CHECK(g.update(true,true,2000,false)==G_WAKE);  // "both" while dark only wakes
 CHECK(g.update(false,false,2100,true)==G_NONE);
}
static void testNightPixel(){
 CHECK(nightPixel(0xFFFF)==0xF800); // WHITE -> full red
 CHECK(nightPixel(0x0006)==0x0000); // BG -> black
 CHECK(nightPixel(0x0000)==0x0000);
 CHECK(nightPixel(0xA514)==0xA000); // GRAY -> medium red
 CHECK(nightPixel(0x07E0)==0x9000); // GREEN
 CHECK(nightPixel(0xF800)==0x4800); // RED -> dim red
 for(uint32_t c=0;c<=0xFFFF;c++) CHECK((nightPixel((uint16_t)c)&0x07FF)==0); // only red
}
static void testLevels(){
 CHECK(nextLevel(1)==2);
 CHECK(nextLevel(4)==5);
 CHECK(nextLevel(5)==1);
 CHECK(validLevel(3,5)==3);
 CHECK(validLevel(0,5)==5);
 CHECK(validLevel(6,2)==2);
 CHECK(validLevel(255,2)==2);
}
int main(){
 testDebounce();testShortPresses();testBoth();testLongNext();testWake();testNightPixel();testLevels();
 if(failures){std::printf("%d failure(s)\n",failures);return 1;}
 std::printf("all tests passed\n");return 0;
}
```

- [ ] **Step 2: Test ausführen, er muss fehlschlagen**

Test-Befehl (siehe oben). Erwartet: Compilerfehler `'companion_logic.h' file not found`.

- [ ] **Step 3: Header implementieren**

`NINA_Pocket_Companion/companion_logic.h`:

```cpp
// Pure logic without Arduino dependencies, unit-tested on the host:
// see tools/test_companion_logic.cpp.
#pragma once
#include <stdint.h>

enum Gesture : uint8_t { G_NONE, G_SHORT_NEXT, G_SHORT_PAGE, G_BOTH, G_LONG_NEXT, G_WAKE };
const uint32_t LONG_PRESS_MS=800;

// Takes a new raw key state only after it differs for more than 40 ms since the last change.
struct Debounce {
 bool state=false;
 uint32_t changed=0;
 bool update(bool raw,uint32_t now){
  if(raw!=state&&now-changed>40){changed=now;state=raw;}
  return state;
 }
};

// Turns the debounced state of both keys into gestures. A short press fires on
// release; "both" and "long" fire while held, and their release does nothing.
// While the display is off, the first press of a gesture only wakes it.
struct GestureDetector {
 bool active=false,fired=false,startedNext=false;
 uint32_t start=0;
 Gesture update(bool next,bool pageKey,uint32_t now,bool displayOn){
  if(!active){
   if(!next&&!pageKey)return G_NONE;
   active=true;fired=false;startedNext=next;start=now;
   if(!displayOn){fired=true;return G_WAKE;}
  }
  if(!next&&!pageKey){
   active=false;
   if(fired)return G_NONE;
   return startedNext?G_SHORT_NEXT:G_SHORT_PAGE;
  }
  if(fired)return G_NONE;
  if(next&&pageKey){fired=true;return G_BOTH;}
  if(next&&startedNext&&now-start>=LONG_PRESS_MS){fired=true;return G_LONG_NEXT;}
  return G_NONE;
 }
};

// Night mode: RGB565 -> red only, keeping the perceived brightness.
inline uint16_t nightPixel(uint16_t c){
 uint32_t r=(c>>11)&0x1F,g=(c>>5)&0x3F,b=c&0x1F;
 uint32_t l=(r*2*77+g*150+b*2*29)>>8; // 0..62
 return (uint16_t)((l>>1)<<11);
}

// Brightness levels run from 1 to 5.
inline uint8_t nextLevel(uint8_t level){return level>=5?1:level+1;}
inline uint8_t validLevel(uint8_t level,uint8_t fallback){return (level>=1&&level<=5)?level:fallback;}
```

- [ ] **Step 4: Test ausführen, er muss bestehen**

Test-Befehl. Erwartet: `all tests passed`, Exit-Code 0.

- [ ] **Step 5: Commit**

```bash
git add NINA_Pocket_Companion/companion_logic.h tools/test_companion_logic.cpp
git commit -m "Add host-tested key gestures, night-mode pixel mapping and brightness levels

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Hintergrundbeleuchtung per PWM und gespeicherte Einstellungen

**Files:**
- Modify: `NINA_Pocket_Companion/NINA_Pocket_Companion.ino` (Includes ~Z. 19, CONFIGURE-Block ~Z. 47–53, Globals ~Z. 77–88, `sleepDisplay`/`wakeDisplay` ~Z. 655–671, `setup()` ~Z. 700–730)

**Interfaces:**
- Consumes: `nextLevel`, `validLevel` aus `companion_logic.h` (Task 1)
- Produces (für Task 3/4): globale `bool nightMode`, `uint8_t briDay`, `uint8_t briNight`; Funktionen `uint8_t activeLevel()`, `void applyBacklight()`, `void loadSettings()`

- [ ] **Step 1: Header einbinden**

Nach `#include <math.h>`:

```cpp
#include "companion_logic.h"
```

- [ ] **Step 2: Konfiguration ergänzen**

Im CONFIGURE-Block direkt nach `const bool BATTERY_MONITOR = ...`:

```cpp
// Backlight PWM values (0-255) for the 5 brightness levels; a long press on the
// left key steps through the levels of the active mode. Both keys toggle night mode.
const uint8_t BRIGHTNESS_DAY[5]   = {20, 50, 100, 170, 255};
const uint8_t BRIGHTNESS_NIGHT[5] = {1, 3, 6, 12, 24};  // night mode: red on black
const uint8_t DEFAULT_LEVEL_DAY = 5, DEFAULT_LEVEL_NIGHT = 2;
```

- [ ] **Step 3: Globale Variablen**

Nach `bool batUsb=false, batLowWarned=false;`:

```cpp
// Night mode and brightness levels (1-5), stored in Preferences.
bool nightMode=false;
uint8_t briDay=DEFAULT_LEVEL_DAY, briNight=DEFAULT_LEVEL_NIGHT;
```

- [ ] **Step 4: `applyBacklight`/`loadSettings` und Display an/aus umstellen**

Den Block `// ---------- Display power ----------` mit `sleepDisplay` und `wakeDisplay` ersetzen durch:

```cpp
// ---------- Display power ----------
uint8_t activeLevel(){return nightMode?briNight:briDay;}
void applyBacklight(){
 const uint8_t *table=nightMode?BRIGHTNESS_NIGHT:BRIGHTNESS_DAY;
 analogWrite(TFT_BL,displayOn?table[activeLevel()-1]:0);
}
void loadSettings(){
 nightMode=prefs.getBool("night",false);
 briDay=validLevel(prefs.getUChar("briDay",DEFAULT_LEVEL_DAY),DEFAULT_LEVEL_DAY);
 briNight=validLevel(prefs.getUChar("briNight",DEFAULT_LEVEL_NIGHT),DEFAULT_LEVEL_NIGHT);
}
void sleepDisplay(){
 if(!displayOn)return;
 displayOn=false;
 applyBacklight();
 tft.enableSleep(true);
}
// Wakes the display. When it was off and an event caused the wake-up, jump to `target`.
void wakeDisplay(int target){
 lastActivity=millis();
 if(displayOn)return;
 if(target>=0)page=(Page)target;
 tft.enableSleep(false);
 delay(120); // ST7789 needs 120 ms after SLPOUT
 displayOn=true;
 render();
 applyBacklight();
}
```

- [ ] **Step 5: `setup()` anpassen**

Die erste Zeile nach `Serial.begin(115200);` war `pinMode(TFT_BL,OUTPUT);digitalWrite(TFT_BL,HIGH);` und wird ersetzt durch:

```cpp
 prefs.begin("nina",false);
 loadSettings();
 pinMode(TFT_BL,OUTPUT);applyBacklight();
```

Im Auto-Discovery-Block die Zeile `prefs.begin("nina",false);` entfernen. Der Kommentar `// Try the address found last time first; ...` bleibt.

- [ ] **Step 6: Prüfen**

```bash
grep -n "digitalWrite(TFT_BL" NINA_Pocket_Companion/NINA_Pocket_Companion.ino   # erwartet: keine Treffer
grep -c 'prefs.begin' NINA_Pocket_Companion/NINA_Pocket_Companion.ino           # erwartet: 1
```

Den Test-Befehl aus Task 1 erneut laufen lassen. Erwartet: `all tests passed`.

- [ ] **Step 7: Commit**

```bash
git add NINA_Pocket_Companion/NINA_Pocket_Companion.ino
git commit -m "Dim the backlight via PWM and load night mode and brightness from Preferences

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Gesten, Nachtmodus-Umschaltung, Helligkeits-Overlay, Rotfärbung

**Files:**
- Modify: `NINA_Pocket_Companion/NINA_Pocket_Companion.ino` (`footer` ~Z. 443, `render` ~Z. 672, `processButton` ~Z. 682–698, `loop` ~Z. 733–754)

**Interfaces:**
- Consumes: `Debounce`, `GestureDetector`, `Gesture`, `nightPixel`, `nextLevel` (Task 1); `nightMode`, `briDay`, `briNight`, `activeLevel()`, `applyBacklight()` (Task 2)
- Produces: `uint32_t overlayUntil`, `bool overlayActive()`, `void shortPress(bool nextButton)`, `void toggleNightMode()`, `void stepBrightness()`, `void handleKeys()`

- [ ] **Step 1: Overlay-Zustand**

Nach `uint8_t briDay=..., briNight=...;` (Task 2):

```cpp
uint32_t overlayUntil=0; // brightness bar in the footer until this millis(), 0 = off
```

- [ ] **Step 2: Fußzeile mit Helligkeitsbalken**

`footer` ersetzen durch (Default-Argumente bleiben, die Funktion steht wie bisher vor ihrer ersten Verwendung):

```cpp
bool overlayActive(){return overlayUntil&&(int32_t)(overlayUntil-millis())>0;}
void footer(const String &left="WEITER",const String &right="MENU") {
 line(216);
 if(overlayActive()){
  textAt(6,224,"HELL",GRAY);
  for(int i=0;i<5;i++){
   int x=36+i*12;
   if(i<activeLevel())gfx->fillRect(x,224,9,8,WHITE);else gfx->drawRect(x,224,9,8,GRAY);
  }
  return;
 }
 textAt(6,224,left,GRAY);textAt(77,224,right,GRAY);
 if(data.stale)textAt(51,224,"ALT",YELLOW);
}
```

Achtung: `activeLevel()` ist erst in Task 2 weiter unten definiert. Die Arduino IDE erzeugt dafür einen Prototyp (keine Default-Argumente, keine struct-Parameter), das ist also in Ordnung.

- [ ] **Step 3: Rotfärbung in `render()`**

In `render()` die Zeile `if(canvas)tft.drawRGBBitmap(0,0,canvas->getBuffer(),W,H);` ersetzen durch:

```cpp
 if(canvas){
  uint16_t *buf=canvas->getBuffer();
  // Every page redraws the whole canvas, so it can be converted in place.
  if(nightMode)for(uint32_t i=0;i<(uint32_t)W*H;i++)buf[i]=nightPixel(buf[i]);
  tft.drawRGBBitmap(0,0,buf,W,H);
 }
```

- [ ] **Step 4: `processButton` durch Gestensteuerung ersetzen**

Die gesamte Funktion `processButton(...)` ersetzen durch:

```cpp
void shortPress(bool nextButton){
 if(page==HOME){
  if(nextButton)navCursor=(navCursor+1)%8;
  else page=(Page)(navCursor+1);
 }else{
  if(nextButton)page=(Page)((page==ABOUT)?SYSTEM:((int)page+1));
  else page=HOME;
 }
 dirty=true;
}
void toggleNightMode(){
 nightMode=!nightMode;
 prefs.putBool("night",nightMode);
 applyBacklight();dirty=true;
}
void stepBrightness(){
 uint8_t &level=nightMode?briNight:briDay;
 level=nextLevel(level);
 prefs.putUChar(nightMode?"briNight":"briDay",level);
 applyBacklight();
 overlayUntil=millis()+1500;if(!overlayUntil)overlayUntil=1;
 dirty=true;
}
void handleKeys(){
 static Debounce nextKey,pageKey;
 static GestureDetector gestures;
 uint32_t now=millis();
 bool next=nextKey.update(digitalRead(BTN_NEXT)==LOW,now);
 bool pg=pageKey.update(digitalRead(BTN_PAGE)==LOW,now);
 Gesture g=gestures.update(next,pg,now,displayOn);
 if(g==G_NONE)return;
 if(g==G_WAKE){wakeDisplay();return;} // first press only wakes the display
 lastActivity=now;
 switch(g){
 case G_SHORT_NEXT:shortPress(true);break;
 case G_SHORT_PAGE:shortPress(false);break;
 case G_BOTH:toggleNightMode();break;
 case G_LONG_NEXT:stepBrightness();break;
 default:break;
 }
}
```

- [ ] **Step 5: `loop()` anpassen**

Diese drei Zeilen am Anfang von `loop()`:

```cpp
 static bool wasNext=false,wasPage=false;
 static uint32_t changedNext=0,changedPage=0;
 processButton(BTN_NEXT,wasNext,changedNext,true);
 processButton(BTN_PAGE,wasPage,changedPage,false);
```

ersetzen durch:

```cpp
 handleKeys();
```

Vor der Zeile `if(displayOn&&(dirty||(page==ALTITUDE...` einfügen:

```cpp
 if(overlayUntil&&!overlayActive()){overlayUntil=0;dirty=true;} // hide the brightness bar
```

- [ ] **Step 6: Prüfen**

```bash
grep -n "processButton\|wasNext\|changedPage" NINA_Pocket_Companion/NINA_Pocket_Companion.ino  # erwartet: keine Treffer
grep -n "handleKeys\|nightPixel\|overlayActive" NINA_Pocket_Companion/NINA_Pocket_Companion.ino
```

Erwartet: `handleKeys` 2× (Definition und Aufruf in `loop`), `nightPixel` 1×, `overlayActive` 3×. Den Test-Befehl aus Task 1 laufen lassen, erwartet: `all tests passed`. Anschließend den geänderten Code auf Klammerung und Semikolons durchlesen, weil nicht kompiliert wird.

- [ ] **Step 7: Commit**

```bash
git add NINA_Pocket_Companion/NINA_Pocket_Companion.ino
git commit -m "Key gestures: both keys toggle red night mode, long left press steps brightness

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Info-Seite, Mockup, Version 0.3 und Doku

**Files:**
- Modify: `NINA_Pocket_Companion/NINA_Pocket_Companion.ino` (Kopfkommentar Z. 2, `drawAbout` ~Z. 599–614)
- Modify: `tools/render_mockups.py` (`about()` ~Z. 333–346)
- Modify: `README.md`, `CHANGELOG.md`, `docs/superpowers/specs/2026-11-12-nachtmodus-helligkeit-design.md`

**Interfaces:**
- Consumes: `nightMode`, `briDay`, `briNight` (Task 2)

- [ ] **Step 1: Info-Seite im Sketch**

In `drawAbout()` nach `textAt(6,179,DISPLAY_TIMEOUT_MIN?...);` einfügen:

```cpp
 textAt(6,194,"Hell:",GRAY);
 textAt(42,194,"Tag "+String(briDay)+" Nacht "+String(briNight));
 textAt(6,204,"Nachtmodus:",GRAY);
 textAt(78,204,nightMode?"an":"aus");
```

Außerdem `"N.I.N.A. POCKET v0.2"` → `"N.I.N.A. POCKET v0.3"` und im Kopfkommentar `N.I.N.A. Pocket Companion 0.2` → `0.3`.

- [ ] **Step 2: Mockup**

In `tools/render_mockups.py`, Methode `about()`: `"N.I.N.A. POCKET v0.2"` → `"N.I.N.A. POCKET v0.3"`, und nach `self.text(6, 179, "nach 5 min")` einfügen:

```python
        self.text(6, 194, "Hell:", GRAY)
        self.text(42, 194, "Tag 5 Nacht 2")
        self.text(6, 204, "Nachtmodus:", GRAY)
        self.text(78, 204, "aus")
```

Prüfen: `python3 -c "import ast;ast.parse(open('tools/render_mockups.py').read())"`. Die PNGs werden **nicht** neu erzeugt, weil `glcdfont.c` auf dem Laptop fehlt. Das macht der Nutzer zu Hause mit `python3 tools/render_mockups.py`.

- [ ] **Step 3: Spec korrigieren**

In der Spec, Abschnitt „Seite Info“: `Hell: Tag 3/5 Nacht 2/5` → `Hell: Tag 3 Nacht 2` und ergänzen: „(23 Zeichen hätten nicht in 21 Zeichen Breite gepasst; die 5 Stufen zeigt der Balken.)“

- [ ] **Step 4: README**

- Badge `Version-0.2` → `Version-0.3`.
- Highlights-Tabelle, neue Zeile nach „Akku & Stromsparen“:
  `| 🌙 **Nachtmodus** | Beide Tasten gleichzeitig: alles rot auf Schwarz und stark gedimmt – schont die Dunkeladaption am Teleskop. Helligkeit in 5 Stufen, für Tag und Nacht getrennt gespeichert. |`
- CONFIGURE-Tabelle, nach `DISPLAY_TIMEOUT_MIN`:
  `| \`BRIGHTNESS_DAY\`, \`BRIGHTNESS_NIGHT\` | PWM-Werte (0–255) der 5 Helligkeitsstufen für Tag- und Nachtmodus |`
- Abschnitt „🎮 Bedienung“: Unter der Tabelle (vor dem IMPORTANT-Hinweis) einfügen:

```markdown
Kurze Tastendrücke wirken beim **Loslassen**. Dazu kommen zwei Gesten, die auf jeder Seite funktionieren:

| Geste | Wirkung |
|---|---|
| **Beide Tasten** gleichzeitig | Nachtmodus an/aus |
| **Links lang** (0,8 s) | Helligkeit eine Stufe weiter (1 → 5 → 1), kurz als Balken in der Fußzeile |

### 🌙 Nachtmodus

Im Nachtmodus wird das ganze Bild in Rottöne umgerechnet (Helligkeit bleibt erhalten, Farben nicht) und die Hintergrundbeleuchtung nutzt eigene, sehr niedrige Stufen. Tag- und Nachthelligkeit werden getrennt eingestellt. Modus und Stufen bleiben nach einem Neustart erhalten und stehen auf der Seite **Info**.
```

- „Ideen für später“: `- [x] Nachtmodus und Helligkeitssteuerung (v0.3)` nach dem v0.2-Eintrag.
- Im Absatz „Läuft auf einem LilyGO T-Display …“ anhängen: „Nachtmodus und Helligkeit (v0.3) sind noch nicht auf dem Gerät getestet.“

- [ ] **Step 5: CHANGELOG**

Oben (vor `## v0.2`) einfügen:

```markdown
## v0.3 – November 2026

### Nachtmodus
- Beide Tasten gleichzeitig schalten den Nachtmodus um: Das Bild wird in Rottöne auf Schwarz umgerechnet, die Hintergrundbeleuchtung nutzt eigene, niedrige Stufen.
- Ohne Bildpuffer (Notfallpfad) wird nur gedimmt.

### Helligkeit
- Hintergrundbeleuchtung per PWM in 5 Stufen, getrennt für Tag (`BRIGHTNESS_DAY`) und Nacht (`BRIGHTNESS_NIGHT`).
- Linke Taste lang (0,8 s) schaltet die Stufe des aktiven Modus weiter; ein Balken in der Fußzeile zeigt sie 1,5 s lang an.
- Nachtmodus und beide Stufen werden gespeichert und überleben einen Neustart.

### Bedienung
- Kurze Tastendrücke wirken jetzt beim Loslassen, damit sich Doppel- und Langdruck davon unterscheiden lassen.
- Bei ausgeschaltetem Display weckt jede Geste nur das Display.

### Sonstiges
- Seite **Info** zeigt Helligkeitsstufen und Nachtmodus.
- Tastenlogik, Rot-Umrechnung und Stufen liegen in `companion_logic.h` und haben Host-Tests (`tools/test_companion_logic.cpp`).

### Noch nicht getestet
- Noch nicht auf dem Gerät geprüft.
```

- [ ] **Step 6: Prüfen und committen**

```bash
grep -rn "0\.2" README.md NINA_Pocket_Companion/NINA_Pocket_Companion.ino tools/render_mockups.py
```

Erwartet: Nur noch historische Treffer (Ideen-Liste „(v0.2)“, Text zum Gerätetest), keine Versionsangaben. Test-Befehl aus Task 1 laufen lassen, erwartet: `all tests passed`.

```bash
git add NINA_Pocket_Companion/NINA_Pocket_Companion.ino tools/render_mockups.py README.md CHANGELOG.md docs/superpowers/specs/2026-11-12-nachtmodus-helligkeit-design.md
git commit -m "v0.3: show brightness and night mode on the Info page, document gestures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Übergabe an den Nutzer (nach Task 4)

Zu Hause:
1. In der Arduino IDE kompilieren und flashen.
2. `python3 tools/render_mockups.py` ausführen und die neue `about.png` committen.
3. Die Geräte-Checkliste aus der Spec (Abschnitt „Prüfung“, Punkte 1–7) durchgehen.
