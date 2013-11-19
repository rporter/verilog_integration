# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import hashlib
import inspect
import itertools
import math
import sys

import mdb
import message
import utils

################################################################################

class messages :
  CVG_0   = message.ident('CVG',   0, message.INFORMATION, 'coverage')
  CVG_1   = message.ident('CVG',   1, message.INFORMATION, 'cover point "%(name)s"')
  CVG_2   = message.ident('CVG',   2, message.INFORMATION, 'axis "%(name)s"')
  CVG_10  = message.ident('CVG',  10, message.INFORMATION, 'dumping cover point "%(name)s"')
  CVG_20  = message.ident('CVG',  20, message.INFORMATION, 'cover point "%(name)s" is at %(cvg)s%%')
  CVG_21  = message.ident('CVG',  21, message.INFORMATION, 'cover point "%(name)s" is at 100%%')
  CVG_22  = message.ident('CVG',  22, message.INFORMATION, 'coverage : %(hits)d out of %(goal)d = %(cvg)s%%')
  CVG_40  = message.ident('CVG',  40, message.INFORMATION, 'creating coverage root node "%(name)s", id %(id)d')
  CVG_41  = message.ident('CVG',  41, message.INFORMATION, 'coverage tree node "%(name)s", id %(id)d of type %(type)s')
  CVG_42  = message.ident('CVG',  42, message.INFORMATION, 'coverage tree leaf node "%(name)s", id %(id)d of type %(type)s')
  CVG_50  = message.ident('CVG',  50, message.INFORMATION, 'using coverage master %(master_id)s for %(log_id)s')
  CVG_100 = message.ident('CVG', 100, message.INFORMATION, '%(agent)s coverage import start')
  CVG_101 = message.ident('CVG', 101, message.INFORMATION, '%(agent)s coverage import end after %(time)0.2fs')
  CVG_110 = message.ident('CVG', 110, message.INFORMATION, '%(agent)s coverage point import start')
  CVG_111 = message.ident('CVG', 111, message.INFORMATION, '%(agent)s coverage point import end after %(time)0.2fs')

  CVG_200 = message.ident('CVG', 200, message.ERROR      , 'hit on bucket marked as illegal')

  @classmethod
  def hush_creation(cls, hush=True) :
    level = message.IGNORE if hush else message.INFORMATION
    if hush :
      message.note('reducing coverage point creation verbosity')
    for msg in [messages.CVG_1, messages.CVG_2, messages.CVG_40, messages.CVG_41, messages.CVG_42] :
      msg.level = level

################################################################################

class coverage :
  'Helper class to ensure consistent interpretation and formating of coverage result'

  def __init__(self, values=None, **kwargs) :
    if not values : values = kwargs
    self.goal = values.get('goal', 0)
    self.hits = values.get('hits', 0)
    self.dp   = values.get('dp'  , 2)

  def __int__(self) :
    return self.integer()
  def __str__(self) :
    return self.format()

  def __add__(self, other) :
    return coverage(
      goal = self.goal + other.goal,
      hits = self.hits + other.hits,
      dp   = max(self.dp, other.dp)
    )

  def description(self, dp=None) :
    return ('%(hits)d of %(goal)d is ' % self.__dict__) + self.format(dp)

  def format(self, dp=None) :
    'Nadger coverage result to ensure correct rounding'
    if self.goal < 1 : return "error"
    _dp = dp or self.dp
    factor = 10 ** _dp
    return ('%.'+str(_dp)+'f') % (math.floor(factor*self.coverage())/factor)

  def percentage(self, dp=None) :
    'Work around pesky % format issues'
    return self.format(dp) + '%'

  def coverage(self) :
    if int(self.goal) < 1 : return float(-1)
    return 100*float(self.hits)/float(self.goal)

  def integer(self) :
    return int(math.floor(self.coverage()))

  def status(self) :
    if self.goal < 1          : return 'error'
    if self.hits >= self.goal : return 'hit'
    if self.hits              : return 'some'
    return 'unhit'

  def is_hit(self) :
    return self.hits >= self.goal

  def json(self) :
    'Dump as dict for json-ification'
    return dict(goal=self.goal, hits=self.hits, status=self.status(), coverage=self.coverage(), description=self.description())

