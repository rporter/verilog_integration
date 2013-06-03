# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test
import verilog

################################################################################

duv = verilog.scope('example.duv_0_u')

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test mem init'
  def prologue(self) :
    # hush debug messages to database
    self.mdb.filter_fn = lambda cb_id, level, filename : level < message.INFORMATION
    
    duv.mem[0] = 69
    duv.mem[69] = 666
    totin = 0
    message.note('begin initialize')
    for idx, r in enumerate(duv.mem) :
       r.set_value(verilog.vpiInt(idx))
       totin += idx
    message.note('end initialize at %(idx)d, sum is %(tot)d', idx=idx, tot=totin)
    message.note('begin read')
    totout = reduce(lambda a,b : int(a)+int(b), duv.mem)
    message.note('end read, sum is %(tot)d', tot=totout)
  def epilogue(self) :
    message.success('memory[0] is %d' % int(duv.mem[0]))

################################################################################

testing = thistest()
