// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

%module exm_msg

%{
  #define SWIG_PYTHON_EXTRA_NATIVE_CONTAINERS 

  #include "message.h"

  class ident {
    // This is a simple class that wraps around code adding and emitting message by ident
    // Fixes issue in swig with destructor of std::map::const_iterator (there isn't one)
  protected :
    example::msg_tags::const_iterator msg;
  public:
    ident(const char* ident, const unsigned int subident, const unsigned int level, const char* text) {
      msg = example::message::instance()->get_tags().add(ident, subident, level, text);
    }
    ~ident() {};
    void operator()(char* file, unsigned int line) {
      example::message::instance()->by_msg(msg, file, line);
    }
  };

  template <typename func_t>
    class callbacks {
  public :
    typedef boost::function<func_t> wrap_t;
    typedef std::pair<std::string, wrap_t> pair_t;
    typedef std::map<std::string, wrap_t> map_t;
  protected :
    map_t* map;
  public :
    callbacks();
    ~callbacks();
    map_t* get_map();
    bool insert(std::string name, int priority, wrap_t fn);
    wrap_t assign(std::string name, int priority, func_t fn);
    wrap_t assign(std::string name, int priority, wrap_t fn);
    int rm_from_map(std::string name);
  };

  template <typename func_t>
  struct PythonCallback {
    typedef std::map<char*, PythonCallback*> map_t;
    static map_t* hash;
    PyObject *name;
    PyObject *func;
    char *c_str_name;
    PythonCallback (PyObject *name, PyObject *func) : name(name), func(func) {
      Py_INCREF(name);
      Py_INCREF(func);
      c_str_name = PyString_AsString(name);
      (*hash)[c_str_name] = this;
    };
    ~PythonCallback() {
      Py_DECREF(name);
      Py_DECREF(func);
      hash->erase(c_str_name);
    };

    void operator()(const example::cb_id& id) {
      PyObject *result, *arglist;
    
      if (PyCallable_Check(func) < 1) {
        INTERNAL("function call associated with %s no longer callable", c_str_name);
        return;
      }

      PyObject *instance = SWIG_NewPointerObj(SWIG_as_voidptr(&id), SWIGTYPE_p_example__cb_id, 0);

      result = PyObject_CallFunction(func, (char*)"(O)", instance);     // Call Python

      if (result == NULL) {
	WARNING("function call associated with %s returned NULL", c_str_name);
      }
  
      Py_XDECREF(result);
      return;
    }

    void operator()(const example::cb_id& id, unsigned int level, timespec& when, char* severity, const example::tag* tag, char *file, unsigned int line, char* text) {

      PyObject *result, *arglist;
    
      if (PyCallable_Check(func) < 1) {
        INTERNAL("function call associated with %s no longer callable", c_str_name);
        return;
      }

      PyObject *instance = SWIG_NewPointerObj(SWIG_as_voidptr(&id), SWIGTYPE_p_example__cb_id, 0);
      PyObject *pywhen   = SWIG_NewPointerObj(SWIG_as_voidptr(&when), SWIGTYPE_p_timespec, 0);
      PyObject *pytag    = SWIG_NewPointerObj(SWIG_as_voidptr(tag), SWIGTYPE_p_example__tag, 0);

      result = PyObject_CallFunction(func, (char*)"(O, O, i, s, O, s, i, s)", instance, pywhen, level, severity, pytag, file, line, text);     // Call Python
      if (result == NULL) {
        rm(c_str_name);
        WARNING("function call associated with %s returned NULL", c_str_name);
      }
  
      Py_XDECREF(result);
      return;
    }

    static typename callbacks<func_t>::wrap_t callback(PyObject *pyname, PyObject *pyfunc) {
      PythonCallback* pcb = new PythonCallback(pyname, pyfunc);
      typename callbacks<func_t>::wrap_t cb = boost::ref(*pcb);
      return cb;
    }

    static void rm(char* ref) {
      delete (*hash)[ref];
    }
  };

  class StringError {};
  class NumError {};
  class FuncError {};

  template<> PythonCallback<example::cb_emit_fn>::map_t*      PythonCallback<example::cb_emit_fn>::hash      = new PythonCallback<example::cb_emit_fn>::map_t();
  template<> PythonCallback<example::cb_terminate_fn>::map_t* PythonCallback<example::cb_terminate_fn>::hash = new PythonCallback<example::cb_terminate_fn>::map_t();

%}

