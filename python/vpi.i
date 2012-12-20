// Copyright (c) 2012 Rich Porter - see LICENSE for further details

%module vpi

%{
#include "vltstd/vpi_user.h"

int _cbwrap_cb(p_cb_data cbp) {
    PyObject *fn,*result;

    fn=(PyObject *)cbp->user_data;

    if (PyCallable_Check(fn) < 1) {
      return 1;
    }

    result=PyObject_CallFunctionObjArgs(fn, NULL);

    if (result == NULL) {
      PyErr_SetString(PyExc_TypeError, "function call returned NULL");
    }

    return 0;
}
%}

%ignore vpi_vprintf(PLI_BYTE8 *format, va_list ap);
%ignore vpi_mcd_vprintf(PLI_UINT32 mcd, PLI_BYTE8 *format, va_list ap);

/* Parse the header file to generate wrappers */
%include "vltstd/vpi_user.h"

%extend s_cb_data {

  void script(PyObject *pyfunc){
    if (!PyCallable_Check(pyfunc)) {
      PyErr_SetString(PyExc_TypeError, "Need a callable object!");
      return;
    }
    self->cb_rtn=(PLI_INT32 (void*)(struct t_cb_data*))_cbwrap_cb;
    self->user_data=(PLI_BYTE8*)pyfunc;
    Py_INCREF(pyfunc);
  }

}
