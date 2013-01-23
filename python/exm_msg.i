// Copyright (c) 2012 Rich Porter - see LICENSE for further details

%module exm_msg

%{
#include "message.h"
%}

%ignore example::message::emit(unsigned int level, char* severity, char *file, unsigned int line, char* text, va_list args);

%include "std_string.i"
%include "std_map.i"

/* Parse the header file to generate wrappers */
%include "message.h"

namespace example {
%template(callbacks_emit) callbacks<cb_emit_fn>;
%template(callbacks_terminate) callbacks<cb_terminate_fn>;

%extend callbacks<cb_emit_fn> {
     void add_callback(PyObject *pyfunc) {
     }
}

}
