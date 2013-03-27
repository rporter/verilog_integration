// Copyright (c) 2012 Rich Porter - see LICENSE for further details

`include "std.h"

module sim_ctrl (
  output sim_ctrl_clk_op `EXM_VLTOR_PUBLIC_RD,
  output sim_ctrl_rst_op `EXM_VLTOR_PUBLIC_RD
); // sim_ctrl

`ifdef EXM_USE_DPI
  import "DPI-C" context task sim_ctrl_scope_t ();
  export "DPI-C"         task sim_ctrl_sig_t;
  import "DPI-C" context task `EXM_PYTHON (input string filename);
`endif

  /*
   * Clock generation
   *
   * Does need to be done differently across platforms
   *
   * Needs some thought when verilated code runs in lock step to event
   * driven RTL.
   * 
   */
  
  reg sim_ctrl_clk_r;
  
  task sim_ctrl_sig_t;
  
     sim_ctrl_clk_r
  `ifdef verilator
      =
  `else
      <=
  `endif
       ~sim_ctrl_clk_r;
  
  endtask // sim_ctrl_t

  assign sim_ctrl_clk_op = sim_ctrl_clk_r;
  
  initial
    begin
       sim_ctrl_clk_r = `false;
`ifdef verilator
       // driven externally via sim_ctrl_sig_t task
       sim_ctrl_scope_t; // register this scope
`else
       // event driven simulations
       forever #1 sim_ctrl_sig_t;
`endif
    end
   
  /*
   * Generate reset
   */
   
  integer sim_ctrl_cycles_i       `EXM_VLTOR_PUBLIC_RD;
  integer sim_ctrl_cycles_freq_i  `EXM_VLTOR_PUBLIC_RW;
  integer sim_ctrl_rst_i          `EXM_VLTOR_PUBLIC_RW;
  integer sim_ctrl_timeout_i      `EXM_VLTOR_PUBLIC_RW;
  reg     sim_ctrl_finish_r       `EXM_VLTOR_PUBLIC_RW;
  
  always @(posedge sim_ctrl_clk_op)
    begin
      sim_ctrl_cycles_i <= sim_ctrl_cycles_i + 1;
      if (sim_ctrl_cycles_i % sim_ctrl_cycles_freq_i == 0)
        `EXM_INFORMATION("%10d cycles", sim_ctrl_cycles_i);
      if (sim_ctrl_cycles_i > sim_ctrl_timeout_i)
	sim_ctrl_finish_r <= `true;
    end

  initial sim_ctrl_rst_i = 5;
 
  assign sim_ctrl_rst_op = sim_ctrl_cycles_i < sim_ctrl_rst_i;

  /*
   * Timeout for end of simulation
   */
  initial sim_ctrl_timeout_i = 10;

  always @(sim_ctrl_timeout_i)
    `EXM_INFORMATION("%m : timeout set to %d", sim_ctrl_timeout_i);

  initial sim_ctrl_cycles_i      = 0;
  initial sim_ctrl_cycles_freq_i = 1000;

   /*
    * End of simulation
    */
   initial sim_ctrl_finish_r = `false;

   always @(posedge sim_ctrl_finish_r)
     begin
      `EXM_INFORMATION("End of simulation at %d", sim_ctrl_cycles_i);
       $finish;
     end

  /*
   * invoke python shell
   */
  initial if ($test$plusargs("python") > 0) 
    begin : sim_ctrl_python_l
      reg [`std_char_sz_c*128-1:0] sim_ctrl_python_filename_r;
      if ($value$plusargs("python+%s", sim_ctrl_python_filename_r) == 0)
	begin
          sim_ctrl_python_filename_r = "stdin";
	end
      `EXM_INFORMATION("python input set to %s", sim_ctrl_python_filename_r);
      `EXM_PYTHON(sim_ctrl_python_filename_r);
    end

endmodule : sim_ctrl

module arr (
  input clk
); // arr
   
   parameter LENGTH = 1;
   reg [LENGTH-1:0] sig0 /*verilator public_flat_rw*/;
   reg [LENGTH-1:0] sig1 /*verilator public_flat_rw*/;
   bit verbose /*verilator public_flat_rw*/;

   always @(posedge clk)
     begin
       if (sig0 != sig1) `EXM_ERROR("%m : %x != %x", sig0, sig1);
       else if (verbose) `EXM_INFORMATION("%m : %x == %x", sig0, sig1);
     end
   
endmodule : arr

module duv (
  input duv_clk_ip,
  input duv_rst_ip
); // duv
   parameter instances = 255;
   
   genvar i;
   generate

     for (i=1; i<=255; i=i+1) begin : arr
       arr #(.LENGTH(i)) arr(.clk(duv_clk_ip));
     end
   endgenerate
endmodule : duv

module duv_grey_box (
  input duv_clk_ip,
  input duv_rst_ip
); // duv_grey_box
   
endmodule : duv_grey_box

module example;

  wire
    example_clk_w,
    example_rst_w;
     
  sim_ctrl simctrl_0_u (
    .sim_ctrl_clk_op(example_clk_w),
    .sim_ctrl_rst_op(example_rst_w)
  );

  duv duv_0_u (
    .duv_clk_ip(example_clk_w),
    .duv_rst_ip(example_rst_w)
  );

  bind duv_0_u duv_grey_box duv_grey_box_0_u (
    .duv_clk_ip(duv_clk_ip),
    .duv_rst_ip(duv_clk_ip)
  );

endmodule : example