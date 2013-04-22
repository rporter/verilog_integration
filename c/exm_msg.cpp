// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include <execinfo.h>
#include <signal.h>
#include <string.h>
#include "vpi_user.h"
#include "message.h"

void cb_vpi_printf(const example::cb_id& id, unsigned int level, timespec& when, char* severity, example::tag* tag, char *file, unsigned int line, char* text) {
  if (example::message::get_ctrl(level)->echo) {
    struct tm date;
    char buf[16];
    localtime_r(&(when.tv_sec), &date);
    strftime((PLI_BYTE8*)buf, sizeof(buf), "%T", &date);
    if (tag == NULL) {
      vpi_printf((PLI_BYTE8*)"(%12s %s) %s\n", severity, buf, text);
    } else {
      vpi_printf((PLI_BYTE8*)"(%12s %s) [%s] %s\n", severity, buf, tag->id(), text);
    }
  }
}

struct install_s {
  static unsigned int size;
  install_s() {
    example::message::instance()->get_cb_emit()->assign("default", 0, cb_vpi_printf);
    DEBUG("replaced");
    signal(SIGSEGV, (sighandler_t) segv_handler);
    signal(SIGBUS,  (sighandler_t) segv_handler);
  }
  static int segv_handler(int sig) {
    WARNING("Caught signal %d (%s) backtrace follows", sig, strsignal(sig));

    void **buffer  = (void**)malloc(size*sizeof(void*));
    int nptrs      = backtrace(buffer, size);
    char **strings = backtrace_symbols(buffer, nptrs);
    if (strings == NULL) {
      WARNING("backtrace_symbols returned NULL");
    } else {
      for (int j = 0; j < nptrs; j++) {
        INFORMATION("  %s", strings[j]);
      }
      free(strings);
    }
    INTERNAL("Caught signal %d (%s)", sig, strsignal(sig));
    signal(sig, SIG_DFL);
    return 0;
  }
};

// replace default with vpi printf
static install_s* install = new install_s();
unsigned int install_s::size = 100;
