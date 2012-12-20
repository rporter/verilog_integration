# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import re
import sys
import traceback
import vpi

import message

################################################################################

class lazyProperty(object):
    'thanks http://blog.pythonisito.com/2008/08/lazy-descriptors.html'
    def __init__(self, func):
        self._func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, *args):
        if obj is None: return None
        result = obj.__dict__[self.__name__] = self._func(obj)
        return result

################################################################################

class vpiChkError(object) :
  def __init__(self, echo=False) :
    self.error_info = vpi.s_vpi_error_info()
    if vpi.vpi_chk_error(self.error_info) and echo :
      message.message.vpiLevel[self.error_info.level](self.error_info.message)

################################################################################

class vpiVar(object) :
  vpi_type = None
  def __init__(self, value=None) :
    self.vpi_value        = vpi.s_vpi_value()
    self.vpi_value.format = self.vpi_type
    try :
      self.get(value)
    except AttributeError :
      self.encode(value)
  def __repr__(self) :
    return '<'+self.name+' of value '+str(self.decode())+' at 0x%016x'%id(self)+'>'
  def __int__(self) :
    return int(self.decode())
  def __str__(self) :
    return str(self.decode())
  def get(self, signal) :
    vpi.vpi_get_value(signal.handle, self.vpi_value)
    self.vpi_chk_error = vpiChkError()
    return self
  def put(self, signal) :
    vpi.vpi_put_value(signal.handle, self.vpi_value, None, vpi.vpiNoDelay)
    self.vpi_chk_error = vpiChkError()
    return self
  @property
  def name(self) :
   return self.__class__.__name__

class vpiInt(vpiVar) :
  vpi_type = vpi.vpiIntVal
  def encode(self, value) :
    self.vpi_value.value.integer = int(value)
  def decode(self) :
    return self.vpi_value.value.integer

class vpiReal(vpiVar) :
  vpi_type = vpi.vpiRealVal
  def encode(self, value) :
    self.vpi_value.value.real = float(value)
  def decode(self) :
    return self.vpi_value.value.real

class vpiString(vpiVar) :
  vpi_type = vpi.vpiStringVal
  def encode(self, value) :
    self.vpi_value.value.str = str(value)
  def decode(self) :
    return self.vpi_value.value.str

class vpiBinStr(vpiString) :
  vpi_type = vpi.vpiBinStrVal
class vpiOctStr(vpiString) :
  vpi_type = vpi.vpiOctStrVal
class vpiHexStr(vpiString) :
  vpi_type = vpi.vpiHexStrVal

class vpiVector(vpiVar) :
  vpi_type = vpi.vpiVectorVal
  def encode(self, value) :
    self.vpi_value.value.vector = value
  def decode(self) :
    return self.vpi_value.value.vector

class vpiSuppress(vpiVar) :
  vpi_type = vpi.vpiSuppressVal
  def encode(self, value) :
    pass
  def decode(self) :
    return None

################################################################################

class vpi_iter(object) :
  def __init__(self, vpi_i) :
    self.vpi_i = vpi_i
  def __iter__(self):
    return self
  def next(self) :
    v = vpi.vpi_scan(self.vpi_i)
    if v :
      return v
    raise StopIteration

class viterate(object) :
  vpi_default = None
  def __init__(self, handle, _type=None) :
    self.vpi_i = vpi.vpi_iterate(_type or self.vpi_default, handle)
    self.vpi_chk_error = vpiChkError()
  def __iter__(self):
    return self
  def next(self) :
    v = vpi.vpi_scan(self.vpi_i)
    if v :
      return v
    raise StopIteration

class viter_net(viterate) :
  vpi_default = vpi.vpiNet
class viter_port(viterate) :
  vpi_default = vpi.vpiPort
class viter_reg(viterate) :
  vpi_default = vpi.vpiReg

################################################################################

