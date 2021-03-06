# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

def as_a_accessor(cursor) :
  for row in cursor :
    yield accessor(**row)

class accessor(dict) :
  
  def __init__(self, init=[], **kwargs):
    if init : kwargs.update(dict(init))
    if '_init' in kwargs : del kwargs['_init']
    dict.__init__(self, **kwargs)
    self._init = True
  
  def __getattr__(self, attr) :
    try :
      return self[attr]
    except :
      return None
  
  def __setattr__(self, attr, val) :
    if hasattr(self, '_init') and not attr.startswith('_') :
      self[attr] = val
    else :
      dict.__setattr__(self, attr, val)
  
  def __add__(self, other) :
    return self.__class__(self.items() + other.items())
  
