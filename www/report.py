# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import bottle
import cStringIO
import database
import json
import mdb
import message
import os.path
import sys
import time

################################################################################

parser = message.reportOptionParser()
parser.add_option('-p', '--port', default='8080', help='port to serve on')
options, values = parser.parse_args()

################################################################################

mdb.db.connection.set_default_db(db='../db/mdb.db', root=options.root)
m=mdb.mdb('mdb report')

# intercept log messages and redirect to our logger
def bottle_log(msg) :
  message.note(msg.strip())
def wsgi_log(self, format, *args) :
  severity = message.warning if args[-2] == '404' else message.debug
  severity(format.strip() % args)

bottle._stderr = bottle_log
from wsgiref.simple_server import WSGIRequestHandler
WSGIRequestHandler.log_message = wsgi_log

# location of static data
static = os.path.join(options.root, 'static')

################################################################################

class serve_something(object) :
  CONTENTTYPE='text/html'
  encapsulate=True

  def __init__(self) :
    self.page = cStringIO.StringIO()

  def __del__(self) :
    self.page.close()
    #database.connecting.database.close_all()

  def div(self) :
    return ' class="tab"'

  def GET(self, **args):
    self.headers()
    (self.wrap if self.encapsulate else self.time)(**args)
    return self.page.getvalue().replace('&', '&amp;')

  def wrap(self, **args) :
    self.page.write('<div%s>\n' % self.div())
    elapsed = self.time(**args)
    self.page.write('<p class="time" title="Generated in %(elapsed)0.2fs">Generated in %(elapsed)0.2fs</p>' % locals())
    self.page.write('</div>\n<b/>\n')

  def time(self, **args) :
    elapsed=time.time()
    self.doit(**args)
    elapsed = time.time()-elapsed
    message.note('page %(page)s served in %(time)0.2fs', page=bottle.request.fullpath, time=elapsed)
    return elapsed

  def doit(self, inv_id):
    self.page.write('no content')

  def headers(self):
    bottle.response.content_type = self.CONTENTTYPE

################################################################################

class index(serve_something, database.index) :
  CONTENTTYPE='application/json'
  encapsulate=False

  def doit(self, variant, limit=20, start=None, order='down'):
    json.dump(self.result(self.where(variant, limit, start, order)), self.page)

################################################################################

class msgs(serve_something, database.msgs) :
  CONTENTTYPE='application/json'
  encapsulate=False

  def doit(self, log_id):
    json.dump(self.result(log_id), self.page)

################################################################################

class rgr(serve_something, database.rgr) :
  CONTENTTYPE='application/json'
  encapsulate=False

  def doit(self, log_id):
    json.dump(self.result(log_id), self.page)

################################################################################

class cvg(serve_something, database.cvg) :
  CONTENTTYPE='application/json'
  encapsulate=False

  def doit(self, **kwargs):
    json.dump(self.result(**kwargs).points().json(), self.page)

################################################################################

class cvr(serve_something, database.cvr) :
  CONTENTTYPE='application/json'
  encapsulate=False

  def doit(self, log_id):
    json.dump(self.result(log_id), self.page)

################################################################################

class bkt(serve_something, database.bkt) :
  CONTENTTYPE='application/json'
  encapsulate=False

  def doit(self, **kwargs):
    json.dump(self.result(**kwargs), self.page)

################################################################################

@bottle.get('/static/<filename:path>')
def server_static(filename):
    return bottle.static_file(filename, root=static)

@bottle.route('/')
@bottle.route('/index.html')
def index_html() :
  return bottle.static_file('/index.html', root=static)

urls = (
  ('/index/:variant', index,),
  ('/index/:variant/<limit:int>', index,),
  ('/index/:variant/<limit:int>/<start:int>', index,),
  ('/index/:variant/<limit:int>/<order:re:(up|down)>', index,),
  ('/index/:variant/<limit:int>/<start:int>/<order:re:(up|down)>', index,),
  ('/msgs/<log_id:int>', msgs,),
  ('/rgr/<log_id:int>', rgr,),
  ('/cvg/<log_id:int>', cvg,),
  ('/cvg/<log_id:int>/<goal_id:int>', cvg,),
  ('/cvg/<log_id:int>/<cumulative:re:(cumulative)>', cvg,),
  ('/cvg/<log_id:int>/<goal_id:int>/<cumulative:re:(cumulative)>', cvg,),
  ('/cvr/<log_id:int>', cvr,),
  ('/bkt/<log_id:int>/<buckets>', bkt,),
)

for path, cls in urls:
  def serve(_cls) : 
    def fn(**args) : 
      return _cls().GET(**args)
    return fn
  bottle.route(path, name='route_'+cls.__name__)(serve(cls))

################################################################################

bottle.run(port=options.port)
# keyboardInterrupt gets us here ...
mdb.finalize_all()
