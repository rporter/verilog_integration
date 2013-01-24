# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import atexit
import message
import verilog


def fn(*args) : print "fn whoop whoop", args
message.terminate_cbs.add('bob', fn)
try :
  message.emit_cbs.add('bob', True)
except message.CallbackError as cberr :
  message.note('expected exception : ' + str(cberr))


message.message.instance.verbosity(0)
#message.control[message.NOTE].echo = 0
message.control.DEBUG.echo = 1

message.internal('whoops')

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
