# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import exm_msg
import vpi
from exm_msg import INT_DEBUG, DEBUG, INFORMATION, NOTE, WARNING, ERROR, INTERNAL, FATAL

#def vprint() :    
#  vpi.vpi_printf(self.severity() + self.msg % self.args + '\n')

class SeverityError(Exception) : pass

class message(object) :
  instance = exm_msg.message.instance()
  level    = None

  def __init__(self, msg, **args) :
    self.msg = msg
    self.args = args
    self.name = self.__class__.__name__
    self.fn()('file', 0, self.formatted())

  def fn(self) :
    return getattr(self.instance, self.name)

  def formatted(self) :
    return self.msg % self.args

class int_debug(message) :
  pass
class debug(message) :
  pass
class note(message) : 
  level = vpi.vpiNotice
class warning(message) :
  level = vpi.vpiWarning
class error(message) :
  level = vpi.vpiError
class fatal(message) :
  level = vpi.vpiSystem
class internal(message) :
  level = vpi.vpiInternal

message.vpiLevel = {
  vpi.vpiNotice   : note,
  vpi.vpiWarning  : warning,
  vpi.vpiError    : error,
  vpi.vpiSystem   : fatal,
  vpi.vpiInternal : internal
}

class _control(object) :
  def __getattribute__(self, attr) :
    return message.instance.get_ctrl(getattr(exm_msg, attr))
    try :
      return message.instance.get_ctrl(getattr(exm_msg, attr))
    except AttributeError :
      raise SeverityError('No severity ' + str(attr))

  def __getitem__(self, idx) :
    result = message.instance.get_ctrl(idx)
    if result : return result
    raise SeverityError('No severity of level ' + str(idx))

control = _control()
