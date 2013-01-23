# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import atexit
import message
import verilog

print message.message.instance.get_cb_terminate()


t0= message.message.instance.get_cb_emit()
print t0
print message.message.instance.get_cb_emit().get_map()

def fn(*args) : print "fn whoop whoop", args
#message.message.instance.get_cb_emit().add_callback('bob', fn)
message.message.instance.get_cb_terminate().add_callback('bob', fn)

#message.message.instance.verbosity(2)
message.control[message.NOTE].echo = 0
message.control.DEBUG.echo = 1
message.fatal('fata')

def root() :
  return 'example'

simctrl = verilog.scope(root() + '.simctrl_0_u')

if verilog.plusargs().timeout :
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
