# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import atexit
import exm_msg
from exm_msg import INT_DEBUG, DEBUG, INFORMATION, NOTE, WARNING, ERROR, INTERNAL, FATAL

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

class int_debug(message) : pass
class debug(message)     : pass
class note(message)      : pass
class success(message)   : pass
class warning(message)   : pass
class error(message)     : pass
class fatal(message)     : pass
class internal(message)  : pass

try :
  import vpi
  message.vpiLevel = {
    vpi.vpiNotice   : note,
    vpi.vpiWarning  : warning,
    vpi.vpiError    : error,
    vpi.vpiSystem   : fatal,
    vpi.vpiInternal : internal
  }
  note.level = vpi.vpiNotice
  level = vpi.vpiWarning
  level = vpi.vpiError
  level = vpi.vpiSystem
  level = vpi.vpiInternal
except ImportError :
  pass

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

class CallbackError(Exception) : pass

class callback(object) :
  def __init__(self, cb_map) :
    self.cb_map = cb_map
    self.callbacks = dict()
    atexit.register(self.finalize)
  def finalize(self) :
    for name, cb in self.callbacks.iteritems() :
      int_debug('deleting callback ' + name)
      self.cb_map.rm_callback(name)
  def add(self, name, pri, fn=None) :
    if fn is None :
      pri, fn = 0, pri # default priority is 0
    try :
      self.cb_map.add_callback(name, pri, fn)
    except TypeError as error :
      raise CallbackError(error)
    else :
      self.callbacks[name] = fn
  def rm(self, name, fn) :
    self.cb_map.rm_callback(name, fn)
    del self.callbacks[name]

emit_cbs = callback(message.instance.get_cb_emit())
terminate_cbs = callback(message.instance.get_cb_terminate())