################################################################################

class bucket :
  """
  An individual bucket. Has notion of 

  hits      : number of times event occured
  goal      : desired number of events
  illegal   : flag when event occurs as it shouldn't
  dont_care : do nothing as the event is uninteresting
  """

  class axesRef(dict) :
    """
    To determine state of all axes - read only
    """
    def __init__(self, **kwargs) :
      dict.__init__(self, **kwargs)
  
    def __getattr__(self, attr) :
      return self[attr]

  def __init__(self, parent, idx, seq) :
    self.parent    = parent
    self.idx       = idx
    self.seq       = seq
    self.hits      = 0
    self.goal      = None
    self.illegal   = False
    self.dont_care = False
    self.axis      = bucket.axesRef(**seq)

    # user defined setup
    parent.define(self)
    
    # is there a requirement to iterate again and set goal to 0 for dont_care & illegal

  def default(self, illegal=False, dont_care=False, goal=0, hits=0, **others) :
    self.goal      = goal
    self.illegal   = illegal or goal < 0
    self.dont_care = dont_care or goal == 0
    if hits : self.hits = hits

  def target(self) :
    if self.illegal or self.dont_care : return 0
    return self.goal

  def incr(self, hits=1, oneoff=False, quiet=False) :
    if self.illegal and not quiet : 
      messages.CVG_200(idx=self.idx, enum=self.seq)
    if oneoff and self.hits : 
      # if oneoff is true only count if bucket unhit
      return
    if not (self.illegal or self.dont_care) and self.hits < self.goal : 
      # we keep a tally of point hits
      self.parent.tally_hits(self, hits)
    self.hits += hits

  def hit(self) :
    self.incr(1, True)

  def adj_goal(self) :
    if self.illegal   : return -1
    if self.dont_care : return 0
    return self.goal

  def dump(self, offset=0, reference=False) :
    idx = offset+self.idx
    if reference :
      return (idx, self.adj_goal())
    else :
      return (idx, self.hits)

  def load(self, hits=0, bucket_id=None, **others) :
    # just for loading with coverage
    # if bucket id is given, make sure it tallies
    if bucket_id and bucket_id != self.parent.offset+self.idx :
      message.error('given bucket index does no match actual bucket index')
    self.incr(hits, quiet=True)

  def json(self) :
    'Dump as list for json-ification'
    return (self.adj_goal(), self.hits)

################################################################################

class axisValueError(Exception) : pass
class axisNameError(Exception) : pass

class axis :
  """
  Enumeration of values

  Initialised via list or arglist (for enumerations)

  axis0 = axis(range(0,10))
  axis1 = axis(['one', 'two'])
  axis1 = axis(bob=1, fred=3)
  axis1 = axis({'front' : 1, 'back' : 2})

  enumerations stored as dictionary with integer, values

  """

  def __init__(self, name=None, parent=None, values=None, start=0, **enums) :
    self.name = name or "No Description Given"
    if parent :
      parent.add_axis(self)
    if values is not None :
      if isinstance(values, dict) :
        self.values = values
      elif isinstance(values, list) :
        self.values = dict(zip(values, (range(start, start+len(values)))))
      else :
        message.error('axis %(name)s has illegal value type (%vtype)s', name=self.name, vtype=type(values))
        raise axisValueError
    else :
      # must have some values
      if not len(enums) :
        message.error('axis %(name)s has no values', name=self.name)
        raise axisValueError
      self.values = enums
    # make sure enum indices are integers
    non_int = filter(lambda x : not(isinstance(x, int)), self.values.values())
    if non_int :
      message.error('axis %(name)s has non integer indices %(non_int)s', name=self.name, non_int=non_int)
      raise axisValueError
    # reverse lookup
    self.rev = dict((value, key) for key, value in self.values.iteritems())
    # check enum values unique
    if len(self.rev) != len(self.values) :
      raise axisValueError
    self.ord = dict((key, idx) for idx, key in enumerate(self.get_enums()))

  def __len__(self) :
    return len(self.values.keys())

  def get_values(self) :
    return sorted(self.values.values())

  def get_enums(self) :
    return [self.rev[value] for value in self.get_values()]

  def __set__(self, instance, value) :
    if value in self.values.values() :
      self.value = value
    elif type(value) == type(int) and value in self.rev.keys():
      self.value = self.rev[value]
    else :
      message.error('axis %(name) has no enumeration %(value)', name=self.name, value=value)

  def __get__(self, instance, owner) :
    return self.value

  def json(self) :
    'Dump as dict for json-ification'
    return dict(name=self.name, values=map(str, self.get_enums()))

  def sql(self, inst) :
    return inst.axis(self)

  @utils.lazyProperty
  def md5(self) :
    'md5 hash of axis'
    md5 = hashlib.md5()
    md5.update(str(self.values))
    return md5.hexdigest()

