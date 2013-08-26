# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

class pytn :
  test = message.ident('PYTN', 69, message.INFORMATION, 'a message')

################################################################################

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test mdb ident'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.warning('a warning %(c)d', c=666)
    message.note('a note')
    pytn.test()
  def epilogue(self) :
    self.success()

################################################################################

testing = thistest()
