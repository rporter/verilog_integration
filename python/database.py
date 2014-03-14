# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import collections
from lxml import etree
import pwd
import random
import re
import sys
import time

import coverage
import mdb
import message
import utils

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

  order = 'log.log_id ASC, level DESC, msg_id ASC'

  def result(self, subquery) :
    return self.summary([self.log(log, msgs) for log, msgs in self.groupby(self.execute(subquery), lambda x : x.log_id, self.keyfact, self.grpfact)])

  def where(self, variant, limit, start, order='down', coverage=False) :
    'Note that asking for coverage here slows the query significantly'
    if variant == 'sngl' :
      result = self.subquery('l0.*, null AS children', frm='log AS l0 LEFT JOIN log AS l1 ON (l0.log_id = l1.root)', group=['l0.log_id'], where='l1.log_id IS NULL AND l0.root IS NULL')
    elif variant == 'rgr' :
      result = self.subquery('l0.*, COUNT(l1.log_id) AS children, SUM(l1.status = 1) AS passing', frm='log AS l0 LEFT JOIN log AS l1 ON (l0.log_id = l1.root)', group=['l0.log_id'], where='l1.log_id IS NOT NULL')
    else :
      result = self.subquery('l0.*, COUNT(l1.log_id) AS children, SUM(l1.status = 1) AS passing', frm='log AS l0 LEFT JOIN log AS l1 ON (l0.log_id = l1.root)', group=['l0.log_id'])
    result.limit = self.limit(limit)
    if start :
      result.where_and('l0.log_id %c %d' % ('>' if order == 'up' else '<', start))
    if coverage :
      result.select += ', goal.log_id AS goal, hits.log_id AS coverage, master.goal_id AS master'
      result.frm    += ' LEFT OUTER JOIN goal USING (log_id) LEFT OUTER JOIN hits USING (log_id) LEFT OUTER JOIN master USING (log_id)'
    result.update(order=order)
    return result

  def execute(self, subquery) :
    with mdb.connection().row_cursor() as db :
      message.debug('SELECT log.*, message.*, COUNT(*) AS count FROM (%s) AS log NATURAL LEFT JOIN message GROUP BY log.log_id, level ORDER BY %s;' % (str(subquery), self.order))
      db.execute('SELECT log.*, message.*, COUNT(*) AS count FROM (%s) AS log NATURAL LEFT JOIN message GROUP BY log.log_id, level ORDER BY %s;' % (str(subquery), self.order))
      return db.fetchall()

  testseed = re.compile(r'-(?P<seed>(0x)?[0-9a-fA-F]+)$')
  @staticmethod
  def keyfact(self) :
    'key factory for grouping'
    testname = self.currvalue.test
    seed = None
    if self.currvalue.test :
      seed = index.testseed.search(self.currvalue.test)
      if seed :
        testname = self.currvalue.test[:seed.start()]
        seed = seed.group('seed')
    return [mdb.accessor(testname=testname, seed=seed, user=pwd.getpwuid(self.currvalue.uid).pw_name, **self.currvalue), self._grouper(self.tgtkey)]
  @staticmethod
  def grpfact(self) :
    'group factory for grouping'
    return mdb.accessor(level=self.currvalue.level, severity=self.currvalue.severity, count=self.currvalue.count, msg=self.currvalue.msg, ident=self.currvalue.ident, subident=self.currvalue.subident, filename=self.currvalue.filename, line=self.currvalue.line)

################################################################################

class msgs :
  def result(self, log_id):
    with mdb.connection().row_cursor() as db :
      message.debug('retrieving %(log_id)s messages', log_id=log_id)
      db.execute('SELECT * FROM message WHERE log_id = %(log_id)s;' % locals())
      return db.fetchall()

################################################################################

class rgr(index) :
  order = 'parent ASC, log.log_id ASC, level DESC, msg_id ASC'
  
  def result(self, log_id, root=True):
    relationship = 'root' if root else 'parent'
    # call result method of parent class
    return index.result(self, self.subquery('l0.*, count(l1.log_id) as children', frm='log as l0 left join log as l1 on (l0.log_id = l1.%(relationship)s)', where='l0.log_id = %(log_id)s or l0.%(relationship)s = %(log_id)s', group=['l0.log_id'], limit=self.limit(), log_id=log_id, relationship=relationship))