################################################################################

class hierarchy :
  """
  A hierarchical container for coverpoints.
  """
  ROOTNAME  = 'coverage'
  SYMBOL    = '>'
  MESSAGE   = messages.CVG_41
  
  class rootMixin :
    'dynamic mixin for root nodes'
    def __init__(self, id) :
      # default to 0 for root node
      self.id = int(id or 0)
      self.next_id = self.id + 1
      self.offset = 0
      self.all_nodes = dict()
      hierarchy.aroot = self.root # store latest root for backwards compatability
    def get_id(self) :
      value, self.next_id = self.next_id, self.next_id+1
      return value
    def calc_offset(self, offset) :
      current_offset = self.offset
      self.offset += offset
      return current_offset
    @classmethod
    def mixin(cls, inst, *args) :
      inst.__class__.__bases__ = (cls,) + inst.__class__.__bases__
      cls.__init__(inst, *args)

  def __init__(self, name, description=None, parent=None, root=False, type=None, id=None) :
    if parent is None :
      if root :
        # this is the new root node
        self.root = self
      else :
        # default is root node
        _parent = self.root
        message.debug("Hierarchy '%(name)s' given no parent id, defaulting to root", name=name)
    else :
      try :
        # it might be an integer reference
        _parent = self.all_nodes[int(parent)]
        message.debug('Parent id given as integer %(parent)d', parent=int(parent))
      except :
        # must be hierarchy object
        _parent = parent

    self.name        = name
    self.description = description or 'None given'
    self.children    = list()

    if root :
      self.parent = None
      self.rootMixin.mixin(self, id)
    else :
      _parent.add_child(self)
      # assign unique id
      self.id = id or self.root.get_id()

    # store hashed by this id
    self.all_nodes[self.id] = self
    if self.is_root :
      # root node
      messages.CVG_40(name=self.name, id=self.id)
    self.MESSAGE(name=name, id=self.id, type=self.__class__.__name__, parent=self.get_parent_id())

  def add_child(self, child) :
    child.parent = self
    self.children.append(child)

  def get_parent_id(self) :
    if self.parent :
      return self.parent.id
    return None

  def debug(self, indent='', pfix='-', verbose=True) :
    message.debug(indent + self.SYMBOL + ' ' + self.name + ' ' + self.coverage().description() if verbose else '')
    for child in self.children :
      child.debug(indent=indent+pfix, pfix=pfix, verbose=verbose)

  def coverage(self) :
    'determine coverage'
    return sum([pt.coverage() for pt in self.children], coverage())

  def dump(self, func=None, reference=False) :
    'dump coverage data'
    result = sum([pt.dump(func, reference) for pt in self.children], coverage())
    if not reference :
      messages.CVG_22(hits=result.hits, goal=result.goal, cvg=result.format())
    return result

  def load(self, func=None) :
    'dump coverage data'
    return sum([pt.load(func) for pt in self.children], coverage())

  def html(self, chan=sys.stdout) :
    cvg = self.coverage()
    chan.write('<li><span><b>%s</b> %s <i class="%s">%s</i></span>' % (self.name, self.description, cvg.status(), cvg.description()))
    if self.children :
      chan.write('<ul>')
      for child in self.children :
        child.html(chan)
      chan.write('</ul>')
    chan.write('</li>')

  def json(self) :
    'Dump as dict for json-ification'
    return dict(hierarchy=self.name, description=self.description, id=self.id, coverage=self.coverage().json(), children=[child.json() for child in self.children])

  def sql(self, inst) :
    return inst.hierarchy(self)
  @utils.lazyProperty
  def md5(self) :
    'return tuple of 2 md5 sums : self, children'
    return (self.md5_self, self.md5_children)
  @utils.lazyProperty
  def md5_self(self) :
    md5 = hashlib.md5()
    md5.update(self.name + self.description)
    return md5.hexdigest()
  @utils.lazyProperty
  def md5_children(self) :
    md5 = hashlib.md5()
    md5.update(str([child.md5 for child in self.children]))
    return md5.hexdigest()

  @utils.lazyProperty
  def root(self) :
    'If no root node exists, make one'
    if getattr(self, 'parent', None) is None :
      if self.aroot is None :
        self.root = hierarchy(name=self.ROOTNAME, root=True)
      else :
        self.root = self.aroot
      return self.root
    return self.parent.root

  @utils.lazyProperty
  def is_root(self) :
    return self.parent == None

  @utils.lazyProperty
  def all_nodes(self) :
    return self.root.all_nodes

  # The following are for backward compatability with singleton root model
  aroot     = None

  @classmethod
  def get_root(cls) :
    return cls.aroot

  @classmethod
  def populated(cls) :
    'is there anything here?'
    return cls.get_root() != None

  @classmethod
  def dump_all(cls, func=None, reference=False) :
    total_cvg = cls.get_root().dump(func, reference)

  @classmethod
  def load_all(cls, func=None) :
    cls.get_root().load(func)

  @classmethod
  def reset(cls) :
    cls.aroot = None

