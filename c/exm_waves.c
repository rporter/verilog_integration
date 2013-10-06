// Copyright (c) 2013 Rich Porter - see LICENSE for further details

#include "vpi_user.h"
#include "message.h"
#include "exm_waves.h"

static struct {
  const char *filename;
  int depth;
} default_waves = {
  "waves.vcd",
  0
};

int exm_waves(const char** filename, int* depth) {
  s_vpi_value vpi_value;
  s_vpi_vlog_info vlog_info;
  static std::string arg = "";

  vpi_get_vlog_info(&vlog_info);

  // Scan options for +waves plusarg
  for (int i=0; i<vlog_info.argc; i++) {
    if (strncmp(vlog_info.argv[i], "+waves", 6) == 0) {
      if (strlen(vlog_info.argv[i]) > 7) {
        arg = vlog_info.argv[i]+7;
      } else {
        arg = default_waves.filename;
      }
    }
  }

  if (arg.length() < 1) {
    // no argument
    return 0;
  }

  // look for depth in format +waves+filename+depth
  size_t pos = arg.find_first_of("+,");
  if (pos != std::string::npos) {
    *depth = atoi(arg.substr(pos+1).c_str());
    arg.erase(pos);
  } else {
    *depth = default_waves.depth;
  }
  if (arg.length() < 1) {
    // e.g. +waves++5
    arg = default_waves.filename;
  }

  *filename = arg.c_str();

  return 1;
}

