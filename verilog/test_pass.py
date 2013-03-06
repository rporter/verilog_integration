# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import mdb
import message

mdb.db.connection.set_default_db(db='../db/mdb.db')
mdb.mdb('test mdb pass')
message.message.verbosity(message.INT_DEBUG)
message.warning('a warning %(c)d', c=666)
message.note('a note')
message.success('should be success')
