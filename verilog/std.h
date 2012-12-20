// Copyright (c) 2012 Rich Porter - see LICENSE for further details

`define true 1'b1
`define false 1'b0

`define std_char_sz_c 8

`define EXM_INFORMATION $display

`ifdef EXM_USE_DPI
`define EXM_PYTHON exm_python
`else
`define EXM_PYTHON $exm_python
`endif

`define EXM_VLTOR_PUBLIC_RD /*verilator public_flat_rd */
`define EXM_VLTOR_PUBLIC_RW /*verilator public_flat_rw */
