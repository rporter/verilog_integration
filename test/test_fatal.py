# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

################################################################################

message.message.instance.verbosity(0)

class thistest(test.test) :
  name='test mdb fail'
  def prologue(self) :
    message.fatal('a fatal %(c)d', c=69)
    message.note('a note')
  def epilogue(self) :
    'Should not be executed'
    self.success()

################################################################################

testing = thistest()

