# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test
import verilog, vpi

################################################################################

class thistest(test.test) :
  name='test mdb pass'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.information('simulator is %(product)s', product=verilog.vpiInfo().product)
    message.note('a note')
  def epilogue(self) :
    self.success()

################################################################################

testing = thistest()
