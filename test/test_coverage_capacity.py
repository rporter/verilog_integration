# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import mdb
import coverage
import random

mdb.db.connection.set_default_db(db='../db/mdb.db')
mdb_conn = mdb.mdb('coverage capacity test')

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

bits=5
size=1<<bits

cpts = [big_coverpoint('%d big coverpoint' % i, size).cursor() for i in range(0,100)]
coverage.insert.write(coverage.hierarchy, mdb_conn.log_id, coverage.upload.REFERENCE)

for i in range(0, 99999) :
  random.choice(cpts)(x=random.getrandbits(bits), y=random.getrandbits(bits)).incr(random.randrange(10))

coverage.insert.write(coverage.hierarchy, mdb_conn.log_id, coverage.upload.RESULT)

mdb.finalize_all()
