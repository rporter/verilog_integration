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
    PyObject *func;
    PythonCallbackEmit(PyObject *func) : func(func) {
      Py_INCREF(func);
    };
    ~PythonCallbackEmit() {
      //      Py_XDECREF(func);
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
  };
%}

%ignore example::message::emit(unsigned int level, char *file, unsigned int line, char* text, va_list args);

%include "std_string.i"
%include "std_map.i"

/* Parse the header file to generate wrappers */
%include "message.h"

namespace example {
  %template() ::std::map<::std::string, cb_emit_fn>;
  %template(cb_emit) Tcallbacks<cb_emit_fn>;
  %extend Tcallbacks<cb_emit_fn> {
    void add_callback(PyObject *pyname, PyObject *pyfunc) {
      if (!PyCallable_Check(pyfunc)) {
        PyErr_SetString(PyExc_TypeError, "Need a callable object!");
        return;
      }
      ::example::cb_emit_fn cb = PythonCallbackEmit(pyfunc);
      self->insert_to_map(::std::string(PyString_AsString(pyname)), cb);
    }
    void rm_callback(PyObject *pyname) {
      if (!PyString_Check(pyname)) {
        PyErr_SetString(PyExc_TypeError, "Need a string object!");
        return;
      }
      self->rm_from_map(::std::string(PyString_AsString(pyname)));
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
