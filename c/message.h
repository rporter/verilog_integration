#include <stdio.h>
#include <stdarg.h>
#include <time.h>
#include <string>
#include <map>
#include <boost/function.hpp>

namespace example {

////////////////////////////////////////////////////////////////////////////////

enum levels {
  INT_DEBUG = 0,
  DEBUG,
  INFORMATION,
  NOTE,
  SUCCESS,
  WARNING,
  ERROR,
  INTERNAL,
  FATAL,
  MAX_LEVEL
};

////////////////////////////////////////////////////////////////////////////////

struct cb_id {
  std::string name;
  int         priority;
  bool operator> (const cb_id& key) const;
  bool operator< (const cb_id& key) const;
};

template <typename func_t>
  class callbacks {
public :
  typedef boost::function<func_t> wrap_t;
  typedef std::pair<cb_id, wrap_t> pair_t;
  typedef std::map<cb_id, wrap_t> map_t;
  typedef typename map_t::iterator iter_t;
protected :
  map_t* map;

  iter_t find(std::string name) {
    map_t* _map = get_map();
    for (iter_t _cb = _map->begin(); _cb != _map->end(); _cb++) {
      if (_cb->first.name == name) {
        return _cb;
      }
    }
    return _map->end();
  }
public :
  callbacks() : map(NULL) {};
  ~callbacks() {};
  map_t* get_map() {
    if (NULL == map) {
      map = new map_t();
    }
    return map;
  }
  void dprint() {
    // debug listing
    map_t* _map = get_map();
    for (iter_t _cb = _map->begin(); _cb != _map->end(); _cb++) {
      printf("'%s' ", _cb->first.name.c_str());
    }
    printf("\n");
  };
  bool insert(std::string name, int priority, wrap_t fn) {
    cb_id id = {name, priority};
    return get_map()->insert(pair_t(id, fn)).second;
  };
  bool insert(std::string name, int priority, func_t fn) {
    cb_id id = {name, priority};
    // wrap function in boost::function
    wrap_t wrapper = fn;
    return get_map()->insert(pair_t(id, wrapper)).second;
  };
  wrap_t assign(std::string name, int priority, wrap_t fn) {
    cb_id id = {name, priority};
    // wrap function in boost::function
    wrap_t wrapper = fn;
    return (*get_map())[id] = wrapper;
  };
  wrap_t assign(std::string name, int priority, func_t fn) {
    cb_id id = {name, priority};
    return (*get_map())[id] = fn;
  };
  wrap_t assign(std::string name, wrap_t fn) {
    iter_t iter = find(name);
    if (iter != map->end()) {
      iter->second = fn;
    }
    return fn;
  };
  int rm(std::string name) {
    iter_t iter = find(name);
    if (iter == map->end()) {
      return 0;
    }
    get_map()->erase(iter);
    return 1;
  };
};

////////////////////////////////////////////////////////////////////////////////

class tag {
  const std::string _ident;
  const std::string str;
 public :
  const char* ident;
  const unsigned int subident;
  tag(const char* ident, const unsigned int subident);
  ~tag();
  bool operator> (const tag& key) const;
  bool operator< (const tag& key) const;
  const char* id() const;
};

struct msg {
  unsigned int level;
  const char* text;
  msg(const unsigned int level, const char* text);
  const char* severity() const;
};

class msg_tags {
 public :
  typedef std::map<const tag, const msg> tagmap;
  typedef tagmap::const_iterator const_iterator;
  typedef tagmap::value_type value_type;
 private :
  tagmap* map;
 public :
  msg_tags();
  ~msg_tags();
  tagmap& getmap();
  const const_iterator add(const char* ident, const unsigned int subident, const unsigned int level, const char* text);
  const msg& get(const char* ident, const unsigned int subident);
  const msg& get(const tag& id);
};

////////////////////////////////////////////////////////////////////////////////

struct control {
  bool echo;
  int  threshold;
  int  count;
  int  increment();
  int  toomany();
};

struct status_result {
  bool  flag;
  const char* text;
};

typedef void cb_emit_fn(const cb_id&, unsigned int, timespec&, char*, const tag*, char*, unsigned int, char*);
typedef void cb_terminate_fn(const cb_id&);

class message {
 protected :
  static message* self;
  callbacks<cb_emit_fn> cb_emit;
  callbacks<cb_terminate_fn> cb_terminate;
  msg_tags tags;

  int terminating_cnt;
  bool terminated;
  control attrs[MAX_LEVEL];

  unsigned int filter(unsigned int level);

 public :
  message();
  ~message();

  static message* instance();
  static void do_terminate();
  static int  terminate();
  static int  terminating();

  static char* name(int level);
  static char* name(enum levels level);
  static control* get_ctrl();
  static control* get_ctrl(unsigned int level);
  static void verbosity(unsigned int level);

  static callbacks<cb_emit_fn>* get_cb_emit();
  static callbacks<cb_terminate_fn>* get_cb_terminate();
  static msg_tags& get_tags();

  void emit(unsigned int level, char* file, unsigned int line, char* text);
  void emitf(unsigned int level, char* file, unsigned int line, char* text, va_list args);
  void by_id(char* ident, unsigned int subident, char* file, unsigned int line, ...);
  void by_msg(const msg_tags::const_iterator& msg, char* file, unsigned int line, ...);
  void by_msg(const msg_tags::const_iterator& msg, char* formatted, char* file, unsigned int line, ...);

  int  errors();
  struct status_result status();

  #define SEVERITY(level) void level(char* file, unsigned int line, char* text, ...);

  SEVERITY(int_debug  );
  SEVERITY(debug      );
  SEVERITY(information);
  SEVERITY(note       );
  SEVERITY(success    );
  SEVERITY(warning    );
  SEVERITY(error      );
  SEVERITY(internal   );
  SEVERITY(fatal      );

  #undef SEVERITY

};

}

#define INT_DEBUG(MSG, ...)   example::message::instance()->int_debug  ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define DEBUG(MSG, ...)       example::message::instance()->debug      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define INFORMATION(MSG, ...) example::message::instance()->information((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define NOTE(MSG, ...)        example::message::instance()->note       ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define SUCCESS(MSG, ...)     example::message::instance()->success    ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define WARNING(MSG, ...)     example::message::instance()->warning    ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define ERROR(MSG, ...)       example::message::instance()->error      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define INTERNAL(MSG, ...)    example::message::instance()->internal   ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define FATAL(MSG, ...)       example::message::instance()->fatal      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define MSG_BY_IDENT(IDENT, SUBIDENT, ...) example::message::instance()->by_id(IDENT, SUBIDENT, (char*)__FILE__, __LINE__, ## __VA_ARGS__)

