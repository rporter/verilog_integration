# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import coverage
import database
import mdb
import message
import test

import os
import random
import subprocess

################################################################################

message.message.verbosity(message.INT_DEBUG)

################################################################################

choices = (False,)*10 + (True,)

class coverpoint(coverage.coverpoint) :
  'stuff'
  def __init__(self, name) :
    self.x   = self.add_axis('x', values=range(0, random.randrange(5, 10)))
    self.y   = self.add_axis('y', values=range(0, random.randrange(5, 10)))
    self.z   = self.add_axis('z', values=range(0, random.randrange(5, 10)))
    coverage.coverpoint.__init__(self, name=name)

  def define(self, bucket) :
    'set goal'
    # no dont cares or illegals
    bucket.default(goal=random.randrange(1, 100), dont_care=random.choice(choices), illegal=random.choice(choices))

################################################################################

class thistest(test.test) :
  activity='python'
  block='default'
  name='multiple coverage capacity test'
  insts=20
  children=20

  def prologue(self):
    # initialize all the same
    random.seed(self.cvr_seed)
    self.cpts = [coverpoint('%d random coverpoint' % i).cursor() for i in range(0, self.insts)]
    self.master_id = test.plusargs().master_id
  
  def epilogue(self) :

    def enqueue(cmd) :
      'just execute here'
      message.debug('enqueue %(cmd)s', cmd=cmd)
      result = subprocess.Popen(cmd.split(' '), env=dict(os.environ, MDB='root='+str(self.mdb.get_root())+',parent='+str(self.mdb.log_id))).wait()
      if result > 0 :
        message.warning('process %(cmd)s returned non zero %(result)d', cmd=cmd, result=result)

    # set per run seed
    random.seed(self.tst_seed)
    if self.is_master :
      # spawn some children
      for i in range(0, int(test.plusargs().children or self.children)) :
        enqueue('python ' + __file__ + ' +master_id=' + str(self.master_id or self.mdb.log_id)  + ' +cvr_seed='+str(self.cvr_seed)+' +tst_seed='+str(random.randint(0,1<<30)))
      database.rgr().result(self.mdb.log_id, self.mdb.is_root()).summary().summary()
    else :
      # ignore illegal bucket hits
      coverage.messages.CVG_200.level = message.IGNORE
      # make some coverage
      for i in range(0, 9999) :
        with random.choice(self.cpts) as cursor :
          for name, axis in cursor.point.axes() :
            cursor(**{name : random.choice(axis.get_values())})
          cursor.incr(random.randrange(10))
    # if everything else ok
    self.success()

  @property
  def test(self) :
    return thistest.filename()+'-'+str(hex(self.tst_seed))
  @coverage.lazyProperty
  def is_master(self) :
    try :
      return int(test.plusargs().master)
    except :
      return self.mdb.is_root()
  @coverage.lazyProperty
  def cvr_seed(self) :
    try :
      result = int(test.plusargs().cvr_seed, 0)
    except :
      result = 0
    message.information('Using %(seed)08x for cvr_seed', seed=result)
    return result
  @coverage.lazyProperty
  def tst_seed(self) :
    try :
      result = int(test.plusargs().tst_seed, 0)
    except :
      result = 0
    message.information('Using %(seed)08x for tst_seed', seed=result)
    return result

################################################################################

if __name__ == '__main__' :
  thistest()
