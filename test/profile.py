# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import coverage
import database
import mdb
import message

################################################################################

parser = message.reportOptionParser()
parser.add_option('-r', '--regression', default=None, help='Regression root id', action='append')
parser.add_option('-x', '--xml', help='xml out', default='profile_%d.xml')
options, values = parser.parse_args()

################################################################################

mdb.db.connection.set_default_db(db='../db/mdb.db')
mdb_conn=mdb.mdb('profile', activity='profiling')

################################################################################

if options.regression is None :
  # presume leftover args are ids
  options.regression = values

def cast(x) : 
  try :
    return int(x)
  except :
    return None

ids = [cast(o) for o in options.regression if cast(o)]

if not ids :
  message.fatal('No root ids provided')

message.information('profiling begins on %(ids)s', ids=str(ids))

################################################################################

coverage.messages.hush_creation()
# profile by run coverage
profile = database.cvgOrderedProfile(ids)
# do profile run
xml = profile.run()
# annotate optimized coverage result to this invocation
profile.insert(mdb_conn.log_id)

################################################################################

if options.xml :
  outfile = options.xml % int(profile.log_ids[0])
  message.information('dumping profiling to ' + outfile)
  with open(outfile, 'w') as desc :
    xml.write(desc)

message.success('profiling ends')
mdb.finalize_all()
