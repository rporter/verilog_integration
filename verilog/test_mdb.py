# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import message
import test

class thistest(test.test) :
  name='test mdb'
  def prologue(self) :
    message.int_debug('a int_debug %(c)d', c=69)
    message.note('a note')
  def epilogue(self) :
    message.success('should be success')

testing = thistest()
