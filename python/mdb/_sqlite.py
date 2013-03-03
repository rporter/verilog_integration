# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import accessor
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
      self.instance.execute('PRAGMA journal_mode=WAL;')

  def cursor(self, *args) :
    return self._cursor(self.instance, *args)

  def row_cursor(self) :
    return self.cursor(accessor.accessor_factory)

  @classmethod
  def set_default_db(cls, **args) :
    cls.default_db = args['db']

class mixin(object) :
  def init(self) :
    self.db = connection().cursor()

  def commit(self) :
    self.db.commit()

  def insert(self, cb_id, when, level, severity, filename, line, msg) :
    try :
      self.db.execute('INSERT INTO message (log_id, level, severity, date, filename, line, msg) VALUES (?, ?, ?, ?, ?, ?, ?);', (self.log_id, level, severity, when.tv_sec, filename, line, msg))
    except :
      print sys.exc_info()

  def log(self, parent, description) :
    'create entry in log table'
    self.db.execute('INSERT INTO log (parent, description) VALUES (?, ?);', (parent, description))
    self.commit()
    return self.db.lastrowid
