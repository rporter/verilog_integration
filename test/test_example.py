# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import atexit
import message
import test
import verilog

def root() :
  return 'example'

simctrl = verilog.scope(root() + '.simctrl_0_u')

if test.plusargs().timeout :
  simctrl.direct.sim_ctrl_timeout_i = verilog.vpiInt(test.plusargs().timeout)

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
