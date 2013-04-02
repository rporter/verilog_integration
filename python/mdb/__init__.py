# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import message
import os
import Queue
import socket
import threading
from accessor import *

class _mdb(object) :
  queue_limit = 10
  instances = []
  atexit = False
  class repeatingTimer(threading._Timer) :
    def run(self):
      while not self.finished.is_set():
        self.finished.wait(self.interval)
        self.function(*self.args, **self.kwargs)
    def running(self) :
      return not self.finished.is_set()

  def __init__(self, description='none given', root=None, parent=None, level=message.ERROR) :
    self.commit_level = level
    self.queue = Queue.Queue()
    # init filter
    self.filter_fn = self.filter
    # create log entry for this run
    self.log_id = self.log(os.getuid(), socket.gethostname(), root, parent, description)
    # install callbacks
    message.emit_cbs.add('mdb emit', 1, self.add, self.finalize)
    message.terminate_cbs.add('mdb terminate', 1, self.finalize, self.finalize)
    # flush queue every half second
    self.timer = self.repeatingTimer(0.5, self.flush)
    self.timer.start()
    # add to list of instances
    self.instances.append(self)

  def filter(self, cb_id, level, filename) :
    return False

  def finalize(self, inst=None) :
    'set test status & clean up'
    if self.timer.running() :
      message.debug('bye ...')
      self.timer.cancel()
    self.flush()

  def add(self, cb_id, when, level, severity, filename, line, msg) :
    # option to ignore certain messages
    if self.filter_fn(cb_id, level, filename) :
      return
    # add to queue
    self.queue.put([cb_id, when, level, severity, filename, line, msg])
    # flush to db if this message has high severity or there are a number of outstanding messages
    if level >= self.commit_level or self.queue.qsize() >= self.queue_limit :
      self.flush()

  @classmethod
  def finalize_all(cls) :
    for instance in cls.instances :
      instance.finalize()

try :
  import _mysql as db
except ImportError :
  import _sqlite as db

class mdb(_mdb, db.mixin) :
  impl = db

# short cut
finalize_all = mdb.finalize_all
