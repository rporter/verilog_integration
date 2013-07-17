# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test
import verilog

################################################################################

duv = verilog.scope('example.duv_0_u')

# build reset callback on top of verilog abstraction
class rstCallback(verilog.callback) :
  def __init__(self, obj, func) :
    verilog.callback.__init__(self, name='reset callback', obj=obj, reason=verilog.callback.cbValueChange, func=func)

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test mdb fmt'
  def prologue(self) :
    # register simulation controller scope
    self.simctrl = verilog.scope('example.simctrl_0_u')
    # register reset callback to reset signal in simulation controller scope
    self.rstCallback = rstCallback(self.simctrl.sim_ctrl_rst_op, self.assign)
  def assign(self) :
    duv.direct.test_message = 1
    self.rstCallback.remove()
  def epilogue(self) :
    message.success('should be success')
  def fatal(self) :
    'Should not be executed'
    message.fatal('Should not be executed')

################################################################################

testing = thistest()
