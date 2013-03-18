# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import mdb
import message

mdb.db.connection.set_default_db(db='../db/mdb.db')
mdb.mdb('test mdb')

message.int_debug('a int_debug %(c)d', c=69)
message.note('a note')

mdb.finalize_all()
