# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

message.message.instance.get_tags().add('PYTN', 0, message.SUCCESS, 'this is a success')

################################################################################

class thistest(test.test) :
  activity='simulation'
  block='default'
  name='test mdb ident'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.warning('a warning %(c)d', c=666)
    message.note('a note')
  def epilogue(self) :
    message.by_id('PYTN', 0)

################################################################################

testing = thistest()
