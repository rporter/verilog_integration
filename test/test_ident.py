# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

class pytn :
  test = message.ident.add('PYTN', 69, message.INFORMATION, 'a message')
  success = message.ident.add('PYTN', 0, message.SUCCESS, 'this is a success')
  fatal = message.ident.add('PYTN', 1, message.FATAL, 'this is fatal')

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
    message.by_id('PYTN', 0)
  def fatal(self) :
    message.by_id('PYTN', 1)

################################################################################

testing = thistest()
