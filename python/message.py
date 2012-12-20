# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import vpi

class message(object) :
  level = None
  def __init__(self, msg, **args) :
    self.msg = msg
    self.args = args
    self.name = self.__class__.__name__
    vpi.vpi_printf(self.severity() + self.msg % self.args + '\n')

  def severity(self) :
    return '(%8s) ' % self.name.upper()

class debug(message) : pass
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
