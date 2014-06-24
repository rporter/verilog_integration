# Copyright (c) 2014 Rich Porter - see LICENSE for further details

import accessor
import decimal
import json as json_
import message
import MySQLdb, MySQLdb.cursors
import os.path
import Queue
import re
import socket
import sys
import threading

################################################################################

CURSOR=MySQLdb.cursors.Cursor # this is the default
DICT_CURSOR=MySQLdb.cursors.DictCursor
host = socket.gethostname()

class cursor(object) :
  HAS_UPDATE=True
  LAST_SQL='SELECT last_insert_id() AS rowid;'
  def __init__(self, connection, factory) :
    self.factory = factory
    self.connection = connection
    self.create()

  def retry(self, fn0, fn1=None) :
    for attempt in range(0, connection.RETRIES) :
      try :
        return fn0()
      except MySQLdb.OperationalError :
        if sys.exc_info()[1].args == (2006, 'MySQL server has gone away') :
          message.warning('MySQL connection lost; retrying')
          self.reconnect()
          if fn1 :
            fn1()
        else :
          raise
    message.warning('retried %(n)d times', n=connection.RETRIES)
    raise

  def _create(self) :
    self.db = self.connection.cursor(self.factory) if self.factory else self.connection.cursor()
  def create(self) :
    self.retry(self._create) 

  def _execute(self, *args) :
    def exe() :
      return self.db.execute(self.formatter(args[0]), *args[1:])
    return self.retry(exe, self._create) # don't retry the create

  def _executemany(self, *args) :
    def exe() :
      return self.db.executemany(self.formatter(args[0]), *args[1:])
    return self.retry(exe, self._create) # don't retry the create

  def formatter(self, fmt) :
    return re.sub(r'MIN(?=\((?=[^)]*,).+\))', 'LEAST', re.sub(r'MAX(?=\((?=[^)]*,).+\))', 'GREATEST', str(fmt)))

  def split(self, field) :
    return 'SUBSTRING_INDEX('+field+', "-", 1)'

  def info(self) :
    return self.connection.info()
  def warning_count(self) :
    return self.connection.warning_count()

class row_cursor(DICT_CURSOR) :
  def __init__(self, *args) :
    self.row_factory = self._row_factory # default row factory can be replaced
    DICT_CURSOR.__init__(self, *args)
  
  def __enter__(self) :
    return self
  
  def __exit__(self, exc_type, exc_value, traceback) :
    try :
      self.close()
    except :
      message.warning('cursor close raised exception %(exc)s', exc=sys.exc_info()[1])
  
  def __iter__(self) :
    self._check_executed()
    for row in self._rows[self.rownumber:] :
      yield self.row_factory(**row)
      self.rownumber += 1

  def fetchall(self) :
    return [self.row_factory(**row) for row in DICT_CURSOR.fetchall(self)]
  
  def fetchone(self) :
    try :
      return self.row_factory(**DICT_CURSOR.fetchone(self))
    except :
      return None
  
  @staticmethod
  def _row_factory(**kwargs) :
    return accessor.accessor(**kwargs)

class connection(object) :
  RETRIES=5
  default_host   = host
  default_port   = 3307
  default_user   = 'mdb'
  default_passwd = 'mdb'
  default_db     = 'mdb'
  def connect(self, *args, **kwargs) :
    try :
      self.db = kwargs['db']
    except KeyError:
      self.db = self.default_db
    try :
      instance = MySQLdb.connect(
        host=self.default_host,
        port=self.default_port,
        db=self.default_db,
        user=self.default_user,
        passwd=self.default_passwd
      )
      instance.autocommit(False)
    except :
      message.warning('Unable to connect to mysql db %(db)s at %(host)s:%(port)d because %(exc)s', db=self.db, host=self.default_host, port=self.default_port, exc=sys.exc_info()[0])
      return
    message.note("Connected to mysql db %(db)s at %(host)s:%(port)d for %(thread)s", db=self.default_db, host=self.default_host, port=self.default_port, thread=self.id())
    # this should be keyed on db too - but we don't used multiple databases currently
    self.instance[self.id()] = instance

  def row_cursor(self) :
    return self.cursor(row_cursor)

  @classmethod
  def set_default_db(cls, **args) :
    message.warning('set default db on mysql')

class json(json_.JSONEncoder) :
  'Serialize Decimal objects as integers'
  def default(self, obj):
    if isinstance(obj, decimal.Decimal):
      return int(obj)
    # Let the base class default method raise the TypeError
    return json_.JSONEncoder.default(self, obj)
  @classmethod
  def dump(cls, obj, f) :
    json_.dump(obj, f, cls=cls)
  @classmethod
  def dumps(cls, obj) :
    return json_.dumps(obj, cls=cls)
