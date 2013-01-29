# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import mdb
import message

mdb.db.connection.set_default_db(db='../db/mdb.db')
mdb.mdb()

message.note('a note')
