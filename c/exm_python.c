// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include <stdlib.h>
#include "Python.h"
#include "vpi_user.h"
#include "message.h"
#include "exm_python.h"

static void python_finalize() {
  Py_Finalize();
}

static int python(const char *filename) {
  FILE *file;
  char env[2048];
  s_vpi_vlog_info vlog_info;

  if (char *existenv = getenv("PYTHONPATH")) {
    snprintf(env, sizeof(env), "PYTHONPATH=%s:%s", existenv, PYTHONDIR);
  } else {
    snprintf(env, sizeof(env), "PYTHONPATH=%s", PYTHONDIR);
  }
  putenv(env);

  vpi_get_vlog_info(&vlog_info);

  if (filename == NULL) {
    // Scan options for +python plusarg
    for (int i=0; i<vlog_info.argc; i++) {
      if (strncmp(vlog_info.argv[i], "+python", 7) == 0) {
        if (strlen(vlog_info.argv[i]) > 8) {
          filename = vlog_info.argv[i]+8;
        } else {
          filename = "stdin";
        }
      }
    }
    // Not found
    if (filename == NULL) {
      // Don't do anything
      return 0;
    }
  }

  if (strlen(filename) == 0 || strncmp("stdin", filename, 6) == 0) {
    file = stdin;
  } else {
    file = fopen(filename, "r");
    if (file == NULL) {
      ERROR("Cannot open python script file %s\n", filename);
      return 0;
    }
  }

  Py_Initialize();
  PySys_SetArgv(vlog_info.argc, vlog_info.argv);
  // run python interactively until EOF
  PyRun_AnyFile(file, filename);

  // schedule finalization 
  atexit(python_finalize);

  return 1;
}

int exm_python() {
  python(NULL);
}

int exm_python_file(const char *filename) {
  python(filename);
}
