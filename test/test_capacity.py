# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test
import verilog

################################################################################

duv = verilog.scope('example.duv_0_u')

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test capacity'
  def prologue(self) :
    message.note('Creating 1000 signal instances')
    instances = [duv.single_bit for i in range(0, 1000)]
    for idx, inst in enumerate(instances) :
      message.information('%(idx)d is %(val)d', idx=idx, val=int(inst))
  def epilogue(self) :
    self.success()
  def fatal(self) :
    'Should not be executed'
    message.fatal('Should not be executed')

################################################################################

testing = thistest()
