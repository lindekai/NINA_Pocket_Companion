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
