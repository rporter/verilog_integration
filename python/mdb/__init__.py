# Copyright (c) 2012 Rich Porter - see LICENSE for further details

from accessor import *

class _mdb(object) :
  pass

try :
  import _mysql as db
except :
  import _sqlite as db

class mdb(_mdb, db.mixin) :
  impl = db
