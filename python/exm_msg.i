// Copyright (c) 2012 Rich Porter - see LICENSE for further details

%module exm_msg

%{
  #include "message.h"

  struct PythonCallbackTerminate {
    PyObject *func;
    PythonCallbackTerminate(PyObject *func) : func(func) {};

    void operator()(void) {
      PyObject *result, *arglist;
    
      if (PyCallable_Check(func) < 1) {
        return;
      }
  
      result = PyObject_CallFunction(func, "()");     // Call Python
      if (result == NULL) {
        fprintf(stderr, "function call returned NULL\n");
      }
  
      Py_XDECREF(result);
      return;
    }
  };

  struct PythonCallbackEmit {
    static std::map<char*, PythonCallbackEmit*> hash;
    PyObject *name;
    PyObject *func;
    char *c_str_name;
    PythonCallbackEmit(PyObject *name, PyObject *func) : name(name), func(func) {
      Py_INCREF(name);
      Py_INCREF(func);
      c_str_name = PyString_AsString(name);
      hash[c_str_name] = this;
    };
    ~PythonCallbackEmit() {
      Py_DECREF(name);
      Py_DECREF(func);
      hash.erase(c_str_name);
    };

    void operator()(unsigned int level, char* severity, char *file, unsigned int line, char* text) {

      PyObject *result, *arglist;
    
      if (PyCallable_Check(func) < 1) {
        return;
      }
  
      result = PyObject_CallFunction(func, "(i, s, s, i, s)", level, severity, file, line, text);     // Call Python
      if (result == NULL) {
        fprintf(stderr, "function call returned NULL\n");
      }
  
      Py_XDECREF(result);
      return;
    }
    static void rm(char* ref) {
      delete hash[ref];
    }
  };

  std::map<char*, PythonCallbackEmit*> PythonCallbackEmit::hash;

  class StringError {};
  class FuncError {};


%}

%ignore example::message::emit(unsigned int level, char *file, unsigned int line, char* text, va_list args);

%include "std_string.i"
%include "std_map.i"

/* Parse the header file to generate wrappers */
%include "message.h"


namespace example {

%exception Tcallbacks<cb_emit_fn>::add_callback {
  try {
  	$function
  } catch (::StringError &e) {
 	PyErr_SetString(PyExc_TypeError, "String object required");
	return NULL;
  } catch (::FuncError &e) {
 	PyErr_SetString(PyExc_TypeError, "Function object required");
	return NULL;
  }
}
%exception;

  %template() ::std::map<::std::string, cb_emit_fn>;
  %template(cb_emit) Tcallbacks<cb_emit_fn>;
  %extend Tcallbacks<cb_emit_fn> {
    void add_callback(PyObject *pyname, PyObject *pyfunc) {
      if (!PyString_Check(pyname)) {
        throw StringError();
      }
      if (!PyCallable_Check(pyfunc)) {
        PyErr_SetString(PyExc_TypeError, "Need a callable object!");
        throw FuncError();
      }
      PythonCallbackEmit* pcb = new PythonCallbackEmit(pyname, pyfunc);
      ::example::cb_emit_fn cb = boost::ref(*pcb);
      self->insert_to_map(::std::string(pcb->c_str_name), cb);
    }
    void rm_callback(PyObject *pyname) {
      if (!PyString_Check(pyname)) {
        throw StringError();
      }
      self->rm_from_map(::std::string(PyString_AsString(pyname)));
      PythonCallbackEmit::rm(PyString_AsString(pyname));
    }
  }

  %template() ::std::map<::std::string, cb_terminate_fn>;
  %template(cb_terminate) Tcallbacks<cb_terminate_fn>;
  %extend Tcallbacks<cb_terminate_fn> {
    void add_callback(PyObject *pyname, PyObject *pyfunc) {
      if (!PyCallable_Check(pyfunc)) {
        PyErr_SetString(PyExc_TypeError, "Need a callable object!");
        return;
      }
      ::example::cb_terminate_fn cb = PythonCallbackTerminate(pyfunc);
      self->insert_to_map(::std::string(PyString_AsString(pyname)), cb);
    }
  }
}
