# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message

message.message.instance.verbosity(0)
message.control[message.NOTE].echo = 0
message.control.DEBUG.echo = 1
message.control.FATAL.threshold = -1

def fn0(*args) : print "fn0", args[1].tv_nsec, args
def fn1(*args) : print "fn1", args

message.emit_cbs.add('defaultx', 2, fn0)
message.terminate_cbs.add('bob', 1, fn1)

try :
  message.emit_cbs.add('bob', 1, True)
except message.CallbackError as cberr :
  message.note('expected exception : ' + str(cberr))

def terminate(*args) : 
  message.note('terminate ' + str(args))
  print 'terminate ' + str(args[0])
  print args[0].name

message.terminate_cbs.add('python', 0, terminate)

message.internal('whoops')

