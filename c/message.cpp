#include <stdlib.h>
#include <stdio.h>
#include "message.h"

namespace example {

#define SEVERITY(level, LEVEL) \
  void message::level(char *file, unsigned int line, char* text, ...) { \
    va_list args; \
    va_start(args, text); \
    emit(LEVEL, (char*)#LEVEL, file, line, text, args);	\
    va_end(args); \
  }

void message::cb_account(unsigned int level, char* severity, char *file, unsigned int line, char* text) {
  control* attr = &instance()->attrs[level];
  if ((attr->threshold > 0) && (++attr->count > attr->threshold)) {
    FATAL("Too many %s", severity);
  }
}

void message::cb_emit_default(unsigned int level, char* severity, char *file, unsigned int line, char* text) {
  if (instance()->attrs[level].echo) {
    fprintf(stderr, "(%12s) %s\n",  severity, text);
    fflush(stderr);
  }
}

void message::cb_terminate_default() {
  exit(1);
}

message::message() {
  cb_emit.add(cb_account);
  cb_emit.add(cb_emit_default);
  cb_terminate.add(cb_terminate_default);
  for (int i=INT_DEBUG; i<MAX_LEVEL; i++) {
    attrs[i].echo = i>DEBUG;
    if (i>ERROR) {
      attrs[i].threshold = 1;
    } else if (i>WARNING) {
      attrs[i].threshold = 10; // default to 10 errors before terminate callback
    } else {
      attrs[i].threshold = -1;
    }
    attrs[i].count = 0;
  }
}

message::~message() {};

message* message::instance() {
  if (NULL == self) {
    self = new message();
    atexit(message::destroy);
  }
  return self;
}

void message::destroy() {
  delete self;
}

void message::verbosity(unsigned int level) {
  for (int i=INT_DEBUG; i<MAX_LEVEL;i++) {
    attrs[i].echo = i>=level;
  }
};

void message::emit(unsigned int level, char* severity, char *file, unsigned int line, char* text, va_list args) {
  char buff[8192];
  if (args) {
    vsnprintf(buff, sizeof(buff), text, args);
  }
  
  std::deque<cb_emit_fn>* cbs = cb_emit.get();
  for (std::deque<cb_emit_fn>::iterator _cb = cbs->begin(); _cb != cbs->end(); _cb++) {
    (*_cb)(level, severity, file, line, args?buff:text);
  }
}

message* message::self = 0;

SEVERITY(int_debug  , INT_DEBUG);
SEVERITY(debug      , DEBUG);
SEVERITY(information, INFORMATION);
SEVERITY(note       , NOTE);
SEVERITY(warning    , WARNING);
SEVERITY(error      , ERROR);
SEVERITY(internal   , INTERNAL);
SEVERITY(fatal      , FATAL);

#undef SEVERITY

}
