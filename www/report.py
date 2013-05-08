# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import bottle
import cStringIO
import itertools
import json
import mdb
import message
import os.path
import pwd
import sys
import time

################################################################################

def increase_verbosity(option, opt, value, parser) :
  parser.values.verbosity -= 1

parser = message.reportOptionParser()
parser.add_option('-p', '--port', default='8080', help='port to serve on')
parser.add_option('-r', '--root', help='root directory for server')
parser.add_option('-v', '', help='increase verbosity', action='callback', callback=increase_verbosity)
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
    message.note('page %(page)s served in %(time)0.2fs', page=bottle.request.url, time=elapsed)
    return elapsed

  def doit(self, inv_id):
    self.page.write('no content')

  def headers(self):
    bottle.response.content_type = self.CONTENTTYPE

################################################################################

class index(serve_something) :
  # stolen from python website
  # and mashed around a bit
  class groupby:
    def __init__(self, iterable, keyfunc=None, keyfact=None, grpfact=None):
      self.it = iter(iterable)
      self.tgtkey = self.currkey = self.currvalue = object()
      self.keyfunc, self.keyfact, self.grpfact = keyfunc, keyfact, grpfact
    def __iter__(self):
      return self
    def __next__(self):
      while self.currkey == self.tgtkey:
        self.currvalue = next(self.it)    # Exit on StopIteration
        self.currkey = self.keyfunc(self.currvalue)
      self.tgtkey = self.currkey
      return self.keyfact(self)
 
    next=__next__
    def _grouper(self, tgtkey):
      while self.currkey == tgtkey:
        yield self.grpfact(self)
        self.currvalue = next(self.it)    # Exit on StopIteration
        self.currkey = self.keyfunc(self.currvalue)

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  class result(dict) :

    class messages(list) :
      class message(dict) :
        def __init__(self, values) :
          dict.__init__(self, values)
        def __getattr__(self, attr) :
          return self[attr]
        @property
        def isfail(self) :
          return self.level >= message.ERROR
      def __init__(self, msgs) :
        list.__init__(self, map(self.message, msgs))
        self.sort(key=lambda k : k.level, reverse=True)
      def __getattr__(self, attr) :
        attr = attr.upper()
        for msg in self :
          if msg.severity == attr : return msg
        return None

    def __init__(self, log, msgs, **kwargs) :
      dict.__init__(self, log = log, msgs = self.messages(msgs))
      self.update(status=self.compute_status())

    def __getattr__(self, attr) :
      try : 
        return self[attr]
      except :
        return self.msgs.__getattr__(attr)

    def compute_status(self) :
      'compute status'
      if self.first.isfail :
        return dict(status='FAIL', reason='('+self.first.severity+') '+self.first.msg)
      if self.SUCCESS :
        if self.SUCCESS.count == 1 :
	  return dict(status='PASS', reason=self.SUCCESS.msg)
        else :
          return dict(status='FAIL', reason='Too many SUCCESSes (%d)' % self.SUCCESS.count)
      return dict(status='FAIL', reason='No SUCCESS')

    @property
    def first(self) :
      return self.msgs[0]

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  class limit :
    def __init__(self, finish=None, start=None) :
      self.start, self.finish = start, finish
    def __str__(self) :
      if self.finish :
        if self.start :
          return "LIMIT %(start)d, %(finish)d" % self.__dict__
        else :
          return "LIMIT %(finish)d" % self.__dict__
      return ""

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  CONTENTTYPE='application/json'
  encapsulate=False
  order = 'log_id, msg_id, level ASC'
  def doit(self, variant, start=0, finish=20):
    self.json(self.where(variant), self.limit(finish, start))

  def json(self, where, limit) :
    json.dump([self.result(log, msgs) for log, msgs in self.groupby(self.execute(where, limit), lambda x : x.log_id, self.keyfact, self.grpfact)], self.page)

  def where(self, variant) :
    if variant == 'sngl' :
      return 'SELECT l0.*, null as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) where l1.log_id is null and l0.root is null'
    elif variant == 'rgr' :
      return 'SELECT l0.*, count(l1.log_id) as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) group by l0.log_id having l1.log_id is not null'
    else :
      return 'SELECT l0.*, count(l1.log_id) as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) group by l0.log_id'

  def execute(self, where, limit) :
    with mdb.db.connection().row_cursor() as db :
      db.execute('SELECT log.*, message.*, COUNT(*) AS count FROM (%s ORDER BY log_id DESC %s) AS log NATURAL LEFT JOIN message GROUP BY log_id, level ORDER BY %s;' % (where, str(limit), self.order))
      return db.fetchall()

  @staticmethod
  def keyfact(self) :
    'key factory for grouping'
    return [dict(user=pwd.getpwuid(self.currvalue.uid).pw_name, **self.currvalue), self._grouper(self.tgtkey)]
  @staticmethod
  def grpfact(self) :
    'group factory for grouping'
    return dict(level=self.currvalue.level, severity=self.currvalue.severity, msg=self.currvalue.msg, count=self.currvalue.count)

################################################################################

class msgs(serve_something) :
  CONTENTTYPE='application/json'
  encapsulate=False
  def doit(self, log_id):
    db = mdb.db.connection().row_cursor()
    message.debug('retrieving %(log_id)s messages', log_id=log_id)
    db.execute('SELECT * FROM message WHERE log_id = %(log_id)s;' % locals())
    json.dump(db.fetchall(), self.page)
    return

################################################################################

class rgr(index) :
  order = 'parent ASC, log_id, msg_id, level ASC'
  
  def doit(self, log_id):
    self.json('SELECT l0.*, count(l1.log_id) as children FROM log as l0 left join log as l1 on (l0.log_id = l1.root) WHERE l0.log_id = %(log_id)s or l0.root = %(log_id)s group by l0.log_id' % locals(), self.limit())

################################################################################

@bottle.get('/static/:filename#.*#')
def server_static(filename):
    return bottle.static_file(filename, root=static)

@bottle.route('/')
@bottle.route('/index.html')
def index_html() :
  return bottle.static_file('/index.html', root=static)

urls = (
  ('/index/:variant', index,),
  ('/msgs/:log_id', msgs,),
  ('/rgr/:log_id', rgr,),
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
