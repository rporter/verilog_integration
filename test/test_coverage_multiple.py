# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import coverage
import database
import mdb
import message
import test

import os
import random
import subprocess

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
  insts=2
  children=2

  def prologue(self):
    # initialize all the same
    self.cvr_seed = int(test.plusargs().cvr_seed or 0)
    random.seed(self.cvr_seed)
    self.cpts = [coverpoint('%d random coverpoint' % i).cursor() for i in range(0, self.insts)]
    self.master_id = test.plusargs().master_id
    self.is_master = test.plusargs().master or self.mdb.is_root()
    print self.is_master
  
  def epilogue(self) :

    def enqueue(cmd) :
      'just execute here'
      message.debug('enqueue %(cmd)s', cmd=cmd)
      result = subprocess.Popen(cmd.split(' '), env=dict(os.environ, MDB='root='+str(self.mdb.get_root())+',parent='+str(self.mdb.log_id))).wait()
      if result > 0 :
        message.warning('process %(cmd)s returned non zero %(result)d', cmd=cmd, result=result)

    # set per run seed
    random.seed(test.plusargs().tst_seed or 0)
    if self.is_master :
      # spawn some children
      for i in range(0, self.children) :
        enqueue('python ' + __file__ + ' +master_id=' + str(self.master_id or self.mdb.log_id)  + ' +cvr_seed='+str(self.cvr_seed)+' +tst_seed='+str(random.randint(0,1<<30)))
      database.rgr().result(self.mdb.log_id, self.mdb.is_root()).summary().summary()
    else :
      # ignore illegal bucket hits
      coverage.messages.CVG_200.level = message.IGNORE
      # make some coverage
      for i in range(0, 99999) :
        with random.choice(self.cpts) as cursor :
          for name, axis in cursor.point.axes() :
            cursor(**{name : random.choice(axis.get_values())})
          cursor.incr(random.randrange(10))
    # if everything else ok
    self.success()

################################################################################

if __name__ == '__main__' :
  thistest()
