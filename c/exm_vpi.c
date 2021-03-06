// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include <boost/format.hpp>
#include <boost/regex.hpp>

#include "vpi_user.h"
#include "message.h"
#include "exm_python.h"
#include "exm_waves.h"

int exm_python_vpi(char* arg) {
  return exm_python();
}

int exm_python_vpi_file(char* arg) {
  vpiHandle href;
  vpiHandle arglist;
  s_vpi_value vpi_value;

  href = vpi_handle(vpiSysTfCall, 0);
  arglist = vpi_iterate(vpiArgument, href);
  vpi_value.format = vpiStringVal;
  vpi_get_value(vpi_scan(arglist), &vpi_value);

  return exm_python_file(vpi_value.value.str);
}

static unsigned int filename_buff_size = 1024;
int exm_waves_vpi_sizetf(char* arg) {
  // filename_buff_size << 3
  // get size of register
}

int exm_waves_vpi(char* arg) {
  vpiHandle href;
  vpiHandle arglist;
  s_vpi_value vpi_value;

  int retval, depth;
  const char *filename;
  retval = exm_waves(&filename, &depth);

  href = vpi_handle(vpiSysTfCall, 0);
  arglist = vpi_iterate(vpiArgument, href);

  vpi_value.format = vpiIntVal;
  vpi_value.value.integer = retval;
  vpi_put_value(href, &vpi_value, NULL, vpiNoDelay);

  // assign other values if valid
  if (retval) {
    vpi_value.format = vpiStringVal;
    vpi_value.value.str = (PLI_BYTE8*)filename;
    vpi_put_value(vpi_scan(arglist), &vpi_value, NULL, vpiNoDelay);

    vpi_value.format = vpiIntVal;
    vpi_value.value.integer = depth;
    vpi_put_value(vpi_scan(arglist), &vpi_value, NULL, vpiNoDelay);
  }

  return 0;
}

int exm_message(char* level, ...) {
  vpiHandle href;
  vpiHandle arglist;
  vpiHandle arg;
  s_vpi_value vpi_value;
  const char *result;
  boost::format tmpl;

  // regexp stuff
  static boost::regex fmt("(?<!%)%(-?[0-9\056]+)?([bdefhimosx])", boost::regex::perl);
  static boost::regex mod("(?<!%)%[bhm]", boost::regex::perl);

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

  {

  std::string cp(vpi_value.value.str);
  boost::cregex_iterator re_match(cp.c_str(), cp.c_str()+strlen(vpi_value.value.str), fmt);
  boost::cregex_iterator end;

  // now replace %m with %s for format
  std::string fmt_str(boost::regex_replace(std::string(vpi_value.value.str), mod, "%s"));

  try {
    tmpl.parse(fmt_str);
  } catch (boost::io::bad_format_string& exc) {
    WARNING("Format raised %s", exc.what());
    result = "** Format Failed **";
    goto emit;
  }

  // now iterate over remaining arguments
  for (; re_match != end; ++re_match) {
    char fident = *(*re_match)[(*re_match).size()-1].first;
    switch (fident) {
      case 'b' : vpi_value.format = vpiBinStrVal; break;
      case 'h' : vpi_value.format = vpiHexStrVal; break;
      case 'e' :
      case 'f' : vpi_value.format = vpiRealVal; break;
      case 'i' :
      case 'o' :
      case 'x' :
      case 'd' : vpi_value.format = vpiIntVal; break;
      case 'm' : goto insert;
      case 's' : vpi_value.format = vpiStringVal; break;
    }
    if (!(arg=vpi_scan(arglist))) {
      WARNING("Not enough vpi arguments");
      goto emit;
    }
    vpi_get_value(arg, &vpi_value);
  insert:
    try {
      switch (fident) {
        case 'i' :
        case 'x' :
        case 'o' :
        case 'd' : tmpl % vpi_value.value.integer; break;
        case 'e' :
        case 'f' : tmpl % vpi_value.value.real; break;
        case 'm' : {
          vpiHandle scope = vpi_handle(vpiScope, href);
          tmpl % vpi_get_str(vpiFullName, scope);
          vpi_free_object(scope);
          break;
        }
        case 'b' :
        case 'h' :
        case 's' : tmpl % vpi_value.value.str;
      }
    } catch (boost::io::too_many_args& exc) {
      WARNING(exc.what());
      goto emit;
    }
  }

  try {
    result = tmpl.str().c_str();
  } catch (boost::io::too_few_args& exc) {
    WARNING(exc.what());
    result = "** Format Failed **";
  }
  }

 emit:
  example::message::instance()->emit((int)*level, vpi_get_str(vpiFile, href), vpi_get(vpiLineNo, href), (char*)result);

  return 0;
}

static PLI_BYTE8 levels[] = {
  example::IGNORE,
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
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_python",      (PLI_INT32(*)(PLI_BYTE8*))exm_python_vpi, 0, 0, 0},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_python_file", (PLI_INT32(*)(PLI_BYTE8*))exm_python_vpi_file, 0, 0, 0},
  {vpiSysFunc, vpiIntFunc, (PLI_BYTE8*)"$exm_waves",       (PLI_INT32(*)(PLI_BYTE8*))exm_waves_vpi, 0, 0, 0},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_int_debug",   (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::INT_DEBUG},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_debug",       (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::DEBUG},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_information", (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::INFORMATION},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_note",        (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::NOTE},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_error",       (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::ERROR},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_internal",    (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::INTERNAL},
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_fatal",       (PLI_INT32(*)(PLI_BYTE8*))exm_message, 0, 0, levels + example::FATAL},
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

