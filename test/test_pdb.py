# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

################################################################################

class thistest(test.test) :
  name='test interactive pdb'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.warning('a warning %(c)d', c=666)
    message.note('a note')
    self.pdb()
  def epilogue(self) :
    self.success()

################################################################################

testing = thistest()
