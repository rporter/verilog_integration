# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import os
import Queue
import socket
import threading
import utils
from accessor import *

class activityBlockVersion :
  def __init__(self, **kwargs) :
    self.activity = kwargs.get('activity', None)
    self.block    = kwargs.get('block', None)
    self.version  = kwargs.get('version', self.get_version())

  def get_version(self) :
    import subprocess
    try :
      return subprocess.check_output(['git', 'log', '-1', '--format=%h']).strip()
    except :
      return 'Not available'

class mdbDefault(dict) :
  'Pull some attributes from the enviroment'
  __env = None
  def __init__(self) :
    if self.__env is None :
      MDB=os.environ.get('MDB', [])
      if MDB :
        self.__env = map(lambda x : x.split('='), MDB.split(','))
        self.update(self.__env)
      else :
        self.__env = []
  def __getattr__(self, attr) :
    return self.get(attr, None)

################################################################################

class _cursor(object) :
  ident=0
  debug=False
  HAS_UPDATE=False
  def __init__(self, connection, factory) :
    self.connection = connection
    self.dump = open(self.filename(), 'w') if self.debug else None
    if self.dump :
      import inspect, pprint
      pprint.pprint(inspect.stack(), stream=self.dump)

  def execute(self, *args) :
    if self.dump :
      self.dump.write('%08x : ' % id(self.db) + ' << '.join(map(str, args)) + '\n')
    return self._execute(*args)

  def executemany(self, *args) :
    if self.dump :
      self.dump.write('%08x : ' % id(self.db) + ' << '.join(map(str, args)) + '\n')
    return self._executemany(*args)

  def commit(self) :
    self.connection.commit()

  def last_id(self) :
    self.execute(self.LAST_SQL)
    row = self.fetchone()
    try :
      return row['rowid']
    except :
      return row[0]

  def reconnect(self) :
    self.connection = connection(reconnect=True)

  def info(self) :
    return None
  def warning_count(self) :
    return 0

  def __getattr__(self, attr) :
    return getattr(self.db, attr)

  def __iter__(self) :
    try :
      return iter(self.db)
    except :
      return self

  def __enter__(self) :
    return self

  def __exit__(self, type, value, traceback):
    try :
      self.db.__exit__(type, value, traceback)
    except :
      self.commit()
      self.db.close()

  def __del__(self) :
    if self.dump :
      self.dump.close()

  @classmethod
  def filename(cls) :
    name, cls.ident = 'sql_%d' % cls.ident, cls.ident + 1
    return name

class _connection(object) :
  _instance = dict()

  def __init__(self, *args, **kwargs) :
    'pools connections on per process/thread basis'
    if kwargs.get('reconnect', False) :
      try :
        self.instance[self.id()].close()
      except :
        pass
      del self.instance[self.id()]
    if self.id() not in self.instance :
      self.connect(*args, **kwargs)

  def cursor(self, *args) :
    return cursor(self.instance[self.id()], *args)

  def id(self) :
    'connection id; pid & thread'
    return str(os.getpid())+'.'+str(threading.current_thread().name)

  @property
  def instance(self) :
    return _connection._instance

try :
  raise ImportError
  import _mysql as db
except ImportError :
  import _sqlite as db

class cursor(db.cursor, _cursor) :
  impl = db
  def __init__(self, connection, factory=None) :
    db.cursor.__init__(self, connection, factory)
    _cursor.__init__(self, connection, factory)

class connection(_connection, db.connection) :
  impl = db

class json :
  dump = db.json.dump
  dumps = db.json.dumps

################################################################################

