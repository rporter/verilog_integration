# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import coverage
import mdb
import message
import sys

# need to fix this test for non embeddedness
if open('/proc/self/cmdline').read().startswith('python') :
  # try to emulate verilog library
  class epilogue :
    def __init__(self, func) :
      pass

  class verilog :
    class info :
      product = 'Not Specified'
      version = 'Not Specified'
    class args :
      db = None
    class callback :
      @staticmethod
      def remove_all() :
        pass
    @staticmethod
    def vpiInfo() :
      return verilog.info
    @staticmethod
    def plusargs() :
      return verilog.args
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
  def __init__(self, name=None, activity=None, block=None, db=None) :
    self.epilogue_cb = epilogue(self.end_of_simulation)
    self.name = name or self.name
    self.is_success = None
    activity = activity or self.activity
    block = block or self.block
    message.terminate_cbs.add(self.name, 10, self.terminate, self.check_success)
    try :
      mdb.db.connection.set_default_db(db=self.get_db())
      self.mdb = mdb.mdb(self.name, activity=activity, block=block)
    except :
      message.note('Not using mdb because ' + str(sys.exc_info()))

    self.START()

    try :
      self.prologue()
    except :
      exc = sys.exc_info()
      message.error('prologue failed because ' + str(exc[0]))
      self.traceback(exc[2])

    if coverage.hierarchy.populated() :
      coverage.insert.write(coverage.hierarchy, self.mdb.log_id, coverage.upload.REFERENCE)

    # is verilog library synthetic?
    if type(verilog) == type(test) :
      self.end_of_simulation()

  def get_db(self) :
    return verilog.plusargs().db or self.default_db

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
    if coverage.hierarchy.populated() :
      coverage.insert.write(coverage.hierarchy, self.mdb.log_id, coverage.upload.RESULT)
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
  def pdb(self) :
    message.note('entering pdb command line')
    try :
      import pdb
      pdb.set_trace()
      pass
    except :
      pass
    message.note('leaving pdb command line')

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
