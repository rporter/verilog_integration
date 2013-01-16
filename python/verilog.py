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

class vpiInfo(object) :
  _instance = None
  def __new__(self) :
    if self._instance is None :
      self._instance = vpi.s_vpi_vlog_info()
      vpi.vpi_get_vlog_info(self._instance)
    return self._instance

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
      self.encode(self.cast(value))
  def __repr__(self) :
    return '<'+self.name+' of value '+str(self.decode())+' at 0x%016x'%id(self)+'>'
  def __int__(self) :
    return int(self.decode())
  def __long__(self) :
    return long(self.decode())
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
  cast = int
  def encode(self, value) :
    self.vpi_value.value.integer = self.cast(value)
  def decode(self) :
    return self.vpi_value.value.integer

class vpiReal(vpiVar) :
  vpi_type = vpi.vpiRealVal
  cast = float
  def encode(self, value) :
    self.vpi_value.value.real = self.cast(value)
  def decode(self) :
    return self.vpi_value.value.real

class vpiString(vpiVar) :
  vpi_type = vpi.vpiStringVal
  cast     = str
  def encode(self, value) :
    self.vpi_value.value.str = self.cast(value)
  def decode(self) :
    return self.vpi_value.value.str

class vpiNumStr(vpiString) :
  base     = 10
  def __int__(self) :
    return int(self.decode(), self.base)
  def __long__(self) :
    return long(self.decode(), self.base)
  def __add__(self, other) :
    return self.__class__(int(self) + int(other))
  def __iadd__(self, other) :
    return self.__add__(other)
  def __sub__(self, other) :
    return self.__class__(int(self) + int(other))
  def __isub__(self, other) :
    self.encode(self.__add__(other).decode())
    return self
  def encode(self, value) :
    self.vpi_value.value.str = self.cast(value).rstrip('L')

class vpiBinStr(vpiNumStr) :
  vpi_type = vpi.vpiBinStrVal
  base = 2
  def cast(self, value) :
    if isinstance(value, (int, long)) :
      return bin(value)
    return str(value)
class vpiOctStr(vpiNumStr) :
  vpi_type = vpi.vpiOctStrVal
  base = 8
  def cast(self, value) :
    if isinstance(value, (int, long)) :
      return oct(value)
    return str(value)
class vpiDecStr(vpiNumStr) :
  vpi_type = vpi.vpiDecStrVal
  base = 10
  def cast(self, value) :
    if isinstance(value, (int, long)) :
      return str(long(value))
    return str(value)
class vpiHexStr(vpiNumStr) :
  vpi_type = vpi.vpiHexStrVal
  base = 16
  def cast(self, value) :
    if isinstance(value, (int, long)) :
      return hex(value)
    return str(value)

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

class viter_int(viterate) :
  vpi_default = vpi.vpiIntegerVar
class viter_net(viterate) :
  vpi_default = vpi.vpiNet
class viter_port(viterate) :
  vpi_default = vpi.vpiPort
class viter_reg(viterate) :
  vpi_default = vpi.vpiReg
class viter_mod(viterate) :
  vpi_default = vpi.vpiModule
class viter_beg(viterate) :
  vpi_default = vpi.vpiBegin

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

class signalFormatException(Exception) : pass

class signal(vpiObject) :
  vpiBinStrVal   = vpi.vpiBinStrVal  
  vpiOctStrVal   = vpi.vpiOctStrVal  
  vpiDecStrVal   = vpi.vpiDecStrVal  
  vpiHexStrVal   = vpi.vpiHexStrVal  
  vpiScalarVal   = vpi.vpiScalarVal  
  vpiIntVal      = vpi.vpiIntVal     
  vpiRealVal     = vpi.vpiRealVal    
  vpiStringVal   = vpi.vpiStringVal  
  vpiVectorVal   = vpi.vpiVectorVal  
  vpiStrengthVal = vpi.vpiStrengthVal
  vpiTimeVal     = vpi.vpiTimeVal    
  vpiObjTypeVal  = vpi.vpiObjTypeVal 
  vpiSuppressVal = vpi.vpiSuppressVal

  _vpiStringVals = [vpiBinStrVal, vpiOctStrVal, vpiDecStrVal, vpiHexStrVal, vpiStringVal]

  # can update this later to accomodate 4 value
  def __init__(self, handle, rtn=vpiVectorVal, val_type=None) :
    vpiObject.__init__(self, handle)
    self.type = val_type
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
    return self.get_value(signal.vpiIntVal)
  def __float__(self) :
    return self.get_value(signal.vpiRealVal)
  def __str__(self) :
    return self.get_value(signal.vpiStringVal)

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

  def get_value(self, value=None) :
    if value :
      try :
        return value(self)
      except :
        try : 
          self.set_format(value)
        except :
          raise signalFormatException(repr(value))
    elif self.type : 
      return self.type(self)
    
    vpi.vpi_get_value(self.handle, self.vpi_value)
    self.vpi_chk_error = vpiChkError()
    return self.decode(self.vpi_value)

  def set_format(self, format) :
    if format == self.vpi_value.format : return
    self.vpi_value.format = format
    message.debug('%(signal)s format set to %(fmt)d', signal=self.fullname, fmt=format)
    return self
  def set_type(self, val_type) :
    self.type = val_type
    if self.type :
      message.debug('%(signal)s type set to %(name)s', signal=self.fullname, name=val_type.name)
    return self

  def encode(self, value) :
    if self.vpi_value.format == signal.vpiIntVal :
      self.vpi_value.value.integer = value
    elif self.vpi_value.format == signal.vpiVectorVal :
      if not self.vpi_value.value.vector : self.get_value()
      self.vpi_value.value.vector.aval = value
    elif self.vpi_value.format in signal._vpiStringVals :
      if self.vpi_value.format == signal.vpiStringVal :
        self.vpi_value.value.str = value
      else :
        self.vpi_value.value.str = value.rstrip('L')

  @classmethod
  def decode(cls, vpi_value) :
    if vpi_value.format == signal.vpiIntVal :
      return vpi_value.value.integer
    if vpi_value.format == signal.vpiVectorVal :
      return vpi_value.value.vector.aval
    if vpi_value.format in signal._vpiStringVals :
      return vpi_value.value.str.strip()
    return None

