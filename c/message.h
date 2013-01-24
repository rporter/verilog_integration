#include <cstddef>
#include <stdarg.h>
#include <string>
#include <map>
#include <boost/function.hpp>

namespace example {

template <typename func_t>
  class callbacks {
public :
  typedef boost::function<func_t> wrap_t;
  typedef std::pair<std::string, wrap_t> pair_t;
  typedef std::map<std::string, wrap_t> map_t;
protected :
  map_t* map;
public :
  callbacks() : map(NULL) {};
  ~callbacks() {};
  map_t* get_map() {
    if (NULL == map) {
      map = new map_t();
    }
    return map;
  }
  bool insert_to_map(std::string name, wrap_t fn) {
    return get_map()->insert(pair_t(name, fn)).second;
  };
  wrap_t assign(std::string name, func_t fn) {
    // wrap function in boost::function
    wrap_t wrapper = fn;
    return (*get_map())[name] = wrapper;
  };
  wrap_t assign(std::string name, wrap_t fn) {
    return (*get_map())[name] = fn;
  };
  int rm_from_map(std::string name) {
    return get_map()->erase(name);
  };
};

struct control {
  bool echo;
  int  threshold;
  int  count;
};

typedef void cb_emit_fn(unsigned int, char*, char*, unsigned int, char*);
typedef void cb_terminate_fn(void);

enum levels {
  INT_DEBUG,
  DEBUG,
  INFORMATION,
  NOTE,
  WARNING,
  ERROR,
  INTERNAL,
  FATAL,
  MAX_LEVEL
};

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

  #define SEVERITY(level) void level(char* file, unsigned int line, char* text, ...);

  SEVERITY(int_debug  );
  SEVERITY(debug      );
  SEVERITY(information);
  SEVERITY(note       );
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
#define WARNING(MSG, ...)     example::message::instance()->warning    ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define ERROR(MSG, ...)       example::message::instance()->error      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define INTERNAL(MSG, ...)    example::message::instance()->internal   ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define FATAL(MSG, ...)       example::message::instance()->fatal      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)


