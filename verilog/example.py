# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import atexit
import message
import verilog

simctrl = verilog.scope('TOP.example.simctrl_0_u')

if verilog.plusargs().timeout :
  simctrl.direct.sim_ctrl_timeout_i = verilog.vpiBinStr(verilog.plusargs().timeout)
  simctrl.direct.sim_ctrl_timeout_i = verilog.vpiInt(verilog.plusargs().timeout)

def finalize() :
  message.note('finalize')

atexit.register(finalize)
