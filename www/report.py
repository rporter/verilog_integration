# Copyright (c) 2012 Rich Porter - see LICENSE for further details

import bottle
import mdb
import message
import os.path

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-p', '--port', default='8080', help='port to serve on')
parser.add_option('-r', '--root', help='root directory for server')
options, values = parser.parse_args()

mdb.db.connection.set_default_db(db=os.path.join(options.root, '../db/mdb.db'))
mdb.mdb('mdb report')

static = os.path.join(options.root, 'static')

@bottle.get('/static/:filename#.*#')
def server_static(filename):
    return bottle.static_file(filename, root=static)

@bottle.route('/')
@bottle.route('/index.html')
def index_html() :
  return bottle.static_file('/index.html', root=static)

@bottle.get('/index/:variant')
def index(variant) :
  'SELECT log.*, message.severity, COUNT(*) AS error FROM log NATURAL JOIN message GROUP BY log_id, level;'
  import functools
  
  return '<h1>'+variant+'</h1>'

bottle.run(port=options.port)


