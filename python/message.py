# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import atexit
import collections
import exm_msg
from exm_msg import IGNORE, INT_DEBUG, DEBUG, INFORMATION, NOTE, SUCCESS, WARNING, ERROR, INTERNAL, FATAL
import inspect
import sys

################################################################################

class SeverityError(Exception) : pass

################################################################################

class message :
  instance = exm_msg.message.instance()
  level    = None

  def __init__(self, msg, **args) :
    self.msg = msg
    self.args = args
    self.name = self.__class__.__name__
    # default to scope above
    file, line = inspect.stack()[1][1:3]
    # call library function
    self.emit(args.setdefault('file', file), args.setdefault('line', line), self.formatted())

  def emit(self, *args) :
    'get library function and apply arguments'
    return getattr(self.instance, self.name)(*args)

  def formatted(self) :
    if self.args.get('formatted', False) :
      return str(self.msg) # cast from possible unicode
    return str(self.msg % self.args) # cast from possible unicode

  @classmethod
  def status(cls) :
    'return test status'
    return cls.instance.status().text
  @classmethod
  def verbosity(cls, verbosity=INFORMATION) :
    cls.instance.verbosity(verbosity)
  @classmethod
  def summary(cls, display=True) :
    if display is False :
      terminate_cbs.rm('summary')
  @classmethod
  def terminating(cls) :
    return cls.instance.terminating()
  @classmethod
  def get_msg(cls, *args) :
    return cls.instance.get_tags().get(*args)

################################################################################

class int_debug(message)   : pass
class debug(message)       : pass
class note(message)        : pass
class information(message) : pass
class success(message)     : pass
class warning(message)     : pass
class error(message)       : pass
class fatal(message)       : pass
class internal(message)    : pass

################################################################################

class ident(message, object) :
  'thin wrapper around ident class which is declared in swig exm_msg.i'
  def __init__(self, ident, subident, level, msg) :
    self.msg_id = exm_msg.ident(ident, subident, level, msg)
    self.tag    = exm_msg.tag(ident, subident)
    self.text   = msg
    self._init = True
  def __call__(self, **args) :
    # default to scope above
    file, line = inspect.stack()[1][1:3]
    try :
      self.msg_id(str(self.text % args), args.setdefault('file', file), args.setdefault('line', line))
    except :
      self.msg_id(args.setdefault('file', file), args.setdefault('line', line))
  def __setattr__(self, attr, val) :
    if hasattr(self, '_init') :
      setattr(message.get_msg(self.tag), attr, val)
    else :
      object.__setattr__(self, attr, val)

class by_id(message) :
  def __init__(self, ident, subident, **args) :
    self.args = args
    # default to scope above
    file, line = inspect.stack()[1][1:3]
    self.instance.by_id(ident, subident, args.setdefault('file', file), args.setdefault('line', line))

################################################################################

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
  warning.level = vpi.vpiWarning
  error.level = vpi.vpiError
  fatal.level = vpi.vpiSystem
  internal.level = vpi.vpiInternal
except ImportError :
  pass

################################################################################

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

################################################################################

class CallbackError(Exception) : pass

class callback(object) :
  python = collections.namedtuple('python', ['message', 'finalize'])
  def __init__(self, cb_map) :
    self.cb_map = cb_map
    self.callbacks = dict()
    # this runs when the python interpreter exits, before the message lib finishes
    atexit.register(self.atexit)
  def atexit(self) :
    if message.terminating() : return
    self.finalize()
  def finalize(self) :
    for name, cb in self.callbacks.items() :
      int_debug('deleting callback ' + name)
      self.rm(name)
    int_debug('all callbacks deleted')
  def add(self, name, pri=0, msg_fn=None, fin_fn=None) :
    int_debug('adding callback ' + name)
    try :
      self.cb_map.add_callback(name, pri, msg_fn)
    except TypeError as error :
      raise CallbackError(error)
    else :
      self.callbacks[name] = callback.python(message=msg_fn, finalize=fin_fn)
  def rm(self, name) :
    try :
      if self.callbacks[name].finalize is not None : self.callbacks[name].finalize()
    except KeyError, AttributeError :
      debug('callback finalize %(name)s raised exception %(exc)s', name=name, exc=sys.exc_info()[0])
    self.cb_map.rm_callback(name)
    try :
      del self.callbacks[name]
    except KeyError :
      internal('callback %(name)s not in callback list', name=name)

################################################################################

emit_cbs = callback(message.instance.get_cb_emit())
terminate_cbs = callback(message.instance.get_cb_terminate())

################################################################################

import cStringIO
from optparse import OptionParser

class reportOptionParser(OptionParser):
  def __init__(self, *args, **kwargs) :
    OptionParser.__init__(self, *args, **kwargs)

    def increase_verbosity(option, opt, value, parser) :
      parser.values.verbosity -= 1
    
    self.add_option('', '--root', help='root directory')
    self.add_option('', '--verbosity', help='set absolute verbosity', default=INFORMATION)
    self.add_option('-v', '', help='increase verbosity', action='callback', callback=increase_verbosity)

  def exit(self, status=0, msg=None):
    if msg:
        fatal(msg.rstrip())
    sys.exit(status)
  def error(self, msg):
    """error(msg : string)

    Print a usage message incorporating 'msg' to stderr and exit.
    If you override this in a subclass, it should not return -- it
    should either exit or raise an exception.
    """
    chan = cStringIO.StringIO()
    self.print_usage(chan)
    for line in chan :
      warning(line.rstrip())
    chan.close()
    self.exit(2, "%s: error: %s\n" % (self.get_prog_name(), msg))
  def parse_args(self, *args, **kwargs) :
    # call super
    result = OptionParser.parse_args(self, *args, **kwargs)
    # set message verbosity
    message.verbosity(result[0].verbosity)
    return result

################################################################################

def excepthook(type, value, traceback) :
  import traceback as _traceback
  warning('Exception encountered : %(type)s', type=str(type))
  warning(' %(value)s', value=str(value))
  for detail in _traceback.extract_tb(traceback) :
    warning(detail[-1], file=detail[0], line=detail[1], formatted=True)
  internal('Exception encountered')
  sys.exit(1)

sys.excepthook = excepthook