################################################################################

class cvg : 
  class hierarchy :
    def __init__(self, goal_id, defaults, cumulative) :
      self.all_nodes = dict()
      with mdb.connection().row_cursor() as db :
        db.execute('SELECT * FROM point LEFT OUTER JOIN axis USING (point_id) LEFT OUTER JOIN enum USING (axis_id) WHERE log_id=%(goal_id)s ORDER BY point_id ASC, axis_id ASC, enum_id ASC;' % locals())
        points = db.fetchall()
      for parent, children in index.groupby(points, lambda row : row.point_id) :
        _parent = self.all_nodes.get(parent.parent, None)
        if parent.axis_id :
          self.all_nodes[parent.point_id] = coverage.coverpoint(name=parent.point_name, description=parent.desc, id=parent.point_id, parent=_parent, axes=self.get_axes(children), defaults=defaults, cumulative=cumulative)
        else :
          self.all_nodes[parent.point_id] = coverage.hierarchy(parent.point_name, parent.desc, id=parent.point_id, root=parent.root == None, parent=_parent)

    def get_axes(self, nodes) :
      return collections.OrderedDict([(axis.axis_name, coverage.axis(axis.axis_name, **dict([(e.enum, e.enum_id) for e in enum]))) for axis, enum in index.groupby(nodes, lambda node : node.axis_id)])
    def get_root(self) :
      return self.all_nodes.values()[0].root
  class single :
    cumulative=False
    query='SELECT goal.bucket_id, goal.goal, IFNULL(hits.hits, 0) AS hits, goal < 0 as illegal, goal = 0 as dont_care FROM goal LEFT JOIN hits ON (goal.bucket_id = hits.bucket_id AND hits.log_id=%(log_id)s) WHERE goal.log_id=%(goal_id)s ORDER BY goal.bucket_id ASC;'
    def __init__(self, log_id, goal_id=None) :
      self.log_id = log_id
      self.goal_id = goal_id or log_id
    def points(self) :
      return cvg.hierarchy(self.goal_id, self.coverage(), self.cumulative).get_root()
    def coverage(self) :
      with mdb.connection().row_cursor() as db :
        message.debug(self.query % self.__dict__)
        db.execute(self.query % self.__dict__)
        for result in db.fetchall() :
          yield result
        while (1) : 
          message.warning('missing bucket')
          yield {}

  class cumulative(single) :
    cumulative=True
    query='SELECT goal.goal, IFNULL(cumulative.hits, 0) AS hits FROM goal LEFT OUTER JOIN (SELECT bucket_id, SUM(hits.hits) AS hits, COUNT(hits.hits) as tests FROM hits JOIN (SELECT log_id FROM log WHERE root=%(log_id)s AND parent is not NULL) AS runs USING (log_id) GROUP BY bucket_id) AS cumulative USING (bucket_id) WHERE goal.log_id=%(goal_id)s ORDER BY goal.bucket_id ASC;'

  def result(self, log_id, goal_id=None, cumulative=False) :
    return (self.cumulative if cumulative else self.single)(log_id, goal_id)

################################################################################

class bkt :
  def result(self, log_id, buckets) :
    with mdb.connection().row_cursor() as db :
      message.debug('retrieving %(log_id)s bucket coverage', log_id=log_id)
      db.execute('SELECT hits.log_id, log.test, log.description, SUM(hits.hits) AS hits FROM hits NATURAL JOIN log WHERE log.root = %(log_id)s AND bucket_id IN (%(buckets)s) GROUP BY hits.log_id ORDER BY hits DESC;' % locals())
      return db.fetchall()

################################################################################

