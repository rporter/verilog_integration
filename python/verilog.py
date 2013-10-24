# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

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

class platform :
  iverilog  = 'Icarus Verilog'
  verilator = 'Verilator'
  @classmethod
  def is_icarus(cls) :
    return vpiInfo().product == cls.iverilog
  @classmethod
  def is_verilator(cls) :
    return vpiInfo().product == cls.verilator

################################################################################

class vpiChkError :
  def __init__(self, echo=False) :
    self.error_info = vpi.s_vpi_error_info()
    if vpi.vpi_chk_error(self.error_info) and echo :
      message.message.vpiLevel[self.error_info.level](self.error_info.message)

################################################################################

class vpiVar :
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
  def __getitem__(self, idx) :
    return (int(self) >> idx)&1
  def __setitem__(self, idx, val) : pass
  def __getslice__(self, hi, lo) : pass
  def __setslice__(self, hi, lo, val) : pass

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
  def get(self, signal) :
    vpi.vpi_get_value(signal.handle, self.vpi_value)
    self.copy = str(self.vpi_value.value.str)
    self.vpi_chk_error = vpiChkError()
    return self
  def encode(self, value) :
    self.vpi_value.value.str = self.cast(value)
    self.copy = str(self.vpi_value.value.str)
  def decode(self) :
    return self.copy

class vpiNumStr(vpiString) :
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
    if platform.is_icarus() and (self.vpi_value.value.str.startswith('0b') or self.vpi_value.value.str.startswith('0x')):
      self.vpi_value.value.str = self.vpi_value.value.str[2:]
    self.copy = str(self.vpi_value.value.str)
  def decode(self) :
    if platform.is_icarus() :
      return self.copy.replace('X','0').replace('x','0')
    return self.copy

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

class viterate :
  vpi_default = None
  def __init__(self, handle, _type=None) :
    self.vpi_i = vpi.vpi_iterate(_type or self.vpi_default, handle)
    self.vpi_chk_error = vpiChkError()
  def __del__(self) :
    if self.vpi_i  :
      # final iterate may have free'd object
      vpi.vpi_free_object(self.vpi_i)
  def __iter__(self):
    return self
  def next(self) :
    if self.vpi_i :
      value = vpi.vpi_scan(self.vpi_i)
      if value :
        return value
    self.vpi_i = None
    raise StopIteration

class viter_int(viterate) :
  vpi_default = vpi.vpiIntegerVar
class viter_net(viterate) :
  vpi_default = vpi.vpiNet
class viter_port(viterate) :
  vpi_default = vpi.vpiPort
class viter_reg(viterate) :
  vpi_default = vpi.vpiReg
class viter_mem(viterate) :
  vpi_default = vpi.vpiMemory
class viter_mod(viterate) :
  vpi_default = vpi.vpiModule
class viter_beg(viterate) :
  vpi_default = vpi.vpiBegin

################################################################################

class vpiObject(object) :
  def __init__(self, handle) :
    self.handle = handle
    self.vpi_chk_error = None
  def __del__(self) :
    vpi.vpi_free_object(self.handle)

  def __str__(self) :
    return self.get_str(vpi.vpiName)

  def get_str(self, prop) :
    result = vpi.vpi_get_str(prop, self.handle)
    try :
      self.vpi_chk_error = vpiChkError()
    except ReadOnlyException :
      pass
    return result

  @lazyProperty
  def name(self) :
    return self.get_str(vpi.vpiName)
  @lazyProperty
  def fullname(self) :
    return self.get_str(vpi.vpiFullName)

  @lazyProperty
  def scalar(self) :
    return vpi.vpi_get(vpi.vpiScalar, self.handle)
  @lazyProperty
  def vector(self) :
    return vpi.vpi_get(vpi.vpiVector, self.handle)
  @lazyProperty
  def size(self) :
    result = vpi.vpi_get(vpi.vpiSize, self.handle)
    self.vpi_chk_error = vpiChkError()
    return result
  @lazyProperty
  def index(self) :
    handle = vpi.vpi_handle(vpi.vpiIndex, self.handle)
    self.vpi_chk_error = vpiChkError()
    return int(signal(handle))

  @lazyProperty
  def lhs(self) :
    handle = vpi.vpi_handle(vpi.vpiLeftRange, self.handle)
    self.vpi_chk_error = vpiChkError(True)
    return int(signal(handle))
  @lazyProperty
  def rhs(self) :
    handle = vpi.vpi_handle(vpi.vpiRightRange, self.handle)
    self.vpi_chk_error = vpiChkError(True)
    return int(signal(handle))

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
    # take a copy of the string value
    if self.vpi_value.format in self._vpiStringVals :
      self.copy = str(self.vpi_value.value.str)
    else :
      self.copy = None
    return self.decode(self.vpi_value, self.copy)

  def set_format(self, format) :
    if format == self.vpi_value.format : return
    self.vpi_value.format = format
    return self
  def set_type(self, val_type) :
    self.type = val_type
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
  def decode(cls, vpi_value, copy=None) :
    if vpi_value.format == signal.vpiIntVal :
      return vpi_value.value.integer
    if vpi_value.format == signal.vpiVectorVal :
      return vpi_value.value.vector.aval
    if vpi_value.format in signal._vpiStringVals :
      result = copy if copy is not None else vpi_value.value.str
      return result.strip()
    return None