class vpiObject(object) :
  def __init__(self, handle) :
    self.handle = handle

  @lazyProperty
  def name(self) :
    result = vpi.vpi_get_str(vpi.vpiName, self.handle)
    self.vpi_chk_error = vpiChkError()
    return result

  @lazyProperty
  def fullname(self) :
    result = vpi.vpi_get_str(vpi.vpiFullName, self.handle)
    self.vpi_chk_error = vpiChkError()
    return result

################################################################################

class signal(vpiObject) :
  VPI_BINSTR = vpi.vpiBinStrVal  
  VPI_OCTSTR = vpi.vpiOctStrVal  
  VPI_DECSTR = vpi.vpiDecStrVal  
  VPI_HEXSTR = vpi.vpiHexStrVal  
  VPI_SCLR   = vpi.vpiScalarVal  
  VPI_INT    = vpi.vpiIntVal     
  VPI_REAL   = vpi.vpiRealVal    
  VPI_STR    = vpi.vpiStringVal  
  VPI_VEC    = vpi.vpiVectorVal  
  VPI_STRNG  = vpi.vpiStrengthVal
  VPI_TIME   = vpi.vpiTimeVal    
  VPI_OBJ    = vpi.vpiObjTypeVal 
  VPI_NONE   = vpi.vpiSuppressVal

  # can update this later to accomodate 4 value
  def __init__(self, handle, rtn=VPI_VEC, _type=None) :
    vpiObject.__init__(self, handle)
    self.type = _type
    self.vpi_value = vpi.s_vpi_value()
    self.vpi_value.format = rtn
  def __set__(self, value) :
    'Try and guess type'
    if isinstance(value, int) :
      value = vpiInt(value)
    elif isinstance(value, str) :
      value = vpiStr(value)
    elif isinstance(value, float) :
      value = vpiReal(value)
    self.set_value(value)
  def __get__(self) :
    return self.get_value()
  def __repr__(self) :
    return '<' + self.__class__.__name__ + ' ' + self.name + '>'
  def __int__(self) :
    return self.get_value(format=signal.VPI_INT)
  def __float__(self) :
    return self.get_value(format=signal.VPI_REAL)
  def __str__(self) :
    return self.get_value(format=signal.VPI_STR)
  def set_value(self, value, format=None) :
    try :
      value.put(self)
      return
    except AttributeError :
      pass
    if format :
      self.set_format(format)
    self.encode(value)
    vpi.vpi_put_value(self.handle, self.vpi_value, None, vpi.vpiNoDelay)
    self.vpi_chk_error = vpiChkError()
  def get_value(self, format=None, _type=None) :
    if self.type:
      return self.type(self)
    if _type:
      return _type(self)
    if format :
      self.set_format(format)
    vpi.vpi_get_value(self.handle, self.vpi_value)
    self.vpi_chk_error = vpiChkError()
    return self.decode(self.vpi_value)
  def set_format(self, format) :
    if format == self.vpi_value.format : return
    self.vpi_value.format = format
    message.debug('%(signal)s format set to %(fmt)d', signal=self.fullname, fmt=format)
    return self
  def set_type(self, _type) :
    self.type = _type
    message.debug('%(signal)s type set to %(name)s', signal=self.fullname, name=_type.name)
    return self

  def encode(self, value) :
    if self.vpi_value.format == signal.VPI_INT :
      self.vpi_value.value.integer = value
    elif self.vpi_value.format == signal.VPI_VEC :
      if not self.vpi_value.value.vector : self.get_value()
      self.vpi_value.value.vector.aval = value
    elif self.vpi_value.format == signal.VPI_STR :
      self.vpi_value.value.str = value

  @classmethod
  def decode(cls, vpi_value) :
    if vpi_value.format == signal.VPI_INT :
      return vpi_value.value.integer
    if vpi_value.format == signal.VPI_VEC :
      return vpi_value.value.vector.aval
    if vpi_value.format == signal.VPI_STR :
      return vpi_value.value.str.strip()
    return None

################################################################################

class scopeException(Exception) : pass