################################################################################

class scopeException(Exception) : pass
class ReadOnlyException(Exception) : pass

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

  def __init__(self, _scope) :
    self.read_only = False
    if isinstance(_scope, str) :
      handle = vpi.vpi_handle_by_name(_scope, None)
      if handle is None :
        raise scopeException("Cannot find scope " + _scope)
    else :
      handle = _scope
    vpiObject.__init__(self, handle)
    self.direct = scope.direct(self)
    for viter in [viter_net, viter_reg, viter_int] :
      for sig in map(signal, viter(self.handle)) :
        setattr(self, sig.name, sig)
    #for hier in map(scope, viter_scope(self.handle)) :
    #  setattr(self, scope.name, scope)
    self.read_only = True

  def __getattr__(self, name) :
    message.error('scope %(scope)s contains no object %(name)s', scope=self.name, name=name)
    raise scopeException

  def __setattr__(self, name, value) :
    if hasattr(self, 'read_only') and self.read_only :
      raise ReadOnlyException
    object.__setattr__(self, name, value)

################################################################################

class callback(object) :
  callbacks = list()

  cbValueChange            = vpi.cbValueChange            
  cbStmt                   = vpi.cbStmt                   
  cbForce                  = vpi.cbForce                  
  cbRelease                = vpi.cbRelease                
  cbAtStartOfSimTime       = vpi.cbAtStartOfSimTime       
  cbReadWriteSynch         = vpi.cbReadWriteSynch         
  cbReadOnlySynch          = vpi.cbReadOnlySynch          
  cbNextSimTime            = vpi.cbNextSimTime            
  cbAfterDelay             = vpi.cbAfterDelay             
  cbEndOfCompile           = vpi.cbEndOfCompile           
  cbStartOfSimulation      = vpi.cbStartOfSimulation      
  cbEndOfSimulation        = vpi.cbEndOfSimulation        
  cbError                  = vpi.cbError                  
  cbTchkViolation          = vpi.cbTchkViolation          
  cbStartOfSave            = vpi.cbStartOfSave            
  cbEndOfSave              = vpi.cbEndOfSave              
  cbStartOfRestart         = vpi.cbStartOfRestart         
  cbEndOfRestart           = vpi.cbEndOfRestart           
  cbStartOfReset           = vpi.cbStartOfReset           
  cbEndOfReset             = vpi.cbEndOfReset             
  cbEnterInteractive       = vpi.cbEnterInteractive       
  cbExitInteractive        = vpi.cbExitInteractive        
  cbInteractiveScopeChange = vpi.cbInteractiveScopeChange 
  cbUnresolvedSystf        = vpi.cbUnresolvedSystf        
  cbAssign                 = vpi.cbAssign                 
  cbDeassign               = vpi.cbDeassign               
  cbDisable                = vpi.cbDisable                
  cbPLIError               = vpi.cbPLIError               
  cbSignal                 = vpi.cbSignal                 
  cbNBASynch               = vpi.cbNBASynch               
  cbAtEndOfSimTime         = vpi.cbAtEndOfSimTime         

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

    message.debug('registered callback "%(name)s" for %(reason)s', reason=self.cb_type(), name=self.name)
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

  def cb_type(self) :
    return self.cb_enum(self.callback.reason)

  def get_value(self) :
    return signal.decode(self.callback.value)

  def remove(self) :
    vpi.vpi_remove_cb(self.cb)
    self.vpi_chk_error = vpiChkError()
    self.callbacks.remove(self)
    message.note('callback "%(name)s" called %(cnt)d times, filtered %(filtered)d, exceptions raised %(excepted)d', cnt=self.cnt, filtered=self.filtered, excepted=self.excepted, name=self.name)

  def __del__(self) :
    self.remove()

  @staticmethod
  def remove_all() :
    for c in callback.callbacks : c.remove()

  @classmethod
  def cb_enum(cls, val) :
    import inspect
    return reduce(lambda a, b: b[0] if b[0].startswith('cb') and b[1] == 1 else a, inspect.getmembers(cls), None)

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
    callback.__init__(self, name='PLI error callback', reason=vpi.cbPLIError, func=self.execute)

  def execute(self) :
    self.vpi_chk_error = vpiChkError(True)

# install pli error callback
PLIErrorcb = vpiChkErrorCb()
