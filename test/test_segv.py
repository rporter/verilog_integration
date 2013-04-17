# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import test

################################################################################

class thistest(test.test) :
  name='test segv'
  def prologue(self) :
    message.message.verbosity(message.INT_DEBUG)
    message.warning('a warning %(c)d', c=666)
    
    import os, signal
    message.debug(str(os.getpid()))
    os.kill(os.getpid(), signal.SIGSEGV)
    
  def epilogue(self) :
    message.success('should not be seen')

################################################################################

testing = thistest()
