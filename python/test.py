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
  def __init__(self, name=None, db=None) :
    self.epilogue_cb = epilogue(self.end_of_simulation)
    name = name or self.name
    try :
      mdb.db.connection.set_default_db(db=self.default_db)
      mdb.mdb(name)
    except :
      message.note('Not using mdb because ' + str(sys.exc_info()))

    try :
      self.prologue()
    except :
      exc = sys.exc_info()
      message.error("prologue failed because " + str(exc[0]))
      self.traceback(exc[2])

  def end_of_simulation(self) :
    'Wrapper for epilogue'
    message.debug('End of Simulation')
    try :
      self.epilogue()
    except :
      exc = sys.exc_info()
      message.error("prologue failed because " + str(exc[0]))
      self.traceback(exc[2])
    # tidy up
    mdb.finalize_all()

  def traceback(self, _traceback) :
    import traceback
    for details in traceback.format_tb(_traceback) :
      for detail in details.strip('\n').split('\n') :
        message.warning(detail)
