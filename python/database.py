# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import collections

import coverage
import mdb
import message
import pwd

################################################################################

class index :
  # stolen from python website
  # and mashed around a bit
  class groupby:
    def __init__(self, iterable, keyfunc=None, keyfact=None, grpfact=None):
      self.it = iter(iterable)
      self.tgtkey = self.currkey = self.currvalue = object()
      self.keyfunc, self.keyfact, self.grpfact = keyfunc, keyfact or self.default_keyfact, grpfact or self.default_grpfact
    def __iter__(self):
      return self
    def __next__(self):
      while self.currkey == self.tgtkey:
        self.currvalue = next(self.it)    # Exit on StopIteration
        self.currkey = self.keyfunc(self.currvalue)
      self.tgtkey = self.currkey
      return self.keyfact(self)
 
    next=__next__
    def _grouper(self, tgtkey):
      while self.currkey == tgtkey:
        yield self.grpfact(self)
        self.currvalue = next(self.it)    # Exit on StopIteration
        self.currkey = self.keyfunc(self.currvalue)

    @staticmethod
    def default_keyfact(self) :
      return [self.currvalue, self._grouper(self.tgtkey)]
    @staticmethod
    def default_grpfact(self) :
      return self.currvalue

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  class log(dict) :

    class messages(list) :
      class message(dict) :
        def __init__(self, values) :
          dict.__init__(self, values)
        def __getattr__(self, attr) :
          return self[attr]
        @property
        def isfail(self) :
          return self.level >= message.ERROR
      def __init__(self, msgs) :
        list.__init__(self, map(self.message, msgs))
        self.sort(key=lambda k : k.level, reverse=True)
      def __getattr__(self, attr) :
        attr = attr.upper()
        for msg in self :
          if msg.severity == attr : return msg
        return None

    def __init__(self, log, msgs, **kwargs) :
      dict.__init__(self, log = log, msgs = self.messages(msgs))
      self.update(status=self.compute_status())

    def __getattr__(self, attr) :
      try : 
        return self[attr]
      except :
        return self.msgs.__getattr__(attr)

    def compute_status(self) :
      'compute status'
      if self.first.isfail :
        return mdb.accessor(status='FAIL', reason='('+self.first.severity+') '+self.first.msg)
      if self.SUCCESS :
        if self.SUCCESS.count == 1 :
	  return mdb.accessor(status='PASS', reason=self.SUCCESS.msg)
        else :
          return mdb.accessor(status='FAIL', reason='Too many SUCCESSes (%d)' % self.SUCCESS.count)
      return mdb.accessor(status='FAIL', reason='No SUCCESS')

    @property
    def first(self) :
      return self.msgs[0]

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  class limit :
    def __init__(self, finish=None, start=None) :
      self.start, self.finish = start, finish
    def __str__(self) :
      if self.finish :
        if self.start :
          return "LIMIT %(start)d, %(finish)d" % self.__dict__
        else :
          return "LIMIT %(finish)d" % self.__dict__
      return ""

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  class subquery(dict) :
    def __init__(self, select, frm, **kwargs) :
      dict.__init__(self, select=select, frm=frm, **kwargs)
    def __getattr__(self, attr) :
      try :
        return self[attr]
      except KeyError :
        return None
    def __str__(self) :
      order = 'ASC' if self.order == 'up' else 'DESC';
      return ('SELECT ' + self.select + ' FROM ' + self.frm +
              ((' WHERE ' + self.where)              if self.where  else '') +
              ((' GROUP BY ' + ','.join(self.group)) if self.group  else '') +
              ((' HAVING ' + self.having)            if self.having else '') +
              ' ORDER BY log_id ' + order + ' ' + str(self.limit)) % self
    def update(self, **kwargs) :
      dict.update(self, **kwargs)
      return self
    def where_and(self, expr) :
      if self.where :
        self.where += ' AND ' + expr
      else :
        self.where = expr

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  class summary(list) :
    class result(mdb.accessor) :
      def __init__(self, total) :
        mdb.accessor.__init__(self, passes=0, fails=0, total=total)
      def summary(self) :
        if self.passes != self.total :
          msg = message.error
        else :
          msg = message.information
        msg('%(total)d %(tests)s, %(passes)d pass, %(fails)d fail', tests='test' if self.total == 1 else 'tests', **self)
    
    def __init__(self, results) :
      list.__init__(self, results)
    def summary(self, include=False) :
      tests = self if include else self[1:]
      result = self.result(total=len(tests))
      for r in tests :
        if r.status.status == 'PASS' :
          result.passes += 1
        else :
          result.fails += 1
      return result
    def listing(self, include=False, verbose=True) :
      tests = self if include else self[1:]
      for test in tests : pass

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  order = 'log_id, msg_id, level ASC'

  def result(self, subquery) :
    return self.summary([self.log(log, msgs) for log, msgs in self.groupby(self.execute(subquery), lambda x : x.log_id, self.keyfact, self.grpfact)])

  def where(self, variant, limit, start, order='down', coverage=False) :
    'Note that asking for coverage here slows the query significantly'
    if variant == 'sngl' :
      result = self.subquery('l0.*, null as children', frm='log as l0 left join log as l1 on (l0.log_id = l1.root)', group=['l0.log_id'], where='l1.log_id is null and l0.root is null')
    elif variant == 'rgr' :
      result = self.subquery('l0.*, count(l1.log_id) as children', frm='log as l0 left join log as l1 on (l0.log_id = l1.root)', group=['l0.log_id'], having='l1.log_id is not null')
    else :
      result = self.subquery('l0.*, count(l1.log_id) as children', frm='log as l0 left join log as l1 on (l0.log_id = l1.root)', group=['l0.log_id'])
    result.limit = self.limit(limit)
    if start :
      result.where_and('l0.log_id %c %d' % ('>' if order == 'up' else '<', start))
    if coverage :
      result.select += ', goal.log_id as goal, hits.log_id as coverage, master.goal_id AS master'
      result.frm    += ' left outer join goal using (log_id) left outer join hits using (log_id) left outer join master using (log_id)'
    result.update(order=order)
    return result

  def execute(self, subquery) :
    with mdb.db.connection().row_cursor() as db :
      message.debug('SELECT log.*, message.*, COUNT(*) AS count FROM (%s) AS log NATURAL LEFT JOIN message GROUP BY log_id, level ORDER BY %s;' % (str(subquery), self.order))
      db.execute('SELECT log.*, message.*, COUNT(*) AS count FROM (%s) AS log NATURAL LEFT JOIN message GROUP BY log_id, level ORDER BY %s;' % (str(subquery), self.order))
      return db.fetchall()

  @staticmethod
  def keyfact(self) :
    'key factory for grouping'
    return [mdb.accessor(user=pwd.getpwuid(self.currvalue.uid).pw_name, **self.currvalue), self._grouper(self.tgtkey)]
  @staticmethod
  def grpfact(self) :
    'group factory for grouping'
    return mdb.accessor(level=self.currvalue.level, severity=self.currvalue.severity, msg=self.currvalue.msg, count=self.currvalue.count)

