#include <cstddef>
#include <stdarg.h>
#include <string>
#include <map>
#include "boost/function.hpp"

namespace example {

template <typename func>
  class Tcallbacks {
protected :
  std::map<std::string, func>* map;
public :
  Tcallbacks() : map(NULL) {};
  ~Tcallbacks() {};
  std::map<std::string, func>* get_map() {
    if (NULL == map) {
      map = new std::map<std::string, func>();
    }
    return map;
  }
  bool insert_to_map(std::string name, func fn) {
    return get_map()->insert(std::pair<std::string, func>(name, fn)).second;
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

//typedef void (*cb_emit_fn)(unsigned int level, char* severity, char *file, unsigned int line, char* text);
//typedef void (*cb_terminate_fn)(void);
typedef boost::function<void(unsigned int level, char* severity, char *file, unsigned int line, char* text)> cb_emit_fn;
typedef boost::function<void(void)> cb_terminate_fn;

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
  Tcallbacks<cb_emit_fn> cb_emit;
  Tcallbacks<cb_terminate_fn> cb_terminate;

  control attrs[MAX_LEVEL];

 public :
  message();
  ~message();

  static message* instance();
  static void destroy();
  static void terminate();

  static char* name(int level);
  static char* name(enum levels level);
  static control* get_ctrl();
  static control* get_ctrl(unsigned int level);
  static void verbosity(unsigned int level);

  static Tcallbacks<cb_emit_fn>* get_cb_emit();
  static Tcallbacks<cb_terminate_fn>* get_cb_terminate();

  void emit(unsigned int level, char* severity, char *file, unsigned int line, char* text, va_list args);

  #define SEVERITY(level) void level(char *file, unsigned int line, char* text, ...);

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
#define DEBUG(MSG, ...)       example::message::instance()->int_debug  ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)

#define INFORMATION(MSG, ...) example::message::instance()->information((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define NOTE(MSG, ...)        example::message::instance()->note       ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define ERROR(MSG, ...)       example::message::instance()->error      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define INTERNAL(MSG, ...)    example::message::instance()->internal   ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)
#define FATAL(MSG, ...)       example::message::instance()->fatal      ((char*)__FILE__, __LINE__, (char*)MSG, ## __VA_ARGS__)


