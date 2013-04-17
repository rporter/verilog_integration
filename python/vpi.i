// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

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

/*
 * Follows weak references for simulators that do not fully support 
 * IEEE Std 1800-2012 Programming Language Interface (PLI)
 *
 */

#define PROTO_PARAMS(params) params
#define XXTERN __attribute__ ((weak))

// START COPIED FROM vpi_user.h

/**************************** FUNCTION DECLARATIONS ***************************/

/* Include compatibility mode macro definitions. */
//#include "vpi_compatibility.h"

/* callback related */

XXTERN vpiHandle    vpi_register_cb     PROTO_PARAMS((p_cb_data cb_data_p));
XXTERN PLI_INT32    vpi_remove_cb       PROTO_PARAMS((vpiHandle cb_obj));
XXTERN void         vpi_get_cb_info     PROTO_PARAMS((vpiHandle object,
                                                      p_cb_data cb_data_p));
XXTERN vpiHandle    vpi_register_systf  PROTO_PARAMS((p_vpi_systf_data
                                                      systf_data_p));
XXTERN void         vpi_get_systf_info  PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_systf_data
                                                      systf_data_p));

/* for obtaining handles */

XXTERN vpiHandle    vpi_handle_by_name  PROTO_PARAMS((PLI_BYTE8    *name,
                                                      vpiHandle    scope));
XXTERN vpiHandle    vpi_handle_by_index PROTO_PARAMS((vpiHandle    object,
                                                      PLI_INT32    indx));

/* for traversing relationships */

XXTERN vpiHandle    vpi_handle          PROTO_PARAMS((PLI_INT32   type,
                                                      vpiHandle   refHandle));
XXTERN vpiHandle    vpi_handle_multi    PROTO_PARAMS((PLI_INT32   type,
                                                      vpiHandle   refHandle1,
                                                      vpiHandle   refHandle2,
                                                      ... ));
XXTERN vpiHandle    vpi_iterate         PROTO_PARAMS((PLI_INT32   type,
                                                      vpiHandle   refHandle));
XXTERN vpiHandle    vpi_scan            PROTO_PARAMS((vpiHandle   iterator));

/* for processing properties */

XXTERN PLI_INT32    vpi_get             PROTO_PARAMS((PLI_INT32   property,
                                                      vpiHandle   object));
XXTERN PLI_INT64    vpi_get64           PROTO_PARAMS((PLI_INT32   property,
                                                      vpiHandle   object));
XXTERN PLI_BYTE8   *vpi_get_str         PROTO_PARAMS((PLI_INT32   property,
                                                      vpiHandle   object));

/* delay processing */

XXTERN void         vpi_get_delays      PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_delay delay_p));
XXTERN void         vpi_put_delays      PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_delay delay_p));

/* value processing */

XXTERN void         vpi_get_value       PROTO_PARAMS((vpiHandle expr,
                                                      p_vpi_value value_p));
XXTERN vpiHandle    vpi_put_value       PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_value value_p,
                                                      p_vpi_time time_p,
                                                      PLI_INT32 flags));
XXTERN void         vpi_get_value_array PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_arrayvalue arrayvalue_p,
                                                      PLI_INT32 *index_p,
                                                      PLI_UINT32 num));
XXTERN void         vpi_put_value_array PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_arrayvalue arrayvalue_p,
                                                      PLI_INT32 *index_p,
                                                      PLI_UINT32 num));

/* time processing */

XXTERN void         vpi_get_time        PROTO_PARAMS((vpiHandle object,
                                                      p_vpi_time time_p));

/* I/O routines */

XXTERN PLI_UINT32   vpi_mcd_open        PROTO_PARAMS((PLI_BYTE8 *fileName));
XXTERN PLI_UINT32   vpi_mcd_close       PROTO_PARAMS((PLI_UINT32 mcd));
XXTERN PLI_BYTE8   *vpi_mcd_name        PROTO_PARAMS((PLI_UINT32 cd));
XXTERN PLI_INT32    vpi_mcd_printf      PROTO_PARAMS((PLI_UINT32 mcd,
                                                      PLI_BYTE8 *format,
                                                      ...));
XXTERN PLI_INT32    vpi_printf          PROTO_PARAMS((PLI_BYTE8 *format,
                                                      ...));

/* utility routines */

XXTERN PLI_INT32    vpi_compare_objects PROTO_PARAMS((vpiHandle object1,
                                                      vpiHandle object2));
XXTERN PLI_INT32    vpi_chk_error       PROTO_PARAMS((p_vpi_error_info
                                                      error_info_p));
/* vpi_free_object() was deprecated in 1800-2009 */
XXTERN PLI_INT32    vpi_free_object     PROTO_PARAMS((vpiHandle object));
XXTERN PLI_INT32    vpi_release_handle  PROTO_PARAMS((vpiHandle object));
XXTERN PLI_INT32    vpi_get_vlog_info   PROTO_PARAMS((p_vpi_vlog_info
                                                      vlog_info_p));

/* routines added with 1364-2001 */

XXTERN PLI_INT32    vpi_get_data        PROTO_PARAMS((PLI_INT32 id,
                                                      PLI_BYTE8 *dataLoc,
                                                      PLI_INT32 numOfBytes));
XXTERN PLI_INT32    vpi_put_data        PROTO_PARAMS((PLI_INT32 id,
                                                      PLI_BYTE8 *dataLoc,
                                                      PLI_INT32 numOfBytes));
XXTERN void        *vpi_get_userdata    PROTO_PARAMS((vpiHandle obj));
XXTERN PLI_INT32    vpi_put_userdata    PROTO_PARAMS((vpiHandle obj,
                                                      void *userdata));
XXTERN PLI_INT32    vpi_vprintf         PROTO_PARAMS((PLI_BYTE8 *format,
                                                      va_list ap));
XXTERN PLI_INT32    vpi_mcd_vprintf     PROTO_PARAMS((PLI_UINT32 mcd,
                                                      PLI_BYTE8 *format,
                                                      va_list ap));
XXTERN PLI_INT32    vpi_flush           PROTO_PARAMS((void));
XXTERN PLI_INT32    vpi_mcd_flush       PROTO_PARAMS((PLI_UINT32 mcd));
XXTERN PLI_INT32    vpi_control         PROTO_PARAMS((PLI_INT32 operation,
                                                      ...));
XXTERN vpiHandle    vpi_handle_by_multi_index PROTO_PARAMS((vpiHandle obj,
                                                      PLI_INT32 num_index,
                                                      PLI_INT32 *index_array));
/****************************** GLOBAL VARIABLES ******************************/

#if (defined(_MSC_VER) || defined(__MINGW32__) || defined(__CYGWIN__))
#ifndef PLI_DLLESPEC
#define PLI_DLLESPEC __declspec(dllexport)
#endif
#else
#ifndef PLI_DLLESPEC
#define PLI_DLLESPEC
#endif
#endif

XXTERN PLI_DLLESPEC void (*vlog_startup_routines[])() /*ADDED*/ = { 0 } /*END ADDED*/;

  /* array of function pointers, last pointer should be null */

// END COPIED FROM vpi_user.h
#undef PLI_DLLESPEC
#undef XXTERN
#undef PROTO_PARAMS

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
    self->cb_rtn=(PLI_INT32 (*)(struct t_cb_data*))_cbwrap_cb;
    self->user_data=(PLI_BYTE8*)pyfunc;
    Py_INCREF(pyfunc);
  }

}
