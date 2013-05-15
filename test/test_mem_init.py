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
    print duv.mem
    duv.mem[0] = 69
    print [int(r) for r in duv.mem]
  def epilogue(self) :
    message.note('memory is %d' % int(duv.mem[0]))

################################################################################

testing = thistest()
