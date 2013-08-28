# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import coverage
import message
import test
import verilog

# we reuse vpi test
import test_vpi

message.message.verbosity(message.INT_DEBUG)

################################################################################

class test_cvg :
  class coverpoint_sig(coverage.coverpoint) :
    'bits toggle'
    def __init__(self, signal, name=None, parent=None) :
      self.size   = signal.size
      self.bit    = coverage.axis('bit', values=range(0, 1+self.size))
      self.sense  = coverage.axis('sense', true=1, false=0)
      self.fmt    = coverage.axis('fmt', vpiBinStr=0, vpiOctStr=1, vpiHexStr=2, vpiDecStr=3)
      coverage.coverpoint.__init__(self, signal, name, parent=parent)

    def define(self, bucket) :
      'set goal'
      # no dont cares or illegals
      bucket.default(goal=10)

  class coverpoint_format(coverage.coverpoint) :
    'read x write format'
    def __init__(self, signal, name=None, parent=None) :
      self.fmt    = coverage.axis('fmt0', vpiBinStr=0, vpiOctStr=1, vpiHexStr=2, vpiDecStr=3)
      self.fmt    = coverage.axis('fmt1', vpiBinStr=0, vpiOctStr=1, vpiHexStr=2, vpiDecStr=3)
      coverage.coverpoint.__init__(self, signal, name, parent=parent)

    def define(self, bucket) :
      'set goal'
      # no dont cares or illegals
      bucket.default(goal=10)

################################################################################

class cbClk(test_vpi.cbClk) :
  class assign(test_vpi.cbClk.assign) :
    def __init__(self, size, scope) :
      test_vpi.cbClk.assign.__init__(self, size, scope)
      self.cvr_pt0 = test_cvg.coverpoint_sig(self.scope.sig0, name=scope.sig0.fullname)
      self.cursor0 = self.cvr_pt0.cursor()

    def put(self) :
      sig0 = self.value(self.rand())
      self.scope.direct.sig0 = sig0
      self.scope.direct.sig1 = self.value()
      for i in range(0, 1+self.cvr_pt0.size) :
        self.cursor0(bit=i, sense='true' if sig0[i] else 'false', fmt=sig0.__class__.__name__).incr()

  def fcty(self, *args) :
    'object factory'
    return self.assign(*args)

class test_vpi_coverage(test_vpi.test_vpi) :
  name='test vpi coverage'
  MAX_INSTS=20
  def cb_fcty(self, *args) :
    'object factory'
    return cbClk(*args)

testing = test_vpi_coverage()
