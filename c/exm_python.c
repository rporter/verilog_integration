// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include <stdlib.h>
#include "Python.h"
#include "vpi_user.h"
#include "exm_python.h"

void exm_python_finalize() {
  Py_Finalize();
}

int exm_python(const char *filename) {
  FILE *file;
  char env[2048];
  s_vpi_vlog_info vlog_info;

  if (char *existenv = getenv("PYTHONPATH")) {
    snprintf(env, sizeof(env), "PYTHONPATH=%s:%s", existenv, PYTHONDIR);
  } else {
    snprintf(env, sizeof(env), "PYTHONPATH=%s", PYTHONDIR);
  }
  putenv(env);

  if (strncmp("stdin", filename, 6) == 0) {
    file = stdin;
  } else {
    file = fopen(filename, "r");
    if (file == NULL) {
      vpi_printf((PLI_BYTE8*)"Cannot open python script file %s\n", (PLI_BYTE8*)filename);
      return 0;
    }
  }

  vpi_get_vlog_info(&vlog_info);

  Py_Initialize();
  PySys_SetArgv(vlog_info.argc, vlog_info.argv);
  // run python interactively until EOF
  PyRun_AnyFile(file, filename);

  // schedule finalization 
  atexit(exm_python_finalize);

  return 1;
}
