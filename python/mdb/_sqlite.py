# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import accessor
import message
import os.path
import Queue
import sqlite3
import sys
import threading

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

    def __iter__(self) :
      return self.db

    def __enter__(self) :
      return self.db

    def __exit__(self, type, value, traceback): 
      if traceback : print traceback
      self.connection.commit()
      self.db.close()      

  instance = dict()
  default_db = 'default.db'
  def __init__(self, *args, **kwargs) :
    'pools connections on per thread basis'
    if threading.current_thread() not in self.instance :
      try :
        self.db = kwargs['db']
      except KeyError:
        self.db = self.default_db
      instance = sqlite3.connect(self.db)
      instance.execute('PRAGMA journal_mode=WAL;')
      self.instance[threading.current_thread()] = instance

  def cursor(self, *args) :
    return self._cursor(self.instance[threading.current_thread()], *args)

  def row_cursor(self) :
    return self.cursor(accessor.accessor_factory)

  @classmethod
  def set_default_db(cls, **args) :
    cls.default_db = os.path.join(args.get('root',''), args['db'])

class mixin(object) :
  def cursor(self) :
    return connection().cursor()

  def flush(self) :
    with self.cursor() as cursor :
      def insert(cb_id, when, level, severity, ident, subident, filename, line, msg) :
        cursor.execute('INSERT INTO message (log_id, level, severity, date, ident, subident, filename, line, msg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);', (self.log_id, level, severity, when.tv_sec, ident, subident, filename, line, msg))
      try :
        while (1) :
          insert(*self.queue.get(False))
      except Queue.Empty :
        pass # done

  def log(self, uid, hostname, abv, root, parent, description) :
    'create entry in log table'
    with self.cursor() as db :
      db.execute('INSERT INTO log (uid, root, parent, activity, block, version, description, hostname) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', (uid, root, parent, abv.activity, abv.block, abv.version, description, hostname))
      return db.lastrowid
