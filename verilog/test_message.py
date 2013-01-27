# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import message

message.message.instance.verbosity(0)
message.control[message.NOTE].echo = 0
message.control.DEBUG.echo = 1
message.control.FATAL.threshold = -1

def fn0(*args) : print "fn0", args
def fn1(*args) : print "fn1", args

message.emit_cbs.add('bob', fn0)

message.terminate_cbs.add('bob', fn0)

try :
  message.emit_cbs.add('bob', True)
except message.CallbackError as cberr :
  message.note('expected exception : ' + str(cberr))


def terminate(*args) : 
  message.note('terminate ' + str(args))
  print 'terminate ' + str(args)
  return 1

message.terminate_cbs.add('1 python', terminate)

message.internal('whoops')