class cvr :
  def result(self, log_id) :
    with mdb.connection().row_cursor() as db :
      message.debug('retrieving %(log_id)s coverage information', log_id=log_id)
      db.execute('SELECT %(log_id)s as log_id, (SELECT log_id FROM goal WHERE log_id = %(log_id)s LIMIT 1) AS goal, (SELECT log_id FROM hits WHERE log_id = %(log_id)s LIMIT 1) AS coverage, (SELECT goal_id FROM master WHERE log_id = %(log_id)s LIMIT 1) AS master, (SELECT goal.log_id FROM goal JOIN log ON (log.root = goal.log_id) WHERE log.log_id = %(log_id)s LIMIT 1) AS root;' % locals())
      return db.fetchone()

################################################################################

class hm :
  'heat map - classify bucket hits by testname'
  class compress :
    def __init__(self) :
      self.values = dict()
    def __call__(self, grp) :
      row = grp.currvalue
      if row.testname in self.values :
        self.values[row.testname].hits += row.hits
      else :
        self.values[row.testname] = mdb.accessor(idx=len(self.values), hits=row.hits)
      row.testname = self.values[row.testname].idx
      return row
    def tests(self) :
      return [test + dict(testname=testname) for testname, test in self.values.iteritems()]

  def result(self, log_id, offset, size) :
    '''
      log_id : regression id
      offset : first bucket index
      size   : number of buckets
    '''
    with mdb.connection().row_cursor() as db :
      message.debug('calculating %(log_id)s coverage heat map [%(offset)s+:%(size)s]', log_id=log_id, offset=offset, size=size)
      db.execute('SELECT bucket_id, SUM(hits) AS hits, count(hits) AS tests, '+db.split('test')+' AS testname FROM hits JOIN log USING (log_id) WHERE log.root = %s AND hits.bucket_id >= %s AND hits.bucket_id < %s GROUP BY bucket_id, testname ORDER BY bucket_id ASC, hits DESC;', (log_id, offset, offset+size))
      testnames = self.compress()
      data = list(index.groupby(db, lambda row : row.bucket_id, keyfact=lambda s : list(s._grouper(s.tgtkey)), grpfact=testnames))
      return dict(testnames=testnames.tests(), data=data)

################################################################################

class upload :
  REFERENCE=True
  RESULT=False
  """
  Base Class for all coverage upload types
  """
  def __del__(self) :
    pass

  def __enter__(self) :
    return self

  def __exit__(self, type, value, traceback) :
    self.close()

  @classmethod
  def write(cls, root, log_id, reference=False) :
    agent = cls.__name__
    if reference:
      root.debug()
      elapsed = time.time()
      coverage.messages.CVG_110(agent=agent, reference=reference)
      root.sql(cls.sql(log_id=log_id))
      elapsed = time.time()-elapsed
      coverage.messages.CVG_111(agent=agent, time=elapsed, reference=reference)
    coverage.messages.CVG_100(agent=agent, reference=reference)
    elapsed = time.time()
    target  = (log_id, )
    with cls(reference) as out :
      def dump(bucket) :
        out.insert(target + bucket)
      root.dump(dump, reference)
    elapsed = time.time()-elapsed
    coverage.messages.CVG_101(agent=agent, time=elapsed, reference=reference)

################################################################################

