# Copyright (c) 2014 Rich Porter - see LICENSE for further details

import test_coverage_multiple
import random

################################################################################

class thistest(test_coverage_multiple.thistest) :
  def choice(self, opts) :
    v = random.betavariate(1, 3)
    return opts[int(v*len(opts))]

################################################################################

if __name__ == '__main__' :
  thistest()
