// Copyright (c) 2012 Rich Porter - see LICENSE for further details

#include "vltstd/svdpi.h"
#include "verilated_vpi.cpp"

#include "Vexample.h"           // From Verilating "example.v"

#if VM_TRACE
# include <verilated_vcd_c.h>   // Trace file format header
#endif

#include "exm_python.h"

Vexample *example;              // Instantiation of module
svScope sim_ctrl_0_u;           // sim controller for clock injection

vluint64_t main_time = 0;       // Current simulation time (64-bit unsigned)

double sc_time_stamp () {       // Called by $time in Verilog
  // fetch cycles from sim
    return main_time;           // Note does conversion to real, to match SystemC
}

int sim_ctrl_scope_t() {
  sim_ctrl_0_u = svGetScope();
}

int main(int argc, char **argv, char **env) {
    if (0 && argc && argv && env) {}    // Prevent unused variable warnings
    example = new Vexample;             // Create instance of module

    Verilated::commandArgs(argc, argv);
    Verilated::debug(0);

#if VM_TRACE                    // If verilator was invoked with --trace
    Verilated::traceEverOn(true);       // Verilator must compute traced signals
    VL_PRINTF("Enabling waves...\n");
    VerilatedVcdC* tfp = new VerilatedVcdC;
    example->trace (tfp, 99);       // Trace 99 levels of hierarchy
    tfp->open ("vlt_dump.vcd"); // Open the dump file
#endif

    VerilatedVpi::callCbs(cbStartOfSimulation);

    while (!Verilated::gotFinish()) {
      example->eval();	            // Evaluate model
      VerilatedVpi::callValueCbs(); // Evaluate any callbacks

      // Toggle clock
      svSetScope(sim_ctrl_0_u);
      sim_ctrl_sig_t();

    }

#if VM_TRACE
    if (tfp) tfp->dump (main_time);	// Create waveform trace for this timestamp
#endif

    example->final();
    VerilatedVpi::callCbs(cbEndOfSimulation);

#if VM_TRACE
    if (tfp) tfp->close();
#endif

    exit(0L);

}
