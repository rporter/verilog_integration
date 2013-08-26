# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import coverage
import message
import test
import verilog

#message.message.verbosity(message.INT_DEBUG)

################################################################################

class test_cvg :
  class coverpoint_sig(coverage.coverpoint) :
    'bits toggle'
    def __init__(self, signal, name=None, parent=None) :
      self.size  = signal.size
      self.bit   = coverage.axis('bit', values=range(0, 1+self.size))
      self.sense = coverage.axis('sense', true=1, false=0)
      coverage.coverpoint.__init__(self, signal, name, parent=parent)

    def define(self, bucket) :
      'set goal'
      # no dont cares or illegals
      bucket.default(goal=150)

################################################################################

class arr_cb(verilog.callback) :
  def __init__(self, obj, scope, container, **kwargs) :
    verilog.callback.__init__(self, obj, func=self.execute, name=str(scope), **kwargs)
    self.cvr_pt0 = test_cvg.coverpoint_sig(scope.sig0, name=scope.sig0.fullname , parent=container)
    self.cursor0 = self.cvr_pt0.cursor()

  def execute(self) :
    if int(self.obj.get_value()) : # on clock edge
      value = str(self.cvr_pt0.model.get_value(verilog.vpiBinStr))
      for bit in self.cvr_pt0.bit.values :
        self.cursor0(bit=bit, sense=int(value[0-bit])).incr()

  def _filter(self) : pass

################################################################################

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test coverge'
  def prologue(self) :
    simctrl = verilog.scope('example.simctrl_0_u')
    # up timeout 
    simctrl.direct.sim_ctrl_timeout_i = 200
    instances = dict([(i, verilog.scope('example.duv_0_u.arr[%d].arr' % i)) for i in range(4,20)])
    self.callbacks = [arr_cb(simctrl.sim_ctrl_clk_op.set_type(verilog.vpiInt), instance, None) for instance in instances.values()]
  def epilogue(self) :
    self.success()
  def fatal(self) :
    'Should not be executed'
    message.fatal('Should not be executed')

################################################################################

testing = thistest()