################################################################################

class msgs :
  def result(self, log_id):
    with mdb.db.connection().row_cursor() as db :
      message.debug('retrieving %(log_id)s messages', log_id=log_id)
      db.execute('SELECT * FROM message WHERE log_id = %(log_id)s;' % locals())
      return db.fetchall()

################################################################################

class rgr(index) :
  order = 'parent ASC, log_id, msg_id, level ASC'
  
  def result(self, log_id, root=True):
    relationship = 'root' if root else 'parent'
    # call result method of parent class
    return index.result(self, self.subquery('l0.*, count(l1.log_id) as children', frm='log as l0 left join log as l1 on (l0.log_id = l1.%(relationship)s)', where='l0.log_id = %(log_id)s or l0.%(relationship)s = %(log_id)s', group=['l0.log_id'], limit=self.limit(), log_id=log_id, relationship=relationship))

################################################################################

class cvg : 
  class hierarchy :
    def __init__(self, db, defaults) :
      coverage.hierarchy.reset()
      for parent, children in index.groupby(db, lambda row : row.point_id) :
        if parent.axis_id :
          coverage.coverpoint(name=parent.point_name, description=parent.desc, id=parent.point_id, parent=parent.parent, axes=self.get_axes(children), defaults=defaults)
        else :
          coverage.hierarchy(parent.point_name, parent.desc, id=parent.point_id, root=parent.root == None, parent=parent.parent)
    def get_axes(self, nodes) :
      return collections.OrderedDict([(axis.axis_name, coverage.axis(axis.axis_name, **dict([(e.enum, e.enum_id) for e in enum]))) for axis, enum in index.groupby(nodes, lambda node : node.axis_id)])
        
  class single :
    def __init__(self, log_id, goal_id=None) :
      self.log_id = log_id
      self.goal_id = goal_id or log_id
    def points(self) :
      with mdb.db.connection().row_cursor() as db :
        db.execute('SELECT * FROM point LEFT OUTER JOIN axis USING (point_id) LEFT OUTER JOIN enum USING (axis_id) WHERE log_id=%(log_id)s ORDER BY point_id ASC, axis_id ASC, enum_id ASC;' % self.__dict__)
        cvg.hierarchy(db.fetchall(), self.coverage())
        return coverage.hierarchy.get_root()
    def coverage(self) :
      with mdb.db.connection().row_cursor() as db :
        db.execute('SELECT goal.bucket_id, goal.goal, IFNULL(hits.hits, 0) AS hits, goal < 0 as illegal, goal = 0 as dont_care FROM goal LEFT OUTER JOIN hits ON (goal.bucket_id = hits.bucket_id AND hits.log_id=%(log_id)s) WHERE goal.log_id=%(goal_id)s ORDER BY goal.bucket_id ASC;' % self.__dict__)
        for result in db.fetchall() :
          yield result
        while (1) : 
          message.warning('missing bucket')
          yield {}

  class cumulative(single) :
    def coverage(self) :
      with mdb.db.connection().row_cursor() as db :
        db.execute('SELECT goal.goal, IFNULL(cumulative.hits, 0) AS hits FROM goal LEFT OUTER NATURAL JOIN (SELECT bucket_id, SUM(hits.hits) AS hits, COUNT(hits.hits) as tests FROM hits JOIN (SELECT log_id FROM log WHERE root=%(log_id)s AND parent != NULL) AS runs ON (log_id) GROUP BY bucket_id) AS cumulative WHERE goal.log_id=%(goal_id)s ORDER BY goal.bucket_id ASC;' % self.__dict__)
        return db.fetchall()

  def result(self, log_id, goal_id=None, cumulative=False) :
    return (self.cumulative if cumulative else self.single)(log_id, goal_id)

################################################################################

class cvr :
  def result(self, log_id, goal_id=None) :
    with mdb.db.connection().row_cursor() as db :
      message.debug('retrieving %(log_id)s coverage information', log_id=log_id)
      db.execute('SELECT IFNULL((SELECT log_id FROM goal WHERE log_id = %(log_id)s LIMIT 1), 0) AS goal, IFNULL((SELECT log_id FROM hits WHERE log_id = %(log_id)s LIMIT 1), 0) AS coverage, (SELECT goal_id FROM master WHERE log_id = %(log_id)s LIMIT 1) AS master;' % locals())
      return db.fetchone()

################################################################################