class mdb(object) :
  instance = None
  instances = []
  atexit = False
  class queue :
    queue_limit = 10
    @classmethod
    def do_flush(cls, level) :
      return level >= cls.queue_limit
    class proxy :
      'proxy for cursor in flush method. do not open cursor unless something to insert'
      def __init__(self, parent, test) :
        self.parent = parent
        self.test = test
        self.used = False
      def __enter__(self) :
        return self
      def __exit__(self, type, value, traceback) :
        if self.test(type) :
          # not what we were looking for
          return False
        if self.used :
          self.cursor.__exit__(type, value, traceback)
        return True # suppress the Queue.Empty exception
      @utils.lazyProperty
      def cursor(self) :
        self.used = True
        return self.parent.cursor()
      def insert(self, cb_id, when, level, severity, ident, subident, filename, line, msg) :
        self.cursor.execute('INSERT INTO message (log_id, level, severity, date, ident, subident, filename, line, msg) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);', (self.parent.log_id, level, severity, when.tv_sec, ident, subident, filename, line, msg))
    class unthreaded(object) :
      def __init__(self, abv, root, parent, description, test) :
        self.queue = Queue.Queue()
        # create log entry for this run
        self.log_id = self.log(os.getuid(), socket.gethostname(), abv, root, parent, description, test)
        # install callback
        message.terminate_cbs.add('mdb terminate', 20, self.finalize, self.finalize)
      def put(self, *args, **kwargs) :
        self.queue.put(args)
        # flush to db if this message has high severity or there are a number of outstanding messages
        if kwargs.get('commit', False) or mdb.queue.do_flush(self.queue.qsize()) :
          self.flush()
      def flush(self) :
        with mdb.queue.proxy(self, lambda value : value != Queue.Empty) as insert :
          while (1) :
            insert.insert(*self.queue.get(False))
      def finalize(self, *args) :
        'set test status & clean up'
        self.flush()
        self.status()
      def log(self, uid, hostname, abv, root, parent, description, test) :
        'create entry in log table'
        with self.cursor() as db :
          db.execute('INSERT INTO log (uid, root, parent, activity, block, version, description, test, hostname) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);', (uid, root, parent, abv.activity, abv.block, abv.version, description, test, hostname))
          return db.lastrowid
      def status(self) :
        'update status at end'
        with self.cursor() as cursor :
          cursor.execute('UPDATE log SET status = %s WHERE log_id = %s;', (int(message.message.status().flag), self.log_id))
      @classmethod
      def cursor(cls) :
        return connection().cursor()
    class threaded(unthreaded) :
      class repeatingTimer(threading._Timer) :
        def run(self):
          message.debug('Timer thread is ' + threading.current_thread().name)
          while not self.finished.is_set():
            self.finished.wait(self.interval)
            self.function(*self.args, **self.kwargs)
          message.debug('is finished ' + threading.current_thread().name)
        def running(self) :
          return not self.finished.is_set()
      def __init__(self, *args, **kwargs) :
        # create semaphore
        self.semaphore = threading.Semaphore()
        # flush queue every half second
        self.timer = self.repeatingTimer(0.5, self.flush)
        self.timer.start()
        mdb.queue.unthreaded.__init__(self, *args, **kwargs)
      def flush(self) :
        if not self.semaphore.acquire(False) :
          # if we can't get the semaphore somebody is already doing this
          # But there is a race when the other thread is just finishing
          return
        super(mdb.queue.threaded, self).flush()
        self.semaphore.release()
      def finalize(self, *args) :
        'set test status & clean up'
        if self.timer.running() :
          message.debug('... bye')
          self.timer.cancel()
        super(mdb.queue.threaded, self).finalize(*args)

  def __init__(self, description='none given', test=None, root=None, parent=None, level=message.ERROR, queue='threaded', **kwargs) :
    self.commit_level = level
    self.abv = activityBlockVersion(**kwargs)
    # init default filter
    self.filter_fn = self.filter
    self.root = root or mdbDefault().root
    self.parent = parent or mdbDefault().parent
    # add to list of instances
    mdb.instances.append(self)
    # psuedo singleton
    if mdb.instance is None :
      try :
        _queue = getattr(self.queue, queue)
      except AttributeError :
        message.fatal('No mdb queue type %(queue)s', queue=queue)
      message.information('Using queue %(queue)s', queue=queue)
      mdb.instance = _queue(self.abv, self.root, self.parent, description, test)
    # install callback
    message.emit_cbs.add('mdb emit', 1, self.add, None)
    message.debug('hello ...')

  def filter(self, cb_id, level, filename) :
    'do not store messages less important that INFORMATION by default'
    return level < message.INFORMATION

  def add(self, cb_id, when, level, severity, tag, filename, line, msg) :
    # option to ignore certain messages
    if self.filter_fn(cb_id, level, filename) :
      return
    # add to queue, take copy of filename and msg
    mdb.instance.put(cb_id, accessor(tv_sec=when.tv_sec, tv_nsec=when.tv_nsec), level, severity, tag and tag.ident, tag and tag.subident, str(filename), line, str(msg), commit=level >= self.commit_level)

  def get_root(self) :
    return self.root or mdb.instance.log_id
  def is_root(self) :
    return self.root is None

  @property
  def log_id(self) :
    return mdb.instance.log_id
  @classmethod
  def cursor(cls, *args, **kwargs) :
    return cls.instance.cursor(*args, **kwargs)

  @classmethod
  def finalize(cls) :
    message.debug('Finalize')
    if cls.instance :
      cls.instance.finalize()

# short cut
finalize_all = mdb.finalize
