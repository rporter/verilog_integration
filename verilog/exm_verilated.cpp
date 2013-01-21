#include "verilated.h"
#include "message.h"

void vl_finish (const char* filename, int linenum, const char* hier) {
  example::message::instance()->information((char*)filename, linenum, (char*)"%s : verilator $finish", hier);
  if (Verilated::gotFinish()) {
    example::message::instance()->warning((char*)filename, linenum, (char*)"Multiple verilator $finish");
    Verilated::flushCall();
    exit(0);
  }
  Verilated::gotFinish(true);
}

void vl_stop (const char* filename, int linenum, const char* hier) {
  Verilated::gotFinish(true);
  Verilated::flushCall();
  example::message::instance()->fatal((char*)filename, linenum, (char*)"%s : verilator $stop", hier);
}

void vl_fatal (const char* filename, int linenum, const char* hier, const char* msg) {
  Verilated::gotFinish(true);
  example::message::instance()->fatal((char*)filename, linenum, (char*)"%s : verilator fatal : %s", hier, msg);
  Verilated::flushCall();
}
