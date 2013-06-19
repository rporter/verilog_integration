// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include "boost/format.hpp"

#include "vpi_user.h"
#include "exm_python.h"
#include "message.h"

int exm_python_vpi(char* arg) {
  vpiHandle href;
  vpiHandle arglist;
  s_vpi_value vpi_value;

  href = vpi_handle(vpiSysTfCall, 0);
  arglist = vpi_iterate(vpiArgument, href);
  vpi_value.format = vpiStringVal;
  vpi_get_value(vpi_scan(arglist), &vpi_value);

  return exm_python(vpi_value.value.str);
}

int exm_message(char* level, ...) {
  vpiHandle href;
  vpiHandle arglist;
  vpiHandle arg;
  s_vpi_value vpi_value;
  const char *result;
  va_list args;
  boost::format tmpl;

  href = vpi_handle(vpiSysTfCall, 0);
  arglist = vpi_iterate(vpiArgument, href);
  vpi_value.format = vpiStringVal;
  if (arg=vpi_scan(arglist)) {
    vpi_get_value(arg, &vpi_value);
  } else {
    WARNING("Message has no arguments");
    result = "** No Message Given **";
    goto emit;
  }

  try {
    tmpl.parse(vpi_value.value.str);
  } catch (boost::io::bad_format_string& exc) {
    WARNING("Format raised %s", exc.what());
    result = "** Format Failed **";
    goto emit;
  }

  // now iterate over remaining arguments
  while (vpi_scan(arglist)) {
    vpi_get_value(arg, &vpi_value);
    try {
      tmpl % vpi_value.value.str;
    } catch (boost::io::too_many_args& exc) {
      WARNING(exc.what());
      goto emit;
    }
  }

 try {
   result = tmpl.str().c_str();
 } catch (boost::io::too_many_args& exc) {
   WARNING(exc.what());
 }

 emit:
  va_start(args, level); // will be empty
  example::message::instance()->emit((int)*level, vpi_get_str(vpiFile, href), vpi_get(vpiLineNo, href), (char*)result, args);
  va_end(args);

  return 0;
}

static PLI_BYTE8 levels[] = {
  example::INT_DEBUG,
  example::DEBUG,
  example::INFORMATION,
  example::NOTE,
  example::SUCCESS,
  example::WARNING,
  example::ERROR,
  example::INTERNAL,
  example::FATAL
};

static s_vpi_systf_data vpi_systf_data[] = {
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_python", (PLI_INT32(*)(PLI_BYTE8*))exm_python_vpi, 0, 0, 0},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_information", (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::INFORMATION},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_error", (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::ERROR},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_fatal", (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0,levels + example::FATAL },
  0
};

// cver entry
void vpi_compat_bootstrap(void) {
  p_vpi_systf_data systf_data_p;
  systf_data_p = &(vpi_systf_data[0]);
  while (systf_data_p->type != 0) vpi_register_systf(systf_data_p++);
}

// icarus entry
void (*vlog_startup_routines[])() = {
      vpi_compat_bootstrap,
      0
};

