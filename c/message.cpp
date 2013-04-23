#include <stdlib.h>
#include <sstream>
#include "message.h"

namespace example {

void cb_account(const cb_id& id, unsigned int level, timespec& when, char* severity, const tag* tag, char *file, unsigned int line, char* text) {
  control* attr = message::get_ctrl(level);
  ++attr->count;
  if ((attr->threshold > 0) && (attr->count == attr->threshold)) { // only do it once!
    if (!message::terminating()) {
      FATAL("Too many %s", severity);
    }
    message::terminate();
  }
}

void cb_emit_default(const cb_id& id, unsigned int level, timespec& when, char* severity, const tag* tag, char *file, unsigned int line, char* text) {
  if (message::get_ctrl(level)->echo) {
    fprintf(stderr, "(%12s) %s\n",  severity, text);
    fflush(stderr);
  }
}

void cb_terminate_default(const cb_id& id) {
  exit(1);
}

////////////////////////////////////////////////////////////////////////////////

bool cb_id::operator> (const cb_id& key) const {
  if (key.name == name) return false;
  return key.priority < priority;
}
bool cb_id::operator< (const cb_id& key) const {
  if (key.name == name) return false;
  return key.priority > priority;
}

////////////////////////////////////////////////////////////////////////////////

const unsigned int tag::size = 16;
#define STR(x) static_cast<std::ostringstream*>(&(std::ostringstream() << x))->str()

tag::tag(const char* ident, const unsigned int subident) : ident(ident), subident(subident), str(std::string(ident) +  '-' + STR(subident)) {}
tag::~tag() {}
bool tag::operator> (const tag& key) const {
  int cmp = strcmp(key.ident, ident);
  if (cmp == 0) return key.subident > subident;
  return cmp > 0;
}
bool tag::operator< (const tag& key) const {
  int cmp = strcmp(key.ident, ident);
  if (cmp == 0) return key.subident < subident;
  return cmp < 0;
}
const char* tag::id() const {
  return str.c_str();
}

////////////////////////////////////////////////////////////////////////////////

msg::msg(const unsigned int level, const char* text) : level(level) {
  this->text = (const char*)malloc(strlen(text));
  strcpy((char*)this->text, text);
}

const char* msg::severity() const {
  return message::name(level);
}

////////////////////////////////////////////////////////////////////////////////

class noMessageError {};

msg_tags::msg_tags() : map(NULL) {
}
msg_tags::~msg_tags() {
  if (map != NULL) {
    delete map;
  }
}
msg_tags::tagmap& msg_tags::getmap() {
  if (map == NULL) {
    map = new tagmap();
  }
  return *map;
}
const msg_tags::const_iterator msg_tags::add(const char* ident, const unsigned int subident, const unsigned int level, const char* text) {
  const tag _tag(ident, subident);
  const msg _msg(level, text);
  const value_type value(_tag, _msg);
  std::pair<const_iterator,bool> result = getmap().insert(value);
  return result.first;
}
const msg& msg_tags::get(const char* ident, const unsigned int subident) {
  tag _tag(ident, subident);
  return get(_tag);
}
const msg& msg_tags::get(const tag& id) {
  const_iterator it = getmap().find(id);
  if (it == getmap().end()) {
    throw noMessageError();
  }
  return it->second;
}

////////////////////////////////////////////////////////////////////////////////

message::message() : terminating_cnt(0) {
  cb_emit.insert("account", 99, cb_account);
  cb_emit.insert("default", 0, cb_emit_default);
  cb_terminate.insert("exit", 99, cb_terminate_default);
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
}

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
    _cb->second(_cb->first);
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
    (char*)"SUCCESS",
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
msg_tags& message::get_tags() {
  return self->tags;
}

void message::emit(unsigned int level, char* file, unsigned int line, char* text, va_list args) {
  char buff[8192];
  if (args) {
    vsnprintf(buff, sizeof(buff), text, args);
  }
  char *severity = message::name(level);
  struct timespec when;
  clock_gettime(CLOCK_REALTIME, &when);
  callbacks<cb_emit_fn>::map_t* cbs = cb_emit.get_map();
  for (callbacks<cb_emit_fn>::map_t::iterator _cb = cbs->begin(); _cb != cbs->end(); _cb++) {
    _cb->second(_cb->first, level, when, severity, NULL, file, line, args?buff:text);
  }
}

void message::by_id(char* ident, unsigned int subident, char* file, unsigned int line, ...) {
  va_list args;
  va_start(args, line);
  tag tag_id(ident, subident);
  try {
    const msg& msg_id = get_tags().get(tag_id);
    struct timespec when;
    clock_gettime(CLOCK_REALTIME, &when);
    callbacks<cb_emit_fn>::map_t* cbs = cb_emit.get_map();
    for (callbacks<cb_emit_fn>::map_t::iterator _cb = cbs->begin(); _cb != cbs->end(); _cb++) {
      _cb->second(_cb->first, msg_id.level, when, (char*)msg_id.severity(), &tag_id, file, line, (char*)msg_id.text);
    }
  } catch (noMessageError &e) {
    ERROR("No matching message ident found %s", tag_id.id());
  }

  va_end(args);
}

void message::by_msg(const msg_tags::const_iterator& msg, char* file, unsigned int line, ...) {
  va_list args;
  va_start(args, line);

  struct timespec when;
  clock_gettime(CLOCK_REALTIME, &when);
  callbacks<cb_emit_fn>::map_t* cbs = cb_emit.get_map();
  for (callbacks<cb_emit_fn>::map_t::iterator _cb = cbs->begin(); _cb != cbs->end(); _cb++) {
    _cb->second(_cb->first, (*msg).second.level, when, (char*)(*msg).second.severity(), &((*msg).first), file, line, (char*)(*msg).second.text);
  }

  va_end(args);
}

int message::errors() {
  return self->attrs[ERROR].count + self->attrs[INTERNAL].count + self->attrs[FATAL].count;
}

struct status_result message::status() {
  struct status_result result;
  int successes = self->attrs[SUCCESS].count;
  result.flag = self->errors() == 0 && successes == 1;
  result.text = result.flag?"PASS":"FAIL";
  return result;
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
  //SEVERITY(success    , SUCCESS);
SEVERITY(warning    , WARNING);
SEVERITY(error      , ERROR);
SEVERITY(internal   , INTERNAL);
SEVERITY(fatal      , FATAL);

void message::success(char *file, unsigned int line, char* text, ...) {
  va_list args;
  va_start(args, text);
  unsigned int level = SUCCESS;
  if (self->errors()) {
    WARNING("due to previous errors following message SUCCESS masked");
    level = WARNING;
  }
  emit(level, file, line, text, args);
  va_end(args);
}

#undef SEVERITY

}