################################################################################

class coverpoint(hierarchy) :
  """
  Base class for all coverpoints
  """
  SYMBOL  = '+'
  MESSAGE = messages.CVG_42

  DUMP_HITS      = 0
  DUMP_ILLEGAL   = 1
  DUMP_DONT_CARE = 2
  DUMP_ALL       = DUMP_ILLEGAL | DUMP_DONT_CARE

  # change what hits get dumped
  # e.g. coverpoint.DUMP = coverpoint.DUMP_NONE
  # default dumps everything
  DUMP = DUMP_ALL

  def __init__(self, model=None, name=None, description=None, parent=None, id=None, axes={}, defaults=None, cumulative=False) :
    self.name        = name or self.__doc__.strip()
    self.model       = model
    # if given merge axes
    self.__dict__.update(axes)
    # if an OrderedDict is used then order preserved
    if axes :
      self._axes = axes.items()
    # this is a generator that yields the bucket defaults as a dictionary
    self.defaults    = defaults
    self.cumulative  = cumulative
    # enumerate buckets
    self.hits    = 0                 # running total of hits for coverpoint
    self.hit     = False
    self.buckets = [bucket(self, idx, seq) for idx, seq in enumerate(self.indices_dict())]
    self.multipliers = self.significands()
    self.goal    = reduce(lambda a, b : a+b.target(), self.buckets, 0)
    self.total_hits()
    # running count of buckets for all coverpoints and increment global offset
    self.offset = self.root.calc_offset(self.num_of_buckets())
    # record this point
    messages.CVG_1(name=self.name)
    for name, axe in self.axes() :
      msg = messages.CVG_2(name=name)
    hierarchy.__init__(self, name=self.name, description=description or self.__doc__.strip(), parent=parent, id=id)

  def __len__(self) :
    return len(self.buckets)

  def add_axis(self, name, **kwargs) :
    'add axis'
    if hasattr(self, name) :
      raise coverageError('axis name ' + name + ' already exists')
    setattr(self, name, axis(name=name, **kwargs))
    if not hasattr(self, '_axes') :
      self._axes = list()
    self._axes.append((name, getattr(self, name)))
    return getattr(self, name)

  def axes(self) :
    'determine axes'
    if not hasattr(self, '_axes') :
      self._axes = filter(lambda o : isinstance(o[1], axis), inspect.getmembers(self))
    return self._axes

  def get_axes(self) :
    'return axes member objects'
    return [a[1] for a in self.axes()]

  def get_axes_names(self) :
    'determine axes member names'
    return [a[0] for a in self.axes()]

  def num_of_buckets(self) :
    return reduce(lambda a, b : a*b, map(len, self.get_axes()))
  def indices(self) :
    return itertools.product(*map(axis.get_enums, self.get_axes()))
  def indices_dict(self) :
    axes = self.get_axes_names()
    for seq in self.indices() :
      yield dict(zip(axes, seq))
  def significands(self) :
    'return dictionary of significands'
    sizes = list(list((a[0], len(a[1]))) for a in self.axes())
    ref = list(sizes) + list((('',1),))
    for i in range(0, len(sizes)) :
      sizes[i][1] = reduce(lambda a, b : a*b, [a[1] for a in ref[i+1:]])
    return dict(sizes)

  def total_hits(self) :
    self.hits = sum([min(bucket.hits, bucket.target()) for bucket in self.buckets])
    self.is_hit()

  def tally_hits(self, bucket, adjust) :
    # we keep a tally of point hits
    # decrement this buckets contribution ...
    self.hits -= bucket.hits
    # ... then add current total maxing out at goal
    self.hits += min(bucket.hits + adjust, bucket.goal)
    # are we there yet?
    self.is_hit()

  def is_hit(self) :
    if self.hit : return True
    self.hit = self.hits == self.goal
    if self.hit :
      messages.CVG_21(name=self.name)
      self.hit_cb()
    return self.hit

  def hit_cb(self) :
    'Callback upon reaching 100%'
    pass

  def coverage(self) :
    return coverage(hits=self.hits, goal=self.goal)

  def dump(self, func=None, reference=False, compress=True) :
    '''
    serialized dump of buckets associated with this coverpoint

    func      : function called with serialized output data as argument
    reference : output data is tabulation of bucket index and goal, not hit data
    compress  : when not reference, do not dump unhit or dont_care buckets.
    '''
    dump_all = self.DUMP == self.DUMP_HITS
    dump_illegal = self.DUMP & self.DUMP_ILLEGAL
    dump_dont_care = self.DUMP & self.DUMP_DONT_CARE
    def bfilter(bucket) :
      'Filter function to determine if to dump details on hit bucket'
      if dump_all :
        # Dump this bucket
        return False
      if bucket.illegal and not(dump_illegal) :
        # Don't dump this bucket
        return True
      if bucket.dont_care and not(dump_dont_care) :
        # Don't dump this bucket
        return True
      # Dump this bucket
      return False

    if func :
      for bucket in self.buckets :
        if not reference and compress and (bfilter(bucket) or bucket.hits == 0) :
          continue
        func(bucket.dump(self.offset, reference))
    # generate a summary for this point
    if not reference :
      if not self.is_hit() :
        # if it is hit that will already have been recorded
        messages.CVG_20(name=self.name, cvg=self.coverage().format(), hits=self.hits, goal=self.goal, offset=self.offset, buckets=self.num_of_buckets())
    return self.coverage()

  def load(self, func) :
    for bucket in self.buckets :
      bucket.load(**next(func))
    return self.coverage()

  def json(self) :
    'Dump as dict for json-ification'
    return dict(coverpoint=self.name, description=self.description, id=self.id, cumulative=self.cumulative, coverage=self.coverage().json(), offset=self.offset, axes=[axis.json() for axis in self.get_axes()], buckets=[bucket.json() for bucket in self.buckets])

  def sql(self, inst) :
    return inst.coverpoint(self)

  @utils.lazyProperty
  def md5(self) :
    'return tuple of 3 md5 sums : self, goal, axes'
    return (self.md5_self, self.md5_axes, self.md5_goal)
  @utils.lazyProperty
  def md5_axes(self) :
    md5 = hashlib.md5()
    md5.update(str([axis.md5 for axis in self.get_axes()]))
    return md5.hexdigest()
  @utils.lazyProperty
  def md5_goal(self) :
    md5 = hashlib.md5()
    md5.update(str([bucket.goal for bucket in self.buckets]))
    return md5.hexdigest()

  def bucket_id(self, **axes) :
    'Call with dictionary of axis=int(value)'
    return reduce(lambda a, b : a+b, [self.multipliers[key]*value for key, value in axes.iteritems()])

  def cursor(self) :
    return cursor(self)

  def define(self, bucket) :
    'default define'
    bucket.default(**next(self.defaults))

