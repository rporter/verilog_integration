# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import random
import test
import verilog

################################################################################

message.control.ERROR.threshold = 100

# use verilog callback on each clock
class cbClk(verilog.callback) :

  class assign(object) :
    types = {
      True  : [verilog.vpiBinStr, verilog.vpiOctStr, verilog.vpiHexStr],
      False : [verilog.vpiBinStr, verilog.vpiOctStr, verilog.vpiHexStr, verilog.vpiDecStr]
    }

    def __init__(self, size, scope) :
      self.size = size
      self.scope = scope
      self.mask = (1L << size)-1L

    def get(self) :
      if not hasattr(self, 'bits') : return
      # cross these choices
      sig0 = self.scope.sig0.get_value(self.choice())
      sig1 = self.scope.sig1.get_value(self.choice())
      self.check(sig0, sig1)

    def check(self, sig0, sig1) :
      if long(sig0) != long(sig1) :
        message.error("sig0(%x, %s) != sig1(%x, %s) when value(%x)" % (long(sig0), repr(sig0), long(sig1), repr(sig1), self.bits))
      if long(sig0) != self.val :
        message.error("sig0(%x, %s) != value(%x) when value(%x)" % (long(sig0), repr(sig0), self.bits, self.bits))
      if long(sig1) != self.val :
        message.error("sig1(%x, %s) != value(%x) when value(%x)" % (long(sig1), repr(sig1), self.bits, self.bits))

    def put(self) :
      self.scope.direct.sig0 = self.value(self.rand())
      self.scope.direct.sig1 = self.value()

    def value(self, bits=None) :
      if bits is None : bits = self.bits
      choice = self.choice()
      if choice == verilog.vpiDecStr :
        # can't put too many bits in else MAXINT is used
        bits &= self.mask
      return choice(bits)

    def choice(self) :
      return random.choice(self.types[self.size > 32])

    def rand(self) :
      # choose either the vector length or something else
      size = random.choice((self.size, random.choice(range(1,300))))
      self.bits = random.getrandbits(size)
      return self.bits

    @property
    def val(self) :
      return self.bits & self.mask

  def __init__(self, obj, simctrl, array) :
    verilog.callback.__init__(self, name='clock callback', obj=obj, reason=verilog.callback.cbValueChange, func=self.execute)
    self.blks = [self.fcty(*l) for l in array.iteritems()]
    self.simctrl = simctrl
    self.count = 0

  def execute(self) :
    for blk in self.blks :
      if self.count & 1 :
        blk.get()
      else :
        blk.put()
    self.count += 1
    if self.count == 200 :
      # stop
      self.simctrl.direct.sim_ctrl_finish_r = 1

  def cb_filter(self) :
    # ignore rising edge
    return not int(self.obj)

  def fcty(self, *args) :
    'object factory'
    return self.assign(*args)

################################################################################

class test_vpi(test.test) :
  name='test vpi'
  MAX_INSTS=255
  def prologue(self) :
    # initialize random seed with deterministic value
    seed = verilog.plusargs().get('seed', 1)
    random.seed(seed)
    
    simctrl = verilog.scope('example.simctrl_0_u')
    arr = dict([(i, verilog.scope('example.duv_0_u.arr[%d].arr' % i)) for i in range(1,self.MAX_INSTS)])
    
    # up timeout beyond test time
    simctrl.direct.sim_ctrl_timeout_i = 200
    # reduce time step
    simctrl.direct.sim_ctrl_cycles_freq_i = 1
    
    for scope in arr.values() :
      scope.direct.verbose = 0 # display values
    
    # register call back
    cbClk0 = self.cb_fcty(simctrl.sim_ctrl_clk_op.set_type(verilog.vpiInt), simctrl, arr)

  def epilogue(self) :
    self.success()

  def cb_fcty(self, *args) :
    'object factory'
    return cbClk(*args)

################################################################################

if __name__ == '__main__' :
  testing = test_vpi()
