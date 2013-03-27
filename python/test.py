# Copyright (c) 2012 Rich Porter - see LICENSE for further details

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
    mdb.db.connection.set_default_db(db=self.default_db)
    mdb.mdb(name)

    try :
      self.prologue()
    except :
      message.error("prologue failed because " + str(sys.exc_info()))

  def end_of_simulation(self) :
    'Wrapper for epilogue'
    message.debug('End of Simulation')
    try :
      self.epilogue()
    except :
      message.error("prologue failed because " + str(sys.exc_info()))
    # tidy up
    mdb.finalize_all()

