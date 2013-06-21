# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import mdb
import message
import sys
import verilog

class epilogue(verilog.callback) :
  def __init__(self, func) :
    verilog.callback.__init__(self, name='epilogue callback', reason=verilog.callback.cbEndOfSimulation, func=func)

class test(object) :
  default_db = '../db/mdb.db'
  activity=None
  block=None
  SUCCESS = message.ident('PYTN', 0, message.SUCCESS, 'test successful')
  FATAL   = message.ident('PYTN', 1, message.FATAL,   'something nasty happened')
  START   = message.ident('PYTN', 2, message.NOTE,    'simulation starts using %(platform)s[%(version)s]' % {'platform':verilog.vpiInfo().product, 'version':verilog.vpiInfo().version})
  def __init__(self, name=None, activity=None, block=None, db=None) :
    self.epilogue_cb = epilogue(self.end_of_simulation)
    self.name = name or self.name
    activity = activity or self.activity
    block = block or self.block
    message.terminate_cbs.add(self.name, 20, self.nop, self.nop)
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

  def get_db(self) :
    return verilog.plusargs().db or self.default_db

  def end_of_simulation(self) :
    'Wrapper for epilogue'
    message.debug('End of Simulation')
    try :
      self.epilogue()
    except :
      exc = sys.exc_info()
      message.error('epilogue failed because ' + str(exc[0]))
      self.traceback(exc[2])
    # remove fatal callback
    message.terminate_cbs.rm(self.name)
    # tidy up
    mdb.finalize_all()

  def nop(self) :
    pass

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

  def success(self) :
    'Generic success hook'
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
