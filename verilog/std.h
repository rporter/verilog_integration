// Copyright (c) 2012 Rich Porter - see LICENSE for further details

`define true 1'b1
`define false 1'b0

`define std_char_sz_c 8

`ifdef EXM_USE_DPI
import "DPI-C" context task  exm_information(input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_error      (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_fatal      (input string formatted /*verilator sformat*/);

`define EXM_INFORMATION exm_information
`define EXM_ERROR       exm_error
`define EXM_FATAL       exm_fatal
`else
`define EXM_INFORMATION $display
`define EXM_ERROR       $display
`define EXM_FATAL       $display
`endif

`ifdef EXM_USE_DPI
`define EXM_PYTHON exm_python
`else
`define EXM_PYTHON $exm_python
`endif

`define EXM_VLTOR_PUBLIC_RD /*verilator public_flat_rd */
`define EXM_VLTOR_PUBLIC_RW /*verilator public_flat_rw */
