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
    if hasattr(self, '_init') :
      self[attr] = val
    else :
      setattr(self, attr, val)
  
  def __add__(self, other) :
    return self.__class__(self.items() + other.items())
  
  def __iter__(self) :
    'iterator which omits internal keys'
    for key in self.iterkeys() :
      if not key.startswith('_') :
        yield key

def accessor_factory(cursor, row) :
  'Horrible, horrible hack here. Reverse list as when there are duplicates for fields we want use to 1st'
  return accessor(reversed([(name[0], row[idx]) for idx, name in enumerate(cursor.description)]))

