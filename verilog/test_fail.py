# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import message
import test

class thistest(test.test) :
  name='test mdb fail'
  def prologue(self) :
    message.error('a int_debug %(c)d', c=69)
    message.note('a note')
  def epilogue(self) :
    message.success('no')

testing = thistest()

