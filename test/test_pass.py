# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

################################################################################

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test mdb pass'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.warning('a warning %(c)d', c=666)
    message.note('a note')
  def epilogue(self) :
    self.success()
  def fatal(self) :
    'Should not be executed'
    self.fatal()

################################################################################

testing = thistest()
