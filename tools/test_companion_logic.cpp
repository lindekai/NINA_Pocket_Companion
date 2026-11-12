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
