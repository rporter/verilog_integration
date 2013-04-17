# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test
import verilog

################################################################################

# maximum verbosity
message.message.verbosity(message.INT_DEBUG)

# build reset callback on top of verilog abstraction
class rstCallback(verilog.callback) :
  def __init__(self, obj) :
    verilog.callback.__init__(self, name='reset callback', obj=obj, reason=verilog.callback.cbValueChange, func=self.execute)
  def execute(self) :
    message.note('Reset == %(rst)d', rst=self.obj)

################################################################################

class thistest(test.test) :
  name='test reset callback'
  def prologue(self) :
    # register simulation controller scope
    self.simctrl = verilog.scope('example.simctrl_0_u')
    # register reset callback to reset signal in simulation controller scope
    self.rstCallback = rstCallback(self.simctrl.sim_ctrl_rst_op)
  
  def epilogue(self) :
    if self.rstCallback.cnt == 2:
      message.success('Reset callbacks observed = %(cnt)d', cnt=self.rstCallback.cnt)
    else :
      message.error('Reset callbacks observed = %(cnt)d', cnt=self.rstCallback.cnt)
  
  def fatal(self) :
    'Should not be executed'
    message.fatal('Should not be executed')

################################################################################

testing = thistest()
