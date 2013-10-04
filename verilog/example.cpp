// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include "vltstd/svdpi.h"
#include "verilated_vpi.cpp"

#include "Vexample.h"           // From Verilating "example.v"

#if VM_TRACE
# include <verilated_vcd_c.h>   // Trace file format header
#endif

#include "exm_python.h"
#include "message.h"

VM_PREFIX *example_top;         // Instantiation of module
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
    if (0 && argc && argv && env) {}      // Prevent unused variable warnings
    example_top = new VM_PREFIX("");      // Create instance of module

    Verilated::commandArgs(argc, argv);
    Verilated::debug(0);
    Verilated::fatalOnVpiError(0);

#if VM_TRACE                              // If verilator was invoked with --trace
    VerilatedVcdC* tfp = NULL;
#endif
    string filename((char*)Verilated::commandArgsPlusMatch("waves"));
    if (filename.size()) {
#if VM_TRACE                              // If verilator was invoked with --trace
      int depth = 99;                     // default trace depth
      do {
        if (filename.size() > 6) {
          filename = filename.substr(7);
        } else {
          filename = "waves.vcd";
	}
      } while (filename.size() == 0);
      // look for depth in format +waves+filename+depth
      size_t pos = filename.find_first_of("+,");
      if (pos != string::npos) {
	depth = atoi(filename.substr(pos+1).c_str());
	filename.erase(pos);
      }
      INFORMATION("Enabling waves depth %d, dumping to file %s", depth, filename.c_str());
      Verilated::traceEverOn(true);       // Verilator must compute traced signals
      tfp = new VerilatedVcdC;
      example_top->trace(tfp, depth);     // Trace depth levels of hierarchy
      tfp->open(filename.c_str());        // Open the dump file
#else
      WARNING("Verilator executable not built with waveform tracing enabled");
#endif
    }

    VerilatedVpi::callCbs(cbStartOfSimulation);

    while (!Verilated::gotFinish()) {
      example_top->eval();	            // Evaluate model
      VerilatedVpi::callValueCbs();         // Evaluate any callbacks

      // Toggle clock
      svSetScope(sim_ctrl_0_u);
      sim_ctrl_sig_t();
      main_time++;
#if VM_TRACE
      if (tfp) tfp->dump(main_time); 	   // Create waveform trace for this timestamp
#endif
    }

    example_top->final();
    VerilatedVpi::callCbs(cbEndOfSimulation);

#if VM_TRACE
    if (tfp) tfp->close();
#endif

    exit(0L);

}