################################################################################

class cursor :

  class InstanceDescriptorMixin(object):
    def __getattribute__(self, name):
      value = object.__getattribute__(self, name)
      if hasattr(value, '__get__'):
        value = value.__get__(self, self.__class__)
      return value

    def __setattr__(self, name, value):
      try:
        obj = object.__getattribute__(self, name)
      except AttributeError:
        pass
      else:
        if hasattr(obj, '__set__'):
          return obj.__set__(self, value)
      return object.__setattr__(self, name, value)

  class axes(InstanceDescriptorMixin) :

    class axisDesc :
      """
      Read/write model of axis for cursor
      """
      def __init__(self, axis) :
        self.axis  = axis
        self.value = None

      def __set__(self, instance, value) :
        if value in self.axis.values :
          self.value = value
        elif isinstance(value, int) and value in self.axis.rev:
          self.value = self.axis.rev[value]
        else :
          message.error('axis %(name)s has no enumeration %(value)s', name=self.axis.name, value=value)
          raise axisValueError

      def __get__(self, instance, owner) :
        return self.value

      def __int__(self) :
        return self.axis.ord[self.value]

      def __iadd__(self, other) :
        """
        can't use this if __get__ returns non self-object type

        would need to implement __cmp__, __le__ etc.
        """
        if isinstance(other, int) :
          adj = other
        elif other in self.axis.values :
          adj = self.axis.ord[other]
        else :
          message.error('axis %(name)s has no enumeration %(value)s', name=self.axis.name, value=other)
          raise axisValueError
        self.__set__(None, self.__int__ + adj)

    def __init__(self, axes) :
      for name, axis in axes :
        setattr(self, name, cursor.axes.axisDesc(axis))

  def __init__(self, point) :
    self.point = point
    # take copies of axes
    self.axis = cursor.axes(point.axes())

  def __call__(self, **kwargs) :
    for axis, value in kwargs.iteritems() :
      try :
        cursor.axes.axisDesc.__set__(self.axis.__dict__[axis], None, value)
      except :
        raise axisNameError(axis)
    return self

  def __enter__(self) :
    return self

  def __exit__(self, type, value, traceback) :
    pass

  def __getattr__(self, attr) :
    'look for axis name and return state'
    try :
      return cursor.axes.axisDesc.__get__(self.axis.__dict__[attr], None, None)
    except :
      raise axisNameError(axis)

  def hit(self) :
    try :
      self.point.buckets[self.bucket_id()].hit()
    except axisValueError :
      message.warning('hit is not registered')

  def incr(self, hits=1) : 
    try :
      self.point.buckets[self.bucket_id()].incr(hits)
    except axisValueError :
      message.warning('increment is not registered')

  def state(self) :
    return dict([(key, cursor.axes.axisDesc.__get__(value, None, None)) for key, value in self.axis.__dict__.iteritems()])

  def bucket_id(self) :
    try :
      return self.point.bucket_id(**dict([(key, int(value)) for key, value in self.axis.__dict__.iteritems()]))
    except KeyError :
      message.error('cursor value for axis is None')
      raise axisValueError

################################################################################
