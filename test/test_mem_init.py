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
    print duv.mem.name, duv.mem.size, duv.mem
    print duv.mem[0].name, duv.mem[0].size, int(duv.mem[0])
    print duv.mem.handle
    duv.mem[0] = 69
    # for idx, r in enumerate(duv.mem) : message.note('memory %(idx)d is %(val)d', idx=idx, val=int(r))
    #print [int(r) for r in duv.mem]
    for idx, handle in enumerate(verilog.viterate(duv.mem.handle, verilog.vpi.vpiMemoryWord)) :
       message.note("%(idx)d, %(val)d", idx=idx, val=int(verilog.signal(handle)))
  def epilogue(self) :
    message.note('memory is %d' % int(duv.mem[0]))

################################################################################

testing = thistest()
