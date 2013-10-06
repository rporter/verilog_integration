// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

`include "example.h"

module sim_ctrl (
  output reg sim_ctrl_clk_op `EXM_VLTOR_PUBLIC_RW,
  output     sim_ctrl_rst_op `EXM_VLTOR_PUBLIC_RW
); // sim_ctrl

`ifdef EXM_USE_DPI
  import "DPI-C" context task sim_ctrl_scope_t ();
`ifdef verilator
  export "DPI-C"         task sim_ctrl_sig_t;
`endif
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
  
   task sim_ctrl_sig_t;
  
     sim_ctrl_clk_op
  `ifdef verilator
      =
  `else
      <=
  `endif
       ~sim_ctrl_clk_op;
  
  endtask : sim_ctrl_sig_t

  initial
    begin
       sim_ctrl_clk_op = `false;
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
  initial `EXM_PYTHON();

  /*
   * waveform trace for non verilator
   */
  initial
    begin : sim_ctrl_vcd_l
      integer sim_ctrl_vcd_depth_r = 0;
      reg [`std_char_sz_c*128-1:0] sim_ctrl_vcd_filename_r;
      reg 			   sim_ctrl_vcd_r;
      sim_ctrl_vcd_r = `EXM_WAVES(sim_ctrl_vcd_filename_r, sim_ctrl_vcd_depth_r);
      if (sim_ctrl_vcd_r)
	begin
`ifndef verilator
          $dumpfile(sim_ctrl_vcd_filename_r);
          $dumpvars(sim_ctrl_vcd_depth_r);
          `EXM_INFORMATION("Enabling waves depth %d, dumping to file %s", sim_ctrl_vcd_depth_r, sim_ctrl_vcd_filename_r);
`endif
        end
    end
   
endmodule : sim_ctrl

module arr (
  input clk
); // arr
   
   parameter LENGTH = 1;
   reg [LENGTH-1:0] sig0 `EXM_VLTOR_PUBLIC_RW;
   reg [LENGTH-1:0] sig1 `EXM_VLTOR_PUBLIC_RW;
   reg verbose           `EXM_VLTOR_PUBLIC_RW;

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
 
   reg single_bit `EXM_VLTOR_PUBLIC_RW;
   reg [31:0] mem [0:1023] `EXM_VLTOR_PUBLIC_RW;
   reg [31:0] mem_array [0:15] [0:3] [0:3] `EXM_VLTOR_PUBLIC_RW;

   `ifdef IVERILOG
   // seems icarus optimizes the signals away if they're not used
   wire dummy = single_bit || mem[0][0] || mem_array[0][0][0][0];
   `endif

   reg test_message `EXM_VLTOR_PUBLIC_RW = 0;
   always @(posedge duv_clk_ip)
     if (test_message)
       begin
         `EXM_NOTE("test_message %d", test_message);
         `EXM_NOTE("octal %08o", 255);
         `EXM_NOTE("hex %012x %h", 32'hee_55_aa_ff, 32'hff_aa_55_ee);
         `EXM_NOTE("float %f", 6.9);
         `EXM_NOTE("float %2.3f : %m, %1.2e", 6.9, 2.099);
         `EXM_NOTE("%b %m %h %m %%many", 64, 16'haa);
         test_message = 0;
       end

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

  duv_grey_box duv_grey_box_0_u (
    .duv_clk_ip(duv_0_u.duv_clk_ip),
    .duv_rst_ip(duv_0_u.duv_clk_ip)
  );

endmodule : example
