# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import sys
import sqlite3
import message

class connection(object) :

  class _cursor(object) :
    def __init__(self, connection, *args) :
      self.connection = connection
      self.db         = self.connection.cursor(*args)

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
    return self.cursor(sqlite3.Row)

  @classmethod
  def set_default_db(cls, **args) :
    cls.default_db = args['db']

class mixin(object) :

  def __init__(self) :
    self.db = connection().cursor()
    try :
      self.db.execute('''
CREATE TABLE mdb (
  level    INTEGER,
  severity TEXT,
  date     DATETIME,
  filename TEXT,
  line     INTEGER,
  msg      TEXT
);
''')
    except :
      print sys.exc_info()
    # install callback
    message.emit_cbs.add('sqlite', 1,  self.insert)

  def insert(self, cb_id, when, level, severity, filename, line, msg) :
    try :
      self.db.execute('INSERT INTO mdb VALUES(?, ?, ?, ?, ?, ?);', (level, severity, when.tv_sec, filename, line, msg))
    except :
      print sys.exc_info()
    else :
      self.db.commit()
