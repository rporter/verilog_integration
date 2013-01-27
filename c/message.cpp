#include <stdlib.h>
#include <stdio.h>
#include "message.h"

namespace example {

void cb_account(unsigned int level, char* severity, char *file, unsigned int line, char* text) {
  control* attr = message::get_ctrl(level);
  ++attr->count;
  if ((attr->threshold > 0) && (attr->count == attr->threshold)) { // only do it once!
    if (!message::terminating()) {
      FATAL("Too many %s", severity);
    }
    message::terminate();
  }
}

void cb_emit_default(unsigned int level, char* severity, char *file, unsigned int line, char* text) {
  if (message::get_ctrl(level)->echo) {
    fprintf(stderr, "(%12s) %s\n",  severity, text);
    fflush(stderr);
  }
}

void cb_terminate_default() {
  exit(1);
}

message::message() : terminating_cnt(0) {
  cb_emit.insert_to_map("account", 99, cb_account);
  cb_emit.insert_to_map("default", 0, cb_emit_default);
  cb_terminate.insert_to_map("exit", 99, cb_terminate_default);
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

message::~message() {
  for (int i=MAX_LEVEL;--i>=INT_DEBUG;) {
    INFORMATION("%12s : %d", name(i), attrs[i].count);
  }
};

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

void message::terminate() {
  callbacks<cb_terminate_fn>::map_t* cbs = self->cb_terminate.get_map();
  for (callbacks<cb_terminate_fn>::map_t::iterator _cb = cbs->begin(); _cb != cbs->end(); _cb++) {
    _cb->second();
  }
}

int message::terminating() {
  return message::self->terminating_cnt++;
}

char* message::name(int level) {
  return name((enum levels)level);
}

char* message::name(enum levels level) {
  static char* names[] = {
    (char*)"INT_DEBUG",
    (char*)"DEBUG",
    (char*)"INFORMATION",
    (char*)"NOTE",
    (char*)"WARNING",
    (char*)"ERROR",
    (char*)"INTERNAL",
    (char*)"FATAL"
  };
  if (level >= INT_DEBUG && level <= FATAL) {
    return names[level];
  }
  return (char*)"**undefined**";
}

control* message::get_ctrl() {
  return self->attrs;
}

control* message::get_ctrl(unsigned int level) {
  if (level >= INT_DEBUG and level <= FATAL) {
    return &self->attrs[level];
  }
  return NULL;
}

void message::verbosity(unsigned int level) {
  for (int i=INT_DEBUG; i<MAX_LEVEL;i++) {
    self->attrs[i].echo = i>=level;
  }
};

callbacks<cb_emit_fn>* message::get_cb_emit() {
  return &self->cb_emit;
}
callbacks<cb_terminate_fn>* message::get_cb_terminate() {
  return &self->cb_terminate;
}

void message::emit(unsigned int level, char* file, unsigned int line, char* text, va_list args) {
  char buff[8192];
  if (args) {
    vsnprintf(buff, sizeof(buff), text, args);
  }
  char *severity = message::name(level);
  callbacks<cb_emit_fn>::map_t* cbs = cb_emit.get_map();
  for (callbacks<cb_emit_fn>::map_t::iterator _cb = cbs->begin(); _cb != cbs->end(); _cb++) {
    _cb->second(level, severity, file, line, args?buff:text);
  }
}

message* message::self = 0;

#define SEVERITY(level, LEVEL) \
  void message::level(char *file, unsigned int line, char* text, ...) { \
    va_list args; \
    va_start(args, text); \
    emit(LEVEL, file, line, text, args); \
    va_end(args); \
  }

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
