# Copyright (c) 2013 Rich Porter - see LICENSE for further details

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
      self.keyfunc, self.keyfact, self.grpfact = keyfunc, keyfact, grpfact
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

  class summary(list) :
    def __init__(self, results) :
      list.__init__(self, results)
    def summary(self, include=False) :
      tests = self if include else self[1:]
      result = mdb.accessor(passes=0, fails=0, total=len(tests))
      for r in tests :
        if r.status.status == 'PASS' :
          result.passes += 1
        else :
          result.fails += 1
      return result

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  order = 'log_id, msg_id, level ASC'

  def result(self, where, limit) :
    return self.summary([self.log(log, msgs) for log, msgs in self.groupby(self.execute(where, limit), lambda x : x.log_id, self.keyfact, self.grpfact)])

  def where(self, variant) :
    if variant == 'sngl' :
      return 'SELECT l0.*, null as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) where l1.log_id is null and l0.root is null'
    elif variant == 'rgr' :
      return 'SELECT l0.*, count(l1.log_id) as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) group by l0.log_id having l1.log_id is not null'
    else :
      return 'SELECT l0.*, count(l1.log_id) as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) group by l0.log_id'

  def execute(self, where, limit) :
    with mdb.db.connection().row_cursor() as db :
      db.execute('SELECT log.*, message.*, COUNT(*) AS count FROM (%s ORDER BY log_id DESC %s) AS log NATURAL LEFT JOIN message GROUP BY log_id, level ORDER BY %s;' % (where, str(limit), self.order))
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
    return index.result(self, 'SELECT l0.*, count(l1.log_id) as children FROM log as l0 left join log as l1 on (l0.log_id = l1.%(relationship)s) WHERE l0.log_id = %(log_id)s or l0.%(relationship)s = %(log_id)s group by l0.log_id' % locals(), self.limit())

################################################################################
