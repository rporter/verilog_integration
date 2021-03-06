# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import re

import coverage
import database
import mdb
import message

################################################################################

# ids can be given in the form range-or-id,+
# where range-or-id is [0-9]+(..[0-9]+)

parser = message.reportOptionParser()
parser.add_option('',   '--order', help='order sequence '+str(database.optimize.options.keys()), default=[], action='append', choices=database.optimize.options.keys())
parser.add_option('-r', '--regression', default=[], help='Regression root id', action='append')
parser.add_option('',   '--robust', default=False, help='Attempt to make test set robust', action='store_true')
parser.add_option('-t', '--test', default=[], help='Test id', action='append')
parser.add_option('',   '--threshold', default=0, help='Coverage threshold for "incr" order')
parser.add_option('-x', '--xml', help='xml out', default='optimize_%d.xml')
options, values = parser.parse_args()

################################################################################

mdb.db.connection.set_default_db(db='../db/mdb.db')
mdb_conn=mdb.mdb('optimize', activity='optimizing')

################################################################################

# generate lists
def to_list(args, values=[]) :
  def ignoring(arg) :
    message.warning('Ignoring %(arg)s', arg=arg)
  def cast(x) : 
    try :
      return int(x)
    except :
      ignoring(x)
      return None
  if isinstance(args, list) :
    return to_list(args[1:], to_list(args[0], values)) if args else values
  _args = args.split(',')
  if len(_args) > 1 : 
    return to_list(_args, values)
  _match = re.match('(?P<from>\d+)\.{2,3}(?P<to>\d+)', args)
  if _match :
    _to, _from = cast(_match.group('to')), cast(_match.group('from'))
    if _from > _to : _to, _from = _from, _to
    if _to is not None and _from is not None :
      return range(_from, _to + 1) + values
    ignoring(args)
    return values
  if cast(args) :
    return [cast(args), ] + values
  return values

################################################################################

if not options.order :
  options.order = ['cvg', ]

if options.regression is None :
  # presume leftover args are ids
  options.regression = values

regressions = to_list(options.regression)
tests       = to_list(options.test)

if not regressions and not tests :
  message.fatal('No invocations provided')

message.information('optimizing begins')

################################################################################

coverage.messages.hush_creation()
optimize_opts = {'threshold' : options.threshold, 'robust' : options.robust}

def iteration(ordering, iter_cnt=1, xml=None) :
  # use current optimization group if this is not first iteration
  order = ordering[0]
  message.note('Iteration %(iter_cnt)d uses "%(order)s"', **locals())
  if xml :
    opt = database.optimize.options[order](xml=xml, **optimize_opts)
  else :
    opt = database.optimize.options[order](regressions, tests, **optimize_opts)
  run = opt.run()
  optimize_opts['previous'] = opt
  if len(ordering) > 1 :
    return iteration(ordering[1:], iter_cnt+1, run)
  # always return last optimization run
  return opt, run

opt, xml = iteration(options.order)
# annotate optimized coverage result to this invocation
opt.insert(mdb_conn.log_id)

################################################################################

if options.xml :
  try :
    outfile = options.xml % (regressions[0] if regressions else tests[0])
  except :
    outfile = options.xml
  message.information('dumping optimize to ' + outfile)
  with open(outfile, 'w') as desc :
    xml.write(desc)

message.success('optimizing ends')
mdb.finalize_all()
