# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import random
import test
import verilog

################################################################################

message.control.ERROR.threshold = 100

# use verilog callback on each clock
class cbClk(verilog.callback) :
  types = [verilog.vpiBinStr, verilog.vpiOctStr, verilog.vpiHexStr]

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
      sig0 = self.scope.sig0.get_value(self.choice())
      sig1 = self.scope.sig1.get_value(self.choice())
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
    self.blks = [self.assign(*l) for l in array.iteritems()]
    self.simctrl = simctrl
    self.count = 0

  def execute(self) :
    if int(self.obj) : return # ignore rising edge
    for blk in self.blks :
      blk.get()
      blk.put()
    self.count += 1
    if self.count == 100 :
      # stop
      self.simctrl.direct.sim_ctrl_finish_r = 1

################################################################################

class thistest(test.test) :
  name='test vpi'
  def prologue(self) :
    # initialize random seed with deterministic value
    random.seed(1)
    
    def root() :
      return 'example'
    
    simctrl = verilog.scope(root() + '.simctrl_0_u')
    arr = dict([(i, verilog.scope(root() + '.duv_0_u.arr[%d].arr' % i)) for i in range(1,255)])
    
    # up timeout beyond test time
    simctrl.direct.sim_ctrl_timeout_i = 200
    # reduce time step
    simctrl.direct.sim_ctrl_cycles_freq_i = 1
    
    for scope in arr.values() :
      scope.direct.verbose = 0 # display values
    
    # register call back
    cbClk0 = cbClk(simctrl.sim_ctrl_clk_op.set_type(verilog.vpiInt), simctrl, arr)

  def epilogue(self) :
    message.success('End of Simulation')

################################################################################

testing = thistest()
