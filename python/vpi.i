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

  __attribute__ ((weak)) void (*vlog_startup_routines[])() = { 0 };
  __attribute__ ((weak)) PLI_INT32 vpi_remove_cb (vpiHandle cb_obj);
  __attribute__ ((weak)) void vpi_get_cb_info (vpiHandle object, p_cb_data cb_data_p);
  __attribute__ ((weak)) void vpi_get_systf_info (vpiHandle object, p_vpi_systf_data systf_data_p);
  __attribute__ ((weak)) vpiHandle vpi_handle_by_index (vpiHandle object, PLI_INT32 indx);
  __attribute__ ((weak)) vpiHandle vpi_handle_multi (PLI_INT32 type, vpiHandle refHandle1, vpiHandle   refHandle2, ... );
  __attribute__ ((weak)) PLI_INT64 vpi_get64   (PLI_INT32 property, vpiHandle object);
  __attribute__ ((weak)) void vpi_get_delays (vpiHandle object, p_vpi_delay delay_p);
  __attribute__ ((weak)) void vpi_put_delays (vpiHandle object,p_vpi_delay delay_p);
  __attribute__ ((weak)) void vpi_get_value_array (vpiHandle object, p_vpi_arrayvalue arrayvalue_p, PLI_INT32 *index_p, PLI_UINT32 num);
  __attribute__ ((weak)) void vpi_put_value_array (vpiHandle object, p_vpi_arrayvalue arrayvalue_p, PLI_INT32 *index_p, PLI_UINT32 num);
  __attribute__ ((weak)) PLI_UINT32   vpi_mcd_open  (PLI_BYTE8 *fileName);
  __attribute__ ((weak)) PLI_UINT32   vpi_mcd_close (PLI_UINT32 mcd);
  __attribute__ ((weak)) PLI_BYTE8   *vpi_mcd_name  (PLI_UINT32 cd);
  __attribute__ ((weak)) PLI_INT32    vpi_mcd_printf(PLI_UINT32 mcd, PLI_BYTE8 *format, ...);
  __attribute__ ((weak)) PLI_INT32    vpi_compare_objects (vpiHandle object1, vpiHandle object2);
  __attribute__ ((weak)) PLI_INT32    vpi_chk_error       (p_vpi_error_info error_info_p);
  __attribute__ ((weak)) PLI_INT32    vpi_free_object     (vpiHandle object);
  __attribute__ ((weak)) PLI_INT32    vpi_release_handle  (vpiHandle object);
  __attribute__ ((weak)) PLI_INT32    vpi_put_data(PLI_INT32 id, PLI_BYTE8 *dataLoc, PLI_INT32 numOfBytes);
  __attribute__ ((weak)) PLI_INT32    vpi_get_data(PLI_INT32 id, PLI_BYTE8 *dataLoc, PLI_INT32 numOfBytes);
  __attribute__ ((weak)) void        *vpi_get_userdata    (vpiHandle obj);
  __attribute__ ((weak)) PLI_INT32    vpi_put_userdata    (vpiHandle obj, void *userdata);
  __attribute__ ((weak)) PLI_INT32    vpi_mcd_vprintf     (PLI_UINT32 mcd, PLI_BYTE8 *format, va_list ap);
  __attribute__ ((weak)) PLI_INT32    vpi_flush           (void);
  __attribute__ ((weak)) PLI_INT32    vpi_mcd_flush       (PLI_UINT32 mcd);
  __attribute__ ((weak)) vpiHandle    vpi_handle_by_multi_index (vpiHandle obj, PLI_INT32 num_index, PLI_INT32 *index_array);

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