class insert(upload) :
  """
  Use sqlite INSERT
  """

  class sql :
    def __init__(self, parent=None, log_id=None) :
      self.parent = parent
      self.log_id = log_id
    def __del__(self) :
      if self.is_root :
        self.cursor.close()
    def last_id(self) :
      return self.cursor.last_id()

    def axis(self, axis) :
      self.cursor.execute('INSERT INTO axis (point_id, axis_name) VALUES (%s,%s)', (self.parent_id, axis.name))
      self.sql_row_id = self.last_id()
      for enum, value in axis.values.iteritems() :
        self.cursor.execute('INSERT INTO enum (axis_id, enum, value) VALUES (%s,%s,%s)', (self.sql_row_id, enum, value))
    def coverpoint(self, coverpoint) :
      self.cursor.execute('INSERT INTO point (log_id, point_name, description, root, parent, offset, size, md5_self, md5_axes, md5_goal) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (self.root.log_id, coverpoint.name, coverpoint.description, self.root_id, self.parent_id, coverpoint.offset, len(coverpoint)) + coverpoint.md5)
      self.sql_row_id = self.last_id()
      for name, axis in coverpoint.axes() :
        axis.sql(insert.sql(self))
    def hierarchy(self, hierarchy) :
      self.cursor.execute('INSERT INTO point (log_id, point_name, description, root, parent, md5_self, md5_axes) VALUES (%s,%s,%s,%s,%s,%s,%s)', (self.root.log_id, hierarchy.name, hierarchy.description, self.root_id, self.parent_id) + hierarchy.md5)
      self.sql_row_id = self.last_id()
      for child in hierarchy.children :
        child.sql(insert.sql(self))

    @utils.lazyProperty
    def root(self) :
      return self.parent.root if self.parent else self
    @utils.lazyProperty
    def root_id(self) :
      return self.parent and self.root.sql_row_id
    @utils.lazyProperty
    def is_root(self) :
      return self.root == self
    @utils.lazyProperty
    def parent_id(self) :
      return self.parent and self.parent.sql_row_id

    @utils.lazyProperty
    def cursor(self) :
      return mdb.mdb.cursor() if self.is_root else self.root.cursor

  def __init__(self, reference=False) :
    self.reference = reference
    self.data      = list()
    message.debug("sqlite insert created")

  def close(self) :
    table = 'goal' if self.reference else 'hits'
    if len(self.data) == 0 :
      message.note('No data to upload into table "%(table)s", skipping', table=table)
      return
    message.information('starting data upload to table "%(table)s" via insert', table=table)
    with mdb.mdb.cursor() as cursor :
      cursor.executemany('INSERT INTO '+table+' VALUES (%s,%s,%s);', self.data)
      rows = cursor.rowcount
    if rows is None :
      message.warning('upload to db via insert "%(table)s" returned None', table=table)
    else :
      message.information('upload to db via insert added %(rows)d rows to "%(table)s"', rows=int(rows), table=table)

  def insert(self, data) :
    'add data to insert values'
    self.data.append(data)

  @classmethod
  def set_master(cls, log_id, master_id) :
    with mdb.mdb.cursor() as cursor :
      cursor.execute('INSERT INTO master (log_id, goal_id) VALUES (%s, %s);', (log_id, master_id))
    coverage.messages.CVG_50(**locals())

################################################################################

class optimize :
  INVS='invs'
  COVG='covg'
  SEQ=0
  def __init__(self, log_ids=[], test_ids=[], xml=None, threshold=0, robust=False, previous=None) :
    'log_ids is a list of regression roots'
    self.log_ids = log_ids
    s_log_ids = ','.join(map(str, log_ids))
    self.tests = mdb.connection().row_cursor()
    if log_ids :
      # create table of individual runs, but not root node as this may have already summarised coverage
      self.tests.execute('CREATE TEMPORARY TABLE '+self.invs+' AS SELECT l1.*, goal_id AS master FROM log AS l0 JOIN log AS l1 ON (l0.log_id = l1.root) LEFT OUTER JOIN master ON (l1.log_id = master.log_id) WHERE l1.root IN ('+s_log_ids+');')
      self.tests.execute('SELECT count(*) AS children FROM '+self.invs)
      children = self.tests.fetchone().children
      if children :
        message.information('%(log_ids)s %(has)s %(children)d children', log_ids=s_log_ids, children=children, has='have' if len(log_ids) > 1 else 'has')
    # append individual runs as given by test_ids
    if xml :
      xml_ids = xml.xml.xpath('/optimize/test/log_id/text()')
    else :
      xml_ids=[]
    if test_ids or xml_ids :
      s_test_ids = ','.join(map(str, test_ids+xml_ids))
      create = ('INSERT INTO '+self.invs) if log_ids else ('CREATE TEMPORARY TABLE '+self.invs+' AS')
      self.tests.execute(create+' SELECT log.*, goal_id AS master FROM log LEFT OUTER JOIN master ON (log.log_id = master.log_id) WHERE log.log_id IN ('+s_test_ids+');')
    self.tests.execute('SELECT count(*) AS tests FROM '+self.invs)
    tests = self.tests.fetchone().tests
    if tests < 1 :
      message.fatal('no tests')
    message.information('starting with %(count)d tests in table %(table)s', count=tests, table=self.invs)
    # check congruency
    self.cvg = mdb.connection().row_cursor()
    self.cvg.execute("SELECT md5_self AS md5, 'md5_self' AS type, invs.master, invs.root FROM point JOIN "+self.invs+" AS invs ON (invs.master = point.log_id AND point.parent IS NULL) GROUP BY md5;")
    md5 = self.cvg.fetchall()
    if not md5 :
      message.fatal('no master')
    elif len(md5) > 1 :
      message.fatal('md5 of multiple masters do not match')
    else :
      message.debug('md5 query returns %(rows)d', rows=self.cvg.rowcount)
    self.master = mdb.accessor(md5=md5[0])
    self.cvg.execute("SELECT DISTINCT(md5_axes) AS md5, 'md5_axes' AS type, invs.master, invs.root FROM point JOIN "+self.invs+" AS invs ON (invs.master = point.log_id AND point.parent IS NULL) GROUP BY md5;")
    md5 = self.cvg.fetchall()
    if len(md5) > 1 :
      message.fatal('md5 of multiple axis masters do not match')
    self.master.axes = md5[0]
    # create status table, collating goal & hits
    self.cvg.execute('CREATE TEMPORARY TABLE '+self.covg+' (bucket_id INTEGER NOT NULL PRIMARY KEY, goal INTEGER, hits INTEGER, total_hits INTEGER, rhits INTEGER, max_hits INTEGER, tests INTEGER);')
    try :
      self.threshold = float(threshold)
    except :
      self.threshold = 0.0
      message.warning('cannot convert threshold value given "%(arg)s" to float because %(exception)s, using %(threshold)2.1f', arg=threshold, exception=sys.exc_info()[0], threshold=self.threshold)
    self.robust = robust
    self.previous = previous

  def __del__(self) :
    self.tests.execute('DROP TABLE IF EXISTS '+self.invs)
    self.tests.close()
    self.cvg.execute('DROP TABLE IF EXISTS '+self.covg)
    self.cvg.close()

  def __iter__(self) :
    self.reset()
    current = self.status()
    for log in self.testlist() :
      updates = self.increment(log.log_id)
      status  = self.status()
      yield mdb.accessor(log=log, last=current, updates=updates, status=status, hits=status.metric().hits-current.metric().hits)
      current = status

  @utils.lazyProperty
  def seq(self) :
    optimize.SEQ += 1
    return str(optimize.SEQ)
  @utils.lazyProperty
  def invs(self) :
    return self.INVS + self.seq
  @utils.lazyProperty
  def covg(self) :
    return self.COVG + self.seq

  def increment(self, log_id) :
    if self.cvg.HAS_UPDATE :
      # in e.g. mysql we can use a join in an update
      # WHERE hits.log_id = %s
      self.cvg.execute('UPDATE '+self.covg+''' AS status JOIN hits ON (status.bucket_id = hits.bucket_id AND hits.log_id = %s)
SET
  status.hits  = CASE status.goal WHEN -1 THEN 0 WHEN 0 THEN 0 ELSE MIN(status.goal, status.hits + hits.hits) END,
  status.rhits = CASE status.goal WHEN -1 THEN 0 WHEN 0 THEN 0 ELSE MIN(status.goal + status.max_hits, status.rhits + MIN(hits.hits, status.goal)) END,
  status.total_hits = status.total_hits + hits.hits,
  status.max_hits = MIN(status.goal, MAX(max_hits, hits.hits)),
  status.tests = status.tests + 1;''', log_id)
    else :
      # but we need to resort to this for e.g. sqlite
      self.cvg.execute('REPLACE INTO '+self.covg+'''
SELECT
  status.bucket_id,
  status.goal,
  CASE status.goal WHEN -1 THEN 0 WHEN 0 THEN 0 ELSE MIN(status.goal, status.hits + hits.hits) END AS hits,
  CASE status.goal WHEN -1 THEN 0 WHEN 0 THEN 0 ELSE MIN(status.goal + status.max_hits, status.rhits + MIN(hits.hits, status.goal)) END AS rhits,
  status.total_hits + hits.hits as total_hits,
  MIN(status.goal, MAX(max_hits, hits.hits)) as max_hits, status.tests + 1 FROM '''+self.covg+' AS status JOIN hits USING (bucket_id) WHERE hits.log_id = %s;', (log_id,))
    message.debug('update %(cnt)d rows', cnt=self.cvg.rowcount)
    return self.cvg.rowcount

  def reset(self) :
    if self.previous and self.robust :
      # incorporate previous max_hits into coverage accumulator used by robust generator
      self.cvg.execute('REPLACE INTO '+self.covg+' SELECT goal.bucket_id, goal.goal, 0 AS hits, 0 AS total_hits, 0 AS rhits, previous.max_hits AS max_hits, 0 AS tests FROM goal JOIN ' + self.previous.covg + ' AS previous USING (bucket_id) WHERE goal.log_id=%s;', (self.get_master(), ))
      self.cvg.execute('SELECT SUM(goal) as goal, SUM(goal+max_hits) as robust from '+self.covg+';')
      message.note('Incorporating previous max_hits into coverage accumulator. goal %(goal)d is now %(robust)d', **self.cvg.fetchone())
    else :
      self.cvg.execute('REPLACE INTO '+self.covg+' SELECT bucket_id, goal, 0 AS hits, 0 AS total_hits, 0 AS rhits, 0 AS max_hits, 0 AS tests FROM goal WHERE log_id=%s;', (self.get_master(), ))

  def status(self) :
    'calculate & return current coverage'
    with mdb.connection().cursor() as db :
      db.execute('SELECT SUM(MIN(goal, hits)) AS hits, SUM(goal) AS goal, SUM(MIN(goal+max_hits, rhits)) AS rhits, SUM(goal+max_hits) AS rgoal FROM '+self.covg+' WHERE goal > 0;')
      hits, goal, rhits, rgoal = db.fetchone()
      covrge=coverage.coverage(hits=hits, goal=goal)
      robust=coverage.coverage(hits=rhits, goal=rgoal)
      def metric() :
        'be clear instead of using lambda'
        return robust if self.robust else covrge
      return mdb.accessor(coverage=covrge, robust=robust, metric=metric)

  def get_master(self) :
    return int(self.master.md5.master or self.master.md5.root)

  def hierarchy(self) :
    return cvg.hierarchy(self.get_master(), self.dump(), False).get_root()

  def dump(self) :
    with mdb.connection().row_cursor() as db :
      db.execute('SELECT * FROM ' + self.covg)
      buckets = db.fetchall()
    def values() :
      for bucket in buckets : yield bucket
    return values()

  def insert(self, log_id) :
    insert.set_master(log_id, self.get_master())
    coverage.messages.CVG_120()
    self.cvg.execute('REPLACE INTO hits SELECT %(log_id)s AS log_id, bucket_id, hits FROM %(status)s AS status;' % {'log_id' : log_id, 'status' : self.covg})
    self.cvg.commit()

  class xmlDump :
    def __init__(self) :
      self.root = etree.Element('optimize')
      self.xml  = etree.ElementTree(self.root)
    def add(self, test) :
      node = etree.SubElement(self.root, 'test')
      for attr, value in test.log.iteritems() :
        etree.SubElement(node, attr).text = str(value)
    def append(self, node) :
      self.root.append(node)
    def write(self, file) :
      self.xml.write(file, pretty_print=True)

  def run(self) :
    xml = self.xmlDump()
    cnt = 0
    for incr in self :
      if cnt % 20 == 0 :
        message.information(' log_id :   rows :   hits : coverage')
      cnt+=1
      message.information(' %(log_id)6d : %(rows)6d : %(hits)6d : %(cvg)s', log_id=incr.log.log_id, rows=incr.updates, hits=incr.hits, cvg=incr.status.coverage.description())
      if incr.hits :
        # this test contributed to overall coverage
        xml.add(incr)
      if incr.status.metric().is_hit() :
        message.note('all coverage hit')
        break
    message.information('coverage : ' + self.status().coverage.description())
    if self.robust :
      message.information('robust : ' + self.status().robust.description())
    message.information('tests : %(count)d', count=int(xml.xml.xpath('count(/optimize/test/log_id)')))

    # now regenerate hierarchy and report coverage on point basis
    xml.append(self.hierarchy().xml())

    return xml

################################################################################

class cvgOrderedOptimize(optimize) :
  'order tests in coverage order'
  def testlist(self) :
    self.tests.execute('SELECT invs.*, IFNULL(SUM(MIN(status.goal, hits.hits)), 0) AS hits FROM '+self.invs+' AS invs LEFT OUTER JOIN hits USING (log_id) JOIN '+self.covg+' AS status ON (hits.bucket_id = status.bucket_id AND status.goal > 0) GROUP BY log_id ORDER BY hits DESC;')
    return self.tests.fetchall()

################################################################################

class posOrderedOptimize(optimize) :
  'order tests in log order'
  ORDER='ASC'
  def testlist(self) :
    self.tests.execute('SELECT * FROM '+self.invs+' ORDER BY log_id '+self.ORDER+';')
    return self.tests.fetchall()

################################################################################

class revOrderedOptimize(posOrderedOptimize) :
  'order tests in reverse log order'
  ORDER='DESC'

################################################################################

class randOrderedOptimize(optimize) :
  'order tests in random order'
  def testlist(self) :
    self.tests.execute('SELECT * FROM '+self.invs+';')
    result = self.tests.fetchall()
    random.shuffle(result)
    return result

################################################################################

class incrOrderedOptimize(cvgOrderedOptimize) :
  'order tests in incremental coverage order'
  def __iter__(self) :
    self.reset()
    switched = False
    current = self.status()
    testlist = self.testlist()
    while testlist :
      log = testlist.pop(0)
      updates = self.increment(log.log_id)
      status  = self.status()
      yield mdb.accessor(log=log, last=current, updates=updates, status=status, hits=status.metric().hits-current.metric().hits)
      current = status
      # calculate incremental coverage of remaining tests
      with mdb.connection().row_cursor() as db :
        db.execute('DELETE FROM '+self.invs+' WHERE log_id = %s;', (log.log_id,))
        if status.metric().coverage() > self.threshold :
          if not switched :
            switched = True
            message.note('Switching to incremental selection at %(threshold)0.2f', threshold=self.threshold)
          # switch to incremental as coverage closes
          minexpr = '(status.goal+status.max_hits)-status.rhits' if self.robust else 'status.goal-status.hits'
          if self.robust :
            db.execute('SELECT invs.*, IFNULL(SUM(MIN((status.goal+status.max_hits)-status.rhits, hits.hits)), 0) AS hits FROM '+self.invs+' AS invs LEFT OUTER JOIN hits USING (log_id) JOIN '+self.covg+' AS status ON (hits.bucket_id = status.bucket_id AND status.goal > 0 AND status.hits < (status.goal+status.max_hits)) GROUP BY log_id ORDER BY hits DESC;')
          else :
            db.execute('SELECT invs.*, IFNULL(SUM(MIN(status.goal-status.hits, hits.hits)), 0) AS hits FROM '+self.invs+' AS invs LEFT OUTER JOIN hits USING (log_id) JOIN '+self.covg+' AS status ON (hits.bucket_id = status.bucket_id AND status.goal > 0 AND status.hits < status.goal) GROUP BY log_id ORDER BY hits DESC;')
          testlist = db.fetchall()

################################################################################

optimize.options = {
  'cvg'  : cvgOrderedOptimize,
  'pos'  : posOrderedOptimize,
  'rev'  : revOrderedOptimize,
  'rand' : randOrderedOptimize,
  'incr' : incrOrderedOptimize
}

################################################################################
