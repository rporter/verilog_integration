// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include "vpi_user.h"
#include "exm_python.h"

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

static s_vpi_systf_data vpi_systf_data[] = {
  {vpiSysTask, vpiSysTask, (PLI_BYTE8*)"$exm_python", (PLI_INT32(*)(PLI_BYTE8*))exm_python_vpi, 0, 0, 0},
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