class scope(vpiObject) :

  class direct(object) :
    def __init__(self, scope) :
      self._scope = scope
    def __getattr__(self, attr) :
      return getattr(self._scope, attr).get_value()
    def __setattr__(self, attr, value) :
      if attr == '_scope' :
        object.__setattr__(self, attr, value)
        return
      getattr(self._scope, attr).set_value(value)

  def __init__(self, sname) :
    handle = vpi.vpi_handle_by_name(sname, None)
    vpiObject.__init__(self, handle)
    if self.handle is None :
      raise scopeException("Cannot find scope " + sname)
    self.direct = scope.direct(self)
    for reg in map(signal, viter_reg(self.handle)) :
      setattr(self, reg.name, reg)
  def __getattr__(self, name) :
    message.error('scope %(scope)s contains no object %(name)s', scope=self.name, name=name)
    raise scopeException

################################################################################

class callback(object) :
  callbacks = list()

  def __init__(self, obj=None, func=None, name=None, cb_filter=None, reason=vpi.cbValueChange, **kwargs) :
    for attr, val in kwargs.iteritems() :
      setattr(self, attr, val)

    self.funcs = set()
    self.__iadd__(func)

    self.cnt             = 0
    self.filtered        = 0
    self.excepted        = 0
    self.name            = name or 'none given'
    self.cb_filter       = cb_filter or self.cb_filter
    self.obj             = obj
    self.callback        = vpi.s_cb_data()

    if obj :
      self.callback.obj     = obj.handle
      self.callback.value   = obj.vpi_value
      self.callback.value = obj.vpi_value
    self.callback.reason = reason
    self.callback.script(self.cb_fn)
    self.cb = vpi.vpi_register_cb(self.callback)
    self.vpi_chk_error = vpiChkError()

    message.debug('registered callback "%(name)s" for %(reason)d', reason=reason, name=self.name)
    self.callbacks.append(self)

  def __iadd__(self, other) :
    if callable(other) :
      self.funcs |= set((other,))

  def __isub__(self, other) :
    self.funcs &= set((other,))

  def cb_fn(self) :
    'As callback executes vpi_get_value, could change callback fn and cb_filter signature to fn(value)'
    self.cnt += 1
    if self.cb_filter() :
      self.filtered += 1
      return
    for func in self.funcs :
      try :
        func()
      except Exception, exc:
        self.excepted += 1
        message.error('Exception in callback "%(name)s" : %(exc)s', exc=str(exc), name=self.name)
        for detail in traceback.format_exc().strip('\n').split('\n') :
          message.warning(detail)

  def cb_filter(self) :
    return False

  def get_value(self) :
    return signal.decode(self.callback.value)

  def remove(self) :
    vpi.vpi_remove_cb(self.cb)
    self.vpi_chk_error = vpiChkError()
    self.callbacks.remove(self)
    message.note('callback "%(name)s" called %(cnt)d times, filtered %(filtered)d, exceptions raised %(excepted)d', cnt=self.cnt, filtered=self.filtered, excepted=self.excepted, name=self.name)

  def __delete__(self) :
    self.remove()

  @staticmethod
  def remove_all() :
    for c in callback.callbacks : c.remove()

################################################################################

class plusargs(object) :
  argval = re.compile(r'^\+(?P<arg>[^+=]+)(?:[+=](?P<val>.*))?$')
  _instance = None
  class store(dict) :
    def __init__(self, *args) :
      dict.__init__(self, *args)
    def __getattr__(self, attr) :
      return self.get(attr, None)
  def __new__(self, *args, **kwargs) :
    if self._instance is None :
      self._instance = self.store([(arg.group('arg'), True if arg.group('val') is None else arg.group('val')) for arg in map(self.argval.match, sys.argv) if arg])
    return self._instance

################################################################################

class vpiChkErrorCb(callback) :
  def __init__(self) :
    callback.__init__(self, name='PLI error callback', reason=vpi.cbPLIError)

  def execute(self) :
    print 'cb'
    self.vpi_chk_error = vpiChkError(True)

PLIError = vpiChkErrorCb()