################################################################################

def memoize(obj):
  'http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize'
  import functools
  cache = obj.cache = {}
  
  @functools.wraps(obj)
  def memoizer(*args, **kwargs):
    if args not in cache:
      cache[args] = obj(*args, **kwargs)
    return cache[args]
  return memoizer

class memory(vpiObject) :
  '''
  This only provides an abstraction for verilog memories (which have two dimensions)
  and not wire or reg arrays (which have multiple dimensions).
  '''

  def __init__(self, handle, rtn=signal.vpiVectorVal, val_type=None) :
    vpiObject.__init__(self, handle)

  @memoize
  def __getitem__(self, idx) :
    'Will need to memoize?'
    return signal(vpi.vpi_handle_by_index(self.handle, idx))

  def __setitem__(self, idx, val) :
    self[idx].set_value(val)

  def __iter__(self) :
    for idx, handle in enumerate(viterate(self.handle, vpi.vpiMemoryWord)) :
      result = self.__getitem__.cache[(self, idx)] = signal(handle)
      yield result

  def iter(self) :
    'other iteration implementation'
    for idx in self.range() :
      yield self[idx]

  def range(self) :
    i = self.lhs
    while (1) :
      yield i
      if i == self.rhs :
        raise StopIteration
      i += self.direction

  @lazyProperty
  def direction(self):
    return -1 if self.lhs > self.rhs else 1

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
    def abstraction_fcty(handle) :
      'Abstraction factory - return memory or signal on handle type'
      if vpi.vpi_get(vpi.vpiType, handle) == vpi.vpiMemory :
        return memory(handle)
      return signal(handle)
    self._read_only = False
    self._signals   = dict()
    if isinstance(_scope, str) :
      handle = vpi.vpi_handle_by_name(_scope, None)
      if handle is None :
        raise scopeException("Cannot find scope " + _scope)
    else :
      handle = _scope
    vpiObject.__init__(self, handle)
    self.direct = scope.direct(self)
    for viter in [viter_net, viter_reg, viter_int, viter_mem] :
      for sig in map(abstraction_fcty, viter(self.handle)) :
        setattr(self, sig.name, sig)
        self._signals[sig.name] = sig
    #for hier in map(scope, viter_scope(self.handle)) :
    #  setattr(self, scope.name, scope)
    self._read_only = True

  def __getattr__(self, name) :
    message.error('scope %(scope)s contains no object %(name)s', scope=self.name, name=name)
    raise scopeException

  def __setattr__(self, name, value) :
    if hasattr(self, '_read_only') and self._read_only :
      raise ReadOnlyException
    object.__setattr__(self, name, value)

################################################################################

class callback :
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

  def __del__(self) :
    self.remove()

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
    message.note('callback "%(name)s" called %(cnt)d times, filtered %(filtered)d, exceptions raised %(excepted)d', cnt=self.cnt, filtered=self.filtered, excepted=self.excepted, name=self.name)
    # e.g. Icarus can return null pointer for unsupported reasons,
    # so test non NULL/None object prior to remove/free
    if self.cb :
      vpi.vpi_remove_cb(self.cb)
      self.vpi_chk_error = vpiChkError()
      vpi.vpi_free_object(self.cb)
    self.callbacks.remove(self)

  @classmethod
  def remove_all(cls) :
    while cls.callbacks :
      cls.callbacks[0].remove()

  @classmethod
  def cb_enum(cls, val) :
    import inspect
    return reduce(lambda a, b: b[0] if b[0].startswith('cb') and b[1] == 1 else a, inspect.getmembers(cls), None)

################################################################################

class vpiChkErrorCb(callback) :
  def __init__(self) :
    callback.__init__(self, name='PLI error callback', reason=vpi.cbPLIError, func=self.execute)

  def execute(self) :
    self.vpi_chk_error = vpiChkError(True)

# install pli error callback
PLIErrorcb = vpiChkErrorCb()
