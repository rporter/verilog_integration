#include <cstddef>
#include <stdarg.h>
#include <time.h>
#include <string>
#include <map>
#include <boost/function.hpp>

namespace example {

////////////////////////////////////////////////////////////////////////////////

enum levels {
  INT_DEBUG,
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
  bool operator> (const cb_id& key) const {
    if (key.name == name) return false;
    return key.priority < priority;
  }
  bool operator< (const cb_id& key) const {
    if (key.name == name) return false;
    return key.priority > priority;
  }
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
    for (iter_t _cb = map->begin(); _cb != map->end(); _cb++) {
      if (_cb->first.name == name) {
        return _cb;
      }
    }
    return map->end();
  };
public :
  callbacks() : map(NULL) {};
  ~callbacks() {};
  map_t* get_map() {
    if (NULL == map) {
      map = new map_t();
    }
    return map;
  }
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

   struct tag {
     const char* ident;
     const unsigned int subident;
     char *str;
     static const unsigned int size;
     tag(const char* ident, const unsigned int subident) : ident(ident), subident(subident), str(NULL) {};
     ~tag() {
       if (str != NULL) free(str);
     }
     bool operator> (const tag& key) const {
       int cmp = strcmp(key.ident, ident);
       if (cmp == 0) return key.subident > subident;
       return cmp > 0;
     }
     bool operator< (const tag& key) const {
       int cmp = strcmp(key.ident, ident);
       if (cmp == 0) return key.subident < subident;
       return cmp < 0;
     }
     const char* id() {
       str = (char *)malloc(size);
       snprintf(str, sizeof(str), "%s-%d", ident, subident);
       return str;
     }
   };

  const unsigned int tag::size = 16;

  struct msg {
    const unsigned int level;
    const char* text;
    msg(const unsigned int level, const char* text) : level(level), text(text) {};
  };

 class msg_tags {
 public :
   typedef std::map<const tag, const msg*> tagmap;
   typedef tagmap::const_iterator const_iterator;
  private :
   tagmap* map;
  public :
   msg_tags() : map(NULL) {
   }
   ~msg_tags() {
     if (map != NULL) {
       delete map;
     }
   }
   tagmap& getmap() {
     if (map == NULL) {
       map = new tagmap();
     }
     return *map;
   }
   void add(const char* ident, const unsigned int subident, unsigned int level, const char* text) {
     tag _tag(ident, subident);
     msg* _msg = new msg(level, text);
     getmap()[_tag] = _msg; // memory leak on replace
   }
   const msg& get(const char* ident, const unsigned int subident) {
     tag _tag(ident, subident);
     const_iterator it = getmap().find(_tag);
     if (it == getmap().end()) {
       static msg err = msg(ERROR, "can't find message by id");
       return err;
     }
     return *getmap()[_tag];
   }
  };

////////////////////////////////////////////////////////////////////////////////

struct control {
  bool echo;
  int  threshold;
  int  count;
};

struct status_result {
  bool  flag;
  const char* text;
};

 typedef void cb_emit_fn(const cb_id&, unsigned int, timespec&, char*, char*, unsigned int, char*);
 typedef void cb_terminate_fn(const cb_id&);

class message {
 public :
 protected :
  static message* self;
  callbacks<cb_emit_fn> cb_emit;
  callbacks<cb_terminate_fn> cb_terminate;

  int terminating_cnt;
  control attrs[MAX_LEVEL];

 public :
  message();
  ~message();

  static message* instance();
  static void destroy();
  static void terminate();
  static int  terminating();

  static char* name(int level);
  static char* name(enum levels level);
  static control* get_ctrl();
  static control* get_ctrl(unsigned int level);
  static void verbosity(unsigned int level);

  static callbacks<cb_emit_fn>* get_cb_emit();
  static callbacks<cb_terminate_fn>* get_cb_terminate();

  void emit(unsigned int level, char* file, unsigned int line, char* text, va_list args);
  void by_id(char* ident, unsigned int subident, char* file, unsigned int line, ...);

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

