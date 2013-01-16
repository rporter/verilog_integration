# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import message
import random
import verilog

random.seed(1)

def root() :
  return 'example'

simctrl = verilog.scope(root() + '.simctrl_0_u')
arr = dict([(i, verilog.scope(root() + '.duv_0_u.arr[%d].arr' % i)) for i in range(1,255)])

# up timeout beyond test time
simctrl.direct.sim_ctrl_timeout_i = 200

for scope in arr.values() :
  scope.direct.verbose = 0 # display values

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

    def get(self) :
      if not hasattr(self, 'bits') : return
      sig0 = self.scope.sig0.get_value(self.choice())
      sig1 = self.scope.sig1.get_value(self.choice())
      if long(sig0) != long(sig1) :
        message.error("sig0(%x) != sig1(%x)" % (long(sig0), long(sig1)))
      if long(sig0) != self.bits :
        message.error("sig0(%x) != value(%x)" % (long(sig0), self.bits))
      if long(sig1) != self.bits :
        message.error("sig1(%x) != value(%x)" % (long(sig1), self.bits))

    def put(self) :
      self.scope.direct.sig0 = self.value(self.rand())
      self.scope.direct.sig1 = self.value()

    def value(self, bits=None) :
      if bits is None : bits = self.bits
      return self.choice()(bits)

    def choice(self) :
      return random.choice(self.types[self.size > 32])

    def rand(self) :
      self.bits = random.getrandbits(self.size)
      return self.bits

  def __init__(self, obj) :
    verilog.callback.__init__(self, name='clock callback', obj=obj, reason=verilog.callback.cbValueChange, func=self.execute)
    self.blks = [self.assign(*l) for l in arr.iteritems()]
    self.count = 0
  def execute(self) :
    if int(self.obj) : return # ignore rising edge
    for blk in self.blks :
      blk.get()
      blk.put()
    self.count += 1
    if self.count == 100 :
      # stop
      simctrl.direct.sim_ctrl_finish_r = 1

# register call back
cb = cbClk(simctrl.sim_ctrl_clk_op.set_type(verilog.vpiInt))
