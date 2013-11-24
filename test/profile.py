# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import coverage
import database
import mdb
import message

################################################################################

parser = message.reportOptionParser()
parser.add_option('-r', '--regression', default=None, help='Regression root id', action='append')
parser.add_option('-t', '--test', default=None, help='Test id', action='append')
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

regressions = [cast(o) for o in options.regression if cast(o)]
tests       = [cast(o) for o in options.test if cast(o)]

if not regressions and not tests :
  message.fatal('No invocations provided')

message.information('profiling begins')

################################################################################

coverage.messages.hush_creation()
# profile by run coverage
profile = database.cvgOrderedProfile(regressions, tests)
# do profile run
xml = profile.run()
# annotate optimized coverage result to this invocation
profile.insert(mdb_conn.log_id)

################################################################################

if options.xml :
  outfile = options.xml % (regressions[0] if regressions else tests[0])
  message.information('dumping profiling to ' + outfile)
  with open(outfile, 'w') as desc :
    xml.write(desc)

message.success('profiling ends')
mdb.finalize_all()
