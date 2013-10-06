// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

`define true 1'b1
`define false 1'b0

`define std_char_sz_c 8

`define EXM_VLTOR_PUBLIC_RD /*verilator public_flat_rd */
`define EXM_VLTOR_PUBLIC_RW /*verilator public_flat_rw */

`ifdef EXM_USE_DPI

`define EXM_INT_DEBUG   exm_int_debug
`define EXM_DEBUG       exm_debug
`define EXM_INFORMATION exm_information
`define EXM_NOTE        exm_note
`define EXM_WARNING     exm_warning
`define EXM_SUCCESS     exm_success
`define EXM_ERROR       exm_error
`define EXM_INTERNAL    exm_internal
`define EXM_FATAL       exm_fatal

`define EXM_PYTHON exm_python
`define EXM_PYTHON_FILE exm_python_file
`define EXM_WAVES exm_waves

import "DPI-C" context task  `EXM_INT_DEBUG  (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_DEBUG      (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_INFORMATION(input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_NOTE       (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_WARNING    (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_SUCCESS    (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_ERROR      (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_INTERNAL   (input string formatted /*verilator sformat*/);
import "DPI-C" context task  `EXM_FATAL      (input string formatted /*verilator sformat*/);

import "DPI-C" context task `EXM_PYTHON();
import "DPI-C" context task `EXM_PYTHON_FILE(input string filename);
import "DPI-C" function bit `EXM_WAVES(output string filename, output integer depth);

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

`define EXM_PYTHON $exm_python
`define EXM_PYTHON_FILE $exm_python_file
`define EXM_WAVES $exm_waves

`endif

