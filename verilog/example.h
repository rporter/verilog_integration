// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

`define true 1'b1
`define false 1'b0

`define std_char_sz_c 8

`ifdef EXM_USE_DPI
import "DPI-C" context task  exm_int_debug  (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_debug      (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_information(input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_note       (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_warning    (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_success    (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_error      (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_internal   (input string formatted /*verilator sformat*/);
import "DPI-C" context task  exm_fatal      (input string formatted /*verilator sformat*/);

`define EXM_INT_DEBUG   exm_int_debug
`define EXM_DEBUG       exm_debug
`define EXM_INFORMATION exm_information
`define EXM_NOTE        exm_note
`define EXM_WARNING     exm_warning
`define EXM_SUCCESS     exm_success
`define EXM_ERROR       exm_error
`define EXM_INTERNAL    exm_internal
`define EXM_FATAL       exm_fatal
`else
`define EXM_INT_DEBUG   $exm_int_debug
`define EXM_DEBUG       $exm_debug
`define EXM_INFORMATION $exm_information
`define EXM_NOTE        $exm_note
`define EXM_WARNING     $exm_warning
`define EXM_SUCCESS     $exm_success
`define EXM_ERROR       $exm_error
`define EXM_INTERNAL    $exm_internal
`define EXM_FATAL       $exm_fatal
`endif

`ifdef EXM_USE_DPI
`define EXM_PYTHON exm_python
`else
`define EXM_PYTHON $exm_python
`endif

`define EXM_VLTOR_PUBLIC_RD /*verilator public_flat_rd */
`define EXM_VLTOR_PUBLIC_RW /*verilator public_flat_rw */
