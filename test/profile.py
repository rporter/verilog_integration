# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import xml.etree.ElementTree as etree

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

class xmlDump :
  def __init__(self) :
    self.root = etree.Element('profile')
    self.xml  = etree.ElementTree(self.root)
  def add(self, test) :
    node = etree.SubElement(self.root, 'test')
    for attr, value in test.log.iteritems() :
      etree.SubElement(node, attr).text = str(value)
  def write(self, file) :
    self.xml.write(file)

################################################################################

profile = database.cvgOrderedProfile(ids)
xml = xmlDump()

for incr in profile :
  message.information(' %(log_id)6d : %(rows)6d : %(hits)6d : %(cvg)s', log_id=incr.log.log_id, rows=incr.updates, hits=incr.hits, cvg=incr.status.description())
  if incr.hits :
    # this test contributed to overall coverage
    xml.add(incr)
  if incr.status.is_hit() :
    message.note('all coverage hit')
    break
message.information('coverage : ' + profile.status().description())

################################################################################

if options.xml :
  outfile = options.xml % int(profile.log_ids[0])
  message.information('dumping profiling to ' + outfile)
  with open(outfile, 'w') as desc :
    xml.write(desc)

message.success('profiling ends')
mdb.finalize_all()
