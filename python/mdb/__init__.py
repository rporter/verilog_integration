# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import atexit
import message
import os
import Queue
from accessor import *

class _mdb(object) :
  queue_limit = 10
  def __init__(self, description='none given', root=None, parent=None, level=message.ERROR) :
    self.commit_level = level
    self.queue = Queue.Queue()
    # mixin init
    self.init()
    # init filter
    self.filter_fn = self.filter
    # create log entry for this run
    self.log_id = self.log(os.getuid(), root, parent, description)
    # install callbacks
    message.emit_cbs.add('mdb', 1, self.add, self.finalize)
    atexit.register(self.flush)

  def filter(self, cb_id, level, filename) :
    return False

  def finalize(self) :
    'set test status & clean up'
    print message.status()
    self.flush()

  def flush(self) :
    try :
      while (1) :
        self.insert(*self.queue.get(False))
    except Queue.Empty :
      self.commit()

  def add(self, cb_id, when, level, severity, filename, line, msg) :
    # option to ignore certain messages
    if self.filter_fn(cb_id, level, filename) :
      return
    # add to queue
    self.queue.put([cb_id, when, level, severity, filename, line, msg])
    # flush to db if this message has high severity or there are a number of outstanding messages
    if level >= self.commit_level or self.queue.qsize() >= self.queue_limit :
      self.flush()

try :
  import _mysql as db
except ImportError :
  import _sqlite as db

class mdb(_mdb, db.mixin) :
  impl = db
