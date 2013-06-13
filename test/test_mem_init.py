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
    for r in duv.mem :
       r.set_value(verilog.vpiInt(r.index))
       totin += r.index
    message.note('end initialize at %(idx)d, sum is %(tot)d', idx=r.index, tot=totin)
    message.note('begin read')
    totout = reduce(lambda a,b : int(a)+int(b), duv.mem)
    message.note('end read, sum is %(tot)d', tot=totout)
    duv.mem[666] = 69
    message.note('size of [%(lhs)d:%(rhs)d] is %(size)d', lhs=duv.mem.lhs, rhs=duv.mem.rhs, size=duv.mem.size)
    message.note('size of mem[0] [%(lhs)d:%(rhs)d] is %(size)d', lhs=duv.mem[0].lhs, rhs=duv.mem[0].rhs, size=duv.mem[0].size)
  def epilogue(self) :
    self.success()

################################################################################

testing = thistest()
