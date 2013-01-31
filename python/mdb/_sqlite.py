# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import accessor
import atexit
import sys
import sqlite3
import message

class connection(object) :

  class _cursor(object) :
    def __init__(self, connection, factory=None) :
      self.connection             = connection
      self.connection.row_factory = factory
      self.db                     = self.connection.cursor()

    def commit(self) :
      self.connection.commit()

    def __getattr__(self, attr) :
      return getattr(self.db, attr)

  instance = None
  default_db = 'default.db'
  def __init__(self, *args, **kwargs) :
    if self.instance is None :
      try :
        self.db = kwargs['db']
      except KeyError:
        self.db = self.default_db
      self.instance = sqlite3.connect(self.db)

  def cursor(self, *args) :
    return self._cursor(self.instance, *args)

  def row_cursor(self) :
    return self.cursor(accessor.accessor_factory)

  @classmethod
  def set_default_db(cls, **args) :
    cls.default_db = args['db']

class mixin(object) :
  queue_limit = 10
  def __init__(self, description='none given', parent=None, level=message.ERROR) :
    self.commit_level = level
    self.db = connection().cursor()
    self.queue = 0
    # create log entry for this run
    self.log_id = self.log(parent, description)
    # install callbacks
    message.emit_cbs.add('sqlite', 1,  self.insert)
    atexit.register(self.commit)
    # init filter
    self.filter_fn = self.filter

  def commit(self) :
    self.queue = 0
    self.db.commit()

  def filter(self, cb_id, level, filename) :
    return False

  def insert(self, cb_id, when, level, severity, filename, line, msg) :
    # option to ignore certain messages
    if self.filter_fn(cb_id, level, filename) :
      return
    try :
      self.db.execute('INSERT INTO message (log_id, level, severity, date, filename, line, msg) VALUES (?, ?, ?, ?, ?, ?, ?);', (self.log_id, level, severity, when.tv_sec, filename, line, msg))
      self.queue += self.db.rowcount
    except :
      print sys.exc_info()
    else :
      # only commit at certain severity to save time
      if level >= self.commit_level or self.queue > self.queue_limit :
        self.commit()

  def log(self, parent, description) :
    'create entry in log table'
    self.db.execute('INSERT INTO log (parent, description) VALUES (?, ?);', (parent, description))
    self.commit()
    return self.db.lastrowid
