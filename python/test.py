# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import inspect
import os
import re
import sys

import coverage
import database
import mdb
import message

################################################################################

class plusargs(object) :
  argval = re.compile(r'^\+(?P<arg>[^+=]+)(?:[+=](?P<val>.*))?$')
  _instance = None
  class store(dict) :
    def __init__(self, *args) :
      dict.__init__(self, *args)
    def __getattr__(self, attr, default=None) :
      return self.get(attr, default)
  def __new__(self, *args, **kwargs) :
    if self._instance is None :
      self._instance = self.store([(arg.group('arg'), True if arg.group('val') is None else arg.group('val')) for arg in map(self.argval.match, sys.argv) if arg])
    return self._instance

################################################################################

# need to fix this test for non embeddedness
if open('/proc/self/cmdline').read().startswith('python') :
  # try to emulate verilog library
  class epilogue :
    def __init__(self, func) :
      pass

  class verilog :
    class info :
      product = 'Python'
      version = '.'.join(map(str, sys.version_info))
    class callback :
      @staticmethod
      def remove_all() :
        pass
    @staticmethod
    def vpiInfo() :
      return verilog.info
else :
  import verilog

  class epilogue(verilog.callback) :
    def __init__(self, func) :
      verilog.callback.__init__(self, name='epilogue callback', reason=verilog.callback.cbEndOfSimulation, func=func)

class test :
  default_db = '../db/mdb.db'
  activity=None
  block=None
  SUCCESS = message.ident('PYTN', 0, message.SUCCESS, 'test successful')
  FATAL   = message.ident('PYTN', 1, message.FATAL,   'test did not terminate correctly')
  START   = message.ident('PYTN', 2, message.NOTE,    'simulation starts using %(platform)s[%(version)s]' % {'platform':verilog.vpiInfo().product, 'version':verilog.vpiInfo().version})
  def __init__(self, name=None, activity=None, block=None, test=None, db=None) :
    self.epilogue_cb = epilogue(self.end_of_simulation)
    self.name = name or self.name
    self.test = test or self.test
    self.is_success = None
    self.coverage = None
    activity = activity or self.activity
    block = block or self.block
    message.terminate_cbs.add(self.name, 10, self.terminate, self.check_success)
    try :
      mdb.db.connection.set_default_db(db=self.get_db())
      self.mdb = mdb.mdb(self.name, activity=activity, block=block, test=self.test)
    except :
      message.note('Not using mdb because ' + str(sys.exc_info()))

    self.START()

    try :
      self.prologue()
    except :
      exc = sys.exc_info()
      message.error('prologue failed because ' + str(exc[0]))
      self.traceback(exc[2])

    # self.coverage *may* be assigned to root node in prologue,
    # if not check for one and use last one created if exists
    if self.coverage is None and coverage.hierarchy.populated() :
      self.coverage = coverage.hierarchy.last_root
    if self.coverage :
      if getattr(self, 'master_id', False) :
        database.insert.set_master(self.mdb.log_id, self.master_id)
        if getattr(self, 'master_chk', False) :
          # create the hierarchy from master id and verify congruent
          pass
      else :
        database.insert.write(self.coverage, self.mdb.log_id, database.upload.REFERENCE)

    # is verilog library synthetic?
    if verilog.vpiInfo().product == 'Python' :
      self.end_of_simulation()

  def get_db(self) :
    return plusargs().db or self.default_db

  def terminate(self, *args) :
    self.end_of_simulation(False)

  def end_of_simulation(self, run_epilogue=True) :
    'Wrapper for epilogue'
    message.debug('End of Simulation')
    if run_epilogue :
      try :
        self.epilogue()
      except :
        exc = sys.exc_info()
        message.error('epilogue failed because ' + str(exc[0]))
        self.traceback(exc[2])
      # remove fatal callback
      message.terminate_cbs.rm(self.name)
    else :
      message.note('Not running epilogue due to early terminate')
    # tidy up
    mdb.finalize_all()
    # coverage
    if self.coverage :
      database.insert.write(self.coverage, self.mdb.log_id, database.upload.RESULT)
    # remove callbacks
    verilog.callback.remove_all()

  def callback(self) :
    try :
      message.int_debug('test default callback for ' + self.mdb.abv.activity + ' ' + self.mdb.abv.block )
    except :
      # if we haven't set abv yet and above excepts
      message.int_debug('test default callback')

  def prologue(self) :
    message.warning('no prologue defined')
  def epilogue(self) :
    message.warning('no epilogue defined')

  @classmethod
  def pdb(self, traceback=None) :
    message.note('entering pdb command line')
    try :
      import pdb
      if traceback :
        pdb.post_mortem(traceback)
      else :
        pdb.set_trace()
      pass
    except :
      pass
    message.note('leaving pdb command line')
  debug = pdb # alias

  def fatal(self) :
    'Default fatal epilogue'
    self.FATAL()

  def check_success(self) :
    if self.is_success != True :
      self.fatal()

  def success(self) :
    'Generic success hook'
    if self.is_success is not None :
      message.warning('success() called after test issue (status : %(status)s)', status=str(self.is_success))
    self.is_success = True
    self.SUCCESS()

  def simulation_fatal(self) :
    'Wrapper for fatal epilogue'
    message.debug('Fatal - End of Simulation')
    return
    try :
      self.fatal()
    except :
      exc = sys.exc_info()
      message.error('fatal epilogue failed because ' + str(exc[0]))
      self.traceback(exc[2])

  def traceback(self, _traceback) :
    import traceback
    for details in traceback.format_tb(_traceback) :
      for detail in details.strip('\n').split('\n') :
        message.warning(detail)

  def plusarg_opt_int(self, name, default, fmt='08x') :
    'To get default/command line options'
    try :
      result = int(plusargs().get(name, default), 0)
    except :
      message.warning(str(sys.exc_info()))
      result = default
    message.information('Using %(result)'+fmt+' for option "%(name)s"', result=result, name=name)
    return result

  @classmethod
  def filename(cls) :
    return os.path.basename(inspect.getfile(cls))

  @property
  def test(self) :
    return self.filename()
