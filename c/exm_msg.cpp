// Copyright (c) 2012 Rich Porter - see LICENSE for further details

#include "vpi_user.h"
#include "message.h"

void cb_vpi_printf(const example::cb_id& id, unsigned int level, timespec& when, char* severity, char *file, unsigned int line, char* text) {
  if (example::message::get_ctrl(level)->echo) {
    struct tm date;
    char buf[16];
    localtime_r(&(when.tv_sec), &date);
    strftime((PLI_BYTE8*)buf, sizeof(buf), (PLI_BYTE8*)"%T", &date);
    vpi_printf("(%12s %s) %s\n", severity, buf, text);
  }
}

struct install_s {
  install_s() {
    example::message::instance()->get_cb_emit()->assign("default", 0, cb_vpi_printf);
    DEBUG("replaced");
  }
};

// replace default with vpi printf
static install_s* install = new install_s();
