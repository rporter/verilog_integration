# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import mdb
import coverage
import test
import random

class big_coverpoint(coverage.coverpoint) :
  'bits toggle'
  def __init__(self, name, size) :
    self.x   = self.add_axis('x', values=range(0, size))
    self.y   = self.add_axis('y', values=range(0, size))
    coverage.coverpoint.__init__(self, name=name)

  def define(self, bucket) :
    'set goal'
    # no dont cares or illegals
    bucket.default(goal=10)

################################################################################

class thistest(test.test) :
  bits=5
  size=1<<bits
  activity='python'
  block='default'
  name='coverage capacity test'

  def prologue(self):
    cpts = [big_coverpoint('%d big coverpoint' % i, self.size).cursor() for i in range(0,100)]

    for i in range(0, 99999) :
      random.choice(cpts)(x=random.getrandbits(self.bits), y=random.getrandbits(self.bits)).incr(random.randrange(10))
  def epilogue(self) :
    self.success()

################################################################################

if __name__ == '__main__' :
  thistest()
