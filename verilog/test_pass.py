# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import message
import test

class thistest(test.test) :
  name='test mdb pass'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.warning('a warning %(c)d', c=666)
    message.note('a note')
  def epilogue(self) :
    message.success('should be success')

testing = thistest()
