# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import mdb
import message
import coverage
import test
import random

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

  def prologue(self):
    # initialize all the same
    random.seed(test.plusargs().cvr_seed or 0)
    cpts = [coverpoint('%d random coverpoint' % i).cursor() for i in range(0, self.insts)]

    random.seed(test.plusargs().tst_seed or 0)
    
    self.master_id = test.plusargs().master_id
    if self.master_id :
      # make some coverage
      coverage.messages.CVG_200.level = message.IGNORE
      for i in range(0, 99999) :
        with random.choice(cpts) as cursor :
          for name, axis in cursor.point.axes() :
            cursor(**{name : random.choice(axis.get_values())})
          cursor.incr(random.randrange(10))
    else :
      self.is_master = True

  def epilogue(self) :
    self.success()

################################################################################

if __name__ == '__main__' :
  thistest()
