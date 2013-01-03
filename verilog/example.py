# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import atexit
import message
import verilog

scopename = 'example.simctrl_0_u'
if verilog.vpiInfo().product == 'Verilator' :
  scopename = 'TOP.' + scopename

simctrl = verilog.scope(scopename)

simctrl.direct.sim_ctrl_timeout_i = verilog.vpiHexStr('0XDEAD')
message.note("timeout is %(timeout)d", timeout=simctrl.direct.sim_ctrl_timeout_i)
message.note("timeout is %(timeout)s", timeout=simctrl.sim_ctrl_timeout_i.get_value(verilog.signal.vpiHexStrVal))
timeout=simctrl.sim_ctrl_timeout_i.get_value(verilog.vpiHexStr)
message.note("timeout is %(timeout)s", timeout=timeout)
timeout=verilog.vpiHexStr(simctrl.sim_ctrl_timeout_i)
message.note("timeout is %(timeout)s", timeout=timeout)

if verilog.plusargs().timeout :
  simctrl.direct.sim_ctrl_timeout_i = verilog.vpiBinStr(int(verilog.plusargs().timeout))
  simctrl.direct.sim_ctrl_timeout_i = verilog.vpiInt(verilog.plusargs().timeout)

# use verilog vpi cbEndOfSimulation callback
class cbEndOfSimulation(verilog.callback) :
  def __init__(self) :
    verilog.callback.__init__(self, name='PLI end of simulation callback', reason=verilog.callback.cbEndOfSimulation, func=self.execute)
  def execute(self) :
    message.note('vpi cbEndOfSimulation')

end = cbEndOfSimulation()

# show when python interpreter is closed down
def finalize() :
  message.note('finalize')

atexit.register(finalize)