%ignore example::message::emit(unsigned int level, char *file, unsigned int line, char* text, va_list args);

%include "std_string.i"
%include "std_map.i"

/* Parse the header file to generate wrappers */
%include "message.h"

struct timespec {
    long     tv_sec;        /* seconds */
    long     tv_nsec;       /* nanoseconds */
};

class ident {
protected :
  const example::msg_tags::const_iterator msg;
public:
  ident(const char* ident, const unsigned int subident, const unsigned int level, const char* text);
  ~ident();
  void operator()(char* file, unsigned int line);
};

namespace example {

  %exception callbacks<cb_emit_fn>::add_callback {
    try {
    	$function
    } catch (::StringError &e) {
   	PyErr_SetString(PyExc_TypeError, "String object required");
  	return NULL;
    } catch (::NumError &e) {
   	PyErr_SetString(PyExc_TypeError, "Number object required");
  	return NULL;
    } catch (::FuncError &e) {
   	PyErr_SetString(PyExc_TypeError, "Function object required");
  	return NULL;
    }
  }
  %exception;

  %template() ::std::map<::std::string, cb_emit_fn>;
  %template(cb_emit) callbacks<cb_emit_fn>;
  %extend callbacks<cb_emit_fn> {
    void add_callback(PyObject *pyname, PyObject *pynum, PyObject *pyfunc) {
      if (!PyString_Check(pyname)) {
        throw StringError();
      }
      if (!PyNumber_Check(pynum)) {
        throw NumError();
      }
      if (!PyCallable_Check(pyfunc)) {
        throw FuncError();
      }
      self->assign(::std::string(PyString_AsString(pyname)), PyInt_AsSsize_t(pynum), PythonCallback<example::cb_emit_fn>::callback(pyname, pyfunc));
    }
    void rm_callback(PyObject *pyname) {
      if (!PyString_Check(pyname)) {
        throw StringError();
      }
      char *str = PyString_AsString(pyname);
      self->rm(::std::string(str));
      PythonCallback<example::cb_emit_fn>::rm(str);
    }
  }

  %exception callbacks<cb_terminate_fn>::add_callback {
    try {
    	$function
    } catch (::StringError &e) {
   	PyErr_SetString(PyExc_TypeError, "String object required");
  	return NULL;
    } catch (::NumError &e) {
   	PyErr_SetString(PyExc_TypeError, "Number object required");
  	return NULL;
    } catch (::FuncError &e) {
   	PyErr_SetString(PyExc_TypeError, "Function object required");
  	return NULL;
    }
  }
  %exception;

  %template() ::std::map<::std::string, cb_terminate_fn>;
  %template(cb_terminate) callbacks<cb_terminate_fn>;
  %extend callbacks<cb_terminate_fn> {
    void add_callback(PyObject *pyname, PyObject *pynum, PyObject *pyfunc) {
      if (!PyString_Check(pyname)) {
        throw StringError();
      }
      if (!PyNumber_Check(pynum)) {
        throw NumError();
      }
      if (!PyCallable_Check(pyfunc)) {
        throw FuncError();
      }
      self->assign(::std::string(PyString_AsString(pyname)), PyInt_AsSsize_t(pynum), PythonCallback<example::cb_terminate_fn>::callback(pyname, pyfunc));
    }
    void rm_callback(PyObject *pyname) {
      if (!PyString_Check(pyname)) {
        throw StringError();
      }
      char *str = PyString_AsString(pyname);
      self->rm(::std::string(str));
      PythonCallback<example::cb_terminate_fn>::rm(str);
    }
  }
}
